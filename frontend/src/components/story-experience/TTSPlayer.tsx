/**
 * TTSPlayer - TTS audio generation and playback
 * Feature: 016-story-experience-mvp
 *
 * Voice selection, audio generation, and playback controls.
 */

import { useEffect, useRef, useState } from 'react'

import { useStoryExperienceStore } from '@/stores/storyExperienceStore'

export function TTSPlayer() {
  const {
    voices,
    selectedVoiceId,
    setSelectedVoice,
    fetchVoices,
    generateTTS,
    audioContent,
    audioDurationMs,
    isGeneratingTTS,
    isLoadingVoices,
    fullStoryContent,
    editedContent,
    error,
    setStep,
  } = useStoryExperienceStore()

  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)

  // Fetch voices on mount
  useEffect(() => {
    if (voices.length === 0) {
      fetchVoices()
    }
  }, [fetchVoices, voices.length])

  // Create audio URL from base64 content
  const audioUrl = audioContent
    ? `data:audio/mp3;base64,${audioContent}`
    : null

  const handlePlay = () => {
    if (audioRef.current) {
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      setIsPlaying(false)
    }
  }

  const handleReplay = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
  }

  const textContent = editedContent || fullStoryContent
  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">TTS 音頻生成</h2>
        <button
          type="button"
          onClick={() => setStep('preview')}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          返回預覽
        </button>
      </div>

      {/* Text preview */}
      <div className="rounded-md border bg-muted/30 px-4 py-3">
        <p className="text-sm text-muted-foreground">
          即將為以下內容生成音頻（{textContent.length} 字）：
        </p>
        <p className="mt-2 max-h-32 overflow-y-auto text-sm leading-relaxed">
          {textContent.substring(0, 200)}
          {textContent.length > 200 && '...'}
        </p>
      </div>

      {/* Voice selector */}
      <div>
        <label htmlFor="voice-select" className="mb-1.5 block text-sm font-medium">
          選擇語音
        </label>
        {isLoadingVoices ? (
          <p className="text-sm text-muted-foreground">載入語音列表中...</p>
        ) : (
          <select
            id="voice-select"
            value={selectedVoiceId ?? ''}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {voices.map((voice) => (
              <option key={voice.id} value={voice.id}>
                {voice.name} ({voice.language}{voice.gender ? `, ${voice.gender}` : ''})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Generate button */}
      <button
        type="button"
        onClick={generateTTS}
        disabled={isGeneratingTTS || !selectedVoiceId}
        className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        {isGeneratingTTS ? '音頻生成中...' : '生成音頻'}
      </button>

      {/* Error display */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Audio player */}
      {audioUrl && (
        <div className="space-y-3 rounded-md border bg-card px-4 py-4">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">音頻就緒</span>
            {audioDurationMs && (
              <span className="text-muted-foreground">
                時長：{formatDuration(audioDurationMs)}
              </span>
            )}
          </div>

          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={handleEnded}
            preload="auto"
          />

          <div className="flex gap-2">
            {!isPlaying ? (
              <button
                type="button"
                onClick={handlePlay}
                className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                播放
              </button>
            ) : (
              <button
                type="button"
                onClick={handlePause}
                className="flex-1 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent"
              >
                暫停
              </button>
            )}
            <button
              type="button"
              onClick={handleReplay}
              className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              重播
            </button>
            <button
              type="button"
              onClick={generateTTS}
              disabled={isGeneratingTTS}
              className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
            >
              換聲音重新生成
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
