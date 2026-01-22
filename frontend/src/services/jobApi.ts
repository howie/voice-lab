/**
 * Job API Service
 * Feature: 007-async-job-mgmt
 *
 * REST API client for async job management.
 */

import { api } from '../lib/api'

// =============================================================================
// Types
// =============================================================================

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

export type JobType = 'multi_role_tts'

export interface DialogueTurn {
  speaker: string
  text: string
  index: number
}

export interface VoiceAssignment {
  speaker: string
  voice_id: string
  voice_name?: string
}

export interface CreateJobRequest {
  provider: string
  turns: DialogueTurn[]
  voice_assignments: VoiceAssignment[]
  language?: string
  output_format?: 'mp3' | 'wav'
  gap_ms?: number
  crossfade_ms?: number
}

export interface JobResponse {
  id: string
  status: JobStatus
  job_type: JobType
  provider: string
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface ResultMetadata {
  duration_ms?: number
  latency_ms?: number
  synthesis_mode?: 'native' | 'segmented'
}

export interface JobDetailResponse extends JobResponse {
  input_params: Record<string, unknown>
  result_metadata: ResultMetadata | null
  audio_file_id: string | null
  error_message: string | null
  retry_count: number
}

export interface JobListResponse {
  items: JobResponse[]
  total: number
  limit: number
  offset: number
}

export interface JobListParams {
  status?: JobStatus
  limit?: number
  offset?: number
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Create a new TTS synthesis job
 */
export async function createJob(request: CreateJobRequest): Promise<JobResponse> {
  const response = await api.post<JobResponse>('/jobs', request)
  return response.data
}

/**
 * List all jobs for the current user
 */
export async function listJobs(params?: JobListParams): Promise<JobListResponse> {
  const response = await api.get<JobListResponse>('/jobs', { params })
  return response.data
}

/**
 * Get job details by ID
 */
export async function getJob(jobId: string): Promise<JobDetailResponse> {
  const response = await api.get<JobDetailResponse>(`/jobs/${jobId}`)
  return response.data
}

/**
 * Cancel a pending job
 */
export async function cancelJob(jobId: string): Promise<JobResponse> {
  const response = await api.delete<JobResponse>(`/jobs/${jobId}`)
  return response.data
}

// Helper to get API base URL from runtime config or env
function getApiBaseUrl(): string {
  const runtimeConfig = (window as { __RUNTIME_CONFIG__?: { VITE_API_BASE_URL?: string } }).__RUNTIME_CONFIG__
  return runtimeConfig?.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || '/api/v1'
}

/**
 * Get download URL for completed job audio
 */
export function getDownloadUrl(jobId: string): string {
  const baseUrl = getApiBaseUrl()
  return `${baseUrl}/jobs/${jobId}/download`
}

/**
 * Download job audio file
 */
export async function downloadJobAudio(jobId: string, filename?: string): Promise<void> {
  const url = getDownloadUrl(jobId)
  const token = localStorage.getItem('auth_token')

  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (!response.ok) {
    throw new Error(`Download failed: ${response.statusText}`)
  }

  const blob = await response.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename || `job-${jobId}.mp3`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Get status display info
 */
export function getStatusDisplay(status: JobStatus): { label: string; color: string } {
  switch (status) {
    case 'pending':
      return { label: '等待中', color: 'yellow' }
    case 'processing':
      return { label: '處理中', color: 'blue' }
    case 'completed':
      return { label: '已完成', color: 'green' }
    case 'failed':
      return { label: '失敗', color: 'red' }
    case 'cancelled':
      return { label: '已取消', color: 'gray' }
    default:
      return { label: status, color: 'gray' }
  }
}

/**
 * Check if job is in terminal state
 */
export function isTerminalStatus(status: JobStatus): boolean {
  return status === 'completed' || status === 'failed' || status === 'cancelled'
}

/**
 * Check if job can be cancelled
 */
export function canCancel(status: JobStatus): boolean {
  return status === 'pending'
}

/**
 * Format duration in milliseconds to human readable format
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  }
  return `${seconds}s`
}

/**
 * Format date for display
 */
export function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-TW')
}
