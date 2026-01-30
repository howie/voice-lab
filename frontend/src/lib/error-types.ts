/**
 * T018: TypeScript types for quota error responses.
 */

export interface QuotaErrorDetails {
  provider: string
  provider_display_name: string
  retry_after?: number
  quota_type?: string
  help_url?: string
  suggestions?: string[]
  original_error?: string
}

export interface QuotaError {
  code: 'QUOTA_EXCEEDED'
  message: string
  details: QuotaErrorDetails
  request_id?: string
}

export interface ApiErrorResponse {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
    request_id?: string
  }
}

/**
 * Type guard to check if an API error response is a quota error.
 */
export function isQuotaError(
  error: unknown
): error is { error: QuotaError } {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    typeof (error as ApiErrorResponse).error === 'object' &&
    (error as ApiErrorResponse).error?.code === 'QUOTA_EXCEEDED'
  )
}

/**
 * Parse quota error details from an error message string.
 * The backend returns JSON in the error message when it's a structured error.
 */
export function parseQuotaErrorFromMessage(
  errorMessage: string
): QuotaErrorDetails | null {
  try {
    const parsed = JSON.parse(errorMessage)
    if (isQuotaError(parsed)) {
      return parsed.error.details
    }
  } catch {
    // Not JSON, check for quota patterns in the string
    if (
      errorMessage.includes('QUOTA_EXCEEDED') ||
      errorMessage.includes('配額已用盡')
    ) {
      // Extract provider display name from message like "Gemini TTS API 配額已用盡"
      const match = errorMessage.match(/^(.+?)\s*API\s*配額已用盡/)
      return {
        provider: 'unknown',
        provider_display_name: match ? match[1] : 'API',
      }
    }
  }
  return null
}
