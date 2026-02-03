/**
 * Audio processor abstraction layer.
 * Feature: 004-interaction-module
 *
 * Provides a unified interface for audio processing, automatically selecting
 * AudioWorklet (modern) or ScriptProcessorNode (fallback) based on browser support.
 */

// =============================================================================
// Types
// =============================================================================

export interface AudioProcessorOptions {
  /** AudioContext instance */
  audioContext: AudioContext
  /** Media stream source node */
  source: MediaStreamAudioSourceNode
  /** Callback for audio chunks */
  onAudioChunk: (chunk: Float32Array, sampleRate: number) => void
}

export interface AudioProcessorResult {
  /** The audio node (AudioWorkletNode or ScriptProcessorNode) */
  node: AudioWorkletNode | ScriptProcessorNode
  /** Cleanup function to release resources */
  cleanup: () => void
}

// =============================================================================
// Feature Detection
// =============================================================================

/**
 * Check if AudioWorklet is supported in the current browser
 */
export function supportsAudioWorklet(): boolean {
  return (
    typeof AudioContext !== 'undefined' &&
    'audioWorklet' in AudioContext.prototype
  )
}

// =============================================================================
// AudioWorklet Implementation
// =============================================================================

/**
 * Create an AudioWorkletNode-based processor (modern, low-latency)
 */
async function createWorkletProcessor(
  audioContext: AudioContext,
  source: MediaStreamAudioSourceNode,
  onAudioChunk: (chunk: Float32Array, sampleRate: number) => void
): Promise<AudioProcessorResult> {
  // Use BASE_URL for correct path in sub-path deployments
  const workletPath = `${import.meta.env.BASE_URL}worklets/audio-processor.js`
  await audioContext.audioWorklet.addModule(workletPath)

  const workletNode = new AudioWorkletNode(audioContext, 'audio-processor')

  // Receive audio data from worklet thread via MessagePort
  workletNode.port.onmessage = (event: MessageEvent) => {
    if (event.data.type === 'audio') {
      const chunk = new Float32Array(event.data.audioData)
      onAudioChunk(chunk, event.data.sampleRate)
    }
  }

  // Connect: source -> workletNode -> destination
  source.connect(workletNode)
  workletNode.connect(audioContext.destination)

  return {
    node: workletNode,
    cleanup: () => {
      // 1. Signal worklet to stop processing (returns false from process())
      try {
        workletNode.port.postMessage({ type: 'stop' })
      } catch {
        // Port may already be closed
      }

      // 2. Remove event listener to prevent residual messages
      workletNode.port.onmessage = null

      // 3. Close MessagePort
      workletNode.port.close()

      // 4. Disconnect node
      workletNode.disconnect()
    },
  }
}

// =============================================================================
// ScriptProcessor Fallback Implementation
// =============================================================================

/**
 * Create a ScriptProcessorNode-based processor (fallback for older browsers)
 * @deprecated ScriptProcessorNode is deprecated, use AudioWorklet when possible
 */
function createScriptProcessor(
  audioContext: AudioContext,
  source: MediaStreamAudioSourceNode,
  onAudioChunk: (chunk: Float32Array, sampleRate: number) => void
): AudioProcessorResult {
  // Match worklet buffer size for consistent behavior
  const bufferSize = 1024
  const processor = audioContext.createScriptProcessor(bufferSize, 1, 1)

  processor.onaudioprocess = (event: AudioProcessingEvent) => {
    const audioData = event.inputBuffer.getChannelData(0)
    onAudioChunk(new Float32Array(audioData), audioContext.sampleRate)
  }

  // Connect: source -> processor -> destination
  source.connect(processor)
  processor.connect(audioContext.destination)

  return {
    node: processor,
    cleanup: () => {
      processor.onaudioprocess = null
      processor.disconnect()
    },
  }
}

// =============================================================================
// Main Factory Function
// =============================================================================

/**
 * Create an audio processor with automatic fallback.
 * Prefers AudioWorklet for better performance, falls back to ScriptProcessorNode.
 *
 * @param options - Configuration options
 * @returns Audio processor result with cleanup function
 *
 * @example
 * ```typescript
 * const processor = await createAudioProcessor({
 *   audioContext,
 *   source,
 *   onAudioChunk: (chunk, sampleRate) => {
 *     // Handle audio data
 *   }
 * })
 *
 * // Later, cleanup
 * processor.cleanup()
 * ```
 */
export async function createAudioProcessor(
  options: AudioProcessorOptions
): Promise<AudioProcessorResult> {
  const { audioContext, source, onAudioChunk } = options

  if (supportsAudioWorklet()) {
    try {
      return await createWorkletProcessor(audioContext, source, onAudioChunk)
    } catch (error) {
      console.warn(
        'Failed to load AudioWorklet, falling back to ScriptProcessorNode:',
        error
      )
      return createScriptProcessor(audioContext, source, onAudioChunk)
    }
  } else {
    console.warn(
      'AudioWorklet not supported, falling back to ScriptProcessorNode'
    )
    return createScriptProcessor(audioContext, source, onAudioChunk)
  }
}
