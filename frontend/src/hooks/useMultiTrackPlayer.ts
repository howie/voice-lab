/**
 * Multi-Track Player Hook
 * Feature: 010-magic-dj-controller
 * Feature: 011-magic-dj-audio-features
 *
 * T005: Web Audio API multi-track playback with AudioContext, GainNode per track,
 * preloading, play/stop/volume control.
 * T046: Track loading error state with per-track error flag and retry capability.
 * 011-T028~T029: Integrate persistent volume from store, real-time GainNode adjustment.
 * 011-T032: Enforce maximum 5 concurrent tracks limit.
 */

import { useCallback, useEffect, useRef } from 'react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { ChannelType, Track } from '@/types/magic-dj'
import { MAX_CONCURRENT_TRACKS } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

interface TrackAudioNode {
  buffer: AudioBuffer | null
  source: AudioBufferSourceNode | null
  gainNode: GainNode
  isPlaying: boolean
}

export interface UseMultiTrackPlayerReturn {
  /** Load a track into memory */
  loadTrack: (track: Track) => Promise<void>
  /** Load multiple tracks */
  loadTracks: (tracks: Track[]) => Promise<void>
  /** Play a track by ID */
  playTrack: (trackId: string, loop?: boolean) => void
  /** Stop a track by ID */
  stopTrack: (trackId: string) => void
  /** Stop all playing tracks */
  stopAll: () => void
  /** Set volume for a track (0-1) */
  setTrackVolume: (trackId: string, volume: number) => void
  /** Set master volume (0-1) */
  setMasterVolume: (volume: number) => void
  /** Retry loading a failed track */
  retryLoadTrack: (trackId: string) => Promise<void>
  /** Check if a track is loaded */
  isTrackLoaded: (trackId: string) => boolean
  /** Check if a track is playing */
  isTrackPlaying: (trackId: string) => boolean
  /** Get loading progress (0-1) */
  getLoadingProgress: () => number
  /** Get count of currently playing tracks (011-T032) */
  getPlayingCount: () => number
  /** Check if can play more tracks (011-T032) */
  canPlayMore: () => boolean
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useMultiTrackPlayer(): UseMultiTrackPlayerReturn {
  const audioContextRef = useRef<AudioContext | null>(null)
  const masterGainRef = useRef<GainNode | null>(null)
  const tracksRef = useRef<Map<string, TrackAudioNode>>(new Map())
  const trackConfigRef = useRef<Map<string, Track>>(new Map())

  const { masterVolume, tracks, trackStates, channelQueues, channelStates, updateTrackState } = useMagicDJStore()

  // Find which channel a track belongs to
  const findChannelForTrack = useCallback(
    (trackId: string): ChannelType | null => {
      for (const [channelType, queue] of Object.entries(channelQueues)) {
        if (queue.some((item) => item.trackId === trackId)) {
          return channelType as ChannelType
        }
      }
      return null
    },
    [channelQueues]
  )

  // Compute effective volume: trackVolume * channelVolume (respecting mute flags)
  const getEffectiveVolume = useCallback(
    (trackId: string): number => {
      const track = tracks.find((t) => t.id === trackId)
      const trackState = trackStates[trackId]
      const trackVolume = track?.volume ?? 1
      const trackMuted = trackState?.isMuted ?? false

      if (trackMuted) return 0

      const channelType = findChannelForTrack(trackId)
      if (channelType) {
        const cs = channelStates[channelType]
        if (cs.isMuted) return 0
        return trackVolume * cs.volume
      }

      return trackVolume
    },
    [tracks, trackStates, channelStates, findChannelForTrack]
  )

  // Initialize AudioContext lazily (requires user interaction)
  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext()
      masterGainRef.current = audioContextRef.current.createGain()
      masterGainRef.current.connect(audioContextRef.current.destination)
      masterGainRef.current.gain.value = masterVolume
    }

    // Resume if suspended (browser policy)
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume()
    }

    return audioContextRef.current
  }, [masterVolume])

  // Get or create track node
  const getTrackNode = useCallback(
    (trackId: string): TrackAudioNode => {
      let node = tracksRef.current.get(trackId)
      if (!node) {
        const ctx = getAudioContext()
        const gainNode = ctx.createGain()
        gainNode.connect(masterGainRef.current!)

        node = {
          buffer: null,
          source: null,
          gainNode,
          isPlaying: false,
        }
        tracksRef.current.set(trackId, node)
      }
      return node
    },
    [getAudioContext]
  )

  // Load a single track
  const loadTrack = useCallback(
    async (track: Track): Promise<void> => {
      const trackId = track.id
      trackConfigRef.current.set(trackId, track)

      // Skip tracks without valid audio:
      // - No URL
      // - Placeholder URL (/audio/*.mp3) without audioBase64
      const isPlaceholderUrl = track.url.startsWith('/audio/')
      const hasNoAudio = !track.url || (isPlaceholderUrl && !track.audioBase64)

      if (hasNoAudio) {
        updateTrackState(trackId, {
          isLoading: false,
          isLoaded: false,
          error: null,
        })
        return
      }

      // Update state: loading
      updateTrackState(trackId, {
        isLoading: true,
        isLoaded: false,
        error: null,
      })

      try {
        const ctx = getAudioContext()
        const response = await fetch(track.url)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const arrayBuffer = await response.arrayBuffer()
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer)

        const node = getTrackNode(trackId)
        node.buffer = audioBuffer

        // Update state: loaded
        updateTrackState(trackId, {
          isLoading: false,
          isLoaded: true,
          error: null,
        })
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : 'Unknown error loading audio'

        // Update state: error (T046)
        updateTrackState(trackId, {
          isLoading: false,
          isLoaded: false,
          error: errorMessage,
        })

        console.error(`Failed to load track ${trackId}:`, error)
      }
    },
    [getAudioContext, getTrackNode, updateTrackState]
  )

  // Load multiple tracks
  const loadTracks = useCallback(
    async (tracksToLoad: Track[]): Promise<void> => {
      await Promise.all(tracksToLoad.map((track) => loadTrack(track)))
    },
    [loadTrack]
  )

  // Retry loading a failed track (T046)
  const retryLoadTrack = useCallback(
    async (trackId: string): Promise<void> => {
      const track = trackConfigRef.current.get(trackId)
      if (track) {
        await loadTrack(track)
      }
    },
    [loadTrack]
  )

  // Get count of currently playing tracks (011-T032)
  const getPlayingCount = useCallback((): number => {
    let count = 0
    for (const [, node] of tracksRef.current) {
      if (node.isPlaying) count++
    }
    return count
  }, [])

  // Check if can play more tracks (011-T032)
  const canPlayMore = useCallback((): boolean => {
    return getPlayingCount() < MAX_CONCURRENT_TRACKS
  }, [getPlayingCount])

  // Play a track (011-T028, T029, T032)
  const playTrack = useCallback(
    (trackId: string, loop = false): void => {
      const node = tracksRef.current.get(trackId)
      if (!node?.buffer) {
        console.warn(`Track ${trackId} is not loaded`)
        return
      }

      // 011-T032: Check concurrent track limit (only if not already playing this track)
      if (!node.isPlaying && getPlayingCount() >= MAX_CONCURRENT_TRACKS) {
        console.warn(`Cannot play more than ${MAX_CONCURRENT_TRACKS} tracks simultaneously`)
        updateTrackState(trackId, {
          error: `最多只能同時播放 ${MAX_CONCURRENT_TRACKS} 個音軌`,
        })
        return
      }

      // Stop if already playing
      if (node.source) {
        try {
          node.source.stop()
        } catch {
          // Already stopped
        }
        node.source.disconnect()
      }

      const ctx = getAudioContext()
      const source = ctx.createBufferSource()
      source.buffer = node.buffer
      source.loop = loop
      source.connect(node.gainNode)

      // 011-T028: Apply effective volume (track × channel)
      node.gainNode.gain.value = getEffectiveVolume(trackId)

      // Handle track end
      source.onended = () => {
        node.isPlaying = false
        node.source = null
        updateTrackState(trackId, { isPlaying: false, currentTime: 0 })
      }

      source.start(0)
      node.source = source
      node.isPlaying = true

      updateTrackState(trackId, { isPlaying: true, currentTime: 0, error: null })
    },
    [getAudioContext, updateTrackState, getPlayingCount, getEffectiveVolume]
  )

  // Stop a track
  const stopTrack = useCallback(
    (trackId: string): void => {
      const node = tracksRef.current.get(trackId)
      if (!node?.source) return

      try {
        node.source.stop()
      } catch {
        // Already stopped
      }

      node.source.disconnect()
      node.source = null
      node.isPlaying = false

      updateTrackState(trackId, { isPlaying: false, currentTime: 0 })
    },
    [updateTrackState]
  )

  // Stop all tracks
  const stopAll = useCallback((): void => {
    for (const [trackId] of tracksRef.current) {
      stopTrack(trackId)
    }
  }, [stopTrack])

  // Set track volume (011-T029: real-time GainNode adjustment)
  const setTrackVolume = useCallback(
    (trackId: string, volume: number): void => {
      const node = tracksRef.current.get(trackId)
      if (!node) return

      const clampedVolume = Math.max(0, Math.min(1, volume))

      // 011-T029: Smooth volume transition for better UX
      const currentTime = audioContextRef.current?.currentTime ?? 0
      node.gainNode.gain.setTargetAtTime(clampedVolume, currentTime, 0.01)

      updateTrackState(trackId, { volume: clampedVolume })
    },
    [updateTrackState]
  )

  // Set master volume
  const setMasterVolume = useCallback((volume: number): void => {
    if (masterGainRef.current) {
      const clampedVolume = Math.max(0, Math.min(1, volume))
      masterGainRef.current.gain.value = clampedVolume
    }
  }, [])

  // Check if track is loaded
  const isTrackLoaded = useCallback((trackId: string): boolean => {
    const node = tracksRef.current.get(trackId)
    return node?.buffer !== null
  }, [])

  // Check if track is playing
  const isTrackPlaying = useCallback((trackId: string): boolean => {
    const node = tracksRef.current.get(trackId)
    return node?.isPlaying ?? false
  }, [])

  // Get loading progress (excluding skipped tracks)
  const getLoadingProgress = useCallback((): number => {
    const total = trackConfigRef.current.size
    if (total === 0) return 1

    let loaded = 0
    let skipped = 0
    for (const [trackId, track] of trackConfigRef.current) {
      // Check if track should be skipped (no valid audio)
      const isPlaceholderUrl = track.url.startsWith('/audio/')
      const hasNoAudio = !track.url || (isPlaceholderUrl && !track.audioBase64)

      if (hasNoAudio) {
        skipped++
      } else if (tracksRef.current.get(trackId)?.buffer) {
        loaded++
      }
    }

    // If all tracks are skipped, consider it complete
    const tracksToLoad = total - skipped
    if (tracksToLoad === 0) return 1

    return loaded / tracksToLoad
  }, [])

  // Sync master volume from store
  useEffect(() => {
    if (masterGainRef.current) {
      masterGainRef.current.gain.value = masterVolume
    }
  }, [masterVolume])

  // Sync channel volume/mute changes to playing tracks in real-time
  useEffect(() => {
    const currentTime = audioContextRef.current?.currentTime ?? 0
    for (const [trackId, node] of tracksRef.current) {
      if (!node.isPlaying) continue
      const vol = getEffectiveVolume(trackId)
      node.gainNode.gain.setTargetAtTime(vol, currentTime, 0.02)
    }
  }, [channelStates, trackStates, getEffectiveVolume])

  // Cleanup on unmount
  useEffect(() => {
    const currentTracks = tracksRef.current
    const currentAudioContext = audioContextRef.current

    return () => {
      // Stop all tracks
      for (const [, node] of currentTracks) {
        if (node.source) {
          try {
            node.source.stop()
          } catch {
            // Already stopped
          }
        }
      }

      // Close audio context
      if (currentAudioContext) {
        currentAudioContext.close()
      }
    }
  }, [])

  return {
    loadTrack,
    loadTracks,
    playTrack,
    stopTrack,
    stopAll,
    setTrackVolume,
    setMasterVolume,
    retryLoadTrack,
    isTrackLoaded,
    isTrackPlaying,
    getLoadingProgress,
    // 011-T032
    getPlayingCount,
    canPlayMore,
  }
}

export default useMultiTrackPlayer
