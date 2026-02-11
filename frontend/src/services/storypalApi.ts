/**
 * StoryPal API Service
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * REST API client for story session and template management.
 */

import { api } from '../lib/api'
import type {
  CreateStorySessionRequest,
  StorySessionListParams,
  StorySessionListResponse,
  StorySessionResponse,
  StoryTemplate,
  StoryTemplateListResponse,
} from '../types/storypal'

// =============================================================================
// Template Endpoints
// =============================================================================

/** List available story templates */
export async function listTemplates(params?: {
  category?: string
  language?: string
}): Promise<StoryTemplateListResponse> {
  const response = await api.get<StoryTemplateListResponse>('/story/templates', { params })
  return response.data
}

/** Get template details by ID */
export async function getTemplate(templateId: string): Promise<StoryTemplate> {
  const response = await api.get<StoryTemplate>(`/story/templates/${templateId}`)
  return response.data
}

// =============================================================================
// Session Endpoints
// =============================================================================

/** Start a new story session */
export async function createSession(
  request: CreateStorySessionRequest
): Promise<StorySessionResponse> {
  const response = await api.post<StorySessionResponse>('/story/sessions', request)
  return response.data
}

/** List story sessions for the current user */
export async function listSessions(
  params?: StorySessionListParams
): Promise<StorySessionListResponse> {
  const response = await api.get<StorySessionListResponse>('/story/sessions', { params })
  return response.data
}

/** Get session details with turns */
export async function getSession(sessionId: string): Promise<StorySessionResponse> {
  const response = await api.get<StorySessionResponse>(`/story/sessions/${sessionId}`)
  return response.data
}

/** Resume a paused session */
export async function resumeSession(sessionId: string): Promise<StorySessionResponse> {
  const response = await api.post<StorySessionResponse>(`/story/sessions/${sessionId}/resume`)
  return response.data
}

/** Delete/end a story session */
export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/story/sessions/${sessionId}`)
}

// =============================================================================
// WebSocket URL helper
// =============================================================================

/** Build WebSocket URL for story interaction */
export function getStoryWSUrl(): string {
  const baseUrl = api.defaults.baseURL || '/api/v1'
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsBase = baseUrl.startsWith('http')
    ? baseUrl.replace(/^https?:/, wsProtocol)
    : `${wsProtocol}//${window.location.host}${baseUrl}`
  return `${wsBase}/story/ws`
}
