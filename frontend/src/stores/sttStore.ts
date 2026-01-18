/**
 * STT State Store
 * Feature: 003-stt-testing-module
 * T022: Create STT store (Zustand)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  STTProviderName,
  STTProvider,
  TranscriptionResponse,
  WERAnalysis,
  ComparisonResponse,
} from '@/types/stt'
import {
  listSTTProviders,
  transcribeAudio,
  compareProviders,
  calculateWER,
  type TranscribeOptions,
  type CompareOptions,
} from '@/services/sttApi'

interface STTState {
  // Audio input
  audioFile: File | null
  audioBlob: Blob | null
  audioUrl: string | null
  isRecording: boolean

  // Provider selection
  selectedProvider: STTProviderName
  availableProviders: STTProvider[]
  providersLoading: boolean

  // Options
  language: string
  childMode: boolean
  groundTruth: string

  // Transcription results
  isTranscribing: boolean
  transcriptionResult: TranscriptionResponse | null
  error: string | null

  // WER Analysis
  werAnalysis: WERAnalysis | null
  isCalculatingWER: boolean

  // Comparison
  comparisonProviders: STTProviderName[]
  comparisonResults: ComparisonResponse | null
  isComparing: boolean

  // Actions - Audio
  setAudioFile: (file: File | null) => void
  setAudioBlob: (blob: Blob | null) => void
  setAudioUrl: (url: string | null) => void
  setIsRecording: (recording: boolean) => void
  clearAudio: () => void

  // Actions - Provider
  setSelectedProvider: (provider: STTProviderName) => void
  loadProviders: () => Promise<void>

  // Actions - Options
  setLanguage: (language: string) => void
  setChildMode: (enabled: boolean) => void
  setGroundTruth: (text: string) => void

  // Actions - Transcription
  transcribe: () => Promise<void>
  clearResult: () => void

  // Actions - WER
  calculateErrorRate: () => Promise<void>

  // Actions - Comparison
  setComparisonProviders: (providers: STTProviderName[]) => void
  runComparison: () => Promise<void>
  clearComparison: () => void

  // Actions - General
  reset: () => void
}

const initialState = {
  audioFile: null,
  audioBlob: null,
  audioUrl: null,
  isRecording: false,
  selectedProvider: 'azure' as STTProviderName,
  availableProviders: [],
  providersLoading: false,
  language: 'zh-TW',
  childMode: false,
  groundTruth: '',
  isTranscribing: false,
  transcriptionResult: null,
  error: null,
  werAnalysis: null,
  isCalculatingWER: false,
  comparisonProviders: ['azure', 'gcp', 'whisper'] as STTProviderName[],
  comparisonResults: null,
  isComparing: false,
}

export const useSTTStore = create<STTState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Audio actions
      setAudioFile: (file) => {
        // Revoke previous URL if exists
        const prevUrl = get().audioUrl
        if (prevUrl) {
          URL.revokeObjectURL(prevUrl)
        }

        if (file) {
          const url = URL.createObjectURL(file)
          set({ audioFile: file, audioBlob: null, audioUrl: url, error: null })
        } else {
          set({ audioFile: null, audioUrl: null })
        }
      },

      setAudioBlob: (blob) => {
        // Revoke previous URL if exists
        const prevUrl = get().audioUrl
        if (prevUrl) {
          URL.revokeObjectURL(prevUrl)
        }

        if (blob) {
          const url = URL.createObjectURL(blob)
          set({ audioBlob: blob, audioFile: null, audioUrl: url, error: null })
        } else {
          set({ audioBlob: null, audioUrl: null })
        }
      },

      setAudioUrl: (url) => set({ audioUrl: url }),

      setIsRecording: (recording) => set({ isRecording: recording }),

      clearAudio: () => {
        const prevUrl = get().audioUrl
        if (prevUrl) {
          URL.revokeObjectURL(prevUrl)
        }
        set({
          audioFile: null,
          audioBlob: null,
          audioUrl: null,
          transcriptionResult: null,
          werAnalysis: null,
          error: null,
        })
      },

      // Provider actions
      setSelectedProvider: (provider) => set({ selectedProvider: provider }),

      loadProviders: async () => {
        set({ providersLoading: true })
        try {
          const providers = await listSTTProviders()
          set({ availableProviders: providers, providersLoading: false })
        } catch (error) {
          console.error('Failed to load STT providers:', error)
          set({
            providersLoading: false,
            error: error instanceof Error ? error.message : 'Failed to load providers',
          })
        }
      },

      // Options actions
      setLanguage: (language) => set({ language }),
      setChildMode: (enabled) => set({ childMode: enabled }),
      setGroundTruth: (text) => set({ groundTruth: text }),

      // Transcription actions
      transcribe: async () => {
        const state = get()
        const audio = state.audioFile || state.audioBlob

        if (!audio) {
          set({ error: 'No audio file selected' })
          return
        }

        set({ isTranscribing: true, error: null })

        try {
          const options: TranscribeOptions = {
            provider: state.selectedProvider,
            language: state.language,
            childMode: state.childMode,
            groundTruth: state.groundTruth || undefined,
            saveToHistory: true,
          }

          const result = await transcribeAudio(audio, options)

          set({
            transcriptionResult: result,
            werAnalysis: result.wer_analysis || null,
            isTranscribing: false,
          })
        } catch (error) {
          console.error('Transcription failed:', error)
          set({
            isTranscribing: false,
            error: error instanceof Error ? error.message : 'Transcription failed',
          })
        }
      },

      clearResult: () => set({ transcriptionResult: null, werAnalysis: null, error: null }),

      // WER actions
      calculateErrorRate: async () => {
        const state = get()

        if (!state.transcriptionResult?.id) {
          set({ error: 'No transcription result to analyze' })
          return
        }

        if (!state.groundTruth.trim()) {
          set({ error: 'Please enter ground truth text' })
          return
        }

        set({ isCalculatingWER: true, error: null })

        try {
          const result = await calculateWER({
            resultId: state.transcriptionResult.id,
            groundTruth: state.groundTruth,
          })

          set({ werAnalysis: result, isCalculatingWER: false })
        } catch (error) {
          console.error('WER calculation failed:', error)
          set({
            isCalculatingWER: false,
            error: error instanceof Error ? error.message : 'WER calculation failed',
          })
        }
      },

      // Comparison actions
      setComparisonProviders: (providers) => set({ comparisonProviders: providers }),

      runComparison: async () => {
        const state = get()
        const audio = state.audioFile || state.audioBlob

        if (!audio) {
          set({ error: 'No audio file selected' })
          return
        }

        if (state.comparisonProviders.length < 2) {
          set({ error: 'Select at least 2 providers for comparison' })
          return
        }

        set({ isComparing: true, error: null })

        try {
          const options: CompareOptions = {
            providers: state.comparisonProviders,
            language: state.language,
            groundTruth: state.groundTruth || undefined,
          }

          const result = await compareProviders(audio, options)
          set({ comparisonResults: result, isComparing: false })
        } catch (error) {
          console.error('Comparison failed:', error)
          set({
            isComparing: false,
            error: error instanceof Error ? error.message : 'Comparison failed',
          })
        }
      },

      clearComparison: () => set({ comparisonResults: null }),

      // General actions
      reset: () => {
        const prevUrl = get().audioUrl
        if (prevUrl) {
          URL.revokeObjectURL(prevUrl)
        }
        set(initialState)
      },
    }),
    {
      name: 'stt-store',
      // Only persist user preferences, not audio data
      partialize: (state) => ({
        selectedProvider: state.selectedProvider,
        language: state.language,
        childMode: state.childMode,
        comparisonProviders: state.comparisonProviders,
      }),
    }
  )
)
