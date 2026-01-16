/**
 * TTS State Store
 * T064: Create TTS state store with parameters (Zustand)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ttsApi, SynthesizeResponse, VoiceProfile } from '@/lib/api'

interface TTSState {
  // Input
  text: string
  provider: string
  voiceId: string
  language: string

  // Parameters
  speed: number
  pitch: number
  volume: number
  outputFormat: string

  // Output
  result: SynthesizeResponse | null
  isLoading: boolean
  error: string | null

  // Voices cache
  voices: VoiceProfile[]
  voicesLoading: boolean

  // Actions
  setText: (text: string) => void
  setProvider: (provider: string) => void
  setVoiceId: (voiceId: string) => void
  setLanguage: (language: string) => void
  setSpeed: (speed: number) => void
  setPitch: (pitch: number) => void
  setVolume: (volume: number) => void
  setOutputFormat: (format: string) => void

  // Async actions
  synthesize: () => Promise<void>
  loadVoices: (provider: string, language?: string) => Promise<void>
  reset: () => void
}

const DEFAULT_VOICES: Record<string, string> = {
  azure: 'zh-TW-HsiaoChenNeural',
  gcp: 'cmn-TW-Standard-A',
  elevenlabs: '21m00Tcm4TlvDq8ikWAM',
  voai: 'voai-tw-female-1',
}

export const useTTSStore = create<TTSState>()(
  persist(
    (set, get) => ({
      // Initial state
      text: '',
      provider: 'azure',
      voiceId: DEFAULT_VOICES.azure,
      language: 'zh-TW',
      speed: 1.0,
      pitch: 0.0,
      volume: 1.0,
      outputFormat: 'mp3',
      result: null,
      isLoading: false,
      error: null,
      voices: [],
      voicesLoading: false,

      // Setters
      setText: (text) => set({ text }),

      setProvider: (provider) => {
        const defaultVoice = DEFAULT_VOICES[provider] || ''
        set({
          provider,
          voiceId: defaultVoice,
          result: null,
          error: null,
        })
        // Load voices for new provider
        get().loadVoices(provider, get().language)
      },

      setVoiceId: (voiceId) => set({ voiceId }),

      setLanguage: (language) => {
        set({ language })
        // Reload voices for new language
        get().loadVoices(get().provider, language)
      },

      setSpeed: (speed) => set({ speed: Math.max(0.5, Math.min(2.0, speed)) }),

      setPitch: (pitch) => set({ pitch: Math.max(-20, Math.min(20, pitch)) }),

      setVolume: (volume) => set({ volume: Math.max(0, Math.min(2.0, volume)) }),

      setOutputFormat: (outputFormat) => set({ outputFormat }),

      // Async actions
      synthesize: async () => {
        const state = get()

        if (!state.text.trim()) {
          set({ error: '請輸入文字' })
          return
        }

        if (!state.voiceId) {
          set({ error: '請選擇語音' })
          return
        }

        set({ isLoading: true, error: null, result: null })

        try {
          const response = await ttsApi.synthesize({
            text: state.text,
            provider: state.provider,
            voice_id: state.voiceId,
            language: state.language,
            speed: state.speed,
            pitch: state.pitch,
            volume: state.volume,
            output_format: state.outputFormat,
          })

          set({ result: response.data, isLoading: false })
        } catch (error: any) {
          const message =
            error.response?.data?.error?.message ||
            error.message ||
            '語音合成失敗'
          set({ error: message, isLoading: false })
        }
      },

      loadVoices: async (provider, language) => {
        set({ voicesLoading: true })

        try {
          const response = await ttsApi.getVoices(provider, language)
          set({ voices: response.data, voicesLoading: false })

          // Auto-select first voice if current voice not in list
          const currentVoiceId = get().voiceId
          const voiceExists = response.data.some((v) => v.id === currentVoiceId)
          if (!voiceExists && response.data.length > 0) {
            set({ voiceId: response.data[0].id })
          }
        } catch (error) {
          console.error('Failed to load voices:', error)
          set({ voicesLoading: false })
        }
      },

      reset: () =>
        set({
          text: '',
          result: null,
          error: null,
          isLoading: false,
        }),
    }),
    {
      name: 'tts-storage',
      partialize: (state) => ({
        provider: state.provider,
        voiceId: state.voiceId,
        language: state.language,
        speed: state.speed,
        pitch: state.pitch,
        volume: state.volume,
        outputFormat: state.outputFormat,
      }),
    }
  )
)
