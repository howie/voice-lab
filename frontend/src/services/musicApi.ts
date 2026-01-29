/**
 * Music Generation API Service
 * Feature: 012-music-generation
 *
 * API calls for Mureka AI music generation.
 */

import { api } from '@/lib/api'
import type {
  ExtendLyricsRequest,
  InstrumentalRequest,
  LyricsRequest,
  MusicGenerationStatus,
  MusicGenerationType,
  MusicJob,
  MusicJobListResponse,
  QuotaStatus,
  SongRequest,
} from '@/types/music'

// =============================================================================
// Music Generation API
// =============================================================================

export const musicApi = {
  // === Submit Jobs ===

  /**
   * Submit an instrumental/BGM generation job
   */
  submitInstrumental: (data: InstrumentalRequest) =>
    api.post<MusicJob>('/music/instrumental', data),

  /**
   * Submit a song generation job
   */
  submitSong: (data: SongRequest) =>
    api.post<MusicJob>('/music/song', data),

  /**
   * Submit a lyrics generation job
   */
  submitLyrics: (data: LyricsRequest) =>
    api.post<MusicJob>('/music/lyrics', data),

  /**
   * Extend existing lyrics
   */
  extendLyrics: (data: ExtendLyricsRequest) =>
    api.post<MusicJob>('/music/lyrics/extend', data),

  // === Job Management ===

  /**
   * List music generation jobs for current user
   */
  listJobs: (params?: {
    status?: MusicGenerationStatus
    type?: MusicGenerationType
    limit?: number
    offset?: number
  }) =>
    api.get<MusicJobListResponse>('/music/jobs', { params }),

  /**
   * Get a single job by ID
   */
  getJob: (jobId: string) =>
    api.get<MusicJob>(`/music/jobs/${jobId}`),

  /**
   * Retry a failed job
   */
  retryJob: (jobId: string) =>
    api.post<MusicJob>(`/music/jobs/${jobId}/retry`),

  /**
   * Get download URL for completed job (redirects to audio file)
   */
  getDownloadUrl: (jobId: string) =>
    `/music/jobs/${jobId}/download`,

  // === Quota ===

  /**
   * Get current user's quota status
   */
  getQuota: () =>
    api.get<QuotaStatus>('/music/quota'),
}

export default musicApi
