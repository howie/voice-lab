/**
 * BGM Generator Modal
 * Feature: 012-music-generation + 010-magic-dj-controller
 *
 * Modal for generating BGM using Mureka AI and adding to Magic DJ tracks.
 */

import { useState, useEffect, useCallback } from 'react'
import { X, Music, Loader2, Play, Pause, Save, RefreshCw, AlertCircle } from 'lucide-react'

import { musicApi } from '@/services/musicApi'
import { cn } from '@/lib/utils'
import type { Track, TrackType } from '@/types/magic-dj'
import type { MusicJob, MusicModel } from '@/types/music'
import { MUSIC_MODEL_LABELS } from '@/types/music'

// =============================================================================
// Types
// =============================================================================

export interface BGMGeneratorModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (track: Track, audioBlob: Blob) => void
}

// =============================================================================
// Polling Interval
// =============================================================================

const POLLING_INTERVAL_MS = 3000

// =============================================================================
// Component
// =============================================================================

export function BGMGeneratorModal({
  isOpen,
  onClose,
  onSave,
}: BGMGeneratorModalProps) {
  // Form state
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState<MusicModel>('auto')
  const [trackName, setTrackName] = useState('')
  const [trackType, setTrackType] = useState<TrackType>('song')
  const [hotkey, setHotkey] = useState('')

  // Job state
  const [currentJob, setCurrentJob] = useState<MusicJob | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Audio state
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null)

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setPrompt('')
      setModel('auto')
      setTrackName('')
      setTrackType('song')
      setHotkey('')
      setCurrentJob(null)
      setIsSubmitting(false)
      setError(null)
      setAudioBlob(null)
      setAudioUrl(null)
    }
  }, [isOpen])

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  // Poll for job status
  useEffect(() => {
    if (!currentJob) return
    if (currentJob.status === 'completed' || currentJob.status === 'failed') return

    const interval = setInterval(async () => {
      try {
        const response = await musicApi.getJob(currentJob.id)
        const job = response.data
        setCurrentJob(job)

        // Auto-set track name from job title
        if (job.title && !trackName) {
          setTrackName(job.title)
        }

        // Job completed - fetch the audio
        if (job.status === 'completed' && job.result_url) {
          clearInterval(interval)
          fetchAudio(job.result_url)
        }

        // Job failed
        if (job.status === 'failed') {
          clearInterval(interval)
          setError(job.error_message || '生成失敗')
        }
      } catch (err) {
        console.error('Failed to poll job status:', err)
      }
    }, POLLING_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [currentJob, trackName])

  // Fetch audio from result URL
  const fetchAudio = async (url: string) => {
    try {
      const response = await fetch(url)
      const blob = await response.blob()

      // Revoke old URL
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }

      const newUrl = URL.createObjectURL(blob)
      setAudioBlob(blob)
      setAudioUrl(newUrl)
    } catch (err) {
      console.error('Failed to fetch audio:', err)
      setError('無法下載音檔')
    }
  }

  // Submit generation job
  const handleSubmit = async () => {
    if (prompt.length < 10) {
      setError('場景描述至少需要 10 個字元')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await musicApi.submitInstrumental({ prompt, model })
      setCurrentJob(response.data)
    } catch (err) {
      console.error('Failed to submit job:', err)
      setError('提交失敗，請稍後再試')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Play preview
  const handlePlay = useCallback(() => {
    if (!audioUrl) return

    if (audioElement) {
      audioElement.pause()
    }

    const audio = new Audio(audioUrl)
    setAudioElement(audio)

    audio.onplay = () => setIsPlaying(true)
    audio.onended = () => setIsPlaying(false)
    audio.onpause = () => setIsPlaying(false)

    audio.play()
  }, [audioUrl, audioElement])

  // Stop playback
  const handleStop = useCallback(() => {
    if (audioElement) {
      audioElement.pause()
      audioElement.currentTime = 0
    }
    setIsPlaying(false)
  }, [audioElement])

  // Save track
  const handleSave = useCallback(() => {
    if (!trackName.trim()) {
      setError('請輸入音軌名稱')
      return
    }

    if (!audioBlob) {
      setError('請先生成音樂')
      return
    }

    const track: Track = {
      id: `bgm_${Date.now()}`,
      name: trackName.trim(),
      type: trackType,
      url: '', // Will be set by parent with blob URL
      hotkey: hotkey || undefined,
      isCustom: true,
      textContent: prompt, // Save prompt for reference
    }

    onSave(track, audioBlob)
    onClose()
  }, [trackName, prompt, audioBlob, trackType, hotkey, onSave, onClose])

  // Reset and try again
  const handleReset = () => {
    setCurrentJob(null)
    setAudioBlob(null)
    setAudioUrl(null)
    setError(null)
  }

  if (!isOpen) return null

  const isProcessing = currentJob && (currentJob.status === 'pending' || currentJob.status === 'processing')
  const isCompleted = currentJob?.status === 'completed' && !!audioBlob

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-background p-6 shadow-xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Music className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-bold">AI 生成 BGM</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-muted"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* Prompt */}
          <div>
            <label className="mb-1 block text-sm font-medium">場景/風格描述</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="例如：magical fantasy forest, whimsical, children friendly"
              rows={3}
              disabled={isProcessing || isCompleted}
              className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
            <div className="mt-1 flex justify-between text-xs text-muted-foreground">
              <span>最少 10 字元</span>
              <span>{prompt.length} / 500</span>
            </div>
          </div>

          {/* Model selection */}
          <div>
            <label className="mb-1 block text-sm font-medium">模型選擇</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as MusicModel)}
              disabled={isProcessing || isCompleted}
              className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            >
              {(Object.keys(MUSIC_MODEL_LABELS) as MusicModel[]).map((m) => (
                <option key={m} value={m}>
                  {MUSIC_MODEL_LABELS[m]}
                </option>
              ))}
            </select>
          </div>

          {/* Processing status */}
          {isProcessing && (
            <div className="flex items-center gap-3 rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
              <div>
                <p className="font-medium text-blue-700 dark:text-blue-400">
                  {currentJob?.status === 'pending' ? '等待處理中...' : '音樂生成中...'}
                </p>
                <p className="text-sm text-blue-600 dark:text-blue-300">
                  這可能需要 30-60 秒，請稍候
                </p>
              </div>
            </div>
          )}

          {/* Completed - Track settings */}
          {isCompleted && (
            <>
              <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
                <p className="font-medium text-green-700 dark:text-green-400">
                  BGM 生成完成！
                </p>
                {currentJob?.duration_ms && (
                  <p className="text-sm text-green-600 dark:text-green-300">
                    長度：{Math.round(currentJob.duration_ms / 1000)} 秒
                  </p>
                )}
              </div>

              {/* Audio preview */}
              <div className="flex items-center gap-2">
                <button
                  onClick={isPlaying ? handleStop : handlePlay}
                  className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 font-medium hover:bg-muted"
                >
                  {isPlaying ? (
                    <>
                      <Pause className="h-4 w-4" />
                      停止
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      試聽
                    </>
                  )}
                </button>
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 font-medium hover:bg-muted"
                >
                  <RefreshCw className="h-4 w-4" />
                  重新生成
                </button>
              </div>

              {/* Track name */}
              <div>
                <label className="mb-1 block text-sm font-medium">音軌名稱</label>
                <input
                  type="text"
                  value={trackName}
                  onChange={(e) => setTrackName(e.target.value)}
                  placeholder="例如：魔法森林 BGM"
                  className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Track type */}
              <div>
                <label className="mb-1 block text-sm font-medium">類型</label>
                <select
                  value={trackType}
                  onChange={(e) => setTrackType(e.target.value as TrackType)}
                  className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="song">歌曲/BGM</option>
                  <option value="transition">過場</option>
                  <option value="effect">音效</option>
                </select>
              </div>

              {/* Hotkey */}
              <div>
                <label className="mb-1 block text-sm font-medium">熱鍵（選填）</label>
                <input
                  type="text"
                  value={hotkey}
                  onChange={(e) => setHotkey(e.target.value.slice(0, 1))}
                  placeholder="例如：1、a、f"
                  maxLength={1}
                  className="w-20 rounded-lg border bg-background px-4 py-2 text-center font-mono focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="ml-auto hover:underline"
              >
                關閉
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border px-4 py-2 hover:bg-muted"
          >
            取消
          </button>

          {!currentJob && (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || prompt.length < 10}
              className={cn(
                'flex items-center gap-2 rounded-lg px-4 py-2 font-medium',
                isSubmitting || prompt.length < 10
                  ? 'bg-muted text-muted-foreground'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              )}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  提交中...
                </>
              ) : (
                <>
                  <Music className="h-4 w-4" />
                  生成 BGM
                </>
              )}
            </button>
          )}

          {isCompleted && (
            <button
              onClick={handleSave}
              disabled={!audioBlob || !trackName.trim()}
              className={cn(
                'flex items-center gap-2 rounded-lg px-4 py-2 font-medium',
                audioBlob && trackName.trim()
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-muted text-muted-foreground'
              )}
            >
              <Save className="h-4 w-4" />
              加入音軌
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default BGMGeneratorModal
