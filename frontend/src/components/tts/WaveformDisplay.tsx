/**
 * WaveformDisplay Component
 * T044: Create WaveformDisplay component using WaveSurfer.js
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import WaveSurfer from 'wavesurfer.js'

interface WaveformDisplayProps {
  audioContent?: string // Base64 encoded audio
  contentType?: string
  onReady?: (duration: number) => void
  onPlay?: () => void
  onPause?: () => void
  onFinish?: () => void
  onTimeUpdate?: (currentTime: number) => void
  onSeek?: (time: number) => void
  autoplay?: boolean
  height?: number
  waveColor?: string
  progressColor?: string
}

export function WaveformDisplay({
  audioContent,
  contentType = 'audio/mpeg',
  onReady,
  onPlay,
  onPause,
  onFinish,
  onTimeUpdate,
  onSeek,
  autoplay = false,
  height = 80,
  waveColor = '#4F4A85',
  progressColor = '#7C3AED',
}: WaveformDisplayProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const wavesurferRef = useRef<WaveSurfer | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isReady, setIsReady] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  // Initialize WaveSurfer
  useEffect(() => {
    if (!containerRef.current) return

    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor,
      progressColor,
      cursorColor: '#fff',
      cursorWidth: 2,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height,
      normalize: true,
      backend: 'WebAudio',
    })

    // Event handlers
    wavesurfer.on('ready', () => {
      setIsReady(true)
      const dur = wavesurfer.getDuration()
      setDuration(dur)
      onReady?.(dur)

      if (autoplay) {
        wavesurfer.play()
      }
    })

    wavesurfer.on('play', () => {
      setIsPlaying(true)
      onPlay?.()
    })

    wavesurfer.on('pause', () => {
      setIsPlaying(false)
      onPause?.()
    })

    wavesurfer.on('finish', () => {
      setIsPlaying(false)
      setCurrentTime(0)
      onFinish?.()
    })

    wavesurfer.on('timeupdate', (time) => {
      setCurrentTime(time)
      onTimeUpdate?.(time)
    })

    wavesurfer.on('seeking', (time) => {
      setCurrentTime(time)
      onSeek?.(time)
    })

    wavesurfer.on('error', (error) => {
      console.error('WaveSurfer error:', error)
    })

    wavesurferRef.current = wavesurfer

    return () => {
      wavesurfer.destroy()
    }
  }, [height, waveColor, progressColor, autoplay, onReady, onPlay, onPause, onFinish, onTimeUpdate, onSeek])

  // Load audio when audioContent changes
  useEffect(() => {
    const wavesurfer = wavesurferRef.current
    if (!wavesurfer || !audioContent) return

    setIsReady(false)
    setIsPlaying(false)
    setCurrentTime(0)

    // Convert base64 to blob
    try {
      const binaryString = atob(audioContent)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const blob = new Blob([bytes], { type: contentType })

      wavesurfer.loadBlob(blob)
    } catch (error) {
      console.error('Failed to load audio:', error)
    }
  }, [audioContent, contentType])

  const togglePlayPause = useCallback(() => {
    const wavesurfer = wavesurferRef.current
    if (!wavesurfer || !isReady) return

    wavesurfer.playPause()
  }, [isReady])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const hasAudio = !!audioContent

  return (
    <div className="space-y-2">
      {/* Waveform container */}
      <div
        ref={containerRef}
        className={`
          rounded-lg border bg-muted/30 p-2
          ${!hasAudio ? 'opacity-50' : ''}
        `}
        style={{ minHeight: height + 16 }}
      />

      {/* Controls */}
      <div className="flex items-center gap-3">
        {/* Play/Pause button */}
        <button
          onClick={togglePlayPause}
          disabled={!isReady}
          className={`
            flex h-10 w-10 items-center justify-center rounded-full
            bg-primary text-primary-foreground
            hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50
            transition-colors
          `}
          aria-label={isPlaying ? '暫停' : '播放'}
        >
          {isPlaying ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-5 w-5"
            >
              <path
                fillRule="evenodd"
                d="M6.75 5.25a.75.75 0 01.75-.75H9a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H7.5a.75.75 0 01-.75-.75V5.25zm7.5 0A.75.75 0 0115 4.5h1.5a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H15a.75.75 0 01-.75-.75V5.25z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-5 w-5 ml-0.5"
            >
              <path
                fillRule="evenodd"
                d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </button>

        {/* Time display */}
        <span className="min-w-[100px] text-sm text-muted-foreground">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        {/* Status indicator */}
        {!hasAudio && (
          <span className="text-sm text-muted-foreground">
            等待音訊輸入...
          </span>
        )}
        {hasAudio && !isReady && (
          <span className="text-sm text-muted-foreground">
            載入中...
          </span>
        )}
      </div>
    </div>
  )
}
