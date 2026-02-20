/**
 * Music Generation Types
 * Feature: 012-music-generation
 *
 * TypeScript types and interfaces for Music Generation module.
 */

// =============================================================================
// Enums
// =============================================================================

/**
 * Type of music generation
 */
export type MusicGenerationType = 'song' | 'instrumental' | 'lyrics'

/**
 * Status of music generation job
 */
export type MusicGenerationStatus = 'pending' | 'processing' | 'completed' | 'failed'

/**
 * Music generation provider
 */
export type MusicProvider = 'mureka' | 'lyria'

/**
 * Model selection (provider-specific)
 */
export type MusicModel = 'auto' | 'mureka-01' | 'v7.5' | 'v6' | 'lyria-002'

// =============================================================================
// Request Types
// =============================================================================

/**
 * Request to submit instrumental/BGM generation
 */
export interface InstrumentalRequest {
  /** Scene/style description (10-500 chars) */
  prompt: string
  /** Model selection */
  model?: MusicModel
  /** Music generation provider */
  provider?: MusicProvider
}

/**
 * Request to submit song generation
 */
export interface SongRequest {
  /** Style description (optional, max 500 chars) */
  prompt?: string
  /** Song lyrics (optional, max 3000 chars) */
  lyrics?: string
  /** Mureka model selection */
  model?: MusicModel
}

/**
 * Request to submit lyrics generation
 */
export interface LyricsRequest {
  /** Theme/topic description (2-200 chars) */
  prompt: string
}

/**
 * Request to extend existing lyrics
 */
export interface ExtendLyricsRequest {
  /** Existing lyrics (max 3000 chars) */
  lyrics: string
  /** Extension direction description (optional, max 200 chars) */
  prompt?: string
}

// =============================================================================
// Response Types
// =============================================================================

/**
 * Music generation job response
 */
export interface MusicJob {
  id: string
  type: MusicGenerationType
  status: MusicGenerationStatus
  provider: MusicProvider
  prompt: string | null
  lyrics: string | null
  model: MusicModel
  result_url: string | null
  cover_url: string | null
  generated_lyrics: string | null
  duration_ms: number | null
  title: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

/**
 * Paginated list of music jobs
 */
export interface MusicJobListResponse {
  items: MusicJob[]
  total: number
  limit: number
  offset: number
}

/**
 * User's quota status
 */
export interface QuotaStatus {
  daily_used: number
  daily_limit: number
  monthly_used: number
  monthly_limit: number
  concurrent_jobs: number
  max_concurrent_jobs: number
  can_submit: boolean
}

// =============================================================================
// Store State Types
// =============================================================================

/**
 * Music generation store state
 */
export interface MusicState {
  // === Job Management ===
  jobs: MusicJob[]
  currentJob: MusicJob | null
  isLoading: boolean
  isSubmitting: boolean
  error: string | null

  // === Quota ===
  quota: QuotaStatus | null

  // === Polling ===
  isPolling: boolean
  pollingJobIds: Set<string>

  // === Form State ===
  formType: MusicGenerationType
  formPrompt: string
  formLyrics: string
  formModel: MusicModel
}

// =============================================================================
// Default Values
// =============================================================================

export const DEFAULT_MUSIC_STATE: MusicState = {
  jobs: [],
  currentJob: null,
  isLoading: false,
  isSubmitting: false,
  error: null,
  quota: null,
  isPolling: false,
  pollingJobIds: new Set(),
  formType: 'instrumental',
  formPrompt: '',
  formLyrics: '',
  formModel: 'auto',
}

export const MUSIC_TYPE_LABELS: Record<MusicGenerationType, string> = {
  instrumental: '純音樂 (BGM)',
  song: '歌曲',
  lyrics: '歌詞',
}

export const MUSIC_STATUS_LABELS: Record<MusicGenerationStatus, string> = {
  pending: '等待中',
  processing: '處理中',
  completed: '完成',
  failed: '失敗',
}

export const MUSIC_MODEL_LABELS: Record<MusicModel, string> = {
  auto: '自動選擇',
  'mureka-01': 'Mureka-01',
  'v7.5': 'V7.5',
  v6: 'V6',
  'lyria-002': 'Lyria 2',
}

export const MUSIC_PROVIDER_LABELS: Record<MusicProvider, string> = {
  mureka: 'Mureka AI',
  lyria: 'Google Lyria',
}
