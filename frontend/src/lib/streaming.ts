/**
 * Streaming utilities for TTS audio playback
 * T039: Add streaming fetch support (ReadableStream)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export interface StreamingOptions {
  text: string
  provider: string
  voice_id: string
  language?: string
  speed?: number
  pitch?: number
  volume?: number
  output_format?: string
  onChunk?: (chunk: Uint8Array) => void
  onProgress?: (loaded: number) => void
  onError?: (error: Error) => void
}

/**
 * Fetch streaming audio from TTS API
 * Returns an AudioContext-compatible ArrayBuffer
 */
export async function fetchStreamingAudio(
  options: StreamingOptions
): Promise<ArrayBuffer> {
  const token = localStorage.getItem('auth_token')

  const response = await fetch(`${API_BASE_URL}/tts/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      text: options.text,
      provider: options.provider,
      voice_id: options.voice_id,
      language: options.language ?? 'zh-TW',
      speed: options.speed ?? 1.0,
      pitch: options.pitch ?? 0.0,
      volume: options.volume ?? 1.0,
      output_format: options.output_format ?? 'mp3',
    }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      errorData.error?.message || `HTTP error! status: ${response.status}`
    )
  }

  if (!response.body) {
    throw new Error('Response body is not available')
  }

  const reader = response.body.getReader()
  const chunks: Uint8Array[] = []
  let totalLoaded = 0

  while (true) {
    const { done, value } = await reader.read()

    if (done) break

    if (value) {
      chunks.push(value)
      totalLoaded += value.length

      options.onChunk?.(value)
      options.onProgress?.(totalLoaded)
    }
  }

  // Combine all chunks into a single ArrayBuffer
  const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0)
  const result = new Uint8Array(totalLength)
  let offset = 0

  for (const chunk of chunks) {
    result.set(chunk, offset)
    offset += chunk.length
  }

  return result.buffer
}

/**
 * Create a streaming audio player
 */
export class StreamingAudioPlayer {
  private audioContext: AudioContext | null = null
  private sourceNode: AudioBufferSourceNode | null = null
  private chunks: Uint8Array[] = []
  private isPlaying = false

  constructor() {
    // AudioContext is created on user interaction
  }

  private getAudioContext(): AudioContext {
    if (!this.audioContext) {
      this.audioContext = new AudioContext()
    }
    return this.audioContext
  }

  async playFromStream(options: StreamingOptions): Promise<void> {
    this.stop()
    this.chunks = []

    try {
      const buffer = await fetchStreamingAudio({
        ...options,
        onChunk: (chunk) => {
          this.chunks.push(chunk)
          options.onChunk?.(chunk)
        },
        onProgress: options.onProgress,
      })

      await this.playBuffer(buffer)
    } catch (error) {
      options.onError?.(error as Error)
      throw error
    }
  }

  async playBuffer(buffer: ArrayBuffer): Promise<void> {
    const audioContext = this.getAudioContext()

    // Resume if suspended (browser autoplay policy)
    if (audioContext.state === 'suspended') {
      await audioContext.resume()
    }

    // Decode audio data
    const audioBuffer = await audioContext.decodeAudioData(buffer)

    // Create source node
    this.sourceNode = audioContext.createBufferSource()
    this.sourceNode.buffer = audioBuffer
    this.sourceNode.connect(audioContext.destination)

    this.sourceNode.onended = () => {
      this.isPlaying = false
    }

    this.sourceNode.start()
    this.isPlaying = true
  }

  stop(): void {
    if (this.sourceNode) {
      try {
        this.sourceNode.stop()
      } catch {
        // Ignore if already stopped
      }
      this.sourceNode.disconnect()
      this.sourceNode = null
    }
    this.isPlaying = false
  }

  pause(): void {
    if (this.audioContext) {
      this.audioContext.suspend()
    }
  }

  resume(): void {
    if (this.audioContext) {
      this.audioContext.resume()
    }
  }

  get playing(): boolean {
    return this.isPlaying
  }

  dispose(): void {
    this.stop()
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
  }
}

/**
 * Convert base64 to ArrayBuffer
 */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = atob(base64)
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }
  return bytes.buffer
}

/**
 * Convert ArrayBuffer to base64
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

/**
 * Create a blob URL from base64 audio
 */
export function createAudioBlobUrl(
  base64: string,
  contentType: string
): string {
  const buffer = base64ToArrayBuffer(base64)
  const blob = new Blob([buffer], { type: contentType })
  return URL.createObjectURL(blob)
}

/**
 * Download audio file
 */
export function downloadAudio(
  base64: string,
  contentType: string,
  filename: string
): void {
  const buffer = base64ToArrayBuffer(base64)
  const blob = new Blob([buffer], { type: contentType })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}
