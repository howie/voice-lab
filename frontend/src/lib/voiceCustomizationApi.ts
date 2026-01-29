/**
 * Voice Customization API Client
 *
 * Feature: 013-tts-role-mgmt
 * T009: API service for voice customization CRUD operations
 */

import { api } from './api'
import type {
  VoiceCustomization,
  VoiceWithCustomization,
  UpdateVoiceCustomizationRequest,
  BulkUpdateVoiceCustomizationRequest,
  BulkUpdateResult,
  VoiceListResponse,
  VoiceFilterParams,
  CustomizationFilterParams,
} from '@/types/voice-customization'

/**
 * Convert snake_case API response to camelCase for TypeScript
 */
function toCamelCase<T>(obj: Record<string, unknown>): T {
  const result: Record<string, unknown> = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
      const value = obj[key]
      if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
        result[camelKey] = toCamelCase(value as Record<string, unknown>)
      } else {
        result[camelKey] = value
      }
    }
  }
  return result as T
}

/**
 * Convert camelCase request to snake_case for API
 */
function toSnakeCase(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
      const value = obj[key]
      if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
        result[snakeKey] = toSnakeCase(value as Record<string, unknown>)
      } else {
        result[snakeKey] = value
      }
    }
  }
  return result
}

/**
 * Voice Customization API endpoints
 */
export const voiceCustomizationApi = {
  /**
   * List all voice customizations
   */
  listCustomizations: async (
    filters?: CustomizationFilterParams
  ): Promise<VoiceCustomization[]> => {
    const params: Record<string, boolean> = {}
    if (filters?.isFavorite !== undefined) {
      params.is_favorite = filters.isFavorite
    }
    if (filters?.isHidden !== undefined) {
      params.is_hidden = filters.isHidden
    }

    const response = await api.get<Record<string, unknown>[]>('/voice-customizations', {
      params,
    })
    return response.data.map((item) => toCamelCase<VoiceCustomization>(item))
  },

  /**
   * Get a single voice customization by voice cache ID
   */
  getCustomization: async (voiceCacheId: string): Promise<VoiceCustomization | null> => {
    try {
      const response = await api.get<Record<string, unknown>>(
        `/voice-customizations/${encodeURIComponent(voiceCacheId)}`
      )
      return toCamelCase<VoiceCustomization>(response.data)
    } catch (error: unknown) {
      // Return null for 404 (no customization exists)
      if ((error as { response?: { status?: number } })?.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  /**
   * Update a voice customization (upsert)
   */
  updateCustomization: async (
    voiceCacheId: string,
    data: UpdateVoiceCustomizationRequest
  ): Promise<VoiceCustomization> => {
    const response = await api.put<Record<string, unknown>>(
      `/voice-customizations/${encodeURIComponent(voiceCacheId)}`,
      toSnakeCase(data as unknown as Record<string, unknown>)
    )
    return toCamelCase<VoiceCustomization>(response.data)
  },

  /**
   * Delete a voice customization (reset to defaults)
   */
  deleteCustomization: async (voiceCacheId: string): Promise<void> => {
    await api.delete(`/voice-customizations/${encodeURIComponent(voiceCacheId)}`)
  },

  /**
   * Bulk update multiple voice customizations
   */
  bulkUpdate: async (data: BulkUpdateVoiceCustomizationRequest): Promise<BulkUpdateResult> => {
    const response = await api.patch<Record<string, unknown>>('/voice-customizations/bulk', {
      updates: data.updates.map((item) => toSnakeCase(item as unknown as Record<string, unknown>)),
    })
    return toCamelCase<BulkUpdateResult>(response.data)
  },

  /**
   * List voices with customization data merged
   * This is the main endpoint for the voice management page
   */
  listVoicesWithCustomizations: async (
    filters?: VoiceFilterParams
  ): Promise<VoiceListResponse> => {
    const params: Record<string, string | number | boolean> = {}

    if (filters?.provider) params.provider = filters.provider
    if (filters?.language) params.language = filters.language
    if (filters?.gender) params.gender = filters.gender
    if (filters?.ageGroup) params.age_group = filters.ageGroup
    if (filters?.search) params.search = filters.search
    if (filters?.excludeHidden !== undefined) params.exclude_hidden = filters.excludeHidden
    if (filters?.favoritesOnly !== undefined) params.favorites_only = filters.favoritesOnly
    if (filters?.limit !== undefined) params.limit = filters.limit
    if (filters?.offset !== undefined) params.offset = filters.offset

    const response = await api.get<{
      items: Record<string, unknown>[]
      total: number
      limit: number
      offset: number
    }>('/voices', { params })

    return {
      items: response.data.items.map((item) => toCamelCase<VoiceWithCustomization>(item)),
      total: response.data.total,
      limit: response.data.limit,
      offset: response.data.offset,
    }
  },

  /**
   * Toggle favorite status for a voice
   */
  toggleFavorite: async (voiceCacheId: string, isFavorite: boolean): Promise<VoiceCustomization> => {
    return voiceCustomizationApi.updateCustomization(voiceCacheId, { isFavorite })
  },

  /**
   * Toggle hidden status for a voice
   */
  toggleHidden: async (voiceCacheId: string, isHidden: boolean): Promise<VoiceCustomization> => {
    return voiceCustomizationApi.updateCustomization(voiceCacheId, { isHidden })
  },

  /**
   * Update custom name for a voice
   */
  updateCustomName: async (
    voiceCacheId: string,
    customName: string | null
  ): Promise<VoiceCustomization> => {
    return voiceCustomizationApi.updateCustomization(voiceCacheId, { customName })
  },
}
