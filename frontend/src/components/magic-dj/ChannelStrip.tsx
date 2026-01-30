/**
 * Channel Strip Component
 * Feature: 010-magic-dj-controller (DD-001)
 *
 * A single vertical channel in the DJ Mixer layout.
 * Shows a queue of tracks with reorder support, volume control,
 * and current playback position indicator.
 */

import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import {
  GripVertical,
  Play,
  Square,
  Trash2,
  ChevronDown,
} from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'
import { VolumeSlider } from './VolumeSlider'
import type { ChannelConfig, ChannelQueueItem, Track } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface ChannelStripProps {
  config: ChannelConfig
  onPlayTrack: (trackId: string) => void
  onStopTrack: (trackId: string) => void
}

interface SortableQueueItemProps {
  item: ChannelQueueItem
  track: Track | undefined
  index: number
  isCurrent: boolean
  isPlaying: boolean
  channelType: string
  onPlay: () => void
  onStop: () => void
  onRemove: () => void
}

// =============================================================================
// Sortable Queue Item
// =============================================================================

function SortableQueueItem({
  item,
  track,
  index,
  isCurrent,
  isPlaying,
  onPlay,
  onStop,
  onRemove,
}: SortableQueueItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  if (!track) {
    return (
      <div
        ref={setNodeRef}
        style={style}
        className="flex items-center gap-2 rounded border border-destructive/30 bg-destructive/5 px-2 py-1.5 text-xs text-destructive"
      >
        <span className="flex-1 truncate">來源已刪除</span>
        <button
          onClick={onRemove}
          className="shrink-0 rounded p-0.5 hover:bg-destructive/10"
          title="移除"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    )
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'group flex items-center gap-1.5 rounded border px-2 py-1.5 text-sm transition-all',
        isDragging && 'z-50 opacity-50 shadow-lg',
        isCurrent && isPlaying
          ? 'border-primary bg-primary/10 font-medium'
          : isCurrent
            ? 'border-primary/50 bg-primary/5'
            : 'border-border bg-background hover:bg-accent/50',
      )}
    >
      {/* Drag handle */}
      <div
        className="flex shrink-0 cursor-grab items-center text-muted-foreground hover:text-foreground active:cursor-grabbing touch-none"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-3.5 w-3.5" />
      </div>

      {/* Index */}
      <span className="w-4 shrink-0 text-center text-xs text-muted-foreground">
        {index + 1}
      </span>

      {/* Name */}
      <span className="flex-1 truncate">{track.name}</span>

      {/* Actions (visible on hover / when current) */}
      <div className={cn(
        'flex shrink-0 items-center gap-1',
        !isCurrent && 'opacity-0 group-hover:opacity-100',
      )}>
        <button
          onClick={onRemove}
          className="rounded p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          title="移除"
        >
          <Trash2 className="h-3 w-3" />
        </button>
        <button
          onClick={isPlaying ? onStop : onPlay}
          className={cn(
            'flex h-6 w-6 items-center justify-center rounded-full transition-colors',
            isPlaying
              ? 'bg-primary text-primary-foreground hover:bg-primary/80'
              : 'bg-muted hover:bg-muted/80',
          )}
        >
          {isPlaying ? (
            <Square className="h-3 w-3" />
          ) : (
            <Play className="h-3 w-3 ml-0.5" />
          )}
        </button>
      </div>
    </div>
  )
}

// =============================================================================
// Component
// =============================================================================

export function ChannelStrip({
  config,
  onPlayTrack,
  onStopTrack,
}: ChannelStripProps) {
  const {
    tracks,
    channelQueues,
    channelStates,
    trackStates,
    removeFromChannel,
    setChannelVolume,
    toggleChannelMute,
    advanceChannel,
  } = useMagicDJStore()

  const queue = channelQueues[config.type]
  const channelState = channelStates[config.type]

  // Droppable zone for this channel
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `channel-${config.type}`,
    data: { channelType: config.type },
  })

  // Resolve queue items to tracks
  const queueItems = queue.map((item) => ({
    ...item,
    track: tracks.find((t) => t.id === item.trackId),
  }))

  // Play next item in queue
  const handlePlayNext = () => {
    const nextIndex = channelState.currentIndex + 1
    const nextItem = queue[nextIndex < queue.length ? nextIndex : 0]
    if (nextItem) {
      if (nextIndex >= queue.length) {
        // Wrap around - handled by advanceChannel resetting to -1 then we set to 0
      }
      advanceChannel(config.type)
      onPlayTrack(nextItem.trackId)
    }
  }

  return (
    <div className="flex h-full w-48 flex-col rounded-lg border bg-card">
      {/* Channel Header */}
      <div className="border-b p-3">
        <h3 className="text-sm font-semibold">{config.label}</h3>
        <p className="text-xs text-muted-foreground">{config.description}</p>
      </div>

      {/* Queue Area - Droppable */}
      <div
        ref={setDropRef}
        className={cn(
          'flex flex-1 flex-col gap-1 overflow-y-auto p-2 transition-colors',
          isOver && 'bg-primary/5 ring-2 ring-inset ring-primary/30',
          queue.length === 0 && 'items-center justify-center',
        )}
      >
        {queue.length === 0 ? (
          <div className="text-center text-xs text-muted-foreground">
            <ChevronDown className="mx-auto mb-1 h-5 w-5 opacity-40" />
            從右側拖入
          </div>
        ) : (
          <SortableContext
            items={queue.map((item) => item.id)}
            strategy={verticalListSortingStrategy}
          >
            {queueItems.map((item, index) => {
              const isPlaying = item.track
                ? (trackStates[item.trackId]?.isPlaying ?? false)
                : false
              return (
                <SortableQueueItem
                  key={item.id}
                  item={item}
                  track={item.track}
                  index={index}
                  isCurrent={index === channelState.currentIndex}
                  isPlaying={isPlaying}
                  channelType={config.type}
                  onPlay={() => onPlayTrack(item.trackId)}
                  onStop={() => onStopTrack(item.trackId)}
                  onRemove={() => removeFromChannel(config.type, item.id)}
                />
              )
            })}
          </SortableContext>
        )}
      </div>

      {/* Channel Footer: Play Next + Volume */}
      <div className="border-t p-2">
        {/* Play Next Button */}
        <button
          onClick={handlePlayNext}
          disabled={queue.length === 0}
          className={cn(
            'mb-2 flex w-full items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
            queue.length === 0
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-primary text-primary-foreground hover:bg-primary/90',
          )}
        >
          <Play className="h-3.5 w-3.5" />
          播放下一個
        </button>

        {/* Volume Slider */}
        <VolumeSlider
          value={channelState.volume}
          onChange={(v) => setChannelVolume(config.type, v)}
          onMuteToggle={() => toggleChannelMute(config.type)}
          isMuted={channelState.isMuted}
          size="sm"
        />
      </div>
    </div>
  )
}

export default ChannelStrip
