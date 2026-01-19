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
  setSessionStats: (stats: LatencyStats | null) => void

  // Actions - Configuration
  setMode: (mode: InteractionMode) => void
  setProviderConfig: (config: ProviderConfig) => void
  setSystemPrompt: (prompt: string) => void
  setOptions: (options: Partial<InteractionOptions>) => void
  setAvailableTemplates: (templates: SystemPromptTemplate[]) => void

  // Actions - Error
  setError: (error: string | null) => void

  // Actions - General
  reset: () => void
  resetSession: () => void
}

// =============================================================================
// Initial State
// =============================================================================

const defaultOptions: InteractionOptions = {
  mode: 'realtime',
  providerConfig: {
    provider: 'openai',
    voice: 'alloy',
  },
  systemPrompt: '',
  autoPlayResponse: true,
  enableVAD: true,
  vadSensitivity: 0.5,
  showLatencyMetrics: true,
  showTranscripts: true,
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
                ? { provider: 'openai', voice: 'alloy' }
                : {
                    stt_provider: 'azure',
                    llm_provider: 'openai',
                    tts_provider: 'azure',
                  },
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
    }
  )
)

export default useInteractionStore
