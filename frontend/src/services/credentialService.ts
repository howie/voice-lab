/**
 * Credential Service for Provider API Key Management
 * T031: API client for managing TTS/STT provider credentials
 */

import { api } from '../lib/api'

// Types
export interface Provider {
  id: string
  name: string
  display_name: string
  type: ('tts' | 'stt' | 'llm')[]
  is_active: boolean
}

export interface ProviderModel {
  id: string
  name: string
  language: string
  gender?: string | null
  description?: string | null
}

export interface CredentialSummary {
  id: string
  provider: string
  provider_display_name: string
  masked_key: string
  is_valid: boolean
  selected_model_id: string | null
  last_validated_at: string | null
  created_at: string
}

export interface CredentialResponse extends CredentialSummary {
  updated_at: string
}

export interface AddCredentialRequest {
  provider: string
  api_key: string
  selected_model_id?: string
}

export interface UpdateCredentialRequest {
  api_key?: string
  selected_model_id?: string
}

export interface QuotaInfo {
  character_count?: number | null
  character_limit?: number | null
  remaining_characters?: number | null
  tier?: string | null
}

export interface ValidationResult {
  is_valid: boolean
  validated_at: string | null
  error_message?: string | null
  quota_info?: QuotaInfo | null
}

export interface ValidationError {
  error: string
  message: string
  details?: {
    provider_error?: string
  }
}

// API Response types
interface CredentialListResponse {
  credentials: CredentialSummary[]
}

interface ProviderListResponse {
  providers: Provider[]
}

interface ProviderModelsResponse {
  models: ProviderModel[]
}

/**
 * Credential API service for managing provider API keys
 */
export const credentialService = {
  /**
   * List all credentials for the current user
   */
  listCredentials: async (): Promise<CredentialSummary[]> => {
    const response = await api.get<CredentialListResponse>('/credentials')
    return response.data.credentials
  },

  /**
   * Get a specific credential by ID
   */
  getCredential: async (credentialId: string): Promise<CredentialResponse> => {
    const response = await api.get<CredentialResponse>(
      `/credentials/${credentialId}`
    )
    return response.data
  },

  /**
   * Add a new provider credential
   * @throws ValidationError if API key validation fails
   */
  addCredential: async (
    data: AddCredentialRequest
  ): Promise<CredentialResponse> => {
    const response = await api.post<CredentialResponse>('/credentials', data)
    return response.data
  },

  /**
   * Update an existing credential
   */
  updateCredential: async (
    credentialId: string,
    data: UpdateCredentialRequest
  ): Promise<CredentialResponse> => {
    const response = await api.put<CredentialResponse>(
      `/credentials/${credentialId}`,
      data
    )
    return response.data
  },

  /**
   * Delete a credential
   */
  deleteCredential: async (credentialId: string): Promise<void> => {
    await api.delete(`/credentials/${credentialId}`)
  },

  /**
   * Re-validate an existing credential
   */
  validateCredential: async (
    credentialId: string
  ): Promise<ValidationResult> => {
    const response = await api.post<ValidationResult>(
      `/credentials/${credentialId}/validate`
    )
    return response.data
  },

  /**
   * Get available models for a credential's provider
   */
  getCredentialModels: async (
    credentialId: string,
    language?: string
  ): Promise<ProviderModel[]> => {
    const response = await api.get<ProviderModelsResponse>(
      `/credentials/${credentialId}/models`,
      { params: language ? { language } : undefined }
    )
    return response.data.models
  },
}

/**
 * Provider API service for listing supported providers
 */
export const providerService = {
  /**
   * List all supported providers
   */
  listProviders: async (): Promise<Provider[]> => {
    const response = await api.get<ProviderListResponse>('/credentials/providers')
    return response.data.providers
  },

  /**
   * Get a specific provider by ID
   */
  getProvider: async (providerId: string): Promise<Provider> => {
    const response = await api.get<Provider>(`/credentials/providers/${providerId}`)
    return response.data
  },
}

/**
 * Helper function to check if an error is a validation error
 */
export function isValidationError(error: unknown): error is { response: { data: ValidationError } } {
  if (typeof error !== 'object' || error === null) return false
  const err = error as { response?: { data?: { error?: string } } }
  return err.response?.data?.error === 'validation_failed'
}

/**
 * Helper function to get provider display name
 */
export function getProviderDisplayName(providerId: string): string {
  const displayNames: Record<string, string> = {
    elevenlabs: 'ElevenLabs',
    azure: 'Azure Cognitive Services',
    gemini: 'Google Gemini',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gcp: 'Google Cloud Platform',
    voai: 'VoAI',
    speechmatics: 'Speechmatics',
  }
  return displayNames[providerId] ?? providerId
}

/**
 * Helper function to get provider icon/color based on provider ID
 */
export function getProviderTheme(
  providerId: string
): { color: string; bgColor: string } {
  const themes: Record<string, { color: string; bgColor: string }> = {
    elevenlabs: { color: '#000000', bgColor: '#f3f3f3' },
    azure: { color: '#0078d4', bgColor: '#e8f4fd' },
    gemini: { color: '#4285f4', bgColor: '#e8f0fe' },
    openai: { color: '#10a37f', bgColor: '#e6f7f1' },
    anthropic: { color: '#d97757', bgColor: '#fdf0eb' },
    gcp: { color: '#4285f4', bgColor: '#e8f0fe' },
    voai: { color: '#6366f1', bgColor: '#eef2ff' },
    speechmatics: { color: '#1e40af', bgColor: '#dbeafe' },
  }
  return themes[providerId] ?? { color: '#6b7280', bgColor: '#f3f4f6' }
}
