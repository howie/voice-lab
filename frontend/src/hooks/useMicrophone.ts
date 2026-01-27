/**
 * Microphone hook for audio recording.
 * Feature: 004-interaction-module
 *
 * T023: Provides microphone access, recording, and audio streaming.
 *
 * Uses AudioWorklet for low-latency audio processing when supported,
 * with automatic fallback to ScriptProcessorNode for older browsers.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import {
  createAudioProcessor,
  type AudioProcessorResult,
} from '@/lib/audioProcessor'

// =============================================================================
// Types
// =============================================================================

export interface UseMicrophoneOptions {
  /** Sample rate for audio (default: 16000) */
  sampleRate?: number
  /** Channel count (default: 1) */
  channelCount?: number
  /** Enable noise suppression (default: true) */
  noiseSuppression?: boolean
  /** Enable echo cancellation (default: true) */
  echoCancellation?: boolean
  /** Callback for audio chunks during recording */
  onAudioChunk?: (chunk: Float32Array, sampleRate: number) => void
  /** Callback for volume level changes (0-1) */
  onVolumeChange?: (volume: number) => void
}

export interface UseMicrophoneReturn {
  /** Whether microphone permission is granted */
  hasPermission: boolean | null
  /** Whether currently recording */
  isRecording: boolean
  /** Current volume level (0-1) */
  volume: number
  /** Error message if any */
  error: string | null
  /** Request microphone permission */
  requestPermission: () => Promise<boolean>
  /** Start recording */
  startRecording: () => Promise<void>
  /** Stop recording */
  stopRecording: () => void
  /** Get recorded audio as Blob */
  getRecordedBlob: () => Blob | null
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useMicrophone(options: UseMicrophoneOptions = {}): UseMicrophoneReturn {
  const {
    sampleRate = 16000,
    channelCount = 1,
    noiseSuppression = true,
    echoCancellation = true,
    onAudioChunk,
    onVolumeChange,
  } = options

  const [hasPermission, setHasPermission] = useState<boolean | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [volume, setVolume] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const processorRef = useRef<AudioProcessorResult | null>(null)
  const recordedChunksRef = useRef<Float32Array[]>([])
  const animationFrameRef = useRef<number | null>(null)

  // Request microphone permission
  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      setError(null)

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: { ideal: sampleRate },
          channelCount: { exact: channelCount },
          noiseSuppression: { ideal: noiseSuppression },
          echoCancellation: { ideal: echoCancellation },
        },
      })

      // Permission granted, but we don't need to keep the stream
      stream.getTracks().forEach((track) => track.stop())
      setHasPermission(true)
      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to access microphone'
      setError(message)
      setHasPermission(false)
      return false
    }
  }, [sampleRate, channelCount, noiseSuppression, echoCancellation])

  // Update volume meter
  const updateVolume = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)

    // Calculate RMS volume
    let sum = 0
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i] * dataArray[i]
    }
    const rms = Math.sqrt(sum / dataArray.length) / 255

    setVolume(rms)
    onVolumeChange?.(rms)

    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateVolume)
    }
  }, [isRecording, onVolumeChange])

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null)
      recordedChunksRef.current = []

      // Get microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: { ideal: sampleRate },
          channelCount: { exact: channelCount },
          noiseSuppression: { ideal: noiseSuppression },
          echoCancellation: { ideal: echoCancellation },
        },
      })

      mediaStreamRef.current = stream
      setHasPermission(true)

      // Create audio context
      const audioContext = new AudioContext({ sampleRate })
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)

      // Branch A: AnalyserNode for volume metering (stays on main thread)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      analyserRef.current = analyser
      source.connect(analyser)

      // Branch B: Audio processor for recording (uses AudioWorklet when supported)
      const processor = await createAudioProcessor({
        audioContext,
        source,
        onAudioChunk: (chunk, chunkSampleRate) => {
          // Store for later use
          recordedChunksRef.current.push(chunk)
          // Notify listener
          onAudioChunk?.(chunk, chunkSampleRate)
        },
      })
      processorRef.current = processor

      setIsRecording(true)

      // Start volume monitoring
      animationFrameRef.current = requestAnimationFrame(updateVolume)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start recording'
      setError(message)
      setHasPermission(false)
    }
  }, [
    sampleRate,
    channelCount,
    noiseSuppression,
    echoCancellation,
    onAudioChunk,
    updateVolume,
  ])

  // Stop recording
  const stopRecording = useCallback(() => {
    // Stop animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    // Cleanup processor (handles both AudioWorklet and ScriptProcessor)
    if (processorRef.current) {
      processorRef.current.cleanup()
      processorRef.current = null
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }

    analyserRef.current = null
    setIsRecording(false)
    setVolume(0)
  }, [])

  // Get recorded audio as Blob
  const getRecordedBlob = useCallback((): Blob | null => {
    if (recordedChunksRef.current.length === 0) return null

    // Merge all chunks
    const totalLength = recordedChunksRef.current.reduce((acc, chunk) => acc + chunk.length, 0)
    const mergedArray = new Float32Array(totalLength)

    let offset = 0
    for (const chunk of recordedChunksRef.current) {
      mergedArray.set(chunk, offset)
      offset += chunk.length
    }

    // Convert to 16-bit PCM
    const pcm16 = new Int16Array(mergedArray.length)
    for (let i = 0; i < mergedArray.length; i++) {
      const s = Math.max(-1, Math.min(1, mergedArray[i]))
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff
    }

    return new Blob([pcm16.buffer], { type: 'audio/pcm' })
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

  return {
    hasPermission,
    isRecording,
    volume,
    error,
    requestPermission,
    startRecording,
    stopRecording,
    getRecordedBlob,
  }
}

export default useMicrophone
