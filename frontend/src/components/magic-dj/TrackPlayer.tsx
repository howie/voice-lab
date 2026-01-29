/**
 * Track Player
 * Feature: 010-magic-dj-controller
 * Feature: 011-magic-dj-audio-features
 *
 * T017: TrackPlayer component with play/stop button, volume slider,
 * progress indicator per track.
 * 011-T027: Integrate VolumeSlider component with persistent volume.
 */

import { Play, Square } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'
import { VolumeSlider } from './VolumeSlider'

// =============================================================================
// Types
// =============================================================================

export interface TrackPlayerProps {
  trackId: string
  onPlay: () => void
  onStop: () => void
  onVolumeChange: (volume: number) => void
  onMuteToggle?: () => void
}

// =============================================================================
// Component
// =============================================================================

export function TrackPlayer({
  trackId,
  onPlay,
  onStop,
  onVolumeChange,
  onMuteToggle,
}: TrackPlayerProps) {
  const { tracks, trackStates } = useMagicDJStore()

  const track = tracks.find((t) => t.id === trackId)
  const state = trackStates[trackId]

  if (!track || !state) return null

  const { isPlaying, isLoaded, volume, currentTime, isMuted } = state
  const duration = track.duration ?? 0

  // Calculate progress percentage
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="flex items-center gap-4 rounded-lg border bg-card p-4">
      {/* Play/Stop Button */}
      <button
        onClick={isPlaying ? onStop : onPlay}
        disabled={!isLoaded}
        className={cn(
          'flex h-12 w-12 items-center justify-center rounded-full transition-colors',
          !isLoaded
            ? 'cursor-not-allowed bg-muted text-muted-foreground'
            : isPlaying
              ? 'bg-primary text-primary-foreground hover:bg-primary/80'
              : 'bg-muted hover:bg-muted/80'
        )}
      >
        {isPlaying ? (
          <Square className="h-5 w-5" />
        ) : (
          <Play className="h-5 w-5 ml-0.5" />
        )}
      </button>

      {/* Track Info */}
      <div className="flex-1">
        <div className="mb-1 font-medium">{track.name}</div>

        {/* Progress Bar */}
        <div className="h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-primary transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Volume Control (011-T027) */}
      <VolumeSlider
        value={volume}
        onChange={onVolumeChange}
        onMuteToggle={onMuteToggle}
        isMuted={isMuted}
        size="md"
        showPercentage={false}
      />

      {/* Hotkey Badge */}
      {track.hotkey && (
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted font-mono text-sm font-bold">
          {track.hotkey.toUpperCase()}
        </div>
      )}
    </div>
  )
}

export default TrackPlayer
