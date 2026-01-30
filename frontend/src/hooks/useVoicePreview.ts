/**
 * Voice Preview Hook
 *
 * Feature: 013-tts-role-mgmt
 * US5: 播放聲音預覽 (Voice Preview Playback)
 *
 * Module-level Audio singleton ensures only one preview plays at a time (FR-017).
 * Uses useSyncExternalStore for cross-component reactivity.
 */

import { useCallback, useSyncExternalStore } from 'react'
import { voiceCustomizationApi } from '@/lib/voiceCustomizationApi'

export type PreviewState = 'idle' | 'loading' | 'playing' | 'error'

/** Per-voice state stored externally */
interface VoicePreviewEntry {
  state: PreviewState
  url: string | null
  error: string | null
}

// --- Module-level singleton state ---
let sharedAudio: HTMLAudioElement | null = null
let activeVoiceId: string | null = null
const voiceStates = new Map<string, VoicePreviewEntry>()
const listeners = new Set<() => void>()

function getSharedAudio(): HTMLAudioElement {
  if (!sharedAudio) {
    sharedAudio = new Audio()
    sharedAudio.addEventListener('ended', () => {
      if (activeVoiceId) {
        setVoiceState(activeVoiceId, { state: 'idle' })
        activeVoiceId = null
      }
    })
    sharedAudio.addEventListener('error', () => {
      if (activeVoiceId) {
        setVoiceState(activeVoiceId, { state: 'error', error: '播放失敗' })
        activeVoiceId = null
      }
    })
  }
  return sharedAudio
}

const DEFAULT_STATE: VoicePreviewEntry = { state: 'idle', url: null, error: null }

function getVoiceState(voiceId: string): VoicePreviewEntry {
  return voiceStates.get(voiceId) ?? DEFAULT_STATE
}

function setVoiceState(voiceId: string, partial: Partial<VoicePreviewEntry>) {
  const current = getVoiceState(voiceId)
  voiceStates.set(voiceId, { ...current, ...partial })
  emitChange()
}

function emitChange() {
  for (const listener of listeners) {
    listener()
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

/** Stop any currently playing preview */
function stopCurrent() {
  const audio = getSharedAudio()
  audio.pause()
  audio.currentTime = 0
  if (activeVoiceId) {
    setVoiceState(activeVoiceId, { state: 'idle' })
    activeVoiceId = null
  }
}

/** Play a preview URL */
function playUrl(voiceId: string, url: string) {
  stopCurrent()
  const audio = getSharedAudio()
  activeVoiceId = voiceId
  setVoiceState(voiceId, { state: 'playing', url, error: null })
  audio.src = url
  audio.play().catch(() => {
    setVoiceState(voiceId, { state: 'error', error: '播放失敗' })
    activeVoiceId = null
  })
}

// --- Public hook ---

export function useVoicePreview(voiceCacheId: string, sampleAudioUrl?: string | null) {
  const snapshot = useSyncExternalStore(
    subscribe,
    () => getVoiceState(voiceCacheId),
    () => getVoiceState(voiceCacheId)
  )

  const togglePreview = useCallback(async () => {
    const current = getVoiceState(voiceCacheId)

    // If this voice is currently playing, stop it
    if (current.state === 'playing') {
      stopCurrent()
      return
    }

    // If we already have a URL cached (either from prop or previously generated)
    const cachedUrl = sampleAudioUrl || current.url
    if (cachedUrl) {
      playUrl(voiceCacheId, cachedUrl)
      return
    }

    // Otherwise, generate preview via API
    stopCurrent()
    setVoiceState(voiceCacheId, { state: 'loading', error: null })

    try {
      const url = await voiceCustomizationApi.generatePreview(voiceCacheId)
      setVoiceState(voiceCacheId, { url })
      playUrl(voiceCacheId, url)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '產生預覽失敗'
      setVoiceState(voiceCacheId, { state: 'error', error: message })
    }
  }, [voiceCacheId, sampleAudioUrl])

  return {
    state: snapshot.state,
    error: snapshot.error,
    togglePreview,
  }
}
