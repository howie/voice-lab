/**
 * Track Editor Modal
 * Feature: 010-magic-dj-controller
 * Feature: 011-magic-dj-audio-features
 *
 * Modal for creating/editing tracks with TTS integration.
 * 011-T017~T019: Audio source selection (TTS / Upload) and preview.
 */

import { useState, useEffect, useCallback } from 'react'
import { X, Play, Square, Loader2, Save, Volume2, Mic, Upload } from 'lucide-react'

import { ttsApi, type VoiceProfile } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useAvailableTTSProviders } from '@/hooks/useAvailableTTSProviders'
import type { Track, TrackType, FileUploadState } from '@/types/magic-dj'
import { AudioDropzone } from './AudioDropzone'

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

/** Audio source mode for the editor (011-T017) */
type AudioSourceMode = 'tts' | 'upload'

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

// 可用的 TTS Providers (full list; filtered at runtime by useAvailableTTSProviders)
const ALL_TTS_PROVIDERS = [
  { id: 'voai', name: 'VoAI 台灣語音' },
  { id: 'azure', name: 'Azure 語音' },
  { id: 'elevenlabs', name: 'ElevenLabs' },
  { id: 'gcp', name: 'Google Cloud TTS' },
  { id: 'gemini', name: 'Gemini TTS' },
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
  gemini: [
    { id: 'Kore', name: 'Kore', gender: 'female' },
    { id: 'Charon', name: 'Charon', gender: 'male' },
    { id: 'Aoede', name: 'Aoede', gender: 'female' },
    { id: 'Puck', name: 'Puck', gender: 'male' },
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

  // 011-T017: Audio source mode
  const [audioSourceMode, setAudioSourceMode] = useState<AudioSourceMode>('tts')

  // 011-T030: Default volume setting
  const [defaultVolume, setDefaultVolume] = useState(1.0)

  // TTS settings
  const [ttsSettings, setTtsSettings] = useState<TTSSettings>(DEFAULT_TTS_SETTINGS)

  // Filter TTS providers to only show available ones (with API keys configured)
  const { providers: ttsProviders, loading: providersLoading } =
    useAvailableTTSProviders({
      allProviders: ALL_TTS_PROVIDERS,
      getKey: (p) => p.id,
      value: ttsSettings.provider,
      onChange: (newProvider) =>
        setTtsSettings((s) => ({ ...s, provider: newProvider })),
    })

  // Available voices (fetched from API)
  const [availableVoices, setAvailableVoices] = useState<VoiceProfile[]>([])
  const [isLoadingVoices, setIsLoadingVoices] = useState(false)

  // Audio state
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 011-T018: Upload state
  const [uploadState, setUploadState] = useState<FileUploadState | null>(null)

  // Audio element ref
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null)

  // Initialize form when editing
  useEffect(() => {
    if (editingTrack) {
      setName(editingTrack.name)
      setTrackType(editingTrack.type)
      setHotkey(editingTrack.hotkey || '')
      // 011-T017: Set audio source mode based on existing track
      setAudioSourceMode(editingTrack.source === 'upload' ? 'upload' : 'tts')
      // 011-T030: Set default volume
      setDefaultVolume(editingTrack.volume ?? 1.0)
    } else {
      setName('')
      setTrackType('effect')
      setHotkey('')
      setAudioSourceMode('tts')
      setDefaultVolume(1.0)
    }

    if (existingText) {
      setText(existingText)
    } else {
      setText('')
    }

    setAudioBlob(null)
    setAudioUrl(null)
    setError(null)
    setUploadState(null)
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

  // 011-T018: Handle file upload
  const handleFileAccepted = useCallback((state: FileUploadState) => {
    setUploadState(state)
    setError(null)

    if (state.audioUrl && state.file) {
      // Convert File to Blob for saving
      setAudioBlob(state.file)
      setAudioUrl(state.audioUrl)
    } else {
      setAudioBlob(null)
      setAudioUrl(null)
    }
  }, [])

  // 011-T019: Play preview (unified for both TTS and upload)
  const handlePreviewPlay = useCallback(() => {
    const previewUrl = audioSourceMode === 'upload' ? uploadState?.audioUrl : audioUrl
    if (!previewUrl) return

    if (audioElement) {
      audioElement.pause()
    }

    const audio = new Audio(previewUrl)
    setAudioElement(audio)

    audio.onplay = () => setIsPlaying(true)
    audio.onended = () => setIsPlaying(false)
    audio.onpause = () => setIsPlaying(false)

    audio.play()
  }, [audioSourceMode, uploadState?.audioUrl, audioUrl, audioElement])

  const handlePreviewStop = useCallback(() => {
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

    // 011-T017: Check audio based on source mode
    if (audioSourceMode === 'tts' && !audioBlob) {
      setError('請先生成語音')
      return
    }

    if (audioSourceMode === 'upload' && !uploadState?.file) {
      setError('請先選擇音檔')
      return
    }

    const isUpload = audioSourceMode === 'upload'
    const finalBlob = isUpload ? uploadState!.file! : audioBlob!

    const track: Track = {
      id: editingTrack?.id || `custom_${Date.now()}`,
      name: name.trim(),
      type: trackType,
      url: '', // Will be set by parent with blob URL
      hotkey: hotkey || undefined,
      isCustom: true,
      textContent: isUpload ? undefined : text.trim(),
      // 011 Audio Features
      source: isUpload ? 'upload' : 'tts',
      originalFileName: isUpload ? uploadState!.fileName : undefined,
      volume: defaultVolume,
      duration: isUpload ? uploadState!.duration ?? undefined : undefined,
      audioBase64: isUpload ? uploadState!.audioBase64 ?? undefined : undefined,
    }

    onSave(track, finalBlob)
    onClose()
  }, [name, text, audioBlob, trackType, hotkey, editingTrack, onSave, onClose, audioSourceMode, uploadState, defaultVolume])

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

          {/* Hotkey and Volume Row */}
          <div className="flex gap-4">
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

            {/* 011-T030: Default Volume */}
            <div className="flex-1">
              <label className="mb-1 block text-sm font-medium">預設音量</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={defaultVolume}
                  onChange={(e) => setDefaultVolume(parseFloat(e.target.value))}
                  className="flex-1 h-2 cursor-pointer appearance-none rounded-full bg-muted"
                />
                <span className="w-12 text-sm text-muted-foreground text-right tabular-nums">
                  {Math.round(defaultVolume * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* 011-T017: Audio Source Mode Toggle */}
          <div>
            <label className="mb-2 block text-sm font-medium">音源方式</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setAudioSourceMode('tts')}
                className={cn(
                  'flex flex-1 items-center justify-center gap-2 rounded-lg border px-4 py-3 transition-colors',
                  audioSourceMode === 'tts'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:bg-muted'
                )}
              >
                <Mic className="h-5 w-5" />
                <span>TTS 語音合成</span>
              </button>
              <button
                type="button"
                onClick={() => setAudioSourceMode('upload')}
                className={cn(
                  'flex flex-1 items-center justify-center gap-2 rounded-lg border px-4 py-3 transition-colors',
                  audioSourceMode === 'upload'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:bg-muted'
                )}
              >
                <Upload className="h-5 w-5" />
                <span>上傳音檔</span>
              </button>
            </div>
          </div>

          {/* 011-T018: Show AudioDropzone when upload mode is selected */}
          {audioSourceMode === 'upload' && (
            <AudioDropzone
              onFileAccepted={handleFileAccepted}
              onError={setError}
              currentFile={uploadState?.file ? {
                fileName: uploadState.fileName,
                fileSize: uploadState.fileSize,
                duration: uploadState.duration,
              } : null}
            />
          )}

          {/* Text Content - Only show for TTS mode */}
          {audioSourceMode === 'tts' && (
            <>
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
                    {providersLoading ? (
                      <div className="flex h-[30px] w-full items-center rounded border bg-background px-2 text-xs text-muted-foreground">
                        載入中...
                      </div>
                    ) : (
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
                        {ttsProviders.map((provider) => (
                          <option key={provider.id} value={provider.id}>
                            {provider.name}
                          </option>
                        ))}
                      </select>
                    )}
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
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Generate & Preview - Different UI based on source mode */}
          <div className="flex gap-2">
            {audioSourceMode === 'tts' ? (
              // TTS Mode: Generate button
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
            ) : (
              // Upload Mode: Just show preview button area (file upload is handled by dropzone)
              <div className="flex-1" />
            )}

            {/* 011-T019: Preview button - shown when audio is available */}
            {((audioSourceMode === 'tts' && audioUrl) ||
              (audioSourceMode === 'upload' && uploadState?.audioUrl)) && (
              <button
                onClick={isPlaying ? handlePreviewStop : handlePreviewPlay}
                className={cn(
                  'flex items-center gap-2 rounded-lg border px-4 py-3 font-medium transition-colors',
                  isPlaying
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'bg-background hover:bg-muted'
                )}
              >
                {isPlaying ? (
                  <>
                    <Square className="h-5 w-5" />
                    <span>停止</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    <span>試聽</span>
                  </>
                )}
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
            disabled={
              !name.trim() ||
              (audioSourceMode === 'tts' && !audioBlob) ||
              (audioSourceMode === 'upload' && !uploadState?.file)
            }
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-2 font-medium',
              name.trim() &&
                ((audioSourceMode === 'tts' && audioBlob) ||
                  (audioSourceMode === 'upload' && uploadState?.file))
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
