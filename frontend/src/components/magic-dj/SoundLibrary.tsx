/**
 * Sound Library Component
 * Feature: 010-magic-dj-controller (DD-001)
 *
 * Right-side panel showing all available sounds categorized by channel type.
 * Items are draggable to the channel strips on the left.
 */

import { useDraggable } from '@dnd-kit/core'
import {
  Plus,
  Pencil,
  Trash2,
  Mic,
  FileAudio,
  Music,
  Volume2,
  AlertCircle,
  ShieldAlert,
} from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'
import type { ChannelConfig, Track } from '@/types/magic-dj'
import { CHANNEL_CONFIGS, TRACK_TYPE_TO_CHANNEL } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface SoundLibraryProps {
  onAddTrack?: () => void
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
}

interface DraggableTrackItemProps {
  track: Track
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
}

// =============================================================================
// Channel Icon Helper
// =============================================================================

function ChannelIcon({ type }: { type: string }) {
  switch (type) {
    case 'rescue':
      return <ShieldAlert className="h-4 w-4" />
    case 'voice':
      return <Mic className="h-4 w-4" />
    case 'sfx':
      return <AlertCircle className="h-4 w-4" />
    case 'music':
      return <Music className="h-4 w-4" />
    default:
      return <Volume2 className="h-4 w-4" />
  }
}

// =============================================================================
// Draggable Track Item
// =============================================================================

function DraggableTrackItem({
  track,
  onEditTrack,
  onDeleteTrack,
}: DraggableTrackItemProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `library-${track.id}`,
    data: { track, source: 'library' },
  })

  const trackState = useMagicDJStore((s) => s.trackStates[track.id])
  const isLoaded = trackState?.isLoaded ?? false

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      className={cn(
        'group flex cursor-grab items-center gap-2 rounded-md border px-2.5 py-1.5 text-sm transition-all active:cursor-grabbing touch-none',
        isDragging
          ? 'z-50 opacity-50 shadow-lg border-primary'
          : 'border-border bg-background hover:bg-accent/50 hover:border-accent',
      )}
    >
      {/* Source icon */}
      {track.source === 'upload' ? (
        <FileAudio className="h-3.5 w-3.5 shrink-0 text-blue-500" />
      ) : (
        <Mic className="h-3.5 w-3.5 shrink-0 text-green-500" />
      )}

      {/* Track name */}
      <span className="flex-1 truncate">{track.name}</span>

      {/* Load status dot */}
      <span
        className={cn(
          'h-1.5 w-1.5 shrink-0 rounded-full',
          isLoaded ? 'bg-green-500' : 'bg-muted-foreground/30',
        )}
        title={isLoaded ? '已載入' : '未載入'}
      />

      {/* Actions (hover) */}
      <div className="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100">
        {onEditTrack && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEditTrack(track)
            }}
            className="rounded p-0.5 text-muted-foreground hover:text-foreground"
            title="編輯"
          >
            <Pencil className="h-3 w-3" />
          </button>
        )}
        {onDeleteTrack && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDeleteTrack(track.id)
            }}
            className="rounded p-0.5 text-muted-foreground hover:text-destructive"
            title="刪除"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Category Section
// =============================================================================

function CategorySection({
  config,
  tracks,
  onEditTrack,
  onDeleteTrack,
}: {
  config: ChannelConfig
  tracks: Track[]
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
}) {
  if (tracks.length === 0) return null

  return (
    <div>
      <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">
        <ChannelIcon type={config.type} />
        {config.label}
        <span className="text-muted-foreground/50">({tracks.length})</span>
      </div>
      <div className="flex flex-col gap-1">
        {tracks.map((track) => (
          <DraggableTrackItem
            key={track.id}
            track={track}
            onEditTrack={onEditTrack}
            onDeleteTrack={onDeleteTrack}
          />
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Component
// =============================================================================

export function SoundLibrary({
  onAddTrack,
  onEditTrack,
  onDeleteTrack,
}: SoundLibraryProps) {
  const { tracks } = useMagicDJStore()

  // Group tracks by channel type
  const groupedTracks = CHANNEL_CONFIGS.reduce(
    (acc, config) => {
      acc[config.type] = tracks.filter(
        (track) => TRACK_TYPE_TO_CHANNEL[track.type] === config.type,
      )
      return acc
    },
    {} as Record<string, Track[]>,
  )

  return (
    <div className="flex h-full w-56 flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-3">
        <h3 className="text-sm font-semibold">Sound Library</h3>
        <span className="text-xs text-muted-foreground">
          {tracks.length} 項
        </span>
      </div>

      {/* Scrollable Content */}
      <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-3">
        {CHANNEL_CONFIGS.map((config) => (
          <CategorySection
            key={config.type}
            config={config}
            tracks={groupedTracks[config.type] ?? []}
            onEditTrack={onEditTrack}
            onDeleteTrack={onDeleteTrack}
          />
        ))}
      </div>

      {/* Footer: Add Track */}
      {onAddTrack && (
        <div className="border-t p-2">
          <button
            onClick={onAddTrack}
            className="flex w-full items-center justify-center gap-1.5 rounded-md border-2 border-dashed border-muted-foreground/30 py-2 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-primary"
          >
            <Plus className="h-4 w-4" />
            新增音軌
          </button>
        </div>
      )}
    </div>
  )
}

export default SoundLibrary
