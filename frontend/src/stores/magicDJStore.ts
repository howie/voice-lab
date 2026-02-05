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
  CueItem,
  CueList,
  DJSettings,
  MagicDJState,
  OperationLog,
  OperationMode,
  PendingOperation,
  PromptTemplate,
  SessionRecord,
  StoryPrompt,
  Track,
  TrackPlaybackState,
  TrackSource,
} from '@/types/magic-dj'
import {
  DEFAULT_CHANNEL_QUEUES,
  DEFAULT_CHANNEL_STATES,
  DEFAULT_CUE_LIST,
  DEFAULT_DJ_SETTINGS,
  DEFAULT_PROMPT_TEMPLATES,
  DEFAULT_STORY_PROMPTS,
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

  // === Cue List Actions (US3: FR-028~FR-037) ===
  addToCueList: (trackId: string) => void
  removeFromCueList: (cueItemId: string) => void
  reorderCueList: (activeId: string, overId: string) => void
  playNextCue: () => CueItem | null
  resetCuePosition: () => void
  clearCueList: () => void
  setCueItemStatus: (cueItemId: string, status: CueItem['status']) => void
  advanceCuePosition: () => void
  validateCueList: () => void
  setCueList: (cueList: CueList) => void

  // === Backend Sync Actions (011 Phase 3) ===
  setAuthenticated: (authenticated: boolean) => void
  fetchPresets: () => Promise<void>
  loadPreset: (presetId: string) => Promise<void>
  saveCurrentPreset: () => Promise<void>
  createNewPreset: (name: string, description?: string) => Promise<string>
  deleteCurrentPreset: () => Promise<void>
  importToBackend: (presetName: string) => Promise<string>
  switchToLocalStorage: () => void

  // === Prompt Template Actions (015) ===
  setLastSentPrompt: (id: string) => void
  clearLastSentPrompt: () => void
  addPromptTemplate: (template: Omit<PromptTemplate, 'id' | 'createdAt'>) => void
  updatePromptTemplate: (id: string, updates: Partial<PromptTemplate>) => void
  removePromptTemplate: (id: string) => void
  reorderPromptTemplates: (ids: string[]) => void
  addStoryPrompt: (prompt: Omit<StoryPrompt, 'id'>) => void
  updateStoryPrompt: (id: string, updates: Partial<StoryPrompt>) => void
  removeStoryPrompt: (id: string) => void

  // === IndexedDB Storage Actions (011 Phase 4) ===
  storageQuota: StorageQuota | null
  storageError: AudioStorageError | null
  isStorageReady: boolean
  hasPendingMigration: boolean
  pendingMigrationCount: number
  initializeStorage: (retryCount?: number) => Promise<void>
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
  // Cue List (US3)
  cueList: DEFAULT_CUE_LIST,
  // Prompt Templates (015)
  promptTemplates: DEFAULT_PROMPT_TEMPLATES,
  storyPrompts: DEFAULT_STORY_PROMPTS,
  lastSentPromptId: null,
  lastSentPromptTime: null,
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

// NOTE: base64ToBlobUrl and restoreTracks removed — they were dead code paths.
// Since Phase 4, partialize() removes audioBase64 from persisted state,
// so restoreTracks() could never find audioBase64 to restore.
// All audio blob restoration is now handled by initializeStorage() via IndexedDB.

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
          // Respect caller-provided hasLocalAudio; fall back to upload detection
          hasLocalAudio: track.hasLocalAudio ?? track.source === 'upload',
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

      // === Cue List Actions (US3: FR-028~FR-037) ===

      addToCueList: (trackId) =>
        set((prev) => {
          const newItem: CueItem = {
            id: crypto.randomUUID(),
            trackId,
            order: prev.cueList.items.length + 1,
            status: 'pending',
          }
          return {
            cueList: {
              ...prev.cueList,
              items: [...prev.cueList.items, newItem],
              updatedAt: Date.now(),
            },
          }
        }),

      removeFromCueList: (cueItemId) =>
        set((prev) => {
          const removedIndex = prev.cueList.items.findIndex((item) => item.id === cueItemId)
          const newItems = prev.cueList.items
            .filter((item) => item.id !== cueItemId)
            .map((item, i) => ({ ...item, order: i + 1 }))

          // Adjust currentPosition if needed
          let newPosition = prev.cueList.currentPosition
          if (removedIndex !== -1 && removedIndex <= newPosition) {
            newPosition = Math.max(-1, newPosition - 1)
          }

          return {
            cueList: {
              ...prev.cueList,
              items: newItems,
              currentPosition: newPosition,
              updatedAt: Date.now(),
            },
          }
        }),

      reorderCueList: (activeId, overId) =>
        set((prev) => {
          const items = [...prev.cueList.items]
          const oldIndex = items.findIndex((item) => item.id === activeId)
          const newIndex = items.findIndex((item) => item.id === overId)

          if (oldIndex === -1 || newIndex === -1) return prev

          const [movedItem] = items.splice(oldIndex, 1)
          items.splice(newIndex, 0, movedItem)

          // Re-number orders
          const reordered = items.map((item, i) => ({ ...item, order: i + 1 }))

          return {
            cueList: {
              ...prev.cueList,
              items: reordered,
              updatedAt: Date.now(),
            },
          }
        }),

      playNextCue: () => {
        const prev = get()
        const { items, currentPosition } = prev.cueList
        const nextIndex = currentPosition + 1

        if (nextIndex >= items.length) {
          return null // End of list
        }

        const nextItem = items[nextIndex]
        if (!nextItem || nextItem.status === 'invalid') {
          // Skip invalid, try next
          set((state) => ({
            cueList: {
              ...state.cueList,
              currentPosition: nextIndex,
            },
          }))
          return get().playNextCue()
        }

        // Update statuses
        set((state) => ({
          cueList: {
            ...state.cueList,
            currentPosition: nextIndex,
            items: state.cueList.items.map((item, i) => {
              if (i === nextIndex) return { ...item, status: 'playing' as const }
              if (i < nextIndex && item.status === 'playing') return { ...item, status: 'played' as const }
              return item
            }),
          },
        }))

        return nextItem
      },

      resetCuePosition: () =>
        set((prev) => ({
          cueList: {
            ...prev.cueList,
            currentPosition: -1,
            items: prev.cueList.items.map((item) =>
              item.status !== 'invalid' ? { ...item, status: 'pending' as const } : item
            ),
            updatedAt: Date.now(),
          },
        })),

      clearCueList: () =>
        set((prev) => ({
          cueList: {
            ...prev.cueList,
            items: [],
            currentPosition: -1,
            updatedAt: Date.now(),
          },
        })),

      setCueItemStatus: (cueItemId, status) =>
        set((prev) => ({
          cueList: {
            ...prev.cueList,
            items: prev.cueList.items.map((item) =>
              item.id === cueItemId ? { ...item, status } : item
            ),
          },
        })),

      advanceCuePosition: () =>
        set((prev) => {
          const { items, currentPosition } = prev.cueList

          // Mark current item as played
          const updatedItems = items.map((item, i) =>
            i === currentPosition && item.status === 'playing'
              ? { ...item, status: 'played' as const }
              : item
          )

          // Check if we're at the end
          if (currentPosition >= items.length - 1) {
            // End of list - reset position to start (EC-007)
            return {
              cueList: {
                ...prev.cueList,
                items: updatedItems.map((item) =>
                  item.status !== 'invalid' ? { ...item, status: 'pending' as const } : item
                ),
                currentPosition: -1,
                updatedAt: Date.now(),
              },
            }
          }

          return {
            cueList: {
              ...prev.cueList,
              items: updatedItems,
              updatedAt: Date.now(),
            },
          }
        }),

      validateCueList: () =>
        set((prev) => {
          const trackIds = new Set(prev.tracks.map((t) => t.id))
          return {
            cueList: {
              ...prev.cueList,
              items: prev.cueList.items.map((item) =>
                !trackIds.has(item.trackId) && item.status !== 'invalid'
                  ? { ...item, status: 'invalid' as const }
                  : item
              ),
            },
          }
        }),

      setCueList: (cueList) => set({ cueList }),

      // === Prompt Template Actions (015) ===

      setLastSentPrompt: (id) =>
        set({ lastSentPromptId: id, lastSentPromptTime: Date.now() }),

      clearLastSentPrompt: () =>
        set({ lastSentPromptId: null, lastSentPromptTime: null }),

      addPromptTemplate: (template) =>
        set((prev) => ({
          promptTemplates: [
            ...prev.promptTemplates,
            {
              ...template,
              id: `pt_custom_${crypto.randomUUID().slice(0, 8)}`,
              createdAt: new Date().toISOString(),
            },
          ],
        })),

      updatePromptTemplate: (id, updates) =>
        set((prev) => ({
          promptTemplates: prev.promptTemplates.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          ),
        })),

      removePromptTemplate: (id) =>
        set((prev) => ({
          promptTemplates: prev.promptTemplates.filter(
            (t) => t.id !== id || t.isDefault
          ),
        })),

      reorderPromptTemplates: (ids) =>
        set((prev) => {
          const ordered = ids
            .map((id) => prev.promptTemplates.find((t) => t.id === id))
            .filter(Boolean) as PromptTemplate[]
          // Append any templates not in the ids list
          const remaining = prev.promptTemplates.filter(
            (t) => !ids.includes(t.id)
          )
          return {
            promptTemplates: [...ordered, ...remaining].map((t, i) => ({
              ...t,
              order: i + 1,
            })),
          }
        }),

      addStoryPrompt: (prompt) =>
        set((prev) => ({
          storyPrompts: [
            ...prev.storyPrompts,
            {
              ...prompt,
              id: `sp_custom_${crypto.randomUUID().slice(0, 8)}`,
            },
          ],
        })),

      updateStoryPrompt: (id, updates) =>
        set((prev) => ({
          storyPrompts: prev.storyPrompts.map((s) =>
            s.id === id ? { ...s, ...updates } : s
          ),
        })),

      removeStoryPrompt: (id) =>
        set((prev) => ({
          storyPrompts: prev.storyPrompts.filter(
            (s) => s.id !== id || s.isDefault
          ),
        })),

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

        const presetId = state.currentPresetId
        set({ isSyncing: true, syncError: null })
        try {
          // Update preset settings
          await djApi.updatePreset(presetId, {
            settings: {
              master_volume: state.masterVolume,
              ...djApi.frontendSettingsToApi(state.settings),
            },
          })

          // Update all tracks in parallel
          await Promise.all(
            state.tracks.map((track) =>
              djApi.updateTrack(presetId, track.id, {
                name: track.name,
                type: track.type,
                hotkey: track.hotkey,
                loop: track.loop,
                text_content: track.textContent,
                volume: track.volume,
              })
            )
          )

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

          // Refresh preset list (non-blocking)
          void get().fetchPresets()

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

          // Refresh preset list (non-blocking)
          void get().fetchPresets()
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

          // Refresh preset list (non-blocking)
          void get().fetchPresets()

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

      initializeStorage: async (retryCount = 0) => {
        const MAX_RETRIES = 2

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
                // Revoke stale blob URL before creating a new one (prevent memory leak)
                if (track.url?.startsWith('blob:')) {
                  audioStorage.revokeObjectURL(track.url)
                }
                return {
                  ...track,
                  url: audioStorage.createObjectURL(blob),
                }
              }

              // Ghost track: metadata says audio exists but blob is missing
              if (track.hasLocalAudio) {
                console.warn(
                  `[MagicDJ] Audio blob missing for track "${track.name}" (${track.id}). Clearing hasLocalAudio flag.`
                )
                return { ...track, hasLocalAudio: false, url: '' }
              }

              return track
            })

            set({ tracks: updatedTracks })
          }
        } catch (error) {
          // Retry with exponential backoff
          if (retryCount < MAX_RETRIES) {
            const delay = 1000 * (retryCount + 1)
            console.warn(
              `[MagicDJ] Storage init failed (attempt ${retryCount + 1}/${MAX_RETRIES + 1}), retrying in ${delay}ms...`
            )
            await new Promise((resolve) => setTimeout(resolve, delay))
            return get().initializeStorage(retryCount + 1)
          }

          console.error('Failed to initialize storage after retries:', error)
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
        // Persist cue list (FR-037)
        cueList: state.cueList,
        // Persist prompt templates (015)
        promptTemplates: state.promptTemplates,
        storyPrompts: state.storyPrompts,
      }),
      // After rehydration completes, trigger IndexedDB audio restoration.
      // This eliminates the race condition where components render with empty
      // URLs before MagicDJPage's useEffect calls initializeStorage().
      onRehydrateStorage: () => {
        return (state, error) => {
          if (error) {
            console.error('Magic DJ store rehydration failed:', error)
            return
          }
          // Kick off IndexedDB restoration immediately after rehydration
          state?.initializeStorage()
        }
      },
      // Merge persisted state with defaults (011-T006, T009)
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<MagicDJStoreState>

        // Restore track metadata from persisted state with migration (011-T006)
        // Audio blob URLs are NOT restored here — they are ephemeral.
        // initializeStorage() handles blob restoration from IndexedDB.
        let tracks = currentState.tracks
        if (persisted.tracks && persisted.tracks.length > 0) {
          tracks = persisted.tracks.map(migrateTrackData)
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
          // Restore cue list (FR-037)
          cueList: persisted.cueList ?? DEFAULT_CUE_LIST,
          // Restore prompt templates (015) — fallback to defaults for pre-015 stores
          promptTemplates: persisted.promptTemplates?.length
            ? persisted.promptTemplates
            : DEFAULT_PROMPT_TEMPLATES,
          storyPrompts: persisted.storyPrompts?.length
            ? persisted.storyPrompts
            : DEFAULT_STORY_PROMPTS,
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

// === Cue List Selectors (US3) ===

export const selectCueList = (state: MagicDJStoreState) => state.cueList

export const selectCueItems = (state: MagicDJStoreState) => state.cueList.items

export const selectCurrentCuePosition = (state: MagicDJStoreState) =>
  state.cueList.currentPosition

export const selectCueListRemainingCount = (state: MagicDJStoreState) => {
  const { items, currentPosition } = state.cueList
  const validItems = items.filter((item) => item.status !== 'invalid')
  if (currentPosition === -1) return validItems.length
  return Math.max(0, validItems.length - currentPosition - 1)
}

// Export helper for operation priority
export { OperationPriority }

export default useMagicDJStore
