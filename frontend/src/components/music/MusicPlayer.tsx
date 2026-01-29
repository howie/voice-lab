/**
 * Music Player Component
 * Feature: 012-music-generation
 *
 * Audio player for completed music generation jobs.
 */

import { useState, useRef, useEffect } from 'react'
import { Play, Pause, Download, Volume2, VolumeX, RotateCcw, Clock, Music } from 'lucide-react'
import { MusicJobStatusBadge } from './MusicJobStatus'
import type { MusicJob } from '@/types/music'
import { MUSIC_TYPE_LABELS } from '@/types/music'

interface MusicPlayerProps {
  job: MusicJob
  onRetry?: (jobId: string) => void
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function MusicPlayer({ job, onRetry }: MusicPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(job.duration_ms ? job.duration_ms / 1000 : 0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)

  // Reset state when job changes
  useEffect(() => {
    setIsPlaying(false)
    setCurrentTime(0)
    setDuration(job.duration_ms ? job.duration_ms / 1000 : 0)
  }, [job.id, job.duration_ms])

  const handlePlayPause = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration)
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value)
    setVolume(newVolume)
    if (audioRef.current) {
      audioRef.current.volume = newVolume
    }
    setIsMuted(newVolume === 0)
  }

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleDownload = () => {
    if (job.result_url) {
      const link = document.createElement('a')
      link.href = job.result_url
      link.download = `${job.title || job.id}.mp3`
      link.click()
    }
  }

  const canPlay = job.status === 'completed' && job.result_url
  const canRetry = job.status === 'failed'

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h3 className="font-semibold">{job.title || '未命名音樂'}</h3>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{MUSIC_TYPE_LABELS[job.type]}</span>
            <span>·</span>
            <MusicJobStatusBadge status={job.status} size="sm" />
          </div>
        </div>

        {/* Cover image */}
        {job.cover_url ? (
          <img
            src={job.cover_url}
            alt="Cover"
            className="h-16 w-16 rounded-lg object-cover"
          />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-muted">
            <Music className="h-8 w-8 text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Prompt/Lyrics preview */}
      {job.prompt && (
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">
            <strong>描述：</strong> {job.prompt}
          </p>
        </div>
      )}

      {/* Generated lyrics preview */}
      {job.generated_lyrics && (
        <div className="max-h-32 overflow-y-auto rounded-lg bg-muted/50 p-3">
          <p className="whitespace-pre-wrap font-mono text-sm text-muted-foreground">
            {job.generated_lyrics}
          </p>
        </div>
      )}

      {/* Error message */}
      {job.error_message && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          <strong>錯誤：</strong> {job.error_message}
        </div>
      )}

      {/* Audio player */}
      {canPlay && (
        <>
          <audio
            ref={audioRef}
            src={job.result_url ?? undefined}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={handleEnded}
          />

          {/* Progress bar */}
          <div className="space-y-2">
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={handleSeek}
              className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-muted [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{formatDuration(currentTime * 1000)}</span>
              <span>{formatDuration(duration * 1000)}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Play/Pause */}
              <button
                onClick={handlePlayPause}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:bg-primary/90"
              >
                {isPlaying ? (
                  <Pause className="h-5 w-5" />
                ) : (
                  <Play className="h-5 w-5 pl-0.5" />
                )}
              </button>

              {/* Volume */}
              <button
                onClick={toggleMute}
                className="rounded-md p-2 text-muted-foreground hover:bg-muted"
              >
                {isMuted || volume === 0 ? (
                  <VolumeX className="h-5 w-5" />
                ) : (
                  <Volume2 className="h-5 w-5" />
                )}
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="h-1 w-20 cursor-pointer appearance-none rounded-lg bg-muted [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
              />
            </div>

            {/* Download */}
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted"
            >
              <Download className="h-4 w-4" />
              下載
            </button>
          </div>
        </>
      )}

      {/* Retry button for failed jobs */}
      {canRetry && onRetry && (
        <button
          onClick={() => onRetry(job.id)}
          className="flex w-full items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
        >
          <RotateCcw className="h-4 w-4" />
          重新嘗試
        </button>
      )}

      {/* Metadata */}
      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>建立：{formatDateTime(job.created_at)}</span>
        </div>
        {job.completed_at && (
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>完成：{formatDateTime(job.completed_at)}</span>
          </div>
        )}
        {job.model && (
          <div>
            <span>模型：{job.model}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default MusicPlayer
