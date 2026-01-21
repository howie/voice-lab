/**
 * Job State Store
 * Feature: 007-async-job-mgmt
 *
 * Zustand store for async job management state.
 */

import { create } from 'zustand'
import {
  createJob,
  listJobs,
  getJob,
  cancelJob,
  type CreateJobRequest,
  type JobResponse,
  type JobDetailResponse,
  type JobListParams,
  type JobStatus,
} from '../services/jobApi'

// =============================================================================
// Types
// =============================================================================

interface JobState {
  // Data
  jobs: JobResponse[]
  currentJob: JobDetailResponse | null
  total: number

  // Pagination
  limit: number
  offset: number
  statusFilter: JobStatus | null

  // Loading states
  isLoading: boolean
  isSubmitting: boolean
  isFetchingDetail: boolean

  // Error state
  error: string | null

  // Polling
  pollingInterval: number | null
}

interface JobActions {
  // CRUD operations
  submitJob: (request: CreateJobRequest) => Promise<JobResponse>
  fetchJobs: (params?: JobListParams) => Promise<void>
  fetchJob: (jobId: string) => Promise<void>
  cancelJob: (jobId: string) => Promise<void>

  // State management
  setStatusFilter: (status: JobStatus | null) => void
  setPage: (offset: number) => void
  clearCurrentJob: () => void
  clearError: () => void

  // Polling
  startPolling: (intervalMs?: number) => void
  stopPolling: () => void
}

type JobStore = JobState & JobActions

// =============================================================================
// Store
// =============================================================================

const POLLING_INTERVAL_MS = 5000

export const useJobStore = create<JobStore>((set, get) => ({
  // Initial state
  jobs: [],
  currentJob: null,
  total: 0,
  limit: 20,
  offset: 0,
  statusFilter: null,
  isLoading: false,
  isSubmitting: false,
  isFetchingDetail: false,
  error: null,
  pollingInterval: null,

  // Submit a new job
  submitJob: async (request: CreateJobRequest) => {
    set({ isSubmitting: true, error: null })

    try {
      const job = await createJob(request)

      // Refresh job list after submission
      await get().fetchJobs()

      set({ isSubmitting: false })
      return job
    } catch (error) {
      const message = error instanceof Error ? error.message : '提交工作失敗'
      set({ error: message, isSubmitting: false })
      throw error
    }
  },

  // Fetch job list
  fetchJobs: async (params?: JobListParams) => {
    const { limit, offset, statusFilter } = get()

    set({ isLoading: true, error: null })

    try {
      const response = await listJobs({
        limit: params?.limit ?? limit,
        offset: params?.offset ?? offset,
        status: params?.status ?? statusFilter ?? undefined,
      })

      set({
        jobs: response.items,
        total: response.total,
        limit: response.limit,
        offset: response.offset,
        isLoading: false,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : '取得工作列表失敗'
      set({ error: message, isLoading: false })
    }
  },

  // Fetch single job details
  fetchJob: async (jobId: string) => {
    set({ isFetchingDetail: true, error: null })

    try {
      const job = await getJob(jobId)
      set({ currentJob: job, isFetchingDetail: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : '取得工作詳情失敗'
      set({ error: message, isFetchingDetail: false })
    }
  },

  // Cancel a job
  cancelJob: async (jobId: string) => {
    set({ error: null })

    try {
      await cancelJob(jobId)

      // Update local state
      const { jobs, currentJob } = get()
      const updatedJobs = jobs.map((j) =>
        j.id === jobId ? { ...j, status: 'cancelled' as JobStatus } : j
      )

      set({
        jobs: updatedJobs,
        currentJob: currentJob?.id === jobId ? { ...currentJob, status: 'cancelled' } : currentJob,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : '取消工作失敗'
      set({ error: message })
      throw error
    }
  },

  // Set status filter
  setStatusFilter: (status: JobStatus | null) => {
    set({ statusFilter: status, offset: 0 })
    get().fetchJobs()
  },

  // Set pagination offset
  setPage: (offset: number) => {
    set({ offset })
    get().fetchJobs()
  },

  // Clear current job
  clearCurrentJob: () => {
    set({ currentJob: null })
  },

  // Clear error
  clearError: () => {
    set({ error: null })
  },

  // Start polling for job updates
  startPolling: (intervalMs = POLLING_INTERVAL_MS) => {
    const { pollingInterval } = get()

    // Clear existing interval if any
    if (pollingInterval !== null) {
      window.clearInterval(pollingInterval)
    }

    // Start new polling
    const interval = window.setInterval(() => {
      const { jobs } = get()

      // Only poll if there are active jobs
      const hasActiveJobs = jobs.some((j) => j.status === 'pending' || j.status === 'processing')

      if (hasActiveJobs) {
        get().fetchJobs()
      }
    }, intervalMs)

    set({ pollingInterval: interval })
  },

  // Stop polling
  stopPolling: () => {
    const { pollingInterval } = get()

    if (pollingInterval !== null) {
      window.clearInterval(pollingInterval)
      set({ pollingInterval: null })
    }
  },
}))
