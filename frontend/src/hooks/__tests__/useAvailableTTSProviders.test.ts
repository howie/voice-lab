/**
 * useAvailableTTSProviders Hook Tests
 *
 * Tests the shared hook that filters TTS providers by backend availability.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import {
  useAvailableTTSProviders,
  invalidateTTSProviderCache,
} from '../useAvailableTTSProviders'

// Mock ttsApi
vi.mock('@/lib/api', () => ({
  ttsApi: {
    getProvidersSummary: vi.fn(),
  },
}))

import { ttsApi } from '@/lib/api'

const mockGetProvidersSummary = vi.mocked(ttsApi.getProvidersSummary)

// Test provider items
interface TestProvider {
  id: string
  label: string
}

const ALL: TestProvider[] = [
  { id: 'azure', label: 'Azure' },
  { id: 'gcp', label: 'GCP' },
  { id: 'gemini', label: 'Gemini' },
  { id: 'elevenlabs', label: 'ElevenLabs' },
  { id: 'voai', label: 'VoAI' },
]

function summaryResponse(availableNames: string[]) {
  return {
    data: {
      tts: ['azure', 'gcp', 'gemini', 'elevenlabs', 'voai'].map((name) => ({
        name,
        display_name: name,
        type: 'tts',
        supported_formats: [],
        supported_languages: [],
        supported_params: {},
        status: availableNames.includes(name) ? 'available' : 'unavailable',
      })),
      stt: [],
      llm: [],
    },
  }
}

function defaultOpts(overrides?: Partial<Parameters<typeof useAvailableTTSProviders<TestProvider>>[0]>) {
  return {
    allProviders: ALL,
    getKey: (p: TestProvider) => p.id,
    value: 'azure',
    onChange: vi.fn(),
    ...overrides,
  }
}

describe('useAvailableTTSProviders', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    invalidateTTSProviderCache()
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['azure', 'gcp', 'gemini', 'elevenlabs', 'voai']) as never
    )
  })

  // ---------------------------------------------------------------------------
  // Basic behaviour
  // ---------------------------------------------------------------------------

  it('starts in loading state', () => {
    const { result } = renderHook(() => useAvailableTTSProviders(defaultOpts()))
    expect(result.current.loading).toBe(true)
  })

  it('resolves to all providers when all are available', async () => {
    const { result } = renderHook(() => useAvailableTTSProviders(defaultOpts()))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.providers).toHaveLength(ALL.length)
    expect(result.current.providers.map((p) => p.id)).toEqual([
      'azure', 'gcp', 'gemini', 'elevenlabs', 'voai',
    ])
  })

  // ---------------------------------------------------------------------------
  // Filtering
  // ---------------------------------------------------------------------------

  it('only returns available providers', async () => {
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['azure', 'gemini']) as never
    )

    const { result } = renderHook(() => useAvailableTTSProviders(defaultOpts()))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.providers).toHaveLength(2)
    expect(result.current.providers.map((p) => p.id)).toEqual(['azure', 'gemini'])
  })

  it('exposes availableNames set', async () => {
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['elevenlabs']) as never
    )

    const { result } = renderHook(() =>
      useAvailableTTSProviders(defaultOpts({ value: 'elevenlabs' }))
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.availableNames.has('elevenlabs')).toBe(true)
    expect(result.current.availableNames.has('azure')).toBe(false)
  })

  // ---------------------------------------------------------------------------
  // Auto-switch
  // ---------------------------------------------------------------------------

  it('auto-switches when selected provider is unavailable', async () => {
    const onChange = vi.fn()
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['gemini', 'voai']) as never
    )

    renderHook(() =>
      useAvailableTTSProviders(defaultOpts({ value: 'azure', onChange }))
    )

    await waitFor(() => expect(onChange).toHaveBeenCalledWith('gemini'))
  })

  it('does NOT auto-switch when selected provider is available', async () => {
    const onChange = vi.fn()
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['azure', 'gcp']) as never
    )

    const { result } = renderHook(() =>
      useAvailableTTSProviders(defaultOpts({ value: 'azure', onChange }))
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(onChange).not.toHaveBeenCalled()
  })

  // ---------------------------------------------------------------------------
  // Fallback
  // ---------------------------------------------------------------------------

  it('falls back to full list on API error', async () => {
    mockGetProvidersSummary.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useAvailableTTSProviders(defaultOpts()))

    await waitFor(() => expect(result.current.loading).toBe(false))

    // Should return ALL providers as fallback
    expect(result.current.providers).toHaveLength(ALL.length)
  })

  it('falls back to full list when no providers are available', async () => {
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse([]) as never
    )

    const { result } = renderHook(() => useAvailableTTSProviders(defaultOpts()))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.providers).toHaveLength(ALL.length)
  })

  // ---------------------------------------------------------------------------
  // Cache
  // ---------------------------------------------------------------------------

  it('reuses cache on second call without re-fetching', async () => {
    // First call — populates cache
    const { result: r1 } = renderHook(() => useAvailableTTSProviders(defaultOpts()))
    await waitFor(() => expect(r1.current.loading).toBe(false))

    expect(mockGetProvidersSummary).toHaveBeenCalledTimes(1)

    // Second call — should use cache
    const { result: r2 } = renderHook(() => useAvailableTTSProviders(defaultOpts()))
    await waitFor(() => expect(r2.current.loading).toBe(false))

    // Still only 1 API call
    expect(mockGetProvidersSummary).toHaveBeenCalledTimes(1)
    expect(r2.current.providers).toHaveLength(ALL.length)
  })

  it('re-fetches after cache invalidation', async () => {
    // First call
    const { result: r1 } = renderHook(() => useAvailableTTSProviders(defaultOpts()))
    await waitFor(() => expect(r1.current.loading).toBe(false))
    expect(mockGetProvidersSummary).toHaveBeenCalledTimes(1)

    // Invalidate
    invalidateTTSProviderCache()

    // Change response
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['voai']) as never
    )

    const { result: r2 } = renderHook(() =>
      useAvailableTTSProviders(defaultOpts({ value: 'voai' }))
    )
    await waitFor(() => expect(r2.current.loading).toBe(false))

    expect(mockGetProvidersSummary).toHaveBeenCalledTimes(2)
    expect(r2.current.providers).toHaveLength(1)
    expect(r2.current.providers[0].id).toBe('voai')
  })

  it('auto-switches via cache when selected provider is unavailable', async () => {
    // Populate cache with limited availability
    mockGetProvidersSummary.mockResolvedValue(
      summaryResponse(['gcp']) as never
    )
    const { result: r1 } = renderHook(() =>
      useAvailableTTSProviders(defaultOpts({ value: 'gcp' }))
    )
    await waitFor(() => expect(r1.current.loading).toBe(false))

    // Second hook with a value not in cache
    const onChange = vi.fn()
    const { result: r2 } = renderHook(() =>
      useAvailableTTSProviders(defaultOpts({ value: 'azure', onChange }))
    )
    await waitFor(() => expect(r2.current.loading).toBe(false))

    expect(onChange).toHaveBeenCalledWith('gcp')
  })
})
