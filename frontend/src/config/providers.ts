/**
 * Provider Configuration
 * Defines text length limits and warnings for different TTS providers
 */

export interface ProviderConfig {
  id: string
  name: string
  maxTextLength: number
  recommendedMaxLength?: number
  warningMessage?: string
}

export const PROVIDER_CONFIGS: Record<string, ProviderConfig> = {
  azure: {
    id: 'azure',
    name: 'Azure',
    maxTextLength: 5000,
  },
  gcp: {
    id: 'gcp',
    name: 'Google Cloud',
    maxTextLength: 5000,
  },
  elevenlabs: {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    maxTextLength: 5000,
  },
  voai: {
    id: 'voai',
    name: 'VoAI',
    maxTextLength: 500,  // VoAI API hard limit
  },
}

export const DEFAULT_MAX_TEXT_LENGTH = 5000

/**
 * Get provider configuration by provider ID
 */
export function getProviderConfig(providerId: string): ProviderConfig {
  return PROVIDER_CONFIGS[providerId] || {
    id: providerId,
    name: providerId,
    maxTextLength: DEFAULT_MAX_TEXT_LENGTH,
  }
}

/**
 * Check if text length exceeds recommended limit for provider
 */
export function isTextLengthWarning(providerId: string, textLength: number): boolean {
  const config = getProviderConfig(providerId)
  if (config.recommendedMaxLength) {
    return textLength > config.recommendedMaxLength
  }
  return false
}

/**
 * Get warning message for provider if text exceeds recommended length
 */
export function getTextLengthWarning(providerId: string, textLength: number): string | null {
  const config = getProviderConfig(providerId)
  if (config.recommendedMaxLength && textLength > config.recommendedMaxLength) {
    return config.warningMessage || `建議不超過 ${config.recommendedMaxLength} 字`
  }
  return null
}
