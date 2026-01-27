/**
 * Audio Processor Tests
 *
 * Tests for the audio processor abstraction layer that handles
 * AudioWorklet (modern) and ScriptProcessorNode (fallback) APIs.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import {
  createAudioProcessor,
  supportsAudioWorklet,
} from '../audioProcessor'

// =============================================================================
// Mocks
// =============================================================================

// Mock MessagePort
class MockMessagePort {
  onmessage: ((event: MessageEvent) => void) | null = null
  close = vi.fn()
  postMessage = vi.fn()
}

// Mock AudioWorkletNode
class MockAudioWorkletNode {
  port = new MockMessagePort()
  connect = vi.fn()
  disconnect = vi.fn()

  constructor(_context: AudioContext, _name: string) {
    // Constructor
  }
}

// Mock ScriptProcessorNode
class MockScriptProcessorNode {
  onaudioprocess: ((event: AudioProcessingEvent) => void) | null = null
  connect = vi.fn()
  disconnect = vi.fn()
}

// Mock MediaStreamAudioSourceNode
class MockMediaStreamAudioSourceNode {
  connect = vi.fn()
  disconnect = vi.fn()
}

// Mock AudioWorklet
class MockAudioWorklet {
  addModule = vi.fn().mockResolvedValue(undefined)
}

// Factory to create mock AudioContext with audioWorklet support
function createMockAudioContextWithWorklet() {
  const mockWorklet = new MockAudioWorklet()
  const context = {
    audioWorklet: mockWorklet,
    sampleRate: 16000,
    destination: {},
    createScriptProcessor: vi.fn(() => new MockScriptProcessorNode()),
  }
  return context
}

// Factory to create mock AudioContext without audioWorklet support
function createMockAudioContextWithoutWorklet() {
  return {
    sampleRate: 16000,
    destination: {},
    createScriptProcessor: vi.fn(() => new MockScriptProcessorNode()),
  }
}

// =============================================================================
// Tests
// =============================================================================

describe('audioProcessor', () => {
  // Store original globals
  const originalAudioContext = globalThis.AudioContext
  const originalAudioWorkletNode = globalThis.AudioWorkletNode

  afterEach(() => {
    // Restore originals
    globalThis.AudioContext = originalAudioContext
    globalThis.AudioWorkletNode = originalAudioWorkletNode
    vi.restoreAllMocks()
  })

  describe('supportsAudioWorklet', () => {
    it('should return true when AudioWorklet is supported', () => {
      // Create a mock class with audioWorklet on prototype
      function MockAudioContext() {
        // Constructor
      }
      MockAudioContext.prototype.audioWorklet = {}

      globalThis.AudioContext = MockAudioContext as unknown as typeof AudioContext

      expect(supportsAudioWorklet()).toBe(true)
    })

    it('should return false when AudioWorklet is not supported', () => {
      // Create a mock class without audioWorklet on prototype
      function MockAudioContext() {
        // Constructor
      }

      globalThis.AudioContext = MockAudioContext as unknown as typeof AudioContext

      expect(supportsAudioWorklet()).toBe(false)
    })

    it('should return false when AudioContext is undefined', () => {
      // @ts-expect-error - Testing undefined case
      globalThis.AudioContext = undefined

      expect(supportsAudioWorklet()).toBe(false)
    })
  })

  describe('createAudioProcessor', () => {
    describe('with AudioWorklet support', () => {
      beforeEach(() => {
        // Setup AudioWorklet support on prototype
        function MockAudioContext() {
          // Constructor
        }
        MockAudioContext.prototype.audioWorklet = {}

        globalThis.AudioContext = MockAudioContext as unknown as typeof AudioContext
        globalThis.AudioWorkletNode = MockAudioWorkletNode as unknown as typeof AudioWorkletNode
      })

      it('should create AudioWorkletNode when supported', async () => {
        const mockContext = createMockAudioContextWithWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        // Verify worklet module was loaded
        expect(mockContext.audioWorklet.addModule).toHaveBeenCalledWith(
          expect.stringContaining('worklets/audio-processor.js')
        )

        // Verify source was connected
        expect(mockSource.connect).toHaveBeenCalled()

        // Verify cleanup function exists
        expect(typeof result.cleanup).toBe('function')

        result.cleanup()
      })

      it('should use BASE_URL for worklet path', async () => {
        const mockContext = createMockAudioContextWithWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        // Should include path to worklet
        const addModuleCall = mockContext.audioWorklet.addModule.mock.calls[0][0] as string
        expect(addModuleCall).toMatch(/worklets\/audio-processor\.js$/)
      })

      it('should receive audio data via MessagePort', async () => {
        const mockContext = createMockAudioContextWithWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        // Get the worklet node and simulate message
        const workletNode = result.node as unknown as MockAudioWorkletNode
        const mockAudioData = new Float32Array([0.1, 0.2, 0.3])

        // Simulate message from worklet thread
        workletNode.port.onmessage?.({
          data: {
            type: 'audio',
            audioData: mockAudioData,
            sampleRate: 16000,
          },
        } as MessageEvent)

        expect(onAudioChunk).toHaveBeenCalledWith(
          expect.any(Float32Array),
          16000
        )

        result.cleanup()
      })

      it('should ignore non-audio messages', async () => {
        const mockContext = createMockAudioContextWithWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        const workletNode = result.node as unknown as MockAudioWorkletNode

        // Simulate non-audio message
        workletNode.port.onmessage?.({
          data: {
            type: 'other',
            someData: 'test',
          },
        } as MessageEvent)

        expect(onAudioChunk).not.toHaveBeenCalled()

        result.cleanup()
      })

      it('should cleanup MessagePort on cleanup()', async () => {
        const mockContext = createMockAudioContextWithWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        const workletNode = result.node as unknown as MockAudioWorkletNode

        result.cleanup()

        // Verify cleanup actions
        expect(workletNode.port.onmessage).toBeNull()
        expect(workletNode.port.close).toHaveBeenCalled()
        expect(workletNode.disconnect).toHaveBeenCalled()
      })

      it('should fallback to ScriptProcessor when worklet loading fails', async () => {
        const mockContext = createMockAudioContextWithWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        // Make addModule fail
        mockContext.audioWorklet.addModule = vi.fn().mockRejectedValue(new Error('Failed to load'))

        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        // Should fallback to ScriptProcessor
        expect(mockContext.createScriptProcessor).toHaveBeenCalledWith(1024, 1, 1)
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('falling back'),
          expect.any(Error)
        )

        result.cleanup()
      })
    })

    describe('without AudioWorklet support (fallback)', () => {
      beforeEach(() => {
        // Setup without AudioWorklet support on prototype
        function MockAudioContext() {
          // Constructor
        }

        globalThis.AudioContext = MockAudioContext as unknown as typeof AudioContext
      })

      it('should create ScriptProcessorNode when AudioWorklet not supported', async () => {
        const mockContext = createMockAudioContextWithoutWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        // Should use ScriptProcessor with buffer size 1024
        expect(mockContext.createScriptProcessor).toHaveBeenCalledWith(1024, 1, 1)
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('AudioWorklet not supported')
        )

        result.cleanup()
      })

      it('should receive audio data via onaudioprocess', async () => {
        const mockContext = createMockAudioContextWithoutWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        vi.spyOn(console, 'warn').mockImplementation(() => {})

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        const processor = result.node as unknown as MockScriptProcessorNode

        // Simulate audio process event
        const mockAudioData = new Float32Array([0.1, 0.2, 0.3])
        const mockEvent = {
          inputBuffer: {
            getChannelData: vi.fn().mockReturnValue(mockAudioData),
          },
        } as unknown as AudioProcessingEvent

        processor.onaudioprocess?.(mockEvent)

        expect(onAudioChunk).toHaveBeenCalledWith(
          expect.any(Float32Array),
          16000
        )

        result.cleanup()
      })

      it('should cleanup onaudioprocess on cleanup()', async () => {
        const mockContext = createMockAudioContextWithoutWorklet()
        const mockSource = new MockMediaStreamAudioSourceNode() as unknown as MediaStreamAudioSourceNode
        const onAudioChunk = vi.fn()

        vi.spyOn(console, 'warn').mockImplementation(() => {})

        const result = await createAudioProcessor({
          audioContext: mockContext as unknown as AudioContext,
          source: mockSource,
          onAudioChunk,
        })

        const processor = result.node as unknown as MockScriptProcessorNode

        result.cleanup()

        expect(processor.onaudioprocess).toBeNull()
        expect(processor.disconnect).toHaveBeenCalled()
      })
    })
  })
})
