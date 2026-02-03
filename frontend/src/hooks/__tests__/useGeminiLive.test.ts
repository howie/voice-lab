/**
 * useGeminiLive Hook Tests
 *
 * Verifies WebSocket message handling, specifically:
 * - String-based messages are parsed correctly
 * - Blob-based messages are converted to text before parsing
 * - Invalid messages log errors without throwing
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'

import { useGeminiLive } from '../useGeminiLive'

// jsdom's Blob doesn't implement .text() — polyfill it for tests
if (typeof Blob.prototype.text !== 'function') {
  Blob.prototype.text = function () {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(reader.error)
      reader.readAsText(this)
    })
  }
}

// =============================================================================
// Mock WebSocket
// =============================================================================

type WSEventHandler = ((ev: Event) => void) | null
type WSMessageHandler = ((ev: MessageEvent) => void) | null
type WSCloseHandler = ((ev: CloseEvent) => void) | null

class MockWebSocket {
  static OPEN = 1
  static CLOSED = 3

  readyState = MockWebSocket.OPEN
  onopen: WSEventHandler = null
  onmessage: WSMessageHandler = null
  onerror: WSEventHandler = null
  onclose: WSCloseHandler = null

  send = vi.fn()
  close = vi.fn()

  // Helpers to simulate server messages
  simulateOpen() {
    this.onopen?.(new Event('open'))
  }

  simulateMessage(data: string | Blob) {
    this.onmessage?.(new MessageEvent('message', { data }))
  }

  simulateClose(code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close', { code, reason }))
  }
}

let mockWsInstance: MockWebSocket

beforeEach(() => {
  mockWsInstance = new MockWebSocket()
  vi.stubGlobal(
    'WebSocket',
    vi.fn(() => mockWsInstance)
  )
})

afterEach(() => {
  vi.restoreAllMocks()
})

// =============================================================================
// Helpers
// =============================================================================

const TEST_CONFIG = {
  apiKey: 'test-key',
  wsUrl: 'wss://example.com/ws',
  model: 'gemini-2.5-flash-native-audio-preview',
  voice: 'Kore',
}

function connectHook() {
  const callbacks = {
    onAudioData: vi.fn(),
    onInputTranscript: vi.fn(),
    onOutputTranscript: vi.fn(),
    onTurnComplete: vi.fn(),
    onInterrupted: vi.fn(),
    onStatusChange: vi.fn(),
  }

  const { result } = renderHook(() => useGeminiLive(callbacks))

  act(() => {
    result.current.connect(TEST_CONFIG)
  })

  // Simulate WebSocket open → setup sent
  act(() => {
    mockWsInstance.simulateOpen()
  })

  return { result, callbacks }
}

// =============================================================================
// Tests
// =============================================================================

describe('useGeminiLive', () => {
  describe('message parsing', () => {
    it('should parse string-based JSON messages', async () => {
      const { result } = connectHook()

      const setupMsg = JSON.stringify({ setupComplete: true })

      act(() => {
        mockWsInstance.simulateMessage(setupMsg)
      })

      expect(result.current.status).toBe('connected')
    })

    it('should parse Blob-based JSON messages', async () => {
      const { result } = connectHook()

      const setupMsg = new Blob([JSON.stringify({ setupComplete: true })], {
        type: 'application/json',
      })

      act(() => {
        mockWsInstance.simulateMessage(setupMsg)
      })

      // Blob.text() resolves asynchronously via FileReader
      await waitFor(() => {
        expect(result.current.status).toBe('connected')
      })
    })

    it('should handle invalid string messages without throwing', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      connectHook()

      act(() => {
        mockWsInstance.simulateMessage('not valid json')
      })

      expect(consoleSpy).toHaveBeenCalledWith(
        '[GeminiLive] Failed to parse message:',
        expect.any(SyntaxError)
      )

      consoleSpy.mockRestore()
    })

    it('should handle invalid Blob messages without throwing', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      connectHook()

      const badBlob = new Blob(['not valid json'])

      act(() => {
        mockWsInstance.simulateMessage(badBlob)
      })

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          '[GeminiLive] Failed to parse Blob message:',
          expect.any(SyntaxError)
        )
      })

      consoleSpy.mockRestore()
    })
  })

  describe('serverContent handling', () => {
    it('should call onInputTranscript for input transcription', async () => {
      const { callbacks } = connectHook()

      const msg = JSON.stringify({
        serverContent: {
          inputTranscription: { text: 'hello world' },
        },
      })

      act(() => {
        mockWsInstance.simulateMessage(msg)
      })

      expect(callbacks.onInputTranscript).toHaveBeenCalledWith('hello world')
    })

    it('should call onOutputTranscript for output transcription', () => {
      const { callbacks } = connectHook()

      const msg = JSON.stringify({
        serverContent: {
          outputTranscription: { text: 'response text' },
        },
      })

      act(() => {
        mockWsInstance.simulateMessage(msg)
      })

      expect(callbacks.onOutputTranscript).toHaveBeenCalledWith('response text')
    })

    it('should call onAudioData for inline audio data', () => {
      const { callbacks } = connectHook()

      const msg = JSON.stringify({
        serverContent: {
          modelTurn: {
            parts: [{ inlineData: { data: 'base64audiodata' } }],
          },
        },
      })

      act(() => {
        mockWsInstance.simulateMessage(msg)
      })

      expect(callbacks.onAudioData).toHaveBeenCalledWith('base64audiodata')
    })

    it('should call onTurnComplete on turn complete', () => {
      const { callbacks } = connectHook()

      const msg = JSON.stringify({
        serverContent: { turnComplete: true },
      })

      act(() => {
        mockWsInstance.simulateMessage(msg)
      })

      expect(callbacks.onTurnComplete).toHaveBeenCalled()
    })

    it('should call onInterrupted on interruption', () => {
      const { callbacks } = connectHook()

      const msg = JSON.stringify({
        serverContent: { interrupted: true },
      })

      act(() => {
        mockWsInstance.simulateMessage(msg)
      })

      expect(callbacks.onInterrupted).toHaveBeenCalled()
    })

    it('should handle Blob serverContent messages identically to string', async () => {
      const { callbacks } = connectHook()

      const payload = {
        serverContent: {
          inputTranscription: { text: 'blob transcript' },
          modelTurn: {
            parts: [{ inlineData: { data: 'blobAudio==' } }],
          },
          turnComplete: true,
        },
      }

      const blob = new Blob([JSON.stringify(payload)])

      act(() => {
        mockWsInstance.simulateMessage(blob)
      })

      await waitFor(() => {
        expect(callbacks.onInputTranscript).toHaveBeenCalledWith('blob transcript')
      })
      expect(callbacks.onAudioData).toHaveBeenCalledWith('blobAudio==')
      expect(callbacks.onTurnComplete).toHaveBeenCalled()
    })
  })

  describe('connection lifecycle', () => {
    it('should set status to connected after setupComplete', () => {
      const { result } = connectHook()

      act(() => {
        mockWsInstance.simulateMessage(JSON.stringify({ setupComplete: true }))
      })

      expect(result.current.status).toBe('connected')
    })

    it('should set status to disconnected after close', () => {
      const { result } = connectHook()

      act(() => {
        mockWsInstance.simulateClose()
      })

      expect(result.current.status).toBe('disconnected')
    })

    it('should disconnect and clean up', () => {
      const { result } = connectHook()

      act(() => {
        result.current.disconnect()
      })

      expect(mockWsInstance.close).toHaveBeenCalled()
      expect(result.current.status).toBe('disconnected')
    })
  })
})
