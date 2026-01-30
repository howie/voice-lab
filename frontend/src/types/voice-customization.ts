/**
 * Voice Customization Types
 *
 * Feature: 013-tts-role-mgmt
 * TypeScript type definitions for TTS voice customization.
 */

import type { VoiceProfile } from './index'

/**
 * Voice customization settings stored in the database.
 */
export interface VoiceCustomization {
  id: number
  voiceCacheId: string
  customName: string | null
  isFavorite: boolean
  isHidden: boolean
  createdAt: string // ISO 8601 datetime
  updatedAt: string // ISO 8601 datetime
}

/**
 * Voice profile merged with customization data.
 * Used for display in voice selection and management UIs.
 */
export interface VoiceWithCustomization extends VoiceProfile {
  /** Display name: custom_name if set, otherwise original name */
  displayName: string
  /** Whether the voice is favorited */
  isFavorite: boolean
  /** Whether the voice is hidden from TTS selection */
  isHidden: boolean
  /** The customization record if one exists, null for defaults */
  customization: VoiceCustomization | null
  /** Sample audio URL (camelCase from toCamelCase conversion) */
  sampleAudioUrl?: string
}

/**
 * Request body for updating a single voice customization.
 * All fields are optional - only provided fields will be updated.
 */
export interface UpdateVoiceCustomizationRequest {
  /** New custom display name, null to clear */
  customName?: string | null
  /** Set favorite status */
  isFavorite?: boolean
  /** Set hidden status */
  isHidden?: boolean
}

/**
 * Single item in a bulk update request.
 */
export interface BulkUpdateItem {
  voiceCacheId: string
  customName?: string | null
  isFavorite?: boolean
  isHidden?: boolean
}

/**
 * Request body for bulk updating multiple voice customizations.
 */
export interface BulkUpdateVoiceCustomizationRequest {
  updates: BulkUpdateItem[]
}

/**
 * Failed item in a bulk update result.
 */
export interface BulkUpdateFailure {
  voiceCacheId: string
  error: string
}

/**
 * Result of a bulk update operation.
 */
export interface BulkUpdateResult {
  updatedCount: number
  failed: BulkUpdateFailure[]
}

/**
 * Response from the list voices endpoint.
 */
export interface VoiceListResponse {
  items: VoiceWithCustomization[]
  total: number
  limit: number
  offset: number
}

/**
 * Filter parameters for listing voices.
 */
export interface VoiceFilterParams {
  provider?: string
  language?: string
  gender?: 'male' | 'female' | 'neutral'
  ageGroup?: 'child' | 'young' | 'adult' | 'senior'
  search?: string
  excludeHidden?: boolean
  favoritesOnly?: boolean
  limit?: number
  offset?: number
}

/**
 * Filter parameters for listing customizations.
 */
export interface CustomizationFilterParams {
  isFavorite?: boolean
  isHidden?: boolean
}
