/**
 * Interaction State Store
 * Feature: 004-interaction-module
 *
 * T025: Zustand store for real-time voice interaction state management.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type {
  ConnectionStatus,
  ConversationTurn,
  InteractionMode,
  InteractionOptions,
  InteractionSession,
  InteractionState,
  LatencyStats,
  ProviderConfig,
  SystemPromptTemplate,
  TurnLatencyData,
} from '@/types/interaction'

// =============================================================================
// State Interface
// =============================================================================

interface InteractionStoreState {
  // Connection state
  connectionStatus: ConnectionStatus
  interactionState: InteractionState

  // Session state
  session: InteractionSession | null
  currentTurn: ConversationTurn | null
  turnHistory: ConversationTurn[]

  // Audio state
  isRecording: boolean
  isMuted: boolean
  inputVolume: number
  outputVolume: number

  // Transcript state
  userTranscript: string
  aiResponseText: string
  isTranscriptFinal: boolean

  // Latency tracking
  currentLatency: number | null
  currentTurnLatency: TurnLatencyData | null
  sessionStats: LatencyStats | null

  // Configuration
  options: InteractionOptions
  availableTemplates: SystemPromptTemplate[]

  // Error state
  error: string | null

  // Actions - Connection
  setConnectionStatus: (status: ConnectionStatus) => void
  setInteractionState: (state: InteractionState) => void

  // Actions - Session
  setSession: (session: InteractionSession | null) => void
  setCurrentTurn: (turn: ConversationTurn | null) => void
  addTurnToHistory: (turn: ConversationTurn) => void
  clearTurnHistory: () => void

  // Actions - Audio
  setIsRecording: (recording: boolean) => void
  setIsMuted: (muted: boolean) => void
  setInputVolume: (volume: number) => void
  setOutputVolume: (volume: number) => void

  // Actions - Transcript
  setUserTranscript: (transcript: string, isFinal?: boolean) => void
  appendAIResponse: (text: string) => void
  clearTranscripts: () => void

  // Actions - Latency
  setCurrentLatency: (latency: number | null) => void
  setCurrentTurnLatency: (latency: TurnLatencyData | null) => void
  setSessionStats: (stats: LatencyStats | null) => void

  // Actions - Configuration
  setMode: (mode: InteractionMode) => void
  setProviderConfig: (config: ProviderConfig) => void
  setSystemPrompt: (prompt: string) => void
  setOptions: (options: Partial<InteractionOptions>) => void
  setAvailableTemplates: (templates: SystemPromptTemplate[]) => void
  // US4: Role and scenario configuration
  setUserRole: (role: string) => void
  setAiRole: (role: string) => void
  setScenarioContext: (context: string) => void
  // US5: Barge-in configuration
  setBargeInEnabled: (enabled: boolean) => void
  // Performance optimization
  setLightweightMode: (enabled: boolean) => void

  // Actions - Error
  setError: (error: string | null) => void

  // Actions - General
  reset: () => void
  resetSession: () => void
}

// =============================================================================
// Initial State
// =============================================================================

// Default system prompt for Chinese kindergarten teacher persona
// Note: Speech pace instruction helps control Gemini's output speed
const DEFAULT_SYSTEM_PROMPT = `你是一個講中文台灣腔調的幼教老師。
當小朋友有問題時，你會用 3~6 歲小朋友聽得懂的方式對話和解說。
請用溫柔、有耐心的語氣，並且使用簡單易懂的詞彙。
回答要簡短、清楚，適合小朋友的注意力。
請一律使用繁體中文回覆。

[語音指示] 請用正常偏快的語速說話，發音要清楚流暢，不要停頓太久。`

const defaultOptions: InteractionOptions = {
  mode: 'realtime',
  providerConfig: {
    provider: 'gemini',
    model: 'gemini-2.5-flash-native-audio-preview-12-2025', // 支援中文的模型 (最新版本)
    voice: 'Kore', // 女性語音，較適合幼教老師角色
  },
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  // US4: Role and scenario defaults
  userRole: '小朋友',
  aiRole: '老師',
  scenarioContext: '',
  // Audio settings
  autoPlayResponse: true,
  enableVAD: true,
  vadSensitivity: 0.5,
  // US5: Barge-in enabled by default
  bargeInEnabled: true,
  showLatencyMetrics: true,
  showTranscripts: true,
  // Lightweight mode: skip sync audio storage for lower latency
  lightweightMode: true,
}

const initialState = {
  connectionStatus: 'disconnected' as ConnectionStatus,
  interactionState: 'idle' as InteractionState,
  session: null,
  currentTurn: null,
  turnHistory: [],
  isRecording: false,
  isMuted: false,
  inputVolume: 0,
  outputVolume: 1,
  userTranscript: '',
  aiResponseText: '',
  isTranscriptFinal: false,
  currentLatency: null,
  currentTurnLatency: null,
  sessionStats: null,
  options: defaultOptions,
  availableTemplates: [],
  error: null,
}

// =============================================================================
// Store Implementation
// =============================================================================

export const useInteractionStore = create<InteractionStoreState>()(
  persist(
    (set, _get) => ({
      ...initialState,

      // Connection actions
      setConnectionStatus: (status) => set({ connectionStatus: status }),

      setInteractionState: (state) => set({ interactionState: state }),

      // Session actions
      setSession: (session) => set({ session }),

      setCurrentTurn: (turn) => set({ currentTurn: turn }),

      addTurnToHistory: (turn) =>
        set((state) => ({
          turnHistory: [...state.turnHistory, turn],
        })),

      clearTurnHistory: () => set({ turnHistory: [] }),

      // Audio actions
      setIsRecording: (recording) => set({ isRecording: recording }),

      setIsMuted: (muted) => set({ isMuted: muted }),

      setInputVolume: (volume) => set({ inputVolume: Math.max(0, Math.min(1, volume)) }),

      setOutputVolume: (volume) => set({ outputVolume: Math.max(0, Math.min(1, volume)) }),

      // Transcript actions
      setUserTranscript: (transcript, isFinal = false) =>
        set({
          userTranscript: transcript,
          isTranscriptFinal: isFinal,
        }),

      appendAIResponse: (text) =>
        set((state) => ({
          aiResponseText: state.aiResponseText + text,
        })),

      clearTranscripts: () =>
        set({
          userTranscript: '',
          aiResponseText: '',
          isTranscriptFinal: false,
        }),

      // Latency actions
      setCurrentLatency: (latency) => set({ currentLatency: latency }),

      setCurrentTurnLatency: (latency) => set({ currentTurnLatency: latency }),

      setSessionStats: (stats) => set({ sessionStats: stats }),

      // Configuration actions
      setMode: (mode) =>
        set((state) => ({
          options: {
            ...state.options,
            mode,
            // Reset provider config when mode changes
            providerConfig:
              mode === 'realtime'
                ? {
                    provider: 'gemini',
                    model: 'gemini-2.5-flash-native-audio-preview-12-2025',
                    voice: 'Kore',
                  }
                : {
                    stt_provider: 'azure',
                    llm_provider: 'openai',
                    tts_provider: 'azure',
                  },
            // Lightweight mode for realtime V2V
            lightweightMode: mode === 'realtime',
          },
        })),

      setProviderConfig: (config) =>
        set((state) => ({
          options: { ...state.options, providerConfig: config },
        })),

      setSystemPrompt: (prompt) =>
        set((state) => ({
          options: { ...state.options, systemPrompt: prompt },
        })),

      setOptions: (partialOptions) =>
        set((state) => ({
          options: { ...state.options, ...partialOptions },
        })),

      setAvailableTemplates: (templates) => set({ availableTemplates: templates }),

      // US4: Role and scenario configuration actions
      setUserRole: (role) =>
        set((state) => ({
          options: { ...state.options, userRole: role },
        })),

      setAiRole: (role) =>
        set((state) => ({
          options: { ...state.options, aiRole: role },
        })),

      setScenarioContext: (context) =>
        set((state) => ({
          options: { ...state.options, scenarioContext: context },
        })),

      // US5: Barge-in configuration action
      setBargeInEnabled: (enabled) =>
        set((state) => ({
          options: { ...state.options, bargeInEnabled: enabled },
        })),

      // Performance optimization action
      setLightweightMode: (enabled) =>
        set((state) => ({
          options: { ...state.options, lightweightMode: enabled },
        })),

      // Error actions
      setError: (error) => set({ error }),

      // General actions
      reset: () => set(initialState),

      resetSession: () =>
        set({
          session: null,
          currentTurn: null,
          turnHistory: [],
          userTranscript: '',
          aiResponseText: '',
          isTranscriptFinal: false,
          currentLatency: null,
          currentTurnLatency: null,
          sessionStats: null,
          error: null,
          interactionState: 'idle',
        }),
    }),
    {
      name: 'interaction-store',
      // Only persist user preferences
      partialize: (state) => ({
        options: state.options,
        outputVolume: state.outputVolume,
      }),
      // Merge persisted options with defaults to handle schema migrations
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<InteractionStoreState>
        const persistedOptions = (persisted.options || {}) as Partial<InteractionOptions>

        // Preserve systemPrompt from defaults if persisted one is empty
        // This ensures the Chinese kindergarten teacher prompt is not lost
        const systemPrompt =
          persistedOptions.systemPrompt && persistedOptions.systemPrompt.trim()
            ? persistedOptions.systemPrompt
            : defaultOptions.systemPrompt

        return {
          ...currentState,
          ...persisted,
          // Ensure options always have all default fields
          options: {
            ...defaultOptions,
            ...persistedOptions,
            systemPrompt,
          },
        }
      },
    }
  )
)

export default useInteractionStore
