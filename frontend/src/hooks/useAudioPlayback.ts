/**
 * Audio playback hook for streaming audio.
 * Feature: 004-interaction-module
 *
 * T024: Provides audio playback with support for streaming chunks
 * and queue management.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

// =============================================================================
// Types
// =============================================================================

export interface UseAudioPlaybackOptions {
  /** Sample rate for PCM audio (default: 24000) */
  sampleRate?: number
  /** Channel count (default: 1) */
  channelCount?: number
  /** Volume level 0-1 (default: 1) */
  volume?: number
  /** Callback when playback starts */
  onPlaybackStart?: () => void
  /** Callback when playback ends */
  onPlaybackEnd?: () => void
  /** Callback when playback is interrupted */
  onPlaybackInterrupt?: () => void
}

export interface UseAudioPlaybackReturn {
  /** Whether audio is currently playing */
  isPlaying: boolean
  /** Whether audio is queued for playback */
  hasQueuedAudio: boolean
  /** Current volume (0-1) */
  volume: number
  /** Set volume (0-1) */
  setVolume: (volume: number) => void
  /** Play audio from ArrayBuffer (PCM16 or MP3) */
  playAudio: (data: ArrayBuffer, format?: 'pcm16' | 'mp3') => Promise<void>
  /** Queue audio chunk for streaming playback */
  queueAudioChunk: (chunk: ArrayBuffer, format?: 'pcm16' | 'mp3') => void
  /** Stop current playback */
  stop: () => void
  /** Clear audio queue */
  clearQueue: () => void
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useAudioPlayback(options: UseAudioPlaybackOptions = {}): UseAudioPlaybackReturn {
  const {
    sampleRate = 24000,
    channelCount = 1,
    volume: initialVolume = 1,
    onPlaybackStart,
    onPlaybackEnd,
    onPlaybackInterrupt,
  } = options

  const [isPlaying, setIsPlaying] = useState(false)
  const [hasQueuedAudio, setHasQueuedAudio] = useState(false)
  const [volume, setVolumeState] = useState(initialVolume)

  const audioContextRef = useRef<AudioContext | null>(null)
  const gainNodeRef = useRef<GainNode | null>(null)
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null)
  const audioQueueRef = useRef<AudioBuffer[]>([])
  const isProcessingQueueRef = useRef(false)

  // Initialize audio context
  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate })
      gainNodeRef.current = audioContextRef.current.createGain()
      gainNodeRef.current.gain.value = volume
      gainNodeRef.current.connect(audioContextRef.current.destination)
    }
    return audioContextRef.current
  }, [sampleRate, volume])

  // Set volume
  const setVolume = useCallback((newVolume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, newVolume))
    setVolumeState(clampedVolume)
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = clampedVolume
    }
  }, [])

  // Convert PCM16 to AudioBuffer
  const pcm16ToAudioBuffer = useCallback(
    (data: ArrayBuffer): AudioBuffer => {
      const audioContext = getAudioContext()
      const int16Array = new Int16Array(data)
      const float32Array = new Float32Array(int16Array.length)

      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768
      }

      const audioBuffer = audioContext.createBuffer(channelCount, float32Array.length, sampleRate)
      audioBuffer.copyToChannel(float32Array, 0)
      return audioBuffer
    },
    [getAudioContext, channelCount, sampleRate]
  )

  // Decode MP3 to AudioBuffer
  const decodeMP3 = useCallback(
    async (data: ArrayBuffer): Promise<AudioBuffer> => {
      const audioContext = getAudioContext()
      return await audioContext.decodeAudioData(data.slice(0))
    },
    [getAudioContext]
  )

  // Play a single AudioBuffer
  const playBuffer = useCallback(
    (audioBuffer: AudioBuffer): Promise<void> => {
      return new Promise((resolve) => {
        const audioContext = getAudioContext()

        // Resume if suspended
        if (audioContext.state === 'suspended') {
          audioContext.resume()
        }

        const source = audioContext.createBufferSource()
        source.buffer = audioBuffer
        source.connect(gainNodeRef.current!)

        currentSourceRef.current = source

        source.onended = () => {
          currentSourceRef.current = null
          resolve()
        }

        source.start(0)
      })
    },
    [getAudioContext]
  )

  // Process audio queue
  const processQueue = useCallback(async () => {
    if (isProcessingQueueRef.current || audioQueueRef.current.length === 0) {
      return
    }

    isProcessingQueueRef.current = true
    setIsPlaying(true)
    onPlaybackStart?.()

    while (audioQueueRef.current.length > 0) {
      const buffer = audioQueueRef.current.shift()!
      setHasQueuedAudio(audioQueueRef.current.length > 0)
      await playBuffer(buffer)
    }

    isProcessingQueueRef.current = false
    setIsPlaying(false)
    setHasQueuedAudio(false)
    onPlaybackEnd?.()
  }, [playBuffer, onPlaybackStart, onPlaybackEnd])

  // Play audio from ArrayBuffer
  const playAudio = useCallback(
    async (data: ArrayBuffer, format: 'pcm16' | 'mp3' = 'pcm16'): Promise<void> => {
      try {
        const audioBuffer = format === 'mp3' ? await decodeMP3(data) : pcm16ToAudioBuffer(data)

        setIsPlaying(true)
        onPlaybackStart?.()

        await playBuffer(audioBuffer)

        setIsPlaying(false)
        onPlaybackEnd?.()
      } catch (err) {
        console.error('Failed to play audio:', err)
        setIsPlaying(false)
      }
    },
    [pcm16ToAudioBuffer, decodeMP3, playBuffer, onPlaybackStart, onPlaybackEnd]
  )

  // Queue audio chunk for streaming playback
  const queueAudioChunk = useCallback(
    (chunk: ArrayBuffer, format: 'pcm16' | 'mp3' = 'pcm16') => {
      const processChunk = async () => {
        try {
          const audioBuffer = format === 'mp3' ? await decodeMP3(chunk) : pcm16ToAudioBuffer(chunk)

          audioQueueRef.current.push(audioBuffer)
          setHasQueuedAudio(true)

          // Start processing if not already
          processQueue()
        } catch (err) {
          console.error('Failed to queue audio chunk:', err)
        }
      }

      processChunk()
    },
    [pcm16ToAudioBuffer, decodeMP3, processQueue]
  )

  // Stop playback
  const stop = useCallback(() => {
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop()
      } catch {
        // Ignore if already stopped
      }
      currentSourceRef.current = null
    }

    isProcessingQueueRef.current = false
    audioQueueRef.current = []
    setIsPlaying(false)
    setHasQueuedAudio(false)
    onPlaybackInterrupt?.()
  }, [onPlaybackInterrupt])

  // Clear queue without stopping current playback
  const clearQueue = useCallback(() => {
    audioQueueRef.current = []
    setHasQueuedAudio(false)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop()
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }
    }
  }, [stop])

  return {
    isPlaying,
    hasQueuedAudio,
    volume,
    setVolume,
    playAudio,
    queueAudioChunk,
    stop,
    clearQueue,
  }
}

export default useAudioPlayback
