/**
 * Music Generation Store
 * Feature: 012-music-generation
 *
 * Zustand store for music generation state management.
 */

import { create } from 'zustand'

import { musicApi } from '@/services/musicApi'
import type {
  MusicGenerationStatus,
  MusicGenerationType,
  MusicJob,
  MusicModel,
  MusicState,
} from '@/types/music'
import { DEFAULT_MUSIC_STATE } from '@/types/music'

// =============================================================================
// Store Interface
// =============================================================================

interface MusicStoreState extends MusicState {
  // === Job Actions ===
  fetchJobs: (params?: {
    status?: MusicGenerationStatus
    type?: MusicGenerationType
    limit?: number
    offset?: number
  }) => Promise<void>
  fetchJob: (jobId: string) => Promise<MusicJob | null>
  submitInstrumental: (prompt: string, model?: MusicModel) => Promise<MusicJob | null>
  submitSong: (prompt?: string, lyrics?: string, model?: MusicModel) => Promise<MusicJob | null>
  submitLyrics: (prompt: string) => Promise<MusicJob | null>
  extendLyrics: (lyrics: string, prompt?: string) => Promise<MusicJob | null>
  retryJob: (jobId: string) => Promise<MusicJob | null>

  // === Quota Actions ===
  fetchQuota: () => Promise<void>

  // === Polling Actions ===
  startPolling: (jobId: string) => void
  stopPolling: (jobId: string) => void
  stopAllPolling: () => void

  // === Form Actions ===
  setFormType: (type: MusicGenerationType) => void
  setFormPrompt: (prompt: string) => void
  setFormLyrics: (lyrics: string) => void
  setFormModel: (model: MusicModel) => void
  resetForm: () => void

  // === Selection Actions ===
  setCurrentJob: (job: MusicJob | null) => void

  // === General Actions ===
  clearError: () => void
  reset: () => void
}

// =============================================================================
// Polling Interval
// =============================================================================

const POLLING_INTERVAL_MS = 3000
const pollingIntervals: Map<string, NodeJS.Timeout> = new Map()

// =============================================================================
// Store Implementation
// =============================================================================

export const useMusicStore = create<MusicStoreState>((set, get) => ({
  ...DEFAULT_MUSIC_STATE,

  // === Job Actions ===
  fetchJobs: async (params) => {
    set({ isLoading: true, error: null })
    try {
      const response = await musicApi.listJobs(params)
      set({ jobs: response.data.items, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch jobs'
      set({ error: message, isLoading: false })
    }
  },

  fetchJob: async (jobId) => {
    try {
      const response = await musicApi.getJob(jobId)
      const job = response.data

      // Update job in list if exists
      set((state) => ({
        jobs: state.jobs.map((j) => (j.id === job.id ? job : j)),
        currentJob: state.currentJob?.id === job.id ? job : state.currentJob,
      }))

      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch job'
      set({ error: message })
      return null
    }
  },

  submitInstrumental: async (prompt, model = 'auto') => {
    set({ isSubmitting: true, error: null })
    try {
      const response = await musicApi.submitInstrumental({ prompt, model })
      const job = response.data

      set((state) => ({
        jobs: [job, ...state.jobs],
        currentJob: job,
        isSubmitting: false,
      }))

      // Start polling for this job
      get().startPolling(job.id)
      // Refresh quota
      get().fetchQuota()

      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit instrumental job'
      set({ error: message, isSubmitting: false })
      return null
    }
  },

  submitSong: async (prompt, lyrics, model = 'auto') => {
    set({ isSubmitting: true, error: null })
    try {
      const response = await musicApi.submitSong({ prompt, lyrics, model })
      const job = response.data

      set((state) => ({
        jobs: [job, ...state.jobs],
        currentJob: job,
        isSubmitting: false,
      }))

      // Start polling for this job
      get().startPolling(job.id)
      // Refresh quota
      get().fetchQuota()

      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit song job'
      set({ error: message, isSubmitting: false })
      return null
    }
  },

  submitLyrics: async (prompt) => {
    set({ isSubmitting: true, error: null })
    try {
      const response = await musicApi.submitLyrics({ prompt })
      const job = response.data

      set((state) => ({
        jobs: [job, ...state.jobs],
        currentJob: job,
        isSubmitting: false,
      }))

      // Start polling for this job
      get().startPolling(job.id)
      // Refresh quota
      get().fetchQuota()

      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to submit lyrics job'
      set({ error: message, isSubmitting: false })
      return null
    }
  },

  extendLyrics: async (lyrics, prompt) => {
    set({ isSubmitting: true, error: null })
    try {
      const response = await musicApi.extendLyrics({ lyrics, prompt })
      const job = response.data

      set((state) => ({
        jobs: [job, ...state.jobs],
        currentJob: job,
        isSubmitting: false,
      }))

      // Start polling for this job
      get().startPolling(job.id)
      // Refresh quota
      get().fetchQuota()

      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to extend lyrics'
      set({ error: message, isSubmitting: false })
      return null
    }
  },

  retryJob: async (jobId) => {
    set({ isSubmitting: true, error: null })
    try {
      const response = await musicApi.retryJob(jobId)
      const job = response.data

      set((state) => ({
        jobs: state.jobs.map((j) => (j.id === job.id ? job : j)),
        currentJob: state.currentJob?.id === job.id ? job : state.currentJob,
        isSubmitting: false,
      }))

      // Start polling for this job
      get().startPolling(job.id)

      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to retry job'
      set({ error: message, isSubmitting: false })
      return null
    }
  },

  // === Quota Actions ===
  fetchQuota: async () => {
    try {
      const response = await musicApi.getQuota()
      set({ quota: response.data })
    } catch (error) {
      console.error('Failed to fetch quota:', error)
    }
  },

  // === Polling Actions ===
  startPolling: (jobId) => {
    // Don't start if already polling
    if (pollingIntervals.has(jobId)) return

    set((state) => {
      const newPollingJobIds = new Set(state.pollingJobIds)
      newPollingJobIds.add(jobId)
      return { pollingJobIds: newPollingJobIds, isPolling: newPollingJobIds.size > 0 }
    })

    const interval = setInterval(async () => {
      const job = await get().fetchJob(jobId)

      // Stop polling if job is completed or failed
      if (job && (job.status === 'completed' || job.status === 'failed')) {
        get().stopPolling(jobId)
      }
    }, POLLING_INTERVAL_MS)

    pollingIntervals.set(jobId, interval)
  },

  stopPolling: (jobId) => {
    const interval = pollingIntervals.get(jobId)
    if (interval) {
      clearInterval(interval)
      pollingIntervals.delete(jobId)
    }

    set((state) => {
      const newPollingJobIds = new Set(state.pollingJobIds)
      newPollingJobIds.delete(jobId)
      return { pollingJobIds: newPollingJobIds, isPolling: newPollingJobIds.size > 0 }
    })
  },

  stopAllPolling: () => {
    for (const [jobId, interval] of pollingIntervals) {
      clearInterval(interval)
      pollingIntervals.delete(jobId)
    }
    set({ pollingJobIds: new Set(), isPolling: false })
  },

  // === Form Actions ===
  setFormType: (type) => set({ formType: type }),
  setFormPrompt: (prompt) => set({ formPrompt: prompt }),
  setFormLyrics: (lyrics) => set({ formLyrics: lyrics }),
  setFormModel: (model) => set({ formModel: model }),
  resetForm: () =>
    set({
      formType: 'instrumental',
      formPrompt: '',
      formLyrics: '',
      formModel: 'auto',
    }),

  // === Selection Actions ===
  setCurrentJob: (job) => set({ currentJob: job }),

  // === General Actions ===
  clearError: () => set({ error: null }),
  reset: () => {
    get().stopAllPolling()
    set(DEFAULT_MUSIC_STATE)
  },
}))

// =============================================================================
// Selectors
// =============================================================================

export const selectPendingJobs = (state: MusicStoreState) =>
  state.jobs.filter((j) => j.status === 'pending' || j.status === 'processing')

export const selectCompletedJobs = (state: MusicStoreState) =>
  state.jobs.filter((j) => j.status === 'completed')

export const selectFailedJobs = (state: MusicStoreState) =>
  state.jobs.filter((j) => j.status === 'failed')

export const selectCanSubmit = (state: MusicStoreState) =>
  state.quota?.can_submit ?? true

export const selectQuotaUsagePercent = (state: MusicStoreState) => {
  if (!state.quota) return 0
  return Math.round((state.quota.daily_used / state.quota.daily_limit) * 100)
}

export default useMusicStore
