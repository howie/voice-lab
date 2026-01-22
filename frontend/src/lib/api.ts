/**
 * API Client for Voice Lab
 * T038: Update API client with TTS endpoints
 */

import axios from 'axios'

// Check runtime config first (for Cloud Run), then build-time env, then fallback
const runtimeConfig = (window as { __RUNTIME_CONFIG__?: { VITE_API_BASE_URL?: string } }).__RUNTIME_CONFIG__
const API_BASE_URL = runtimeConfig?.VITE_API_BASE_URL
  || import.meta.env.VITE_API_BASE_URL
  || '/api/v1'
const DISABLE_AUTH = import.meta.env.VITE_DISABLE_AUTH === 'true'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401 && !DISABLE_AUTH) {
      // Handle unauthorized (skip redirect in dev mode with auth disabled)
      localStorage.removeItem('auth_token')
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Types
export interface SynthesizeRequest {
  text: string
  provider: string
  voice_id: string
  language?: string
  speed?: number
  pitch?: number
  volume?: number
  output_format?: string
}

export interface SynthesizeResponse {
  audio_content: string // Base64
  content_type: string
  duration_ms: number
  latency_ms?: number
  storage_path?: string
}

export interface VoiceProfile {
  id: string
  name: string
  provider: string
  language: string
  gender?: string
}

export interface ProviderInfo {
  name: string
  display_name: string
  type?: 'tts' | 'stt' | 'llm'
  supported_formats: string[]
  supported_languages: string[]
  supported_params: {
    [key: string]: {
      min: number
      max: number
      default: number
    }
  }
  status: 'available' | 'unavailable' | 'degraded'
}

export interface ProvidersResponse {
  providers: ProviderInfo[]
}

export interface ProvidersSummaryResponse {
  tts: ProviderInfo[]
  stt: ProviderInfo[]
  llm: ProviderInfo[]
}

// TTS API
export const ttsApi = {
  // Get available providers
  getProviders: () => api.get<ProvidersResponse>('/providers'),

  // Get providers summary (grouped by type)
  getProvidersSummary: () => api.get<ProvidersSummaryResponse>('/providers/summary'),

  // Get provider health status
  getProviderHealth: (provider: string) =>
    api.get<{ provider: string; is_healthy: boolean; message?: string }>(
      `/providers/${provider}/health`
    ),

  // Get voices for a provider
  getVoices: (provider: string, language?: string) =>
    api.get<VoiceProfile[]>(`/voices/${provider}`, {
      params: language ? { language } : undefined,
    }),

  // Get all voices
  getAllVoices: (language?: string) =>
    api.get<VoiceProfile[]>('/voices', {
      params: language ? { language } : undefined,
    }),

  // Synthesize speech (batch mode - returns base64)
  synthesize: (data: SynthesizeRequest) =>
    api.post<SynthesizeResponse>('/tts/synthesize', data),

  // Synthesize speech (binary mode - returns audio blob)
  synthesizeBinary: async (data: SynthesizeRequest): Promise<Blob> => {
    const response = await api.post('/tts/synthesize/binary', data, {
      responseType: 'blob',
    })
    return response.data
  },

  // Get supported parameters for a provider
  getParams: (provider: string) =>
    api.get<{
      speed: { min: number; max: number; default: number }
      pitch?: { min: number; max: number; default: number }
    }>(`/providers/${provider}/params`),
}

// Auth API
export const authApi = {
  // Get Google OAuth URL
  getGoogleAuthUrl: () => api.get<{ url: string }>('/auth/google'),

  // Handle OAuth callback
  callback: (code: string) =>
    api.get<{
      access_token: string
      token_type: string
      user: {
        id: string
        email: string
        name?: string
        picture_url?: string
      }
    }>('/auth/callback', { params: { code } }),

  // Get current user
  getCurrentUser: () =>
    api.get<{
      id: string
      email: string
      name?: string
      picture_url?: string
    }>('/auth/me'),

  // Logout
  logout: () => api.post('/auth/logout'),
}

// STT API
export const sttApi = {
  getProviders: () => api.get('/stt/providers'),
  transcribe: (formData: FormData) =>
    api.post('/stt/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// Interaction API
export const interactionApi = {
  getProviders: () => api.get('/interaction/providers'),
  startSession: (config: {
    stt_provider: string
    llm_provider: string
    tts_provider: string
    voice_id: string
    system_prompt?: string
    language?: string
  }) => api.post('/interaction/start', config),
}

// History API
export const historyApi = {
  list: (params?: { test_type?: string; page?: number; page_size?: number }) =>
    api.get('/history', { params }),
  get: (id: string) => api.get(`/history/${id}`),
  delete: (id: string) => api.delete(`/history/${id}`),
  export: (params?: { test_type?: string; format?: string }) =>
    api.get('/history/export', { params }),
}

// Voices API
export const voicesApi = {
  list: (params?: { language?: string; gender?: string }) =>
    api.get('/voices', { params }),
  listByProvider: (provider: string, params?: { language?: string }) =>
    api.get(`/voices/${provider}`, { params }),
}
