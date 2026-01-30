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
  ChannelQueueItem,
  ChannelType,
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
  DEFAULT_CHANNEL_QUEUES,
  DEFAULT_CHANNEL_STATES,
  DEFAULT_DJ_SETTINGS,
  DEFAULT_TRACKS,
  OperationPriority,
} from '@/types/magic-dj'
import * as djApi from '@/services/djApi'
import {
  audioStorage,
  type StorageQuota,
  type AudioStorageError,
  type MigrationResult,
} from '@/lib/audioStorage'

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

  // === Channel Queue Actions (DD-001) ===
  addToChannel: (channelType: ChannelType, trackId: string) => void
  removeFromChannel: (channelType: ChannelType, itemId: string) => void
  reorderChannel: (channelType: ChannelType, activeId: string, overId: string) => void
  setChannelVolume: (channelType: ChannelType, volume: number) => void
  toggleChannelMute: (channelType: ChannelType) => void
  advanceChannel: (channelType: ChannelType) => void
  resetChannelPosition: (channelType: ChannelType) => void
  clearChannel: (channelType: ChannelType) => void

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

  // === Backend Sync Actions (011 Phase 3) ===
  setAuthenticated: (authenticated: boolean) => void
  fetchPresets: () => Promise<void>
  loadPreset: (presetId: string) => Promise<void>
  saveCurrentPreset: () => Promise<void>
  createNewPreset: (name: string, description?: string) => Promise<string>
  deleteCurrentPreset: () => Promise<void>
  importToBackend: (presetName: string) => Promise<string>
  switchToLocalStorage: () => void

  // === IndexedDB Storage Actions (011 Phase 4) ===
  storageQuota: StorageQuota | null
  storageError: AudioStorageError | null
  isStorageReady: boolean
  hasPendingMigration: boolean
  pendingMigrationCount: number
  initializeStorage: () => Promise<void>
  refreshStorageQuota: () => Promise<void>
  saveAudioToStorage: (trackId: string, blob: Blob) => Promise<void>
  loadAudioFromStorage: (trackId: string) => Promise<Blob | null>
  deleteAudioFromStorage: (trackId: string) => Promise<void>
  checkMigration: () => void
  completeMigration: (result: MigrationResult) => void
  clearStorageError: () => void

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

const initialState: MagicDJState & {
  storageQuota: StorageQuota | null
  storageError: AudioStorageError | null
  isStorageReady: boolean
  hasPendingMigration: boolean
  pendingMigrationCount: number
} = {
  tracks: DEFAULT_TRACKS,
  trackStates: createInitialTrackStates(DEFAULT_TRACKS),
  masterVolume: 1,
  // Channel queues (DD-001)
  channelQueues: DEFAULT_CHANNEL_QUEUES,
  channelStates: DEFAULT_CHANNEL_STATES,
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
  // Backend Sync (011 Phase 3)
  currentPresetId: null,
  presets: [],
  isLoading: false,
  isSyncing: false,
  syncError: null,
  isAuthenticated: false,
  // IndexedDB Storage (011 Phase 4)
  storageQuota: null,
  storageError: null,
  isStorageReady: false,
  hasPendingMigration: false,
  pendingMigrationCount: 0,
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

      addTrack: (track) => {
        // Add track to state with IndexedDB flag
        const migratedTrack = {
          ...migrateTrackData(track),
          // Mark that audio is stored in IndexedDB, not base64
          hasLocalAudio: track.source === 'upload',
        }

        set((prev) => ({
          tracks: [...prev.tracks, migratedTrack],
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
        }))
      },

      removeTrack: (trackId) => {
        const track = get().tracks.find((t) => t.id === trackId)

        // Delete from IndexedDB if it's a local audio track
        if (track && (track.source === 'upload' || track.hasLocalAudio)) {
          audioStorage.delete(trackId).catch((err) => {
            console.error('Failed to delete audio from storage:', err)
          })
        }

        // Revoke blob URL if exists
        if (track?.url && track.url.startsWith('blob:')) {
          audioStorage.revokeObjectURL(track.url)
        }

        set((prev) => {
          const newTracks = prev.tracks.filter((t) => t.id !== trackId)
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { [trackId]: _removed, ...newTrackStates } = prev.trackStates
          return {
            tracks: newTracks,
            trackStates: newTrackStates,
          }
        })
      },

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

      // === Channel Queue Actions (DD-001) ===
      addToChannel: (channelType, trackId) =>
        set((prev) => {
          const newItem: ChannelQueueItem = {
            id: crypto.randomUUID(),
            trackId,
          }
          return {
            channelQueues: {
              ...prev.channelQueues,
              [channelType]: [...prev.channelQueues[channelType], newItem],
            },
          }
        }),

      removeFromChannel: (channelType, itemId) =>
        set((prev) => {
          const queue = prev.channelQueues[channelType]
          const removedIndex = queue.findIndex((item) => item.id === itemId)
          const newQueue = queue.filter((item) => item.id !== itemId)
          const channelState = prev.channelStates[channelType]

          // Adjust currentIndex if needed
          let newIndex = channelState.currentIndex
          if (removedIndex !== -1 && removedIndex <= newIndex) {
            newIndex = Math.max(-1, newIndex - 1)
          }

          return {
            channelQueues: {
              ...prev.channelQueues,
              [channelType]: newQueue,
            },
            channelStates: {
              ...prev.channelStates,
              [channelType]: { ...channelState, currentIndex: newIndex },
            },
          }
        }),

      reorderChannel: (channelType, activeId, overId) =>
        set((prev) => {
          const queue = [...prev.channelQueues[channelType]]
          const oldIndex = queue.findIndex((item) => item.id === activeId)
          const newIndex = queue.findIndex((item) => item.id === overId)

          if (oldIndex === -1 || newIndex === -1) return prev

          const [movedItem] = queue.splice(oldIndex, 1)
          queue.splice(newIndex, 0, movedItem)

          return {
            channelQueues: {
              ...prev.channelQueues,
              [channelType]: queue,
            },
          }
        }),

      setChannelVolume: (channelType, volume) =>
        set((prev) => ({
          channelStates: {
            ...prev.channelStates,
            [channelType]: {
              ...prev.channelStates[channelType],
              volume: Math.max(0, Math.min(1, volume)),
            },
          },
        })),

      toggleChannelMute: (channelType) =>
        set((prev) => {
          const state = prev.channelStates[channelType]
          return {
            channelStates: {
              ...prev.channelStates,
              [channelType]: { ...state, isMuted: !state.isMuted },
            },
          }
        }),

      advanceChannel: (channelType) =>
        set((prev) => {
          const queue = prev.channelQueues[channelType]
          const state = prev.channelStates[channelType]
          const nextIndex = state.currentIndex + 1

          return {
            channelStates: {
              ...prev.channelStates,
              [channelType]: {
                ...state,
                currentIndex: nextIndex < queue.length ? nextIndex : -1,
              },
            },
          }
        }),

      resetChannelPosition: (channelType) =>
        set((prev) => ({
          channelStates: {
            ...prev.channelStates,
            [channelType]: {
              ...prev.channelStates[channelType],
              currentIndex: prev.channelQueues[channelType].length > 0 ? 0 : -1,
            },
          },
        })),

      clearChannel: (channelType) =>
        set((prev) => ({
          channelQueues: {
            ...prev.channelQueues,
            [channelType]: [],
          },
          channelStates: {
            ...prev.channelStates,
            [channelType]: {
              ...prev.channelStates[channelType],
              currentIndex: -1,
            },
          },
        })),

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

      // === Backend Sync Actions (011 Phase 3) ===
      setAuthenticated: (authenticated) => set({ isAuthenticated: authenticated }),

      fetchPresets: async () => {
        const state = get()
        if (!state.isAuthenticated) return

        set({ isLoading: true, syncError: null })
        try {
          const response = await djApi.listPresets()
          set({
            presets: response.items.map((p) => ({
              id: p.id,
              name: p.name,
              description: p.description,
              is_default: p.is_default,
              created_at: p.created_at,
              updated_at: p.updated_at,
            })),
            isLoading: false,
          })
        } catch (error) {
          console.error('Failed to fetch presets:', error)
          set({
            syncError: error instanceof Error ? error.message : 'Failed to fetch presets',
            isLoading: false,
          })
        }
      },

      loadPreset: async (presetId) => {
        set({ isLoading: true, syncError: null })
        try {
          const response = await djApi.getPreset(presetId)

          // Convert API tracks to frontend format
          const tracks = response.tracks.map((t) => djApi.apiTrackToFrontend(t))

          // Convert settings
          const apiSettings = djApi.apiSettingsToFrontend(response.settings)

          set({
            currentPresetId: presetId,
            tracks,
            trackStates: createInitialTrackStates(tracks),
            masterVolume: response.settings.master_volume,
            settings: {
              ...get().settings,
              ...apiSettings,
            },
            isLoading: false,
          })
        } catch (error) {
          console.error('Failed to load preset:', error)
          set({
            syncError: error instanceof Error ? error.message : 'Failed to load preset',
            isLoading: false,
          })
          throw error
        }
      },

      saveCurrentPreset: async () => {
        const state = get()
        if (!state.currentPresetId || !state.isAuthenticated) return

        set({ isSyncing: true, syncError: null })
        try {
          // Update preset settings
          await djApi.updatePreset(state.currentPresetId, {
            settings: {
              master_volume: state.masterVolume,
              ...djApi.frontendSettingsToApi(state.settings),
            },
          })

          // Update each track
          for (const track of state.tracks) {
            await djApi.updateTrack(state.currentPresetId, track.id, {
              name: track.name,
              type: track.type,
              hotkey: track.hotkey,
              loop: track.loop,
              text_content: track.textContent,
              volume: track.volume,
            })
          }

          set({ isSyncing: false })
        } catch (error) {
          console.error('Failed to save preset:', error)
          set({
            syncError: error instanceof Error ? error.message : 'Failed to save preset',
            isSyncing: false,
          })
          throw error
        }
      },

      createNewPreset: async (name, description) => {
        set({ isLoading: true, syncError: null })
        try {
          const state = get()
          const response = await djApi.createPreset({
            name,
            description,
            settings: {
              master_volume: state.masterVolume,
              ...djApi.frontendSettingsToApi(state.settings),
            },
          })

          // Refresh preset list
          await get().fetchPresets()

          set({ isLoading: false })
          return response.id
        } catch (error) {
          console.error('Failed to create preset:', error)
          set({
            syncError: error instanceof Error ? error.message : 'Failed to create preset',
            isLoading: false,
          })
          throw error
        }
      },

      deleteCurrentPreset: async () => {
        const state = get()
        if (!state.currentPresetId) return

        set({ isLoading: true, syncError: null })
        try {
          await djApi.deletePreset(state.currentPresetId)

          // Switch to localStorage mode
          set({
            currentPresetId: null,
            tracks: DEFAULT_TRACKS,
            trackStates: createInitialTrackStates(DEFAULT_TRACKS),
            isLoading: false,
          })

          // Refresh preset list
          await get().fetchPresets()
        } catch (error) {
          console.error('Failed to delete preset:', error)
          set({
            syncError: error instanceof Error ? error.message : 'Failed to delete preset',
            isLoading: false,
          })
          throw error
        }
      },

      importToBackend: async (presetName) => {
        const state = get()
        set({ isLoading: true, syncError: null })

        try {
          // Prepare localStorage data format
          const localStorageData: djApi.LocalStorageData = {
            masterVolume: state.masterVolume,
            settings: state.settings as unknown as Record<string, unknown>,
            tracks: state.tracks.map((track) => ({
              id: track.id,
              name: track.name,
              type: track.type,
              source: track.source,
              hotkey: track.hotkey,
              loop: track.loop,
              text_content: track.textContent,
              audioBase64: track.audioBase64,
              volume: track.volume,
            })),
          }

          const response = await djApi.importFromLocalStorage(presetName, localStorageData)

          // Refresh preset list
          await get().fetchPresets()

          set({ isLoading: false })
          return response.id
        } catch (error) {
          console.error('Failed to import to backend:', error)
          set({
            syncError: error instanceof Error ? error.message : 'Failed to import',
            isLoading: false,
          })
          throw error
        }
      },

      switchToLocalStorage: () => {
        set({
          currentPresetId: null,
          syncError: null,
        })
      },

      // === IndexedDB Storage Actions (011 Phase 4) ===
      storageQuota: null,
      storageError: null,
      isStorageReady: false,
      hasPendingMigration: false,
      pendingMigrationCount: 0,

      initializeStorage: async () => {
        try {
          await audioStorage.init()
          const quota = await audioStorage.getQuota()
          const pendingCount = audioStorage.getPendingMigrationCount()

          set({
            isStorageReady: true,
            storageQuota: quota,
            hasPendingMigration: pendingCount > 0,
            pendingMigrationCount: pendingCount,
            storageError: null,
          })

          // Restore audio URLs for tracks that have local storage
          const state = get()
          const tracksToRestore = state.tracks.filter(
            (t) => t.source === 'upload' || t.hasLocalAudio
          )

          if (tracksToRestore.length > 0) {
            const trackIds = tracksToRestore.map((t) => t.id)
            const blobs = await audioStorage.getMultiple(trackIds)

            const updatedTracks = state.tracks.map((track) => {
              const blob = blobs.get(track.id)
              if (blob) {
                return {
                  ...track,
                  url: audioStorage.createObjectURL(blob),
                }
              }
              return track
            })

            set({ tracks: updatedTracks })
          }
        } catch (error) {
          console.error('Failed to initialize storage:', error)
          set({
            storageError: error as AudioStorageError,
            isStorageReady: false,
          })
        }
      },

      refreshStorageQuota: async () => {
        try {
          const quota = await audioStorage.getQuota()
          set({ storageQuota: quota })
        } catch (error) {
          console.error('Failed to refresh storage quota:', error)
        }
      },

      saveAudioToStorage: async (trackId, blob) => {
        try {
          await audioStorage.save(trackId, blob)

          // Refresh quota after save
          const quota = await audioStorage.getQuota()
          set({ storageQuota: quota, storageError: null })
        } catch (error) {
          console.error('Failed to save audio:', error)
          set({ storageError: error as AudioStorageError })
          throw error
        }
      },

      loadAudioFromStorage: async (trackId) => {
        try {
          return await audioStorage.get(trackId)
        } catch (error) {
          console.error('Failed to load audio:', error)
          set({ storageError: error as AudioStorageError })
          return null
        }
      },

      deleteAudioFromStorage: async (trackId) => {
        try {
          await audioStorage.delete(trackId)

          // Refresh quota after delete
          const quota = await audioStorage.getQuota()
          set({ storageQuota: quota })
        } catch (error) {
          console.error('Failed to delete audio:', error)
        }
      },

      checkMigration: () => {
        const pendingCount = audioStorage.getPendingMigrationCount()
        set({
          hasPendingMigration: pendingCount > 0,
          pendingMigrationCount: pendingCount,
        })
      },

      completeMigration: (result) => {
        set({
          hasPendingMigration: false,
          pendingMigrationCount: 0,
        })

        // Reload tracks to get fresh blob URLs
        get().initializeStorage()

        console.log(
          `Migration complete: ${result.migratedCount} tracks, ${audioStorage.formatBytes(result.totalSizeBytes)}`
        )
      },

      clearStorageError: () => set({ storageError: null }),

      // === General Actions ===
      reset: () => set(initialState),
    }),
    {
      name: 'magic-dj-store',
      // Persist user preferences and track configuration (011-T009)
      partialize: (state) => ({
        settings: state.settings,
        masterVolume: state.masterVolume,
        // Persist tracks (order + custom tracks metadata, source, volume)
        tracks: state.tracks.map((track) => ({
          ...track,
          // Don't persist blob URLs, they're ephemeral
          url: track.isCustom || track.source === 'upload' ? '' : track.url,
          // Ensure source and volume are persisted (011-T009)
          source: track.source ?? 'tts',
          volume: track.volume ?? 1.0,
          // Phase 4: Don't persist audioBase64 anymore - use IndexedDB
          audioBase64: undefined,
          // Flag to indicate audio is in IndexedDB
          hasLocalAudio: track.source === 'upload' || !!track.hasLocalAudio,
        })),
        // Persist channel queues and states (DD-001)
        channelQueues: state.channelQueues,
        channelStates: state.channelStates,
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
          // Restore channel data (DD-001)
          channelQueues: persisted.channelQueues ?? DEFAULT_CHANNEL_QUEUES,
          channelStates: persisted.channelStates ?? DEFAULT_CHANNEL_STATES,
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

// === Channel Selectors (DD-001) ===

export const selectChannelQueue = (channelType: ChannelType) =>
  (state: MagicDJStoreState) => state.channelQueues[channelType]

export const selectChannelState = (channelType: ChannelType) =>
  (state: MagicDJStoreState) => state.channelStates[channelType]

export const selectChannelTracks = (channelType: ChannelType) =>
  (state: MagicDJStoreState) => {
    const queue = state.channelQueues[channelType]
    return queue.map((item) => ({
      ...item,
      track: state.tracks.find((t) => t.id === item.trackId),
    }))
  }

// Export helper for operation priority
export { OperationPriority }

export default useMagicDJStore
