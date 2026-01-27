/**
 * AudioWorkletProcessor for low-latency audio capture.
 * Feature: 004-interaction-module
 *
 * Replaces deprecated ScriptProcessorNode with modern AudioWorklet API.
 * Runs in a separate audio rendering thread for better performance.
 */

class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    // Buffer size determines latency: 1024 samples @ 16kHz = 64ms
    // Smaller = lower latency but more frequent messages
    this.bufferSize = 1024
    this.buffer = new Float32Array(this.bufferSize)
    this.bufferIndex = 0
  }

  /**
   * Process audio frames (called ~375 times/sec at 48kHz, 128 frames each)
   * @param {Float32Array[][]} inputs - Input audio data
   * @param {Float32Array[][]} outputs - Output audio data (unused)
   * @param {Record<string, Float32Array>} parameters - Audio parameters (unused)
   * @returns {boolean} - Return true to keep processor alive
   */
  process(inputs, outputs, parameters) {
    const input = inputs[0]
    if (!input || !input[0]) return true

    const channelData = input[0]

    // Accumulate samples into buffer (each process call = 128 frames)
    for (let i = 0; i < channelData.length; i++) {
      this.buffer[this.bufferIndex++] = channelData[i]

      // Buffer full, send to main thread
      if (this.bufferIndex >= this.bufferSize) {
        const audioData = this.buffer.slice()

        // Use Transferable Objects for zero-copy transfer
        this.port.postMessage(
          {
            type: 'audio',
            audioData: audioData,
            sampleRate: sampleRate, // globalThis.sampleRate available in AudioWorklet
          },
          [audioData.buffer]
        )

        this.bufferIndex = 0
      }
    }

    return true // Keep processor alive
  }
}

registerProcessor('audio-processor', AudioProcessor)
