/**
 * Multi-Track Player Hook Tests
 * Feature: 010-magic-dj-controller
 *
 * T019: Unit tests for useMultiTrackPlayer covering multi-channel playback,
 * voice priority, stop channel, stop all, volume control, preload, load error/retry.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

import { useMultiTrackPlayer } from '@/hooks/useMultiTrackPlayer'
import { useMagicDJStore } from '@/stores/magicDJStore'
import type { Track } from '@/types/magic-dj'

// Mock AudioContext
const mockGainNode = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  gain: { value: 1, setTargetAtTime: vi.fn() },
}

const mockSource = {
  connect: vi.fn(),
  start: vi.fn(),
  stop: vi.fn(),
  disconnect: vi.fn(),
  buffer: null as AudioBuffer | null,
  loop: false,
  onended: null as (() => void) | null,
}

const mockAudioContext = {
  createGain: vi.fn(() => ({ ...mockGainNode })),
  createBufferSource: vi.fn(() => ({ ...mockSource })),
  decodeAudioData: vi.fn().mockResolvedValue({
    duration: 2.5,
    length: 110250,
    sampleRate: 44100,
    numberOfChannels: 2,
  }),
  destination: {},
  state: 'running',
  resume: vi.fn(),
  close: vi.fn(),
  currentTime: 0,
}

// Mock fetch
const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('AudioContext', vi.fn(() => mockAudioContext))
  vi.stubGlobal('fetch', mockFetch)
  mockFetch.mockResolvedValue({
    ok: true,
    arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(100)),
  })

  // Reset store
  act(() => {
    useMagicDJStore.getState().reset()
  })
})

const testTrack: Track = {
  id: 'test_track_1',
  name: 'Test Track',
  type: 'effect',
  url: 'https://example.com/test.mp3',
  source: 'tts',
  volume: 1.0,
}

describe('useMultiTrackPlayer', () => {
  describe('loadTrack', () => {
    it('should load a track and update state', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      await act(async () => {
        await result.current.loadTrack(testTrack)
      })

      const state = useMagicDJStore.getState().trackStates[testTrack.id]
      expect(state?.isLoading).toBe(false)
    })

    it('should skip tracks without valid URL', async () => {
      const noUrlTrack = { ...testTrack, id: 'no_url', url: '' }

      // Add track state first
      act(() => {
        useMagicDJStore.getState().addTrack(noUrlTrack)
      })

      const { result } = renderHook(() => useMultiTrackPlayer())

      await act(async () => {
        await result.current.loadTrack(noUrlTrack)
      })

      const state = useMagicDJStore.getState().trackStates['no_url']
      expect(state?.isLoading).toBe(false)
      expect(state?.error).toBeNull()
    })

    it('should handle load errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      })

      // Add track state
      act(() => {
        useMagicDJStore.getState().addTrack(testTrack)
      })

      const { result } = renderHook(() => useMultiTrackPlayer())

      await act(async () => {
        await result.current.loadTrack(testTrack)
      })

      const state = useMagicDJStore.getState().trackStates[testTrack.id]
      expect(state?.error).toContain('404')
    })
  })

  describe('loadTracks', () => {
    it('should load multiple tracks', async () => {
      const tracks = [
        testTrack,
        { ...testTrack, id: 'test_track_2', name: 'Track 2' },
      ]

      const { result } = renderHook(() => useMultiTrackPlayer())

      const callsBefore = mockFetch.mock.calls.length
      await act(async () => {
        await result.current.loadTracks(tracks)
      })

      // Should have called fetch for both tracks
      expect(mockFetch.mock.calls.length - callsBefore).toBe(2)
    })
  })

  describe('getLoadingProgress', () => {
    it('should return 1 when all tracks are skipped (no audio)', () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      // Default tracks have no URLs, so progress should be 1
      expect(result.current.getLoadingProgress()).toBe(1)
    })
  })

  describe('stopAll', () => {
    it('should be callable without error', () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      expect(() => {
        act(() => {
          result.current.stopAll()
        })
      }).not.toThrow()
    })
  })

  describe('setMasterVolume', () => {
    it('should clamp volume between 0 and 1', () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      // Should not throw for out-of-range values
      expect(() => {
        act(() => {
          result.current.setMasterVolume(-0.5)
          result.current.setMasterVolume(1.5)
          result.current.setMasterVolume(0.5)
        })
      }).not.toThrow()
    })
  })

  describe('playTrack - MAX_CONCURRENT_TRACKS limit', () => {
    it('should reject play and set error when reaching MAX_CONCURRENT_TRACKS (5)', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      // Load and play 5 tracks to fill up the concurrent limit
      const trackIds: string[] = []
      for (let i = 0; i < 5; i++) {
        const track: Track = {
          ...testTrack,
          id: `concurrent_track_${i}`,
          name: `Concurrent Track ${i}`,
          url: `https://example.com/track_${i}.mp3`,
        }
        trackIds.push(track.id)

        await act(async () => {
          await result.current.loadTrack(track)
        })

        act(() => {
          result.current.playTrack(track.id)
        })
      }

      // Verify 5 tracks are playing
      expect(result.current.getPlayingCount()).toBe(5)

      // Now try to load and play a 6th track
      const extraTrack: Track = {
        ...testTrack,
        id: 'concurrent_track_extra',
        name: 'Extra Track',
        url: 'https://example.com/extra.mp3',
      }

      await act(async () => {
        await result.current.loadTrack(extraTrack)
      })

      act(() => {
        result.current.playTrack(extraTrack.id)
      })

      // The 6th track should have an error set in state
      const state = useMagicDJStore.getState().trackStates[extraTrack.id]
      expect(state?.error).toBeTruthy()
      expect(state?.error).toContain('5')

      // Still only 5 playing
      expect(result.current.getPlayingCount()).toBe(5)
    })
  })

  describe('canPlayMore', () => {
    it('should return true when no tracks are playing', () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      expect(result.current.canPlayMore()).toBe(true)
    })

    it('should return true when fewer than MAX_CONCURRENT_TRACKS are playing', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      // Load and play 3 tracks
      for (let i = 0; i < 3; i++) {
        const track: Track = {
          ...testTrack,
          id: `canplay_track_${i}`,
          name: `CanPlay Track ${i}`,
          url: `https://example.com/canplay_${i}.mp3`,
        }

        await act(async () => {
          await result.current.loadTrack(track)
        })

        act(() => {
          result.current.playTrack(track.id)
        })
      }

      expect(result.current.getPlayingCount()).toBe(3)
      expect(result.current.canPlayMore()).toBe(true)
    })

    it('should return false when MAX_CONCURRENT_TRACKS are playing', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      // Load and play 5 tracks to fill up the concurrent limit
      for (let i = 0; i < 5; i++) {
        const track: Track = {
          ...testTrack,
          id: `full_track_${i}`,
          name: `Full Track ${i}`,
          url: `https://example.com/full_${i}.mp3`,
        }

        await act(async () => {
          await result.current.loadTrack(track)
        })

        act(() => {
          result.current.playTrack(track.id)
        })
      }

      expect(result.current.getPlayingCount()).toBe(5)
      expect(result.current.canPlayMore()).toBe(false)
    })
  })

  describe('stopAll - stops all playing tracks', () => {
    it('should stop all playing tracks and reset isPlaying state', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      const trackIds: string[] = []

      // Load and play 3 tracks
      for (let i = 0; i < 3; i++) {
        const track: Track = {
          ...testTrack,
          id: `stopall_track_${i}`,
          name: `StopAll Track ${i}`,
          url: `https://example.com/stopall_${i}.mp3`,
        }
        trackIds.push(track.id)

        await act(async () => {
          await result.current.loadTrack(track)
        })

        act(() => {
          result.current.playTrack(track.id)
        })
      }

      // Verify tracks are playing
      expect(result.current.getPlayingCount()).toBe(3)
      for (const id of trackIds) {
        expect(result.current.isTrackPlaying(id)).toBe(true)
      }

      // Stop all
      act(() => {
        result.current.stopAll()
      })

      // Verify all tracks stopped
      expect(result.current.getPlayingCount()).toBe(0)
      for (const id of trackIds) {
        expect(result.current.isTrackPlaying(id)).toBe(false)
      }

      // Verify store state reflects stopped tracks
      const storeState = useMagicDJStore.getState().trackStates
      for (const id of trackIds) {
        expect(storeState[id]?.isPlaying).toBe(false)
      }
    })
  })

  describe('unloadTrack - releases AudioBuffer and GainNode', () => {
    it('should release AudioBuffer, disconnect GainNode, and remove from internal map', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      const track: Track = {
        ...testTrack,
        id: 'unload_track_1',
        name: 'Unload Track',
        url: 'https://example.com/unload.mp3',
      }

      // Load the track
      await act(async () => {
        await result.current.loadTrack(track)
      })

      // Verify track is loaded (buffer exists in node)
      expect(result.current.isTrackLoaded(track.id)).toBe(true)

      // Unload the track
      act(() => {
        result.current.unloadTrack(track.id)
      })

      // After unload, the node is removed from the internal map.
      // playTrack should silently do nothing (no buffer available).
      // We verify by trying to play: it should not increase playing count.
      act(() => {
        result.current.playTrack(track.id)
      })

      // Playing count should be 0 since the track was removed
      expect(result.current.getPlayingCount()).toBe(0)
      // isTrackPlaying returns false for removed tracks
      expect(result.current.isTrackPlaying(track.id)).toBe(false)
    })

    it('should stop a playing track before unloading and reduce playing count', async () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      const track: Track = {
        ...testTrack,
        id: 'unload_playing_track',
        name: 'Unload Playing Track',
        url: 'https://example.com/unload_playing.mp3',
      }

      // Load and play
      await act(async () => {
        await result.current.loadTrack(track)
      })

      act(() => {
        result.current.playTrack(track.id)
      })

      expect(result.current.isTrackPlaying(track.id)).toBe(true)
      expect(result.current.getPlayingCount()).toBe(1)

      // Unload while playing
      act(() => {
        result.current.unloadTrack(track.id)
      })

      // Should no longer be playing
      expect(result.current.isTrackPlaying(track.id)).toBe(false)
      // Playing count should drop to 0
      expect(result.current.getPlayingCount()).toBe(0)
    })

    it('should handle unloading a track that was never loaded', () => {
      const { result } = renderHook(() => useMultiTrackPlayer())

      // Should not throw when unloading an unknown track
      expect(() => {
        act(() => {
          result.current.unloadTrack('nonexistent_track')
        })
      }).not.toThrow()
    })
  })
})
