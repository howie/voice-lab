/**
 * T023: Frontend test for retry display and error message formatting.
 */

import { describe, it, expect } from 'vitest'

import { formatRetryAfter } from '../error-messages'
import { isQuotaError, parseQuotaErrorFromMessage } from '../error-types'

describe('formatRetryAfter', () => {
  it('formats zero seconds as immediate retry', () => {
    expect(formatRetryAfter(0)).toBe('可以立即重試')
  })

  it('formats negative seconds as immediate retry', () => {
    expect(formatRetryAfter(-10)).toBe('可以立即重試')
  })

  it('formats seconds under 60', () => {
    expect(formatRetryAfter(30)).toBe('約 30 秒後可重試')
  })

  it('formats exactly 60 seconds as 1 minute', () => {
    expect(formatRetryAfter(60)).toBe('約 1 分鐘後可重試')
  })

  it('formats minutes', () => {
    expect(formatRetryAfter(300)).toBe('約 5 分鐘後可重試')
  })

  it('rounds up minutes', () => {
    expect(formatRetryAfter(90)).toBe('約 2 分鐘後可重試')
  })

  it('formats exactly 3600 seconds as 1 hour', () => {
    expect(formatRetryAfter(3600)).toBe('約 1 小時後可重試')
  })

  it('formats hours', () => {
    expect(formatRetryAfter(7200)).toBe('約 2 小時後可重試')
  })

  it('rounds up hours', () => {
    expect(formatRetryAfter(5400)).toBe('約 2 小時後可重試')
  })

  it('formats days', () => {
    expect(formatRetryAfter(86400)).toBe('約 1 天後可重試')
  })

  it('formats multiple days', () => {
    expect(formatRetryAfter(172800)).toBe('約 2 天後可重試')
  })
})

describe('isQuotaError', () => {
  it('returns true for valid quota error object', () => {
    const error = {
      error: {
        code: 'QUOTA_EXCEEDED',
        message: 'Gemini TTS API 配額已用盡',
        details: {
          provider: 'gemini',
          provider_display_name: 'Gemini TTS',
          retry_after: 3600,
        },
      },
    }
    expect(isQuotaError(error)).toBe(true)
  })

  it('returns false for non-quota error', () => {
    const error = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
      },
    }
    expect(isQuotaError(error)).toBe(false)
  })

  it('returns false for null', () => {
    expect(isQuotaError(null)).toBe(false)
  })

  it('returns false for non-object', () => {
    expect(isQuotaError('string')).toBe(false)
  })
})

describe('parseQuotaErrorFromMessage', () => {
  it('parses JSON quota error', () => {
    const json = JSON.stringify({
      error: {
        code: 'QUOTA_EXCEEDED',
        message: 'Gemini TTS API 配額已用盡',
        details: {
          provider: 'gemini',
          provider_display_name: 'Gemini TTS',
          retry_after: 3600,
          help_url: 'https://ai.google.dev/pricing',
          suggestions: ['檢查用量', '升級方案'],
        },
      },
    })
    const result = parseQuotaErrorFromMessage(json)
    expect(result).not.toBeNull()
    expect(result?.provider).toBe('gemini')
    expect(result?.provider_display_name).toBe('Gemini TTS')
    expect(result?.retry_after).toBe(3600)
    expect(result?.help_url).toBe('https://ai.google.dev/pricing')
    expect(result?.suggestions).toHaveLength(2)
  })

  it('parses Chinese quota error string', () => {
    const result = parseQuotaErrorFromMessage('Gemini TTS API 配額已用盡')
    expect(result).not.toBeNull()
    expect(result?.provider_display_name).toBe('Gemini TTS')
  })

  it('parses QUOTA_EXCEEDED code string', () => {
    const result = parseQuotaErrorFromMessage('QUOTA_EXCEEDED: some error')
    expect(result).not.toBeNull()
  })

  it('returns null for non-quota error', () => {
    const result = parseQuotaErrorFromMessage('Network error: connection refused')
    expect(result).toBeNull()
  })
})
