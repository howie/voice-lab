/**
 * AudioPlayer Component
 * T042: Create AudioPlayer component with play/pause/download
 */

import { useRef, useState, useEffect } from 'react'
import { downloadAudio } from '@/lib/streaming'

interface AudioPlayerProps {
  audioContent?: string // Base64 encoded audio
  contentType?: string
  duration?: number // in milliseconds
  onPlay?: () => void
  onPause?: () => void
  onEnded?: () => void
  disabled?: boolean
}

export function AudioPlayer({
  audioContent,
  contentType = 'audio/mpeg',
  duration,
  onPlay,
  onPause,
  onEnded,
  disabled = false,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [audioDuration, setAudioDuration] = useState(duration ? duration / 1000 : 0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  // Create blob URL when audio content changes
  useEffect(() => {
    if (audioContent) {
      // Convert base64 to blob URL
      const binaryString = atob(audioContent)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const blob = new Blob([bytes], { type: contentType })
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)

      return () => {
        URL.revokeObjectURL(url)
      }
    } else {
      setAudioUrl(null)
    }
  }, [audioContent, contentType])

  // Update current time during playback
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleLoadedMetadata = () => {
      setAudioDuration(audio.duration)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
      onEnded?.()
    }

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [onEnded])

  const togglePlay = async () => {
    const audio = audioRef.current
    if (!audio || !audioUrl) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
      onPause?.()
    } else {
      try {
        await audio.play()
        setIsPlaying(true)
        onPlay?.()
      } catch (error) {
        console.error('Playback failed:', error)
      }
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current
    if (!audio) return

    const time = parseFloat(e.target.value)
    audio.currentTime = time
    setCurrentTime(time)
  }

  const handleDownload = () => {
    if (!audioContent) return

    const extension = contentType.includes('mpeg') ? 'mp3' : 'wav'
    const filename = `tts-audio-${Date.now()}.${extension}`
    downloadAudio(audioContent, contentType, filename)
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const hasAudio = !!audioUrl

  return (
    <div className="space-y-3">
      {/* Hidden audio element */}
      {audioUrl && <audio ref={audioRef} src={audioUrl} preload="metadata" />}

      {/* Player controls */}
      <div
        className={`
          flex items-center gap-3 rounded-lg border p-3
          ${!hasAudio ? 'opacity-50' : ''}
        `}
      >
        {/* Play/Pause button */}
        <button
          onClick={togglePlay}
          disabled={disabled || !hasAudio}
          className={`
            flex h-10 w-10 items-center justify-center rounded-full
            bg-primary text-primary-foreground
            hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50
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

        {/* Progress bar */}
        <div className="flex-1">
          <input
            type="range"
            min={0}
            max={audioDuration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            disabled={disabled || !hasAudio}
            className="w-full cursor-pointer disabled:cursor-not-allowed"
          />
        </div>

        {/* Time display */}
        <span className="min-w-[80px] text-sm text-muted-foreground">
          {formatTime(currentTime)} / {formatTime(audioDuration)}
        </span>

        {/* Download button */}
        <button
          onClick={handleDownload}
          disabled={disabled || !hasAudio}
          className="rounded-lg p-2 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="下載音檔"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="h-5 w-5"
          >
            <path
              fillRule="evenodd"
              d="M12 2.25a.75.75 0 01.75.75v11.69l3.22-3.22a.75.75 0 111.06 1.06l-4.5 4.5a.75.75 0 01-1.06 0l-4.5-4.5a.75.75 0 111.06-1.06l3.22 3.22V3a.75.75 0 01.75-.75zm-9 13.5a.75.75 0 01.75.75v2.25a1.5 1.5 0 001.5 1.5h13.5a1.5 1.5 0 001.5-1.5V16.5a.75.75 0 011.5 0v2.25a3 3 0 01-3 3H5.25a3 3 0 01-3-3V16.5a.75.75 0 01.75-.75z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  )
}
