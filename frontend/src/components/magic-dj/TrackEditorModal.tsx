/**
 * Track Editor Modal
 * Feature: 010-magic-dj-controller
 *
 * Modal for creating/editing tracks with TTS integration.
 */

import { useState, useEffect, useCallback } from 'react'
import { X, Play, Loader2, Save, Volume2 } from 'lucide-react'

import { ttsApi, type VoiceProfile } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { Track, TrackType } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface TrackEditorModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (track: Track, audioBlob: Blob) => void
  editingTrack?: Track | null
  existingText?: string
}

interface TTSSettings {
  provider: string
  voiceId: string
  language: string
  speed: number
}

// =============================================================================
// Default TTS Settings (VoAI)
// =============================================================================

const DEFAULT_TTS_SETTINGS: TTSSettings = {
  provider: 'voai', // 預設使用 VoAI 台灣語音
  voiceId: 'voai-tw-female-1', // VoAI 台灣女聲 - 小美
  language: 'zh-TW',
  speed: 1.0,
}

// 可用的 TTS Providers
const TTS_PROVIDERS = [
  { id: 'voai', name: 'VoAI 台灣語音' },
  { id: 'azure', name: 'Azure 語音' },
  { id: 'elevenlabs', name: 'ElevenLabs' },
  { id: 'gcp', name: 'Google Cloud' },
]

// Fallback 聲音（當 API 無法連線時使用）
const FALLBACK_VOICES: Record<string, Array<{ id: string; name: string; gender: string }>> = {
  voai: [
    { id: 'voai-tw-female-1', name: '小美', gender: 'female' },
    { id: 'voai-tw-male-1', name: '小明', gender: 'male' },
    { id: 'voai-tw-female-2', name: '小玲', gender: 'female' },
  ],
  azure: [
    { id: 'zh-TW-HsiaoChenNeural', name: '曉臻', gender: 'female' },
    { id: 'zh-TW-YunJheNeural', name: '雲哲', gender: 'male' },
    { id: 'zh-TW-HsiaoYuNeural', name: '曉雨', gender: 'female' },
  ],
  elevenlabs: [
    { id: 'rachel', name: 'Rachel', gender: 'female' },
    { id: 'adam', name: 'Adam', gender: 'male' },
  ],
  gcp: [
    { id: 'zh-TW-Standard-A', name: 'Standard A', gender: 'female' },
    { id: 'zh-TW-Standard-B', name: 'Standard B', gender: 'male' },
  ],
}

// =============================================================================
// Component
// =============================================================================

export function TrackEditorModal({
  isOpen,
  onClose,
  onSave,
  editingTrack,
  existingText,
}: TrackEditorModalProps) {
  // Form state
  const [name, setName] = useState('')
  const [text, setText] = useState('')
  const [trackType, setTrackType] = useState<TrackType>('effect')
  const [hotkey, setHotkey] = useState('')

  // TTS settings
  const [ttsSettings, setTtsSettings] = useState<TTSSettings>(DEFAULT_TTS_SETTINGS)

  // Available voices (fetched from API)
  const [availableVoices, setAvailableVoices] = useState<VoiceProfile[]>([])
  const [isLoadingVoices, setIsLoadingVoices] = useState(false)

  // Audio state
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Audio element ref
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null)

  // Initialize form when editing
  useEffect(() => {
    if (editingTrack) {
      setName(editingTrack.name)
      setTrackType(editingTrack.type)
      setHotkey(editingTrack.hotkey || '')
    } else {
      setName('')
      setTrackType('effect')
      setHotkey('')
    }

    if (existingText) {
      setText(existingText)
    } else {
      setText('')
    }

    setAudioBlob(null)
    setAudioUrl(null)
    setError(null)
  }, [editingTrack, existingText, isOpen])

  // Fetch voices when provider changes
  useEffect(() => {
    const applyFallbackVoices = (provider: string) => {
      const fallback = FALLBACK_VOICES[provider] || []
      const voices = fallback.map((v) => ({
        id: v.id,
        name: v.name,
        provider: provider,
        language: 'zh-TW',
        gender: v.gender,
      }))
      setAvailableVoices(voices)
      if (voices.length > 0) {
        setTtsSettings((s) => {
          if (!voices.some((v) => v.id === s.voiceId)) {
            return { ...s, voiceId: voices[0].id }
          }
          return s
        })
      }
    }

    const fetchVoices = async () => {
      setIsLoadingVoices(true)
      try {
        const response = await ttsApi.getVoices(ttsSettings.provider, {
          language: 'zh-TW', // 優先顯示台灣中文
        })
        const voices = response.data
        if (voices.length > 0) {
          setAvailableVoices(voices)
          // If current voice is not in the list, select the first one
          setTtsSettings((s) => {
            if (!voices.some((v) => v.id === s.voiceId)) {
              return { ...s, voiceId: voices[0].id }
            }
            return s
          })
        } else {
          // Use fallback if API returns empty
          applyFallbackVoices(ttsSettings.provider)
        }
      } catch (err) {
        console.error('Failed to fetch voices, using fallback:', err)
        applyFallbackVoices(ttsSettings.provider)
      } finally {
        setIsLoadingVoices(false)
      }
    }

    if (isOpen) {
      fetchVoices()
    }
  }, [ttsSettings.provider, isOpen])

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  // Generate TTS audio
  const handleGenerate = useCallback(async () => {
    if (!text.trim()) {
      setError('請輸入語音內容')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      const blob = await ttsApi.synthesizeBinary({
        text: text.trim(),
        provider: ttsSettings.provider,
        voice_id: ttsSettings.voiceId,
        language: ttsSettings.language,
        speed: ttsSettings.speed,
      })

      // Revoke old URL
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }

      const newUrl = URL.createObjectURL(blob)
      setAudioBlob(blob)
      setAudioUrl(newUrl)
    } catch (err) {
      console.error('TTS generation failed:', err)
      setError('語音生成失敗，請確認後端服務已啟動')
    } finally {
      setIsGenerating(false)
    }
  }, [text, ttsSettings, audioUrl])

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
    if (!name.trim()) {
      setError('請輸入音軌名稱')
      return
    }

    if (!audioBlob) {
      setError('請先生成語音')
      return
    }

    const track: Track = {
      id: editingTrack?.id || `custom_${Date.now()}`,
      name: name.trim(),
      type: trackType,
      url: '', // Will be set by parent with blob URL
      hotkey: hotkey || undefined,
      isCustom: true,
      textContent: text.trim(), // Save text for future editing
    }

    onSave(track, audioBlob)
    onClose()
  }, [name, text, audioBlob, trackType, hotkey, editingTrack, onSave, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-background p-6 shadow-xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold">
            {editingTrack ? '編輯音軌' : '新增音軌'}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-muted"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* Track Name */}
          <div>
            <label className="mb-1 block text-sm font-medium">音軌名稱</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：開場白"
              className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Track Type */}
          <div>
            <label className="mb-1 block text-sm font-medium">類型</label>
            <select
              value={trackType}
              onChange={(e) => setTrackType(e.target.value as TrackType)}
              className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="intro">開場</option>
              <option value="transition">過場</option>
              <option value="effect">音效</option>
              <option value="song">歌曲</option>
              <option value="filler">填補音效</option>
              <option value="rescue">救場語音</option>
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

          {/* Text Content */}
          <div>
            <label className="mb-1 block text-sm font-medium">語音內容</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="輸入要轉換成語音的文字..."
              rows={4}
              className="w-full rounded-lg border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <div className="mt-1 text-right text-xs text-muted-foreground">
              {text.length} 字
            </div>
          </div>

          {/* TTS Settings */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <h3 className="mb-3 text-sm font-medium">TTS 設定</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">
                  Provider
                </label>
                <select
                  value={ttsSettings.provider}
                  onChange={(e) => {
                    setTtsSettings((s) => ({
                      ...s,
                      provider: e.target.value,
                    }))
                  }}
                  className="w-full rounded border bg-background px-2 py-1 text-sm"
                >
                  {TTS_PROVIDERS.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">
                  聲音 {isLoadingVoices && '(載入中...)'}
                </label>
                <select
                  value={ttsSettings.voiceId}
                  onChange={(e) =>
                    setTtsSettings((s) => ({ ...s, voiceId: e.target.value }))
                  }
                  disabled={isLoadingVoices}
                  className="w-full rounded border bg-background px-2 py-1 text-sm disabled:opacity-50"
                >
                  {availableVoices.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name} {voice.gender === 'female' ? '(女)' : voice.gender === 'male' ? '(男)' : ''}
                    </option>
                  ))}
                  {availableVoices.length === 0 && !isLoadingVoices && (
                    <option value={ttsSettings.voiceId}>
                      {ttsSettings.voiceId || '無可用聲音'}
                    </option>
                  )}
                </select>
              </div>
            </div>
            <div className="mt-3">
              <label className="mb-1 block text-xs text-muted-foreground">
                語速
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={ttsSettings.speed}
                  onChange={(e) =>
                    setTtsSettings((s) => ({
                      ...s,
                      speed: parseFloat(e.target.value),
                    }))
                  }
                  className="flex-1"
                />
                <span className="text-xs w-10 text-center">{ttsSettings.speed}x</span>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Generate & Preview */}
          <div className="flex gap-2">
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !text.trim()}
              className={cn(
                'flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 font-medium transition-colors',
                isGenerating
                  ? 'bg-muted text-muted-foreground'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              )}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>生成中...</span>
                </>
              ) : (
                <>
                  <Volume2 className="h-5 w-5" />
                  <span>生成語音</span>
                </>
              )}
            </button>

            {audioUrl && (
              <button
                onClick={isPlaying ? handleStop : handlePlay}
                className="flex items-center gap-2 rounded-lg border bg-background px-4 py-3 font-medium hover:bg-muted"
              >
                <Play className={cn('h-5 w-5', isPlaying && 'text-primary')} />
                <span>{isPlaying ? '停止' : '試聽'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border px-4 py-2 hover:bg-muted"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={!audioBlob || !name.trim()}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-2 font-medium',
              audioBlob && name.trim()
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-muted text-muted-foreground'
            )}
          >
            <Save className="h-4 w-4" />
            <span>儲存</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default TrackEditorModal
