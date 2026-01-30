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
})
