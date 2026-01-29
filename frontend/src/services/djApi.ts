/**
 * DJ API Service
 * Feature: 011-magic-dj-audio-features
 * Phase 3: Frontend Integration
 *
 * REST API client for DJ preset and track management.
 */

import { api } from '../lib/api'
import type { TrackType, TrackSource, DJSettings } from '../types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface DJSettingsAPI {
  master_volume: number
  time_warning_at: number
  session_time_limit: number
  ai_response_timeout: number
  auto_play_filler: boolean
}

export interface PresetResponse {
  id: string
  user_id: string
  name: string
  description: string | null
  is_default: boolean
  settings: DJSettingsAPI
  created_at: string
  updated_at: string
}

export interface TrackResponse {
  id: string
  preset_id: string
  name: string
  type: TrackType
  source: TrackSource
  hotkey: string | null
  loop: boolean
  sort_order: number
  text_content: string | null
  tts_provider: string | null
  tts_voice_id: string | null
  tts_speed: string // Decimal as string
  original_filename: string | null
  audio_url: string | null
  duration_ms: number | null
  file_size_bytes: number | null
  content_type: string
  volume: string // Decimal as string
  created_at: string
  updated_at: string
}

export interface PresetDetailResponse extends PresetResponse {
  tracks: TrackResponse[]
}

export interface PresetListResponse {
  items: PresetResponse[]
  total: number
}

export interface TrackListResponse {
  items: TrackResponse[]
  total: number
}

export interface CreatePresetRequest {
  name: string
  description?: string
  is_default?: boolean
  settings?: Partial<DJSettingsAPI>
}

export interface UpdatePresetRequest {
  name?: string
  description?: string
  is_default?: boolean
  settings?: Partial<DJSettingsAPI>
}

export interface CreateTrackRequest {
  name: string
  type: TrackType
  source: TrackSource
  hotkey?: string
  loop?: boolean
  sort_order?: number
  text_content?: string
  tts_provider?: string
  tts_voice_id?: string
  tts_speed?: number
  volume?: number
}

export interface UpdateTrackRequest {
  name?: string
  type?: TrackType
  hotkey?: string
  loop?: boolean
  sort_order?: number
  text_content?: string
  tts_provider?: string
  tts_voice_id?: string
  tts_speed?: number
  volume?: number
}

export interface ReorderTracksRequest {
  track_ids: string[]
}

export interface AudioUploadResponse {
  track_id: string
  storage_path: string
  audio_url: string
  duration_ms: number
  file_size_bytes: number
  content_type: string
}

export interface LocalStorageTrack {
  id: string
  name: string
  type: string
  source?: string
  hotkey?: string
  loop?: boolean
  text_content?: string
  audioBase64?: string
  volume?: number
}

export interface LocalStorageData {
  settings?: Record<string, unknown>
  masterVolume?: number
  tracks?: LocalStorageTrack[]
}

export interface ImportRequest {
  preset_name: string
  data: LocalStorageData
}

export interface ExportResponse {
  preset: PresetResponse
  tracks: TrackResponse[]
}

// =============================================================================
// API Functions - Presets
// =============================================================================

/**
 * List all presets for the current user
 */
export async function listPresets(): Promise<PresetListResponse> {
  const response = await api.get<PresetListResponse>('/dj/presets')
  return response.data
}

/**
 * Create a new preset
 */
export async function createPreset(request: CreatePresetRequest): Promise<PresetResponse> {
  const response = await api.post<PresetResponse>('/dj/presets', request)
  return response.data
}

/**
 * Get preset details with tracks
 */
export async function getPreset(presetId: string): Promise<PresetDetailResponse> {
  const response = await api.get<PresetDetailResponse>(`/dj/presets/${presetId}`)
  return response.data
}

/**
 * Update a preset
 */
export async function updatePreset(
  presetId: string,
  request: UpdatePresetRequest
): Promise<PresetResponse> {
  const response = await api.put<PresetResponse>(`/dj/presets/${presetId}`, request)
  return response.data
}

/**
 * Delete a preset
 */
export async function deletePreset(presetId: string): Promise<void> {
  await api.delete(`/dj/presets/${presetId}`)
}

/**
 * Clone a preset
 */
export async function clonePreset(presetId: string, newName: string): Promise<PresetResponse> {
  const response = await api.post<PresetResponse>(`/dj/presets/${presetId}/clone`, null, {
    params: { new_name: newName },
  })
  return response.data
}

// =============================================================================
// API Functions - Tracks
// =============================================================================

/**
 * List tracks for a preset
 */
export async function listTracks(presetId: string): Promise<TrackListResponse> {
  const response = await api.get<TrackListResponse>(`/dj/presets/${presetId}/tracks`)
  return response.data
}

/**
 * Create a new track
 */
export async function createTrack(
  presetId: string,
  request: CreateTrackRequest
): Promise<TrackResponse> {
  const response = await api.post<TrackResponse>(`/dj/presets/${presetId}/tracks`, request)
  return response.data
}

/**
 * Get track details
 */
export async function getTrack(presetId: string, trackId: string): Promise<TrackResponse> {
  const response = await api.get<TrackResponse>(`/dj/presets/${presetId}/tracks/${trackId}`)
  return response.data
}

/**
 * Update a track
 */
export async function updateTrack(
  presetId: string,
  trackId: string,
  request: UpdateTrackRequest
): Promise<TrackResponse> {
  const response = await api.put<TrackResponse>(
    `/dj/presets/${presetId}/tracks/${trackId}`,
    request
  )
  return response.data
}

/**
 * Delete a track
 */
export async function deleteTrack(presetId: string, trackId: string): Promise<void> {
  await api.delete(`/dj/presets/${presetId}/tracks/${trackId}`)
}

/**
 * Reorder tracks in a preset
 */
export async function reorderTracks(
  presetId: string,
  trackIds: string[]
): Promise<TrackListResponse> {
  const response = await api.put<TrackListResponse>(`/dj/presets/${presetId}/tracks/reorder`, {
    track_ids: trackIds,
  })
  return response.data
}

// =============================================================================
// API Functions - Audio
// =============================================================================

/**
 * Upload audio file for a track
 */
export async function uploadAudio(trackId: string, file: File): Promise<AudioUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('track_id', trackId)

  const response = await api.post<AudioUploadResponse>('/dj/audio/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/**
 * Get audio URL for a track (redirects to signed URL)
 */
export function getAudioUrl(trackId: string): string {
  const runtimeConfig = (
    window as { __RUNTIME_CONFIG__?: { VITE_API_BASE_URL?: string } }
  ).__RUNTIME_CONFIG__
  const baseUrl =
    runtimeConfig?.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${baseUrl}/dj/audio/${trackId}`
}

/**
 * Delete audio for a track
 */
export async function deleteAudio(trackId: string): Promise<void> {
  await api.delete(`/dj/audio/${trackId}`)
}

// =============================================================================
// API Functions - Import/Export
// =============================================================================

/**
 * Import preset from localStorage format
 */
export async function importFromLocalStorage(
  presetName: string,
  data: LocalStorageData
): Promise<PresetResponse> {
  const response = await api.post<PresetResponse>('/dj/import', {
    preset_name: presetName,
    data,
  })
  return response.data
}

/**
 * Export preset to JSON format
 */
export async function exportPreset(presetId: string): Promise<ExportResponse> {
  const response = await api.get<ExportResponse>(`/dj/export/${presetId}`)
  return response.data
}

// =============================================================================
// Conversion Utilities
// =============================================================================

/**
 * Convert API settings to frontend DJSettings format
 */
export function apiSettingsToFrontend(settings: DJSettingsAPI): Partial<DJSettings> {
  return {
    sessionTimeLimit: settings.session_time_limit,
    timeWarningAt: settings.time_warning_at,
    aiResponseTimeout: settings.ai_response_timeout,
    autoPlayFillerOnSubmit: settings.auto_play_filler,
  }
}

/**
 * Convert frontend DJSettings to API format
 */
export function frontendSettingsToApi(settings: Partial<DJSettings>): Partial<DJSettingsAPI> {
  const result: Partial<DJSettingsAPI> = {}
  if (settings.sessionTimeLimit !== undefined) {
    result.session_time_limit = settings.sessionTimeLimit
  }
  if (settings.timeWarningAt !== undefined) {
    result.time_warning_at = settings.timeWarningAt
  }
  if (settings.aiResponseTimeout !== undefined) {
    result.ai_response_timeout = settings.aiResponseTimeout
  }
  if (settings.autoPlayFillerOnSubmit !== undefined) {
    result.auto_play_filler = settings.autoPlayFillerOnSubmit
  }
  return result
}

/**
 * Convert API track to frontend Track format
 */
export function apiTrackToFrontend(track: TrackResponse): {
  id: string
  name: string
  type: TrackType
  url: string
  hotkey?: string
  loop?: boolean
  duration?: number
  isCustom: boolean
  textContent?: string
  source: TrackSource
  originalFileName?: string
  volume: number
} {
  return {
    id: track.id,
    name: track.name,
    type: track.type,
    url: track.audio_url || '',
    hotkey: track.hotkey || undefined,
    loop: track.loop,
    duration: track.duration_ms || undefined,
    isCustom: true, // All backend tracks are "custom" from frontend perspective
    textContent: track.text_content || undefined,
    source: track.source,
    originalFileName: track.original_filename || undefined,
    volume: parseFloat(track.volume) || 1.0,
  }
}
