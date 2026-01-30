/**
 * Channel Board Component
 * Feature: 010-magic-dj-controller (DD-001)
 *
 * Container for 4 vertical ChannelStrips with shared DnD context.
 * Handles cross-container drag-and-drop from SoundLibrary to channels
 * and reordering within channels.
 */

import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  DragOverlay,
  type DragStartEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { useState } from 'react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { ChannelStrip } from './ChannelStrip'
import { SoundLibrary } from './SoundLibrary'
import type { ChannelType, Track } from '@/types/magic-dj'
import { CHANNEL_CONFIGS, TRACK_TYPE_TO_CHANNEL } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface ChannelBoardProps {
  onPlayTrack: (trackId: string) => void
  onStopTrack: (trackId: string) => void
  onAddTrack?: () => void
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
}

// =============================================================================
// Drag Overlay Content
// =============================================================================

function DragOverlayContent({ track }: { track: Track | null }) {
  if (!track) return null

  return (
    <div className="flex items-center gap-2 rounded-md border border-primary bg-card px-3 py-2 text-sm font-medium shadow-lg">
      {track.name}
    </div>
  )
}

// =============================================================================
// Component
// =============================================================================

export function ChannelBoard({
  onPlayTrack,
  onStopTrack,
  onAddTrack,
  onEditTrack,
  onDeleteTrack,
}: ChannelBoardProps) {
  const { tracks, addToChannel, reorderChannel } = useMagicDJStore()
  const [draggedTrack, setDraggedTrack] = useState<Track | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const data = active.data.current

    if (data?.source === 'library' && data.track) {
      setDraggedTrack(data.track as Track)
    } else {
      // Dragging from within a channel queue - find the track
      const trackId = data?.trackId as string | undefined
      if (trackId) {
        const track = tracks.find((t) => t.id === trackId)
        setDraggedTrack(track ?? null)
      }
    }
  }

  const handleDragEnd = (event: DragEndEvent) => {
    setDraggedTrack(null)
    const { active, over } = event

    if (!over) return

    const activeData = active.data.current
    const overData = over.data.current

    // Case 1: Dragging from library to a channel drop zone
    if (activeData?.source === 'library' && activeData.track) {
      const track = activeData.track as Track
      let targetChannel: ChannelType | null = null

      // Dropped on a channel droppable zone
      if (over.id && typeof over.id === 'string' && over.id.startsWith('channel-')) {
        targetChannel = over.id.replace('channel-', '') as ChannelType
      }
      // Dropped on a sortable item inside a channel
      else if (overData?.sortable?.containerId) {
        const containerId = overData.sortable.containerId as string
        if (containerId.startsWith('channel-')) {
          targetChannel = containerId.replace('channel-', '') as ChannelType
        }
      }

      if (targetChannel) {
        addToChannel(targetChannel, track.id)
      } else {
        // Auto-assign to the track's default channel
        const defaultChannel = TRACK_TYPE_TO_CHANNEL[track.type]
        addToChannel(defaultChannel, track.id)
      }
      return
    }

    // Case 2: Reordering within a channel
    if (active.id !== over.id) {
      // Find which channel contains this item
      const channelQueues = useMagicDJStore.getState().channelQueues
      for (const channelType of Object.keys(channelQueues) as ChannelType[]) {
        const queue = channelQueues[channelType]
        const hasActive = queue.some((item) => item.id === active.id)
        const hasOver = queue.some((item) => item.id === over.id)

        if (hasActive && hasOver) {
          reorderChannel(channelType, active.id as string, over.id as string)
          break
        }
      }
    }
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex flex-1 gap-3 overflow-x-auto">
        {/* 4 Channel Strips */}
        <div className="flex gap-2">
          {CHANNEL_CONFIGS.map((config) => (
            <ChannelStrip
              key={config.type}
              config={config}
              onPlayTrack={onPlayTrack}
              onStopTrack={onStopTrack}
            />
          ))}
        </div>

        {/* Sound Library */}
        <SoundLibrary
          onAddTrack={onAddTrack}
          onEditTrack={onEditTrack}
          onDeleteTrack={onDeleteTrack}
        />
      </div>

      {/* Drag Overlay */}
      <DragOverlay>
        <DragOverlayContent track={draggedTrack} />
      </DragOverlay>
    </DndContext>
  )
}

export default ChannelBoard
