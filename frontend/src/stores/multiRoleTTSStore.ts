/**
 * Multi-Role TTS State Store
 * T028: Create Zustand store for multi-role TTS functionality
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { multiRoleTTSApi } from '@/lib/multiRoleTTSApi'
import { ttsApi } from '@/lib/api'
import type {
  DialogueTurn,
  MultiRoleTTSResult,
  ProviderMultiRoleCapability,
  VoiceAssignment,
  MultiRoleTTSProvider,
} from '@/types/multi-role-tts'
import type { VoiceProfile } from '@/lib/api'

interface MultiRoleTTSState {
  // Input
  dialogueText: string
  provider: MultiRoleTTSProvider

  // Parsed data
  parsedTurns: DialogueTurn[]
  speakers: string[]

  // Voice assignments
  voiceAssignments: VoiceAssignment[]

  // Provider capabilities
  capabilities: ProviderMultiRoleCapability[]
  currentCapability: ProviderMultiRoleCapability | null

  // Available voices for current provider
  voices: VoiceProfile[]
  voicesLoading: boolean

  // Synthesis options
  language: string
  outputFormat: string
  gapMs: number
  crossfadeMs: number

  // Output
  result: MultiRoleTTSResult | null
  audioUrl: string | null
  isLoading: boolean
  isParsing: boolean
  error: string | null

  // Request cancellation
  abortController: AbortController | null
  showProviderSwitchConfirm: boolean
  pendingProvider: MultiRoleTTSProvider | null

  // Actions
  setDialogueText: (text: string) => void
  setProvider: (provider: MultiRoleTTSProvider) => void
  setVoiceAssignment: (speaker: string, voiceId: string, voiceName?: string) => void
  setLanguage: (language: string) => void
  setOutputFormat: (format: string) => void
  setGapMs: (gapMs: number) => void
  setCrossfadeMs: (crossfadeMs: number) => void

  // Request cancellation actions
  cancelSynthesis: () => void
  confirmProviderSwitch: () => void
  cancelProviderSwitch: () => void

  // Async actions
  loadCapabilities: () => Promise<void>
  loadVoices: () => Promise<void>
  parseDialogue: () => Promise<void>
  synthesize: () => Promise<void>
  reset: () => void
}

export const useMultiRoleTTSStore = create<MultiRoleTTSState>()(
  persist(
    (set, get) => ({
      // Initial state
      dialogueText: '',
      provider: 'elevenlabs',
      parsedTurns: [],
      speakers: [],
      voiceAssignments: [],
      capabilities: [],
      currentCapability: null,
      voices: [],
      voicesLoading: false,
      language: 'zh-TW',
      outputFormat: 'mp3',
      gapMs: 300,
      crossfadeMs: 50,
      result: null,
      audioUrl: null,
      isLoading: false,
      isParsing: false,
      error: null,
      abortController: null,
      showProviderSwitchConfirm: false,
      pendingProvider: null,

      // Setters
      setDialogueText: (dialogueText) => {
        set({ dialogueText, parsedTurns: [], speakers: [], error: null })
      },

      setProvider: (provider) => {
        const { isLoading } = get()

        // If synthesis is in progress, show confirmation dialog
        if (isLoading) {
          set({ showProviderSwitchConfirm: true, pendingProvider: provider })
          return
        }

        // Proceed with provider switch
        const { capabilities } = get()
        const currentCapability =
          capabilities.find((c) => c.providerName === provider) || null

        // Clear voice assignments when provider changes
        set({
          provider,
          currentCapability,
          voiceAssignments: [],
          voices: [],
          result: null,
          audioUrl: null,
          error: null,
        })

        // Load voices for new provider
        get().loadVoices()
      },

      setVoiceAssignment: (speaker, voiceId, voiceName) => {
        const { voiceAssignments } = get()
        const existing = voiceAssignments.find((va) => va.speaker === speaker)

        if (existing) {
          set({
            voiceAssignments: voiceAssignments.map((va) =>
              va.speaker === speaker ? { ...va, voiceId, voiceName } : va
            ),
          })
        } else {
          set({
            voiceAssignments: [...voiceAssignments, { speaker, voiceId, voiceName }],
          })
        }
      },

      setLanguage: (language) => {
        set({ language })
        get().loadVoices()
      },

      setOutputFormat: (outputFormat) => set({ outputFormat }),

      setGapMs: (gapMs) => set({ gapMs: Math.max(0, Math.min(2000, gapMs)) }),

      setCrossfadeMs: (crossfadeMs) =>
        set({ crossfadeMs: Math.max(0, Math.min(500, crossfadeMs)) }),

      // Request cancellation actions
      cancelSynthesis: () => {
        const { abortController, audioUrl } = get()
        if (abortController) {
          abortController.abort()
        }
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl)
        }
        set({
          abortController: null,
          isLoading: false,
          result: null,
          audioUrl: null,
          error: '合成已取消',
        })
      },

      confirmProviderSwitch: () => {
        const { pendingProvider, abortController, audioUrl } = get()

        // Cancel current synthesis
        if (abortController) {
          abortController.abort()
        }
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl)
        }

        if (pendingProvider) {
          const { capabilities } = get()
          const currentCapability =
            capabilities.find((c) => c.providerName === pendingProvider) || null

          set({
            provider: pendingProvider,
            currentCapability,
            voiceAssignments: [],
            voices: [],
            result: null,
            audioUrl: null,
            error: null,
            isLoading: false,
            abortController: null,
            showProviderSwitchConfirm: false,
            pendingProvider: null,
          })

          // Load voices for new provider
          get().loadVoices()
        }
      },

      cancelProviderSwitch: () => {
        set({ showProviderSwitchConfirm: false, pendingProvider: null })
      },

      // Async actions
      loadCapabilities: async () => {
        try {
          const response = await multiRoleTTSApi.getCapabilities()
          const { provider } = get()
          const currentCapability =
            response.providers.find((c) => c.providerName === provider) || null

          set({
            capabilities: response.providers,
            currentCapability,
          })
        } catch (error) {
          console.error('Failed to load capabilities:', error)
        }
      },

      loadVoices: async () => {
        const { provider, language } = get()
        set({ voicesLoading: true })

        try {
          const response = await ttsApi.getVoices(provider, language)
          set({ voices: response.data, voicesLoading: false })
        } catch (error) {
          console.error('Failed to load voices:', error)
          set({ voices: [], voicesLoading: false })
        }
      },

      parseDialogue: async () => {
        const { dialogueText, currentCapability } = get()

        if (!dialogueText.trim()) {
          set({ error: '請輸入對話文字' })
          return
        }

        set({ isParsing: true, error: null })

        try {
          const response = await multiRoleTTSApi.parseDialogue(dialogueText)

          // Check speaker count against capability
          if (
            currentCapability &&
            response.speakers.length > currentCapability.maxSpeakers
          ) {
            set({
              error: `說話者數量 (${response.speakers.length}) 超過 ${currentCapability.providerName} 的限制 (${currentCapability.maxSpeakers})`,
              isParsing: false,
            })
            return
          }

          // Check character count against capability
          if (
            currentCapability &&
            response.totalCharacters > currentCapability.characterLimit
          ) {
            set({
              error: `字數 (${response.totalCharacters}) 超過 ${currentCapability.providerName} 的限制 (${currentCapability.characterLimit})`,
              isParsing: false,
            })
            return
          }

          // Initialize voice assignments for new speakers
          const { voiceAssignments, voices } = get()
          const newAssignments = [...voiceAssignments]

          for (const speaker of response.speakers) {
            if (!newAssignments.find((va) => va.speaker === speaker)) {
              // Auto-assign first available voice
              const voice = voices[newAssignments.length % voices.length]
              if (voice) {
                newAssignments.push({
                  speaker,
                  voiceId: voice.id,
                  voiceName: voice.name,
                })
              }
            }
          }

          set({
            parsedTurns: response.turns,
            speakers: response.speakers,
            voiceAssignments: newAssignments,
            isParsing: false,
          })
        } catch (error: unknown) {
          const message =
            (error as { response?: { data?: { detail?: string } } })?.response?.data
              ?.detail ||
            (error instanceof Error ? error.message : '解析對話失敗')
          set({ error: message, isParsing: false })
        }
      },

      synthesize: async () => {
        const {
          provider,
          parsedTurns,
          voiceAssignments,
          speakers,
          language,
          outputFormat,
          gapMs,
          crossfadeMs,
        } = get()

        // Validate
        if (parsedTurns.length === 0) {
          set({ error: '請先解析對話' })
          return
        }

        // Check all speakers have voice assignments
        const assignedSpeakers = new Set(voiceAssignments.map((va) => va.speaker))
        const missingSpeakers = speakers.filter((s) => !assignedSpeakers.has(s))
        if (missingSpeakers.length > 0) {
          set({ error: `請為以下說話者指定語音: ${missingSpeakers.join(', ')}` })
          return
        }

        // Create AbortController for cancellation
        const abortController = new AbortController()
        set({ isLoading: true, error: null, result: null, audioUrl: null, abortController })

        try {
          const result = await multiRoleTTSApi.synthesize(
            provider,
            parsedTurns,
            voiceAssignments,
            { language, outputFormat, gapMs, crossfadeMs, signal: abortController.signal }
          )

          // Create audio URL from base64
          let audioUrl: string | null = null
          if (result.audioContent) {
            const binaryString = atob(result.audioContent)
            const bytes = new Uint8Array(binaryString.length)
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i)
            }
            const blob = new Blob([bytes], { type: result.contentType })
            audioUrl = URL.createObjectURL(blob)
          }

          set({ result, audioUrl, isLoading: false, abortController: null })
        } catch (error: unknown) {
          // Check if the request was aborted
          if (error instanceof Error && error.name === 'AbortError') {
            // Already handled by cancelSynthesis
            return
          }
          // Handle axios cancel
          if ((error as { code?: string })?.code === 'ERR_CANCELED') {
            return
          }

          const message =
            (error as { response?: { data?: { detail?: string } } })?.response?.data
              ?.detail ||
            (error instanceof Error ? error.message : '語音合成失敗')
          set({ error: message, isLoading: false, abortController: null })
        }
      },

      reset: () => {
        // Cancel any in-progress synthesis
        const { audioUrl, abortController } = get()
        if (abortController) {
          abortController.abort()
        }
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl)
        }

        set({
          dialogueText: '',
          parsedTurns: [],
          speakers: [],
          voiceAssignments: [],
          result: null,
          audioUrl: null,
          isLoading: false,
          isParsing: false,
          error: null,
          abortController: null,
          showProviderSwitchConfirm: false,
          pendingProvider: null,
        })
      },
    }),
    {
      name: 'multi-role-tts-storage',
      partialize: (state) => ({
        provider: state.provider,
        language: state.language,
        outputFormat: state.outputFormat,
        gapMs: state.gapMs,
        crossfadeMs: state.crossfadeMs,
      }),
    }
  )
)
