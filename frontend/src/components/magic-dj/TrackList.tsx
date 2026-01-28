/**
 * Track List
 * Feature: 010-magic-dj-controller
 *
 * T016: TrackList component displaying all tracks with hotkey labels,
 * play status indicators.
 * T047: Error UI showing failed tracks with red indicator and retry button.
 * Enhanced: Dynamic track management with TTS integration.
 */

import { Play, Square, RefreshCw, AlertCircle, Plus, Pencil, Trash2 } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { useMultiTrackPlayer } from '@/hooks/useMultiTrackPlayer'
import { cn } from '@/lib/utils'
import type { Track } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface TrackListProps {
  onPlayTrack: (trackId: string) => void
  onStopTrack: (trackId: string) => void
  onAddTrack?: () => void
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
}

// =============================================================================
// Component
// =============================================================================

export function TrackList({
  onPlayTrack,
  onStopTrack,
  onAddTrack,
  onEditTrack,
  onDeleteTrack,
}: TrackListProps) {
  const { tracks, trackStates } = useMagicDJStore()
  const { retryLoadTrack } = useMultiTrackPlayer()

  // Filter main tracks (exclude filler and rescue)
  const mainTracks = tracks.filter(
    (track) => track.type !== 'filler' && track.type !== 'rescue'
  )

  return (
    <div className="flex flex-col gap-2">
      {mainTracks.map((track) => {
        const state = trackStates[track.id]
        const isPlaying = state?.isPlaying ?? false
        const isLoaded = state?.isLoaded ?? false
        const isLoading = state?.isLoading ?? false
        const error = state?.error ?? null

        return (
          <div
            key={track.id}
            className={cn(
              'flex items-center gap-3 rounded-lg border p-3 transition-all',
              error
                ? 'border-destructive/50 bg-destructive/10'
                : isPlaying
                  ? 'border-primary bg-primary/10'
                  : 'border-border bg-background hover:bg-accent/50'
            )}
          >
            {/* Hotkey Badge */}
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted font-mono text-sm font-bold">
              {track.hotkey?.toUpperCase() || '-'}
            </div>

            {/* Track Info */}
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{track.name}</div>
              <div className="text-xs text-muted-foreground flex items-center gap-1">
                {track.type === 'intro' && '開場'}
                {track.type === 'song' && '歌曲'}
                {track.type === 'effect' && '音效'}
                {track.type === 'transition' && '過場'}
                {track.isCustom && (
                  <span className="text-primary">(自訂)</span>
                )}
              </div>
            </div>

            {/* Status / Actions */}
            {error ? (
              // Error state (T047)
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span>載入失敗</span>
                </div>
                <button
                  onClick={() => retryLoadTrack(track.id)}
                  className="flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-sm hover:bg-muted/80"
                  title="重新載入"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
            ) : isLoading ? (
              // Loading state
              <div className="text-sm text-muted-foreground">載入中...</div>
            ) : isLoaded ? (
              // Play/Stop button and edit actions
              <div className="flex items-center gap-2">
                {/* Edit button - available for all tracks */}
                {onEditTrack && (
                  <button
                    onClick={() => onEditTrack(track)}
                    className="flex h-8 w-8 items-center justify-center rounded-md bg-muted hover:bg-muted/80"
                    title="編輯語音內容"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                )}

                {/* Delete button - available for all tracks */}
                {onDeleteTrack && (
                  <button
                    onClick={() => onDeleteTrack(track.id)}
                    className="flex h-8 w-8 items-center justify-center rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20"
                    title="刪除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}

                {/* Play/Stop button */}
                <button
                  onClick={() =>
                    isPlaying ? onStopTrack(track.id) : onPlayTrack(track.id)
                  }
                  className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full transition-colors',
                    isPlaying
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
              </div>
            ) : (
              // Not loaded
              <div className="text-sm text-muted-foreground">未載入</div>
            )}
          </div>
        )
      })}

      {/* Add Track Button */}
      {onAddTrack && (
        <button
          onClick={onAddTrack}
          className="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-muted-foreground/30 p-4 text-muted-foreground transition-colors hover:border-primary hover:text-primary"
        >
          <Plus className="h-5 w-5" />
          <span>新增音軌</span>
        </button>
      )}
    </div>
  )
}

export default TrackList
