/**
 * Quota and Rate Limit Dashboard API Service
 */

import { api } from '../lib/api'

export interface ProviderRateLimitInfo {
  free_rpm: number | null
  free_rpd: number | null
  tier1_rpm: number | null
  tier2_rpm: number | null
  notes: string | null
}

export interface ProviderQuotaStatus {
  provider: string
  display_name: string
  has_credential: boolean
  is_valid: boolean
  character_count: number | null
  character_limit: number | null
  remaining_characters: number | null
  usage_percent: number | null
  tier: string | null
  // Tracked usage
  minute_requests: number
  hour_requests: number
  day_requests: number
  quota_hits_today: number
  estimated_rpm_limit: number | null
  usage_warning: string | null
  // Reference
  rate_limits: ProviderRateLimitInfo | null
  help_url: string | null
  suggestions: string[]
  last_validated_at: string | null
}

export interface AppRateLimitStatus {
  general_rpm: number
  general_rph: number
  tts_rpm: number
  tts_rph: number
  general_minute_remaining: number
  general_hour_remaining: number
  tts_minute_remaining: number
  tts_hour_remaining: number
}

export interface QuotaDashboardResponse {
  providers: ProviderQuotaStatus[]
  app_rate_limits: AppRateLimitStatus
  fetched_at: string
}

export const quotaApi = {
  getDashboard: async (): Promise<QuotaDashboardResponse> => {
    const response = await api.get<QuotaDashboardResponse>('/quota')
    return response.data
  },
}
