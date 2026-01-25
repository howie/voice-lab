/**
 * ModeSelector Component
 * Feature: 004-interaction-module
 * T036, T052-T056: Mode and provider selection for voice interaction.
 *
 * Allows users to select between Realtime mode (V2V) and Cascade mode,
 * and choose specific providers for each mode.
 */

import { useCallback, useEffect, useState } from 'react'

import { listProviders } from '@/services/interactionApi'
import type {
  CascadeLLMProvider,
  CascadeProviderConfig,
  CascadeSTTProvider,
  CascadeTTSProvider,
  InteractionMode,
  ProviderConfig,
  ProviderInfo,
  RealtimeProviderConfig,
} from '@/types/interaction'

// Voice information with gender and language support
interface VoiceInfo {
  id: string
  label: string
  gender: '男' | '女' | '中性'
  languages: string
}

// Available voices for each Realtime provider
const OPENAI_VOICES: VoiceInfo[] = [
  { id: 'shimmer', label: 'Shimmer', gender: '女', languages: '多語言（含中文）' },
  { id: 'coral', label: 'Coral', gender: '女', languages: '多語言（含中文）' },
  { id: 'sage', label: 'Sage', gender: '女', languages: '多語言（含中文）' },
  { id: 'ballad', label: 'Ballad', gender: '女', languages: '多語言（含中文）' },
  { id: 'alloy', label: 'Alloy', gender: '中性', languages: '多語言（含中文）' },
  { id: 'verse', label: 'Verse', gender: '男', languages: '多語言（含中文）' },
  { id: 'ash', label: 'Ash', gender: '男', languages: '多語言（含中文）' },
  { id: 'echo', label: 'Echo', gender: '男', languages: '多語言（含中文）' },
]

const GEMINI_VOICES: VoiceInfo[] = [
  { id: 'Kore', label: 'Kore', gender: '女', languages: '多語言（含中文）' },
  { id: 'Aoede', label: 'Aoede', gender: '女', languages: '多語言（含中文）' },
  { id: 'Puck', label: 'Puck', gender: '男', languages: '多語言（含中文）' },
  { id: 'Charon', label: 'Charon', gender: '男', languages: '多語言（含中文）' },
  { id: 'Fenrir', label: 'Fenrir', gender: '男', languages: '多語言（含中文）' },
]

// Available Gemini models for V2V
interface ModelInfo {
  id: string
  label: string
  description: string
  status: 'stable' | 'preview' | 'deprecated'
}

const GEMINI_MODELS: ModelInfo[] = [
  {
    id: 'gemini-2.5-flash-preview-native-audio-dialog',
    label: 'Gemini 2.5 Flash (Native Audio)',
    description: '30種HD語音，24種語言，更自然的對話（推薦）',
    status: 'preview',
  },
  {
    id: 'gemini-2.5-pro-preview-native-audio-dialog',
    label: 'Gemini 2.5 Pro (Native Audio)',
    description: '更強的推理能力，適合複雜對話',
    status: 'preview',
  },
  {
    id: 'gemini-2.5-flash',
    label: 'Gemini 2.5 Flash',
    description: '穩定版本，標準語音',
    status: 'stable',
  },
  {
    id: 'gemini-2.0-flash-exp',
    label: 'Gemini 2.0 Flash (Legacy)',
    description: '舊版，2026年3月退役',
    status: 'deprecated',
  },
]

// Default TTS voices by provider
const DEFAULT_TTS_VOICES: Record<string, string> = {
  azure: 'zh-TW-HsiaoChenNeural',
  gcp: 'zh-TW-Standard-A',
  elevenlabs: 'Rachel',
  voai: 'default',
}

interface ModeSelectorProps {
  /** Currently selected mode */
  mode: InteractionMode
  /** Current provider configuration */
  providerConfig: ProviderConfig
  /** Callback when mode changes */
  onModeChange: (mode: InteractionMode) => void
  /** Callback when provider config changes */
  onProviderChange: (config: ProviderConfig) => void
  /** Whether to disable the selector (e.g., during active session) */
  disabled?: boolean
  /** Additional CSS classes */
  className?: string
}

interface ProvidersState {
  stt: ProviderInfo[]
  llm: ProviderInfo[]
  tts: ProviderInfo[]
  loading: boolean
  error: string | null
}

export function ModeSelector({
  mode,
  providerConfig,
  onModeChange,
  onProviderChange,
  disabled = false,
  className = '',
}: ModeSelectorProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [providers, setProviders] = useState<ProvidersState>({
    stt: [],
    llm: [],
    tts: [],
    loading: false,
    error: null,
  })

  // Fetch available providers from API (T056)
  const fetchProviders = useCallback(async () => {
    setProviders((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const data = await listProviders()
      setProviders({
        stt: data.stt_providers,
        llm: data.llm_providers,
        tts: data.tts_providers,
        loading: false,
        error: null,
      })
    } catch (err) {
      console.error('Failed to fetch providers:', err)
      setProviders((prev) => ({
        ...prev,
        loading: false,
        error: '無法載入提供者清單',
      }))
    }
  }, [])

  useEffect(() => {
    if (mode === 'cascade' && isExpanded && providers.stt.length === 0 && !providers.loading) {
      fetchProviders()
    }
  }, [mode, isExpanded, providers.stt.length, providers.loading, fetchProviders])

  // Get current Realtime provider settings
  const realtimeConfig = providerConfig as RealtimeProviderConfig
  const currentRealtimeProvider = 'provider' in providerConfig ? realtimeConfig.provider : 'gemini'
  const currentRealtimeVoice = 'voice' in providerConfig ? realtimeConfig.voice : 'Kore'
  const currentRealtimeModel = 'model' in providerConfig ? realtimeConfig.model : undefined

  // Get current Cascade provider settings
  const cascadeConfig = providerConfig as CascadeProviderConfig
  const currentSTTProvider =
    'stt_provider' in providerConfig ? cascadeConfig.stt_provider : 'azure'
  const currentLLMProvider =
    'llm_provider' in providerConfig ? cascadeConfig.llm_provider : 'openai'
  const currentTTSProvider =
    'tts_provider' in providerConfig ? cascadeConfig.tts_provider : 'azure'
  const currentTTSVoice = 'tts_voice' in providerConfig ? cascadeConfig.tts_voice : undefined

  // Get available voices based on Realtime provider
  const availableRealtimeVoices =
    currentRealtimeProvider === 'gemini' ? GEMINI_VOICES : OPENAI_VOICES

  const handleModeChange = (newMode: InteractionMode) => {
    onModeChange(newMode)

    // Update provider config based on mode
    if (newMode === 'realtime') {
      onProviderChange({
        provider: 'openai',
        voice: 'shimmer', // 較適合中文對話的語音
      })
    } else {
      onProviderChange({
        stt_provider: 'azure',
        llm_provider: 'openai',
        tts_provider: 'azure',
        tts_voice: DEFAULT_TTS_VOICES['azure'],
      })
    }
  }

  const handleRealtimeProviderChange = (provider: 'openai' | 'gemini') => {
    // 預設選擇女性語音，較適合中文對話
    const defaultVoice = provider === 'gemini' ? 'Kore' : 'shimmer'
    onProviderChange({
      provider,
      voice: defaultVoice,
    })
  }

  const handleRealtimeVoiceChange = (voice: string) => {
    onProviderChange({
      ...providerConfig,
      voice,
    } as ProviderConfig)
  }

  // Cascade mode provider handlers (T052-T055)
  const handleSTTProviderChange = (provider: CascadeSTTProvider) => {
    onProviderChange({
      ...cascadeConfig,
      stt_provider: provider,
    })
  }

  const handleLLMProviderChange = (provider: CascadeLLMProvider) => {
    onProviderChange({
      ...cascadeConfig,
      llm_provider: provider,
    })
  }

  const handleTTSProviderChange = (provider: CascadeTTSProvider) => {
    onProviderChange({
      ...cascadeConfig,
      tts_provider: provider,
      tts_voice: DEFAULT_TTS_VOICES[provider] || undefined,
    })
  }

  const handleTTSVoiceChange = (voice: string) => {
    onProviderChange({
      ...cascadeConfig,
      tts_voice: voice,
    })
  }

  return (
    <div className={`rounded-lg border bg-card p-4 ${className}`}>
      {/* Mode Selection */}
      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium text-foreground">互動模式</label>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => handleModeChange('realtime')}
            disabled={disabled}
            className={`
              rounded-lg px-4 py-3 text-sm font-medium transition-all
              ${
                mode === 'realtime'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }
              disabled:cursor-not-allowed disabled:opacity-50
            `}
          >
            <div className="flex flex-col items-center gap-1">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="h-5 w-5"
              >
                <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06z" />
                <path d="M18.584 5.106a.75.75 0 011.06 0c3.808 3.807 3.808 9.98 0 13.788a.75.75 0 11-1.06-1.06 8.25 8.25 0 000-11.668.75.75 0 010-1.06z" />
                <path d="M15.932 7.757a.75.75 0 011.061 0 6 6 0 010 8.486.75.75 0 01-1.06-1.061 4.5 4.5 0 000-6.364.75.75 0 010-1.06z" />
              </svg>
              <span>即時模式</span>
              <span className="text-xs opacity-70">V2V API</span>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleModeChange('cascade')}
            disabled={disabled}
            className={`
              rounded-lg px-4 py-3 text-sm font-medium transition-all
              ${
                mode === 'cascade'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }
              disabled:cursor-not-allowed disabled:opacity-50
            `}
          >
            <div className="flex flex-col items-center gap-1">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="h-5 w-5"
              >
                <path
                  fillRule="evenodd"
                  d="M3 6a3 3 0 013-3h12a3 3 0 013 3v12a3 3 0 01-3 3H6a3 3 0 01-3-3V6zm4.5 7.5a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0v-2.25a.75.75 0 01.75-.75zm3.75-1.5a.75.75 0 00-1.5 0v4.5a.75.75 0 001.5 0V12zm2.25-3a.75.75 0 01.75.75v6.75a.75.75 0 01-1.5 0V9.75A.75.75 0 0113.5 9zm3.75-1.5a.75.75 0 00-1.5 0v9a.75.75 0 001.5 0v-9z"
                  clipRule="evenodd"
                />
              </svg>
              <span>串接模式</span>
              <span className="text-xs opacity-70">STT → LLM → TTS</span>
            </div>
          </button>
        </div>
      </div>

      {/* Provider Settings - Collapsible */}
      <div className="border-t pt-4">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex w-full items-center justify-between text-sm font-medium text-foreground"
        >
          <span>提供者設定</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={`h-5 w-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          >
            <path
              fillRule="evenodd"
              d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75 0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06 1.06l-7.5 7.5z"
              clipRule="evenodd"
            />
          </svg>
        </button>

        {isExpanded && (
          <div className="mt-4 space-y-4">
            {mode === 'realtime' ? (
              <>
                {/* Realtime Mode Provider */}
                <div>
                  <label className="mb-2 block text-sm text-muted-foreground">V2V 提供者</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => handleRealtimeProviderChange('openai')}
                      disabled={disabled}
                      className={`
                        rounded-lg px-3 py-2 text-sm transition-all
                        ${
                          currentRealtimeProvider === 'openai'
                            ? 'bg-primary/10 text-primary ring-1 ring-primary'
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        }
                        disabled:cursor-not-allowed disabled:opacity-50
                      `}
                    >
                      OpenAI Realtime
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRealtimeProviderChange('gemini')}
                      disabled={disabled}
                      className={`
                        rounded-lg px-3 py-2 text-sm transition-all
                        ${
                          currentRealtimeProvider === 'gemini'
                            ? 'bg-primary/10 text-primary ring-1 ring-primary'
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        }
                        disabled:cursor-not-allowed disabled:opacity-50
                      `}
                    >
                      Gemini Live
                    </button>
                  </div>
                </div>

                {/* Voice Selection */}
                <div>
                  <label className="mb-2 block text-sm text-muted-foreground">語音</label>
                  <select
                    value={currentRealtimeVoice}
                    onChange={(e) => handleRealtimeVoiceChange(e.target.value)}
                    disabled={disabled}
                    className="
                      w-full rounded-lg border bg-background px-3 py-2 text-sm
                      focus:outline-none focus:ring-2 focus:ring-primary
                      disabled:cursor-not-allowed disabled:opacity-50
                    "
                  >
                    {availableRealtimeVoices.map((voice) => (
                      <option key={voice.id} value={voice.id}>
                        {voice.label} ({voice.gender}) - {voice.languages}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Model Selection (Gemini only) */}
                {currentRealtimeProvider === 'gemini' && (
                  <div>
                    <label className="mb-2 block text-sm text-muted-foreground">模型版本</label>
                    <select
                      value={currentRealtimeModel || 'gemini-2.0-flash-exp'}
                      onChange={(e) =>
                        onProviderChange({
                          ...providerConfig,
                          model: e.target.value,
                        } as ProviderConfig)
                      }
                      disabled={disabled}
                      className="
                        w-full rounded-lg border bg-background px-3 py-2 text-sm
                        focus:outline-none focus:ring-2 focus:ring-primary
                        disabled:cursor-not-allowed disabled:opacity-50
                      "
                    >
                      {GEMINI_MODELS.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.label}{' '}
                          {model.status === 'preview'
                            ? '(預覽)'
                            : model.status === 'deprecated'
                              ? '(即將退役)'
                              : ''}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {GEMINI_MODELS.find((m) => m.id === (currentRealtimeModel || 'gemini-2.0-flash-exp'))
                        ?.description}
                    </p>
                  </div>
                )}
              </>
            ) : (
              /* Cascade Mode Providers (T052-T055) */
              <>
                {providers.loading ? (
                  <div className="flex items-center justify-center py-4 text-muted-foreground">
                    <svg
                      className="mr-2 h-4 w-4 animate-spin"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    載入提供者...
                  </div>
                ) : providers.error ? (
                  <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
                    {providers.error}
                    <button
                      type="button"
                      onClick={fetchProviders}
                      className="ml-2 underline hover:no-underline"
                    >
                      重試
                    </button>
                  </div>
                ) : (
                  <>
                    {/* STT Provider (T053) */}
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">
                        語音辨識 (STT)
                      </label>
                      <select
                        value={currentSTTProvider}
                        onChange={(e) =>
                          handleSTTProviderChange(e.target.value as CascadeSTTProvider)
                        }
                        disabled={disabled}
                        className="
                          w-full rounded-lg border bg-background px-3 py-2 text-sm
                          focus:outline-none focus:ring-2 focus:ring-primary
                          disabled:cursor-not-allowed disabled:opacity-50
                        "
                      >
                        {providers.stt.map((p) => (
                          <option key={p.name} value={p.name}>
                            {p.display_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* LLM Provider (T054) */}
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">
                        語言模型 (LLM)
                      </label>
                      <select
                        value={currentLLMProvider}
                        onChange={(e) =>
                          handleLLMProviderChange(e.target.value as CascadeLLMProvider)
                        }
                        disabled={disabled}
                        className="
                          w-full rounded-lg border bg-background px-3 py-2 text-sm
                          focus:outline-none focus:ring-2 focus:ring-primary
                          disabled:cursor-not-allowed disabled:opacity-50
                        "
                      >
                        {providers.llm.map((p) => (
                          <option key={p.name} value={p.name}>
                            {p.display_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* TTS Provider (T055) */}
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">
                        語音合成 (TTS)
                      </label>
                      <select
                        value={currentTTSProvider}
                        onChange={(e) =>
                          handleTTSProviderChange(e.target.value as CascadeTTSProvider)
                        }
                        disabled={disabled}
                        className="
                          w-full rounded-lg border bg-background px-3 py-2 text-sm
                          focus:outline-none focus:ring-2 focus:ring-primary
                          disabled:cursor-not-allowed disabled:opacity-50
                        "
                      >
                        {providers.tts.map((p) => (
                          <option key={p.name} value={p.name}>
                            {p.display_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* TTS Voice Input */}
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">TTS 語音 ID</label>
                      <input
                        type="text"
                        value={currentTTSVoice || DEFAULT_TTS_VOICES[currentTTSProvider] || ''}
                        onChange={(e) => handleTTSVoiceChange(e.target.value)}
                        disabled={disabled}
                        placeholder={DEFAULT_TTS_VOICES[currentTTSProvider] || '輸入語音 ID'}
                        className="
                          w-full rounded-lg border bg-background px-3 py-2 text-sm
                          focus:outline-none focus:ring-2 focus:ring-primary
                          disabled:cursor-not-allowed disabled:opacity-50
                        "
                      />
                      <p className="mt-1 text-xs text-muted-foreground">
                        不同 TTS 提供者支援不同的語音 ID
                      </p>
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ModeSelector
