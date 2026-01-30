/**
 * Shared hook: fetch available TTS providers from backend and filter a given
 * provider list to only include those whose API keys are configured.
 *
 * Used by ProviderSelector, MultiRoleTTSPage, and TrackEditorModal.
 */

import { useEffect, useRef, useState } from 'react'
import { ttsApi } from '@/lib/api'

/** Cached result so multiple components in the same page don't fire duplicate requests. */
let cache: { names: Set<string>; ts: number } | null = null
const CACHE_TTL = 60_000 // 1 minute

interface Options<T> {
  /** Full list of providers to filter. */
  allProviders: T[]
  /** Extract the provider id/name from each item (e.g. `p => p.id`). */
  getKey: (item: T) => string
  /** Currently selected provider value. */
  value: string
  /** Called when the current value is not available and needs to auto-switch. */
  onChange: (newValue: string) => void
}

interface Result<T> {
  /** Filtered list containing only available providers. */
  providers: T[]
  /** True while the initial fetch is in-flight. */
  loading: boolean
  /** The set of available provider names (useful for look-ups outside the list). */
  availableNames: Set<string>
}

export function useAvailableTTSProviders<T>({
  allProviders,
  getKey,
  value,
  onChange,
}: Options<T>): Result<T> {
  const [availableNames, setAvailableNames] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  useEffect(() => {
    let cancelled = false

    async function load() {
      // Use cache if fresh enough
      if (cache && Date.now() - cache.ts < CACHE_TTL) {
        if (!cancelled) {
          setAvailableNames(cache.names)
          if (cache.names.size > 0 && !cache.names.has(value)) {
            const first = allProviders.find((p) => cache!.names.has(getKey(p)))
            if (first) onChangeRef.current(getKey(first))
          }
          setLoading(false)
        }
        return
      }

      try {
        const response = await ttsApi.getProvidersSummary()
        if (cancelled) return

        const names = new Set(
          response.data.tts
            .filter((p) => p.status === 'available')
            .map((p) => p.name)
        )

        cache = { names, ts: Date.now() }
        setAvailableNames(names)

        // Auto-switch if the currently selected provider is not available
        if (names.size > 0 && !names.has(value)) {
          const first = allProviders.find((p) => names.has(getKey(p)))
          if (first) onChangeRef.current(getKey(first))
        }
      } catch {
        // API error — leave availableNames empty so fallback kicks in
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps -- fetch once on mount

  // If no available info yet (API error), fall back to full list
  const providers =
    availableNames.size > 0
      ? allProviders.filter((p) => availableNames.has(getKey(p)))
      : allProviders

  return { providers, loading, availableNames }
}

/** Invalidate the cache (useful after credential changes). */
export function invalidateTTSProviderCache() {
  cache = null
}
