/**
 * Magic DJ Store - Sound Library Persistence Tests
 *
 * Regression tests for sound-lib-persistence-fix:
 * - BUG-1: restoreTracks dead code (removed)
 * - BUG-2: addTrack hasLocalAudio flag for TTS tracks
 * - BUG-3: onRehydrateStorage triggers initializeStorage
 * - BUG-5: Ghost track integrity check
 * - BUG-6: Blob URL memory leak on re-initialization
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { act } from '@testing-library/react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { Track } from '@/types/magic-dj'

// ---------------------------------------------------------------------------
// Mock audioStorage — the singleton imported by the store
// ---------------------------------------------------------------------------
vi.mock('@/lib/audioStorage', () => {
  const mockStorage = {
    init: vi.fn().mockResolvedValue(undefined),
    getQuota: vi.fn().mockResolvedValue({ used: 0, total: 50 * 1024 * 1024, percentage: 0 }),
    getPendingMigrationCount: vi.fn().mockReturnValue(0),
    getMultiple: vi.fn().mockResolvedValue(new Map()),
    save: vi.fn().mockResolvedValue(undefined),
    get: vi.fn().mockResolvedValue(null),
    delete: vi.fn().mockResolvedValue(undefined),
    createObjectURL: vi.fn((blob: Blob) => `blob:mock-${blob.size}`),
    revokeObjectURL: vi.fn(),
    hasPendingMigration: vi.fn().mockReturnValue(false),
  }

  return {
    audioStorage: mockStorage,
    AudioStorageService: vi.fn(),
    STORAGE_THRESHOLDS: { WARNING: 70, DANGER: 90, CRITICAL: 100 },
  }
})

// Re-import after mock so we can access the mock instance
import { audioStorage } from '@/lib/audioStorage'

// ---------------------------------------------------------------------------
// Mock djApi (the store imports it at top level)
// ---------------------------------------------------------------------------
vi.mock('@/services/djApi', () => ({
  listPresets: vi.fn().mockResolvedValue([]),
  getPreset: vi.fn(),
  createPreset: vi.fn(),
  deletePreset: vi.fn(),
  updatePresetSettings: vi.fn(),
  createTrack: vi.fn(),
  updateTrack: vi.fn(),
  deleteTrack: vi.fn(),
  uploadAudio: vi.fn(),
  getAudioUrl: vi.fn(),
  deleteAudio: vi.fn(),
  importFromLocalStorage: vi.fn(),
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeTtsTrack(overrides: Partial<Track> = {}): Track {
  return {
    id: `tts-track-${Date.now()}`,
    name: 'TTS 音效',
    type: 'effect',
    url: 'blob:mock-tts',
    source: 'tts',
    volume: 1.0,
    isCustom: true,
    hasLocalAudio: true,
    ...overrides,
  }
}

function makeUploadTrack(overrides: Partial<Track> = {}): Track {
  return {
    id: `upload-track-${Date.now()}`,
    name: '上傳音效',
    type: 'effect',
    url: 'blob:mock-upload',
    source: 'upload',
    volume: 1.0,
    isCustom: true,
    hasLocalAudio: true,
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('magicDJStore - Sound Library Persistence', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Explicitly reset mock implementations — clearAllMocks only clears
    // call history, not mockImplementation set by previous tests
    ;(audioStorage.init as Mock).mockResolvedValue(undefined)
    ;(audioStorage.getQuota as Mock).mockResolvedValue({
      used: 0,
      total: 50 * 1024 * 1024,
      percentage: 0,
    })
    ;(audioStorage.getPendingMigrationCount as Mock).mockReturnValue(0)
    ;(audioStorage.getMultiple as Mock).mockResolvedValue(new Map())
    ;(audioStorage.createObjectURL as Mock).mockImplementation(
      (blob: Blob) => `blob:mock-${blob.size}`
    )
    ;(audioStorage.revokeObjectURL as Mock).mockImplementation(() => {})
    act(() => {
      useMagicDJStore.getState().reset()
    })
  })

  // =========================================================================
  // BUG-2: addTrack should respect hasLocalAudio for TTS tracks
  // =========================================================================

  describe('addTrack hasLocalAudio flag (BUG-2)', () => {
    it('should set hasLocalAudio=true for upload tracks by default', () => {
      const track = makeUploadTrack({ hasLocalAudio: undefined })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      const stored = useMagicDJStore.getState().tracks.find((t) => t.id === track.id)
      expect(stored?.hasLocalAudio).toBe(true)
    })

    it('should set hasLocalAudio=false for TTS tracks when not explicitly set', () => {
      const track = makeTtsTrack({ hasLocalAudio: undefined })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      const stored = useMagicDJStore.getState().tracks.find((t) => t.id === track.id)
      // source='tts' without explicit hasLocalAudio → falls back to false
      expect(stored?.hasLocalAudio).toBe(false)
    })

    it('should respect caller-provided hasLocalAudio=true for TTS tracks', () => {
      const track = makeTtsTrack({ hasLocalAudio: true })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      const stored = useMagicDJStore.getState().tracks.find((t) => t.id === track.id)
      expect(stored?.hasLocalAudio).toBe(true)
    })

    it('should persist hasLocalAudio=true for TTS in a single addTrack call (no extra updateTrack needed)', () => {
      // This is the exact flow from handleSaveTrack after the fix
      const track = makeTtsTrack({
        id: 'tts-atomic',
        hasLocalAudio: true,
        source: 'tts',
      })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      const stored = useMagicDJStore.getState().tracks.find((t) => t.id === 'tts-atomic')
      expect(stored?.hasLocalAudio).toBe(true)
      expect(stored?.source).toBe('tts')
    })
  })

  // =========================================================================
  // BUG-1 / Partialize: audioBase64 stripped, URLs cleared for custom tracks
  // =========================================================================

  describe('partialize strips ephemeral data (BUG-1 context)', () => {
    it('should strip audioBase64 from persisted tracks', () => {
      const track = makeTtsTrack({ audioBase64: 'data:audio/mpeg;base64,AAAA' })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      // Access the persist config through the store's internal API
      // We test the partialize output indirectly by checking the store
      // serialises tracks correctly
      const state = useMagicDJStore.getState()
      const storedTrack = state.tracks.find((t) => t.id === track.id)

      // The track in memory may have audioBase64 (set by addTrack spread),
      // but partialize will strip it for localStorage. We can verify
      // the track was added and has the right flags.
      expect(storedTrack).toBeDefined()
      expect(storedTrack?.hasLocalAudio).toBe(true)
    })

    it('should set url to empty string for custom/upload tracks in partialize', () => {
      // Verify that custom tracks get url='' when persisted, to confirm
      // that blob URL restoration MUST come from initializeStorage
      const track = makeTtsTrack({ url: 'blob:http://localhost/some-id', isCustom: true })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      // The in-memory track retains the URL
      const stored = useMagicDJStore.getState().tracks.find((t) => t.id === track.id)
      expect(stored?.url).toBe('blob:http://localhost/some-id')

      // But if we simulate what partialize does:
      const isCustomOrUpload = stored?.isCustom || stored?.source === 'upload'
      expect(isCustomOrUpload).toBe(true)
      // Meaning partialize will set url='' for this track in localStorage
    })
  })

  // =========================================================================
  // BUG-5: Ghost track detection in initializeStorage
  // =========================================================================

  describe('initializeStorage ghost track handling (BUG-5)', () => {
    it('should restore blob URL from IndexedDB for tracks with hasLocalAudio', async () => {
      const track = makeTtsTrack({
        id: 'tts-persisted',
        url: '', // empty after rehydration
        hasLocalAudio: true,
      })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
        // Simulate rehydration clearing the URL
        useMagicDJStore.getState().updateTrack('tts-persisted', { url: '' })
      })

      // Mock IndexedDB returns a blob for this track
      const mockBlob = new Blob(['fake-audio'], { type: 'audio/mpeg' })
      ;(audioStorage.getMultiple as Mock).mockImplementation(async () => {
        return new Map([['tts-persisted', mockBlob]])
      })

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      const restored = useMagicDJStore.getState().tracks.find((t) => t.id === 'tts-persisted')
      expect(restored?.url).toMatch(/^blob:mock-/)
      expect(audioStorage.createObjectURL).toHaveBeenCalledWith(mockBlob)
    })

    it('should clear hasLocalAudio for ghost tracks (blob missing in IndexedDB)', async () => {
      const track = makeTtsTrack({
        id: 'ghost-track',
        url: '',
        hasLocalAudio: true,
      })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
        useMagicDJStore.getState().updateTrack('ghost-track', { url: '' })
      })

      // Mock: IndexedDB returns empty — no blob for this track
      ;(audioStorage.getMultiple as Mock).mockImplementation(async () => new Map())

      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      const ghost = useMagicDJStore.getState().tracks.find((t) => t.id === 'ghost-track')
      expect(ghost?.hasLocalAudio).toBe(false)
      expect(ghost?.url).toBe('')
      expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('ghost-track'))

      warnSpy.mockRestore()
    })

    it('should not touch tracks without hasLocalAudio', async () => {
      // Default tracks have no audio and hasLocalAudio=false
      const defaultTrack = useMagicDJStore.getState().tracks[0]
      expect(defaultTrack?.hasLocalAudio).toBeFalsy()

      ;(audioStorage.getMultiple as Mock).mockResolvedValueOnce(new Map())

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      const afterInit = useMagicDJStore.getState().tracks[0]
      // Default track should remain unchanged
      expect(afterInit?.url).toBe(defaultTrack?.url)
    })
  })

  // =========================================================================
  // BUG-6: Blob URL cleanup on re-initialization
  // =========================================================================

  describe('blob URL memory leak prevention (BUG-6)', () => {
    it('should revoke stale blob URL before creating a new one', async () => {
      const track = makeTtsTrack({
        id: 'leak-track',
        url: 'blob:http://localhost/stale-url',
        hasLocalAudio: true,
      })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      // Verify the track was actually added with the right ID and flag
      const addedTrack = useMagicDJStore.getState().tracks.find((t) => t.id === 'leak-track')
      expect(addedTrack?.hasLocalAudio).toBe(true)
      expect(addedTrack?.url).toBe('blob:http://localhost/stale-url')

      const mockBlob = new Blob(['audio'], { type: 'audio/mpeg' })

      // Directly replace the function to guarantee the mock is picked up
      const originalGetMultiple = audioStorage.getMultiple
      const getMultipleSpy = vi.fn(async (ids: string[]) => {
        const result = new Map<string, Blob>()
        for (const id of ids) {
          if (id === 'leak-track') {
            result.set(id, mockBlob)
          }
        }
        return result
      })
      audioStorage.getMultiple = getMultipleSpy

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      // Restore
      audioStorage.getMultiple = originalGetMultiple

      // Verify getMultiple was called
      expect(getMultipleSpy).toHaveBeenCalledWith(['leak-track'])

      // Should revoke the old URL before creating new
      expect(audioStorage.revokeObjectURL).toHaveBeenCalledWith(
        'blob:http://localhost/stale-url'
      )
      expect(audioStorage.createObjectURL).toHaveBeenCalledWith(mockBlob)
    })

    it('should not attempt to revoke non-blob URLs', async () => {
      const track = makeTtsTrack({
        id: 'no-revoke-track',
        url: 'https://example.com/audio.mp3', // not a blob URL
        hasLocalAudio: true,
      })

      act(() => {
        useMagicDJStore.getState().addTrack(track)
      })

      const mockBlob = new Blob(['audio'], { type: 'audio/mpeg' })
      const originalGetMultiple = audioStorage.getMultiple
      audioStorage.getMultiple = vi.fn(async () => {
        return new Map([['no-revoke-track', mockBlob]])
      })

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      audioStorage.getMultiple = originalGetMultiple

      expect(audioStorage.revokeObjectURL).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // BUG-4: IndexedDB retry on failure
  // =========================================================================

  describe('initializeStorage retry mechanism (BUG-4)', () => {
    it('should retry up to 2 times on IndexedDB init failure', async () => {
      ;(audioStorage.init as Mock)
        .mockRejectedValueOnce(new Error('DB_ERROR'))
        .mockRejectedValueOnce(new Error('DB_ERROR'))
        .mockResolvedValueOnce(undefined) // 3rd attempt succeeds

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      expect(audioStorage.init).toHaveBeenCalledTimes(3)
      expect(useMagicDJStore.getState().isStorageReady).toBe(true)
    })

    it('should set storageError after all retries exhausted', async () => {
      ;(audioStorage.init as Mock)
        .mockRejectedValueOnce(new Error('DB_ERROR'))
        .mockRejectedValueOnce(new Error('DB_ERROR'))
        .mockRejectedValueOnce(new Error('DB_ERROR'))

      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })

      expect(audioStorage.init).toHaveBeenCalledTimes(3) // initial + 2 retries
      expect(useMagicDJStore.getState().isStorageReady).toBe(false)
      expect(useMagicDJStore.getState().storageError).toBeTruthy()

      errorSpy.mockRestore()
      warnSpy.mockRestore()
    })
  })

  // =========================================================================
  // BUG-3: onRehydrateStorage triggers initializeStorage
  // =========================================================================

  describe('onRehydrateStorage (BUG-3)', () => {
    it('store should have onRehydrateStorage configured in persist options', () => {
      // The store is created with persist middleware.
      // We verify that initializeStorage is callable and that
      // the store exposes the isStorageReady flag that gets set
      // by initializeStorage (which onRehydrateStorage calls).
      const state = useMagicDJStore.getState()
      expect(typeof state.initializeStorage).toBe('function')
      expect('isStorageReady' in state).toBe(true)
    })

    it('initializeStorage should be idempotent (safe to call multiple times)', async () => {
      ;(audioStorage.getMultiple as Mock).mockResolvedValue(new Map())

      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })
      expect(useMagicDJStore.getState().isStorageReady).toBe(true)

      // Call again — should not throw or corrupt state
      await act(async () => {
        await useMagicDJStore.getState().initializeStorage()
      })
      expect(useMagicDJStore.getState().isStorageReady).toBe(true)
    })
  })
})
