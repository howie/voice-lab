/**
 * Magic DJ Store
 * Feature: 010-magic-dj-controller
 * Feature: 011-magic-dj-audio-features
 *
 * T004: Zustand store for Magic DJ state management.
 * T048: Operation priority queue with debounce logic.
 * 011-T006~T009: Audio features enhancement - migration logic and volume actions.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type {
  DJSettings,
  MagicDJState,
  OperationLog,
  OperationMode,
  PendingOperation,
  SessionRecord,
  Track,
  TrackPlaybackState,
  TrackSource,
} from '@/types/magic-dj'
import {
  DEFAULT_DJ_SETTINGS,
  DEFAULT_TRACKS,
  OperationPriority,
} from '@/types/magic-dj'

// =============================================================================
// Store Interface
// =============================================================================

interface MagicDJStoreState extends MagicDJState {
  // === Track Actions ===
  setTracks: (tracks: Track[]) => void
  addTrack: (track: Track) => void
  removeTrack: (trackId: string) => void
  updateTrack: (trackId: string, updates: Partial<Track>) => void
  updateTrackState: (trackId: string, state: Partial<TrackPlaybackState>) => void
  reorderTracks: (activeId: string, overId: string) => void
  setMasterVolume: (volume: number) => void

  // === 011 Audio Features: Volume Actions (T007, T008) ===
  setTrackVolume: (trackId: string, volume: number) => void
  toggleTrackMute: (trackId: string) => void

  // === Mode Actions ===
  setMode: (mode: OperationMode) => void
  setAIConnected: (connected: boolean) => void

  // === Session Timer Actions ===
  startSession: () => void
  stopSession: () => void
  resetSession: () => void
  updateElapsedTime: (seconds: number) => void

  // === AI Response Timing Actions ===
  startAIWaiting: () => void
  stopAIWaiting: () => void

  // === Settings Actions ===
  updateSettings: (settings: Partial<DJSettings>) => void

  // === Session Record Actions ===
  logOperation: (action: OperationLog['action'], data?: Record<string, unknown>) => void
  getCurrentSession: () => SessionRecord | null

  // === Operation Priority Queue Actions (T048) ===
  queueOperation: (operation: Omit<PendingOperation, 'timestamp'>) => boolean
  processOperationQueue: () => PendingOperation | null
  clearOperationQueue: () => void

  // === General Actions ===
  reset: () => void
}

// =============================================================================
// Initial State
// =============================================================================

const createInitialTrackStates = (tracks: Track[]): Record<string, TrackPlaybackState> => {
  const states: Record<string, TrackPlaybackState> = {}
  for (const track of tracks) {
    states[track.id] = {
      trackId: track.id,
      isPlaying: false,
      isLoaded: false,
      isLoading: false,
      error: null,
      currentTime: 0,
      volume: track.volume ?? 1,
      // 011 Audio Features (T005)
      isMuted: false,
      previousVolume: track.volume ?? 1,
    }
  }
  return states
}

/**
 * Migrate legacy track data (011-T006)
 * - Add source: 'tts' if missing
 * - Add volume: 1.0 if missing
 */
const migrateTrackData = (track: Partial<Track>): Track => ({
  ...track,
  source: (track.source as TrackSource) ?? 'tts',
  volume: track.volume ?? 1.0,
} as Track)

const initialState: MagicDJState = {
  tracks: DEFAULT_TRACKS,
  trackStates: createInitialTrackStates(DEFAULT_TRACKS),
  masterVolume: 1,
  currentMode: 'prerecorded',
  isAIConnected: false,
  isSessionActive: false,
  sessionStartTime: null,
  elapsedTime: 0,
  aiRequestTime: null,
  isWaitingForAI: false,
  settings: DEFAULT_DJ_SETTINGS,
  currentSession: null,
  pendingOperations: [],
  lastOperationTime: 0,
}

// =============================================================================
// Debounce Window (100ms for EC-002)
// =============================================================================

const OPERATION_DEBOUNCE_MS = 100

// =============================================================================
// Helper Functions for Audio Persistence
// =============================================================================

/**
 * Convert base64 audio data to blob URL
 */
const base64ToBlobUrl = (base64: string): string => {
  try {
    // Extract mime type and data from data URL or raw base64
    let mimeType = 'audio/mpeg'
    let data = base64

    if (base64.startsWith('data:')) {
      const matches = base64.match(/^data:([^;]+);base64,(.+)$/)
      if (matches) {
        mimeType = matches[1]
        data = matches[2]
      }
    }

    const byteCharacters = atob(data)
    const byteNumbers = new Array(byteCharacters.length)
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }
    const byteArray = new Uint8Array(byteNumbers)
    const blob = new Blob([byteArray], { type: mimeType })
    return URL.createObjectURL(blob)
  } catch (error) {
    console.error('Failed to convert base64 to blob URL:', error)
    return ''
  }
}

/**
 * Restore tracks from persisted state, recreating blob URLs for custom tracks
 */
const restoreTracks = (persistedTracks: Track[]): Track[] => {
  return persistedTracks.map((track) => {
    // If it's a custom track with base64 audio, recreate the blob URL
    if (track.isCustom && track.audioBase64) {
      return {
        ...track,
        url: base64ToBlobUrl(track.audioBase64),
      }
    }
    return track
  })
}

// =============================================================================
// Store Implementation
// =============================================================================

export const useMagicDJStore = create<MagicDJStoreState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // === Track Actions ===
      setTracks: (tracks) =>
        set({
          tracks,
          trackStates: createInitialTrackStates(tracks),
        }),

      addTrack: (track) =>
        set((prev) => ({
          tracks: [...prev.tracks, migrateTrackData(track)],
          trackStates: {
            ...prev.trackStates,
            [track.id]: {
              trackId: track.id,
              isPlaying: false,
              isLoaded: false,
              isLoading: false,
              error: null,
              currentTime: 0,
              volume: track.volume ?? 1,
              // 011 Audio Features (T005)
              isMuted: false,
              previousVolume: track.volume ?? 1,
            },
          },
        })),

      removeTrack: (trackId) =>
        set((prev) => {
          const newTracks = prev.tracks.filter((t) => t.id !== trackId)
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { [trackId]: _removed, ...newTrackStates } = prev.trackStates
          return {
            tracks: newTracks,
            trackStates: newTrackStates,
          }
        }),

      updateTrack: (trackId, updates) =>
        set((prev) => ({
          tracks: prev.tracks.map((t) =>
            t.id === trackId ? { ...t, ...updates } : t
          ),
        })),

      updateTrackState: (trackId, state) =>
        set((prev) => ({
          trackStates: {
            ...prev.trackStates,
            [trackId]: {
              ...prev.trackStates[trackId],
              ...state,
            },
          },
        })),

      reorderTracks: (activeId, overId) =>
        set((prev) => {
          const oldIndex = prev.tracks.findIndex((t) => t.id === activeId)
          const newIndex = prev.tracks.findIndex((t) => t.id === overId)

          if (oldIndex === -1 || newIndex === -1) return prev

          const newTracks = [...prev.tracks]
          const [movedTrack] = newTracks.splice(oldIndex, 1)
          newTracks.splice(newIndex, 0, movedTrack)

          return { tracks: newTracks }
        }),

      setMasterVolume: (volume) =>
        set({ masterVolume: Math.max(0, Math.min(1, volume)) }),

      // === 011 Audio Features: Volume Actions (T007, T008) ===
      setTrackVolume: (trackId, volume) =>
        set((prev) => {
          const clampedVolume = Math.max(0, Math.min(1, volume))
          return {
            tracks: prev.tracks.map((t) =>
              t.id === trackId ? { ...t, volume: clampedVolume } : t
            ),
            trackStates: {
              ...prev.trackStates,
              [trackId]: {
                ...prev.trackStates[trackId],
                volume: clampedVolume,
                isMuted: clampedVolume === 0,
              },
            },
          }
        }),

      toggleTrackMute: (trackId) =>
        set((prev) => {
          const currentState = prev.trackStates[trackId]
          const track = prev.tracks.find((t) => t.id === trackId)
          if (!currentState || !track) return prev

          const isMuted = currentState.isMuted
          const newVolume = isMuted ? currentState.previousVolume || 1 : 0
          const previousVolume = isMuted ? currentState.previousVolume : track.volume

          return {
            tracks: prev.tracks.map((t) =>
              t.id === trackId ? { ...t, volume: newVolume } : t
            ),
            trackStates: {
              ...prev.trackStates,
              [trackId]: {
                ...currentState,
                volume: newVolume,
                isMuted: !isMuted,
                previousVolume: previousVolume,
              },
            },
          }
        }),

      // === Mode Actions ===
      setMode: (mode) => {
        const prev = get()
        if (prev.currentMode !== mode) {
          get().logOperation('mode_switch', { from: prev.currentMode, to: mode })
        }
        set({ currentMode: mode })
      },

      setAIConnected: (connected) => set({ isAIConnected: connected }),

      // === Session Timer Actions ===
      startSession: () => {
        const now = Date.now()
        const session: SessionRecord = {
          id: crypto.randomUUID(),
          startTime: new Date(now).toISOString(),
          endTime: null,
          durationSeconds: 0,
          operationLogs: [],
          observations: [],
          modeSwitchCount: 0,
          aiInteractionCount: 0,
        }
        set({
          isSessionActive: true,
          sessionStartTime: now,
          elapsedTime: 0,
          currentSession: session,
        })
        get().logOperation('session_start')
      },

      stopSession: () => {
        const prev = get()
        get().logOperation('session_end')
        if (prev.currentSession) {
          set({
            isSessionActive: false,
            currentSession: {
              ...prev.currentSession,
              endTime: new Date().toISOString(),
              durationSeconds: prev.elapsedTime,
            },
          })
        } else {
          set({ isSessionActive: false })
        }
      },

      resetSession: () =>
        set({
          isSessionActive: false,
          sessionStartTime: null,
          elapsedTime: 0,
          currentSession: null,
        }),

      updateElapsedTime: (seconds) => set({ elapsedTime: seconds }),

      // === AI Response Timing Actions ===
      startAIWaiting: () =>
        set({
          aiRequestTime: Date.now(),
          isWaitingForAI: true,
        }),

      stopAIWaiting: () =>
        set({
          aiRequestTime: null,
          isWaitingForAI: false,
        }),

      // === Settings Actions ===
      updateSettings: (settings) =>
        set((prev) => ({
          settings: { ...prev.settings, ...settings },
        })),

      // === Session Record Actions ===
      logOperation: (action, data) => {
        set((prev) => {
          if (!prev.currentSession) return prev

          const log: OperationLog = {
            timestamp: new Date().toISOString(),
            action,
            data,
          }

          // Count mode switches and AI interactions
          let modeSwitchCount = prev.currentSession.modeSwitchCount
          let aiInteractionCount = prev.currentSession.aiInteractionCount

          if (action === 'mode_switch') {
            modeSwitchCount++
          }
          if (action === 'force_submit') {
            aiInteractionCount++
          }

          return {
            currentSession: {
              ...prev.currentSession,
              operationLogs: [...prev.currentSession.operationLogs, log],
              modeSwitchCount,
              aiInteractionCount,
            },
          }
        })
      },

      getCurrentSession: () => get().currentSession,

      // === Operation Priority Queue Actions (T048) ===
      queueOperation: (operation) => {
        const now = Date.now()
        const prev = get()

        // Check if within debounce window
        if (now - prev.lastOperationTime < OPERATION_DEBOUNCE_MS) {
          // Within debounce window - add to queue
          const newOp: PendingOperation = {
            ...operation,
            timestamp: now,
          }

          set((state) => ({
            pendingOperations: [...state.pendingOperations, newOp],
          }))

          return false // Operation queued, not executed immediately
        }

        // Outside debounce window - execute immediately
        set({ lastOperationTime: now })
        return true // Operation can be executed immediately
      },

      processOperationQueue: () => {
        const prev = get()
        if (prev.pendingOperations.length === 0) {
          return null
        }

        // Sort by priority (lower number = higher priority)
        const sorted = [...prev.pendingOperations].sort(
          (a, b) => a.priority - b.priority
        )

        // Get highest priority operation
        const highestPriority = sorted[0]

        // Clear queue and update last operation time
        set({
          pendingOperations: [],
          lastOperationTime: Date.now(),
        })

        return highestPriority
      },

      clearOperationQueue: () => set({ pendingOperations: [] }),

      // === General Actions ===
      reset: () => set(initialState),
    }),
    {
      name: 'magic-dj-store',
      // Persist user preferences and track configuration (011-T009)
      partialize: (state) => ({
        settings: state.settings,
        masterVolume: state.masterVolume,
        // Persist tracks (order + custom tracks with audio data, source, volume)
        tracks: state.tracks.map((track) => ({
          ...track,
          // Don't persist blob URLs, they're ephemeral
          url: track.isCustom || track.source === 'upload' ? '' : track.url,
          // Ensure source and volume are persisted (011-T009)
          source: track.source ?? 'tts',
          volume: track.volume ?? 1.0,
        })),
      }),
      // Merge persisted state with defaults (011-T006, T009)
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<MagicDJStoreState>

        // Restore tracks from persisted state with migration (011-T006)
        let tracks = currentState.tracks
        if (persisted.tracks && persisted.tracks.length > 0) {
          // Apply migration to each track before restoring blob URLs
          const migratedTracks = persisted.tracks.map(migrateTrackData)
          tracks = restoreTracks(migratedTracks)
        }

        return {
          ...currentState,
          settings: {
            ...DEFAULT_DJ_SETTINGS,
            ...(persisted.settings || {}),
          },
          masterVolume: persisted.masterVolume ?? currentState.masterVolume,
          tracks,
          trackStates: createInitialTrackStates(tracks),
        }
      },
    }
  )
)

// =============================================================================
// Selectors
// =============================================================================

export const selectIsPlaying = (trackId: string) => (state: MagicDJStoreState) =>
  state.trackStates[trackId]?.isPlaying ?? false

export const selectIsLoaded = (trackId: string) => (state: MagicDJStoreState) =>
  state.trackStates[trackId]?.isLoaded ?? false

export const selectTrackError = (trackId: string) => (state: MagicDJStoreState) =>
  state.trackStates[trackId]?.error ?? null

export const selectAnyTrackPlaying = (state: MagicDJStoreState) =>
  Object.values(state.trackStates).some((s) => s.isPlaying)

export const selectPlayingTracks = (state: MagicDJStoreState) =>
  Object.values(state.trackStates).filter((s) => s.isPlaying)

export const selectIsTimeWarning = (state: MagicDJStoreState) =>
  state.elapsedTime >= state.settings.timeWarningAt

export const selectIsTimeLimit = (state: MagicDJStoreState) =>
  state.elapsedTime >= state.settings.sessionTimeLimit

export const selectAIWaitingSeconds = (state: MagicDJStoreState) => {
  if (!state.isWaitingForAI || !state.aiRequestTime) return 0
  return Math.floor((Date.now() - state.aiRequestTime) / 1000)
}

export const selectIsAITimeout = (state: MagicDJStoreState) => {
  const waitingSeconds = selectAIWaitingSeconds(state)
  return waitingSeconds >= state.settings.aiResponseTimeout
}

// Export helper for operation priority
export { OperationPriority }

export default useMagicDJStore
