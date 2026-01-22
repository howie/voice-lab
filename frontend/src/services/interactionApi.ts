/**
 * Interaction API Service
 * Feature: 004-interaction-module
 *
 * T026: REST API client for interaction session management.
 */

import { api } from '../lib/api'
import type {
  ConversationTurn,
  InteractionMode,
  InteractionSession,
  LatencyStats,
  ProvidersResponse,
  SessionListParams,
  SessionListResponse,
  SessionStatus,
  SystemPromptTemplate,
} from '../types/interaction'

// =============================================================================
// Session Endpoints
// =============================================================================

/**
 * List interaction sessions for a user with optional filters
 */
export async function listSessions(params: SessionListParams): Promise<SessionListResponse> {
  const queryParams = new URLSearchParams()
  queryParams.set('user_id', params.user_id)

  if (params.mode) queryParams.set('mode', params.mode)
  if (params.status) queryParams.set('status', params.status)
  if (params.start_date) queryParams.set('start_date', params.start_date)
  if (params.end_date) queryParams.set('end_date', params.end_date)
  if (params.page) queryParams.set('page', String(params.page))
  if (params.page_size) queryParams.set('page_size', String(params.page_size))

  const response = await api.get<SessionListResponse>(
    `/interaction/sessions?${queryParams.toString()}`
  )
  return response.data
}

/**
 * Get a specific session by ID
 */
export async function getSession(sessionId: string): Promise<InteractionSession> {
  const response = await api.get<InteractionSession>(`/interaction/sessions/${sessionId}`)
  return response.data
}

/**
 * Delete a session and its associated audio files
 */
export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/interaction/sessions/${sessionId}`)
}

// =============================================================================
// Turn Endpoints
// =============================================================================

/**
 * List all conversation turns for a session
 */
export async function listSessionTurns(sessionId: string): Promise<ConversationTurn[]> {
  const response = await api.get<ConversationTurn[]>(`/interaction/sessions/${sessionId}/turns`)
  return response.data
}

/**
 * Get a specific turn by ID
 */
export async function getTurn(turnId: string): Promise<ConversationTurn> {
  const response = await api.get<ConversationTurn>(`/interaction/turns/${turnId}`)
  return response.data
}

// =============================================================================
// Latency Endpoints
// =============================================================================

/**
 * Get latency statistics for a session
 */
export async function getSessionLatencyStats(sessionId: string): Promise<LatencyStats> {
  const response = await api.get<LatencyStats>(`/interaction/sessions/${sessionId}/latency`)
  return response.data
}

// =============================================================================
// System Prompt Template Endpoints
// =============================================================================

/**
 * List all available system prompt templates
 */
export async function listPromptTemplates(): Promise<SystemPromptTemplate[]> {
  const response = await api.get<{ templates: SystemPromptTemplate[] }>(
    '/interaction/prompt-templates'
  )
  return response.data.templates
}

/**
 * Get a specific prompt template by ID
 */
export async function getPromptTemplate(templateId: string): Promise<SystemPromptTemplate> {
  const response = await api.get<SystemPromptTemplate>(
    `/interaction/prompt-templates/${templateId}`
  )
  return response.data
}

/**
 * Get the default prompt template for a category
 */
export async function getDefaultPromptTemplate(
  category: string
): Promise<SystemPromptTemplate | null> {
  const templates = await listPromptTemplates()
  return templates.find((t) => t.category === category && t.is_default) || null
}

// =============================================================================
// Provider Endpoints (T056)
// =============================================================================

/**
 * List available providers for cascade mode
 */
export async function listProviders(): Promise<ProvidersResponse> {
  const response = await api.get<ProvidersResponse>('/interaction/providers')
  return response.data
}

// =============================================================================
// WebSocket URL Helpers
// =============================================================================

// Helper to get API base URL from runtime config or env
function getApiBaseUrl(): string {
  const runtimeConfig = (window as { __RUNTIME_CONFIG__?: { VITE_API_BASE_URL?: string; VITE_WS_URL?: string } }).__RUNTIME_CONFIG__
  return runtimeConfig?.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || ''
}

function getWsUrl(): string {
  const runtimeConfig = (window as { __RUNTIME_CONFIG__?: { VITE_WS_URL?: string } }).__RUNTIME_CONFIG__
  return runtimeConfig?.VITE_WS_URL || import.meta.env.VITE_WS_URL || ''
}

/**
 * Build WebSocket URL for interaction session
 */
export function buildWebSocketUrl(mode: InteractionMode, userId: string): string {
  // Try dedicated WS URL first, then derive from API URL
  const wsUrl = getWsUrl()
  if (wsUrl) {
    return `${wsUrl}/api/interaction/ws/${mode}?user_id=${userId}`
  }

  const baseUrl = getApiBaseUrl() || window.location.origin
  const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws'
  // Remove /api/v1 suffix if present, then remove protocol
  const host = baseUrl.replace(/\/api\/v1$/, '').replace(/^https?:\/\//, '')

  return `${wsProtocol}://${host}/api/interaction/ws/${mode}?user_id=${userId}`
}

// =============================================================================
// Audio File Helpers
// =============================================================================

/**
 * Get URL for audio file playback
 */
export function getAudioFileUrl(audioPath: string): string {
  const baseUrl = getApiBaseUrl()
  return `${baseUrl}/files/${audioPath}`
}

/**
 * T093: Get URL for turn audio streaming
 */
export function getTurnAudioUrl(
  sessionId: string,
  turnId: string,
  audioType: 'user' | 'ai' = 'ai'
): string {
  const baseUrl = getApiBaseUrl()
  // baseUrl already includes /api/v1, so just append the path
  return `${baseUrl}/interaction/sessions/${sessionId}/turns/${turnId}/audio?audio_type=${audioType}`
}

/**
 * Download audio file
 */
export async function downloadAudioFile(audioPath: string, filename?: string): Promise<void> {
  const url = getAudioFileUrl(audioPath)
  const response = await fetch(url)
  const blob = await response.blob()

  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename || audioPath.split('/').pop() || 'audio.mp3'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Format latency value for display
 */
export function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return '-'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

/**
 * Format session duration for display
 */
export function formatDuration(startedAt: string, endedAt: string | null): string {
  const start = new Date(startedAt)
  const end = endedAt ? new Date(endedAt) : new Date()
  const durationMs = end.getTime() - start.getTime()

  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

/**
 * Get status display info
 */
export function getStatusDisplay(status: SessionStatus): { label: string; color: string } {
  switch (status) {
    case 'active':
      return { label: '進行中', color: 'green' }
    case 'completed':
      return { label: '已完成', color: 'blue' }
    case 'disconnected':
      return { label: '已斷開', color: 'gray' }
    case 'error':
      return { label: '錯誤', color: 'red' }
    default:
      return { label: status, color: 'gray' }
  }
}

/**
 * Get mode display info
 */
export function getModeDisplay(mode: InteractionMode): { label: string; description: string } {
  switch (mode) {
    case 'realtime':
      return {
        label: 'Realtime API',
        description: '使用 OpenAI/Gemini 的即時語音 API，延遲最低',
      }
    case 'cascade':
      return {
        label: 'Cascade Mode',
        description: '使用 STT → LLM → TTS 管道，品質更高',
      }
    default:
      return { label: mode, description: '' }
  }
}
