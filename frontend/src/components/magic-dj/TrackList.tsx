/**
 * Track List
 * Feature: 010-magic-dj-controller
 *
 * T016: TrackList component displaying all tracks with hotkey labels,
 * play status indicators.
 * T047: Error UI showing failed tracks with red indicator and retry button.
 * Enhanced: Dynamic track management with TTS integration.
 * Enhanced: Drag and drop reordering support.
 */

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import {
  Play,
  Square,
  RefreshCw,
  AlertCircle,
  Plus,
  Pencil,
  Trash2,
  GripVertical,
} from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { useMultiTrackPlayer } from '@/hooks/useMultiTrackPlayer'
import { cn } from '@/lib/utils'
import type { Track, TrackPlaybackState } from '@/types/magic-dj'

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

interface SortableTrackItemProps {
  track: Track
  index: number
  state: TrackPlaybackState | undefined
  onPlayTrack: (trackId: string) => void
  onStopTrack: (trackId: string) => void
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
  onRetryLoad: (trackId: string) => void
}

// =============================================================================
// Sortable Track Item Component
// =============================================================================

function SortableTrackItem({
  track,
  index,
  state,
  onPlayTrack,
  onStopTrack,
  onEditTrack,
  onDeleteTrack,
  onRetryLoad,
}: SortableTrackItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: track.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const isPlaying = state?.isPlaying ?? false
  const isLoaded = state?.isLoaded ?? false
  const isLoading = state?.isLoading ?? false
  const error = state?.error ?? null

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'flex items-center gap-3 rounded-lg border p-3 transition-all',
        isDragging && 'opacity-50 shadow-lg z-50',
        error
          ? 'border-destructive/50 bg-destructive/10'
          : isPlaying
            ? 'border-primary bg-primary/10'
            : 'border-border bg-background hover:bg-accent/50'
      )}
    >
      {/* Drag Handle */}
      <div
        className="flex h-8 w-6 shrink-0 cursor-grab items-center justify-center text-muted-foreground hover:text-foreground active:cursor-grabbing touch-none"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-4 w-4" />
      </div>

      {/* Hotkey Badge - 根據位置顯示 1-5 */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted font-mono text-sm font-bold">
        {index < 5 ? index + 1 : '-'}
      </div>

      {/* Track Info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{track.name}</div>
        <div className="text-xs text-muted-foreground flex items-center gap-1 flex-wrap">
          <span className="shrink-0">
            {track.type === 'intro' && '開場'}
            {track.type === 'song' && '歌曲'}
            {track.type === 'effect' && '音效'}
            {track.type === 'transition' && '過場'}
          </span>
          {track.isCustom && <span className="text-primary shrink-0">(自訂)</span>}
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
            onClick={() => onRetryLoad(track.id)}
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
        // Not loaded - show generate button if no valid audio
        <div className="flex items-center gap-2">
          {onEditTrack ? (
            <button
              onClick={() => onEditTrack(track)}
              className="flex items-center gap-1 rounded-md bg-primary/10 px-3 py-1.5 text-sm text-primary hover:bg-primary/20"
            >
              <Pencil className="h-3 w-3" />
              <span>產生音訊</span>
            </button>
          ) : (
            <span className="text-sm text-muted-foreground">未載入</span>
          )}
        </div>
      )}
    </div>
  )
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
  const { tracks, trackStates, reorderTracks } = useMagicDJStore()
  const { retryLoadTrack } = useMultiTrackPlayer()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, // 移動 5px 後開始拖曳
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // Filter main tracks (exclude filler and rescue)
  const mainTracks = tracks.filter(
    (track) => track.type !== 'filler' && track.type !== 'rescue'
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      reorderTracks(active.id as string, over.id as string)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={mainTracks.map((t) => t.id)}
          strategy={verticalListSortingStrategy}
        >
          {mainTracks.map((track, index) => (
            <SortableTrackItem
              key={track.id}
              track={track}
              index={index}
              state={trackStates[track.id]}
              onPlayTrack={onPlayTrack}
              onStopTrack={onStopTrack}
              onEditTrack={onEditTrack}
              onDeleteTrack={onDeleteTrack}
              onRetryLoad={retryLoadTrack}
            />
          ))}
        </SortableContext>
      </DndContext>

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
