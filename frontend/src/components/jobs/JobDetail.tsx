/**
 * Job Detail Component
 * T043: Display detailed job information
 *
 * Feature: 007-async-job-mgmt
 */

import { useEffect, useRef, useState } from 'react'
import { Download, RefreshCw, AlertCircle, Clock, Play, Pause, Volume2 } from 'lucide-react'
import { useJobStore } from '@/stores/jobStore'
import { JobStatusBadge } from './JobStatus'
import {
  formatDateTime,
  formatDuration,
  downloadJobAudio,
  getDownloadUrl,
} from '@/services/jobApi'

interface JobDetailProps {
  jobId: string | null
  onClose?: () => void
}

export function JobDetail({ jobId, onClose }: JobDetailProps) {
  const { currentJob, isFetchingDetail, error, fetchJob, clearCurrentJob } = useJobStore()
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [audioError, setAudioError] = useState<string | null>(null)

  // Fetch job details when ID changes
  useEffect(() => {
    if (jobId) {
      fetchJob(jobId)
    } else {
      clearCurrentJob()
    }
    // Reset audio state when job changes
    setIsPlaying(false)
    setAudioError(null)
  }, [jobId, fetchJob, clearCurrentJob])

  // Handle play/pause toggle
  const handlePlayPause = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play().catch((err) => {
        setAudioError('無法播放音訊: ' + err.message)
      })
    }
  }

  // Handle audio events
  const handleAudioPlay = () => setIsPlaying(true)
  const handleAudioPause = () => setIsPlaying(false)
  const handleAudioEnded = () => setIsPlaying(false)
  const handleAudioError = () => setAudioError('音訊載入失敗')

  // Handle download
  const handleDownload = async () => {
    if (!currentJob?.id) return
    try {
      await downloadJobAudio(currentJob.id)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  // Empty state
  if (!jobId) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-lg border-2 border-dashed text-muted-foreground">
        <Clock className="mb-2 h-8 w-8 opacity-50" />
        <p>選擇一個工作以查看詳情</p>
      </div>
    )
  }

  // Loading state
  if (isFetchingDetail) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Error state
  if (error && !currentJob) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-lg border text-muted-foreground">
        <AlertCircle className="mb-2 h-8 w-8 text-red-500" />
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  // No data
  if (!currentJob) {
    return null
  }

  // Input params parsing
  const inputParams = currentJob.input_params as {
    provider?: string
    turns?: Array<{ speaker: string; text: string }>
    voice_assignments?: Array<{ speaker: string; voice_id: string; voice_name?: string }>
    language?: string
    output_format?: string
    gap_ms?: number
    crossfade_ms?: number
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">工作詳情</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            關閉
          </button>
        )}
      </div>

      {/* Status and ID */}
      <div className="rounded-lg border p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">狀態</span>
          <JobStatusBadge status={currentJob.status} />
        </div>
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">工作 ID</span>
          <code className="rounded bg-muted px-2 py-0.5 text-sm">{currentJob.id}</code>
        </div>
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Provider</span>
          <span className="capitalize">{currentJob.provider}</span>
        </div>
      </div>

      {/* Timestamps */}
      <div className="rounded-lg border p-4">
        <h3 className="mb-3 font-medium">時間軸</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">建立時間</span>
            <span>{formatDateTime(currentJob.created_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">開始時間</span>
            <span>{formatDateTime(currentJob.started_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">完成時間</span>
            <span>{formatDateTime(currentJob.completed_at)}</span>
          </div>
        </div>
      </div>

      {/* Result metadata (only for completed jobs) */}
      {currentJob.status === 'completed' && currentJob.result_metadata && (
        <div className="rounded-lg border p-4">
          <h3 className="mb-3 font-medium">合成結果</h3>
          <div className="space-y-2 text-sm">
            {currentJob.result_metadata.duration_ms && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">音檔長度</span>
                <span>{formatDuration(currentJob.result_metadata.duration_ms)}</span>
              </div>
            )}
            {currentJob.result_metadata.latency_ms && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">處理時間</span>
                <span>{formatDuration(currentJob.result_metadata.latency_ms)}</span>
              </div>
            )}
            {currentJob.result_metadata.synthesis_mode && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">合成模式</span>
                <span>
                  {currentJob.result_metadata.synthesis_mode === 'native'
                    ? '原生'
                    : '分段合併'}
                </span>
              </div>
            )}
          </div>

          {/* Audio Player */}
          {currentJob.audio_file_id && (
            <div className="mt-4">
              <div className="mb-2 flex items-center gap-2">
                <Volume2 className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">音訊預覽</span>
              </div>

              {/* Hidden audio element */}
              <audio
                ref={audioRef}
                src={getDownloadUrl(currentJob.id)}
                onPlay={handleAudioPlay}
                onPause={handleAudioPause}
                onEnded={handleAudioEnded}
                onError={handleAudioError}
                preload="metadata"
              />

              {/* Audio error message */}
              {audioError && (
                <div className="mb-2 rounded bg-red-100 px-3 py-2 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
                  {audioError}
                </div>
              )}

              {/* Play/Pause button with native audio controls */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handlePlayPause}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  {isPlaying ? (
                    <Pause className="h-5 w-5" />
                  ) : (
                    <Play className="ml-0.5 h-5 w-5" />
                  )}
                </button>
                <span className="text-sm text-muted-foreground">
                  {isPlaying ? '播放中' : '點擊播放'}
                </span>
              </div>
            </div>
          )}

          {/* Download button */}
          <button
            onClick={handleDownload}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-primary-foreground hover:bg-primary/90"
          >
            <Download className="h-4 w-4" />
            下載音檔
          </button>
        </div>
      )}

      {/* Error message (only for failed jobs) */}
      {currentJob.status === 'failed' && currentJob.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <h3 className="mb-2 font-medium text-red-700 dark:text-red-400">錯誤訊息</h3>
          <p className="text-sm text-red-600 dark:text-red-400">
            {currentJob.error_message}
          </p>
          {currentJob.retry_count > 0 && (
            <p className="mt-2 text-xs text-red-500 dark:text-red-500">
              重試次數: {currentJob.retry_count}
            </p>
          )}
        </div>
      )}

      {/* Input parameters */}
      {inputParams.turns && inputParams.turns.length > 0 && (
        <div className="rounded-lg border p-4">
          <h3 className="mb-3 font-medium">輸入參數</h3>

          {/* Dialogue turns */}
          <div className="mb-4">
            <h4 className="mb-2 text-sm font-medium text-muted-foreground">對話內容</h4>
            <div className="max-h-48 space-y-2 overflow-y-auto rounded-md bg-muted/50 p-3">
              {inputParams.turns.map((turn, index) => (
                <div key={index} className="text-sm">
                  <span className="font-medium">{turn.speaker}:</span>{' '}
                  <span className="text-muted-foreground">{turn.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Voice assignments */}
          {inputParams.voice_assignments && (
            <div className="mb-4">
              <h4 className="mb-2 text-sm font-medium text-muted-foreground">語音指派</h4>
              <div className="space-y-1">
                {inputParams.voice_assignments.map((va, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <span className="font-medium">{va.speaker}:</span>
                    <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                      {va.voice_name || va.voice_id}
                    </code>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Other settings */}
          <div className="grid grid-cols-2 gap-2 text-sm">
            {inputParams.language && (
              <div>
                <span className="text-muted-foreground">語言:</span> {inputParams.language}
              </div>
            )}
            {inputParams.output_format && (
              <div>
                <span className="text-muted-foreground">格式:</span>{' '}
                {inputParams.output_format.toUpperCase()}
              </div>
            )}
            {inputParams.gap_ms !== undefined && (
              <div>
                <span className="text-muted-foreground">間隔:</span> {inputParams.gap_ms}ms
              </div>
            )}
            {inputParams.crossfade_ms !== undefined && (
              <div>
                <span className="text-muted-foreground">淡入淡出:</span>{' '}
                {inputParams.crossfade_ms}ms
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
