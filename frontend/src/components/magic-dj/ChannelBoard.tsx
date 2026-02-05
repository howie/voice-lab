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

import { useMagicDJStore, selectCueList, selectCueListRemainingCount } from '@/stores/magicDJStore'
import { ChannelStrip } from './ChannelStrip'
import { SoundLibrary } from './SoundLibrary'
import { CueListPanel } from './CueListPanel'
import type { ChannelType, Track } from '@/types/magic-dj'
import { CHANNEL_CONFIGS, TRACK_TYPE_TO_CHANNEL } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface ChannelBoardProps {
  onPlayTrack: (trackId: string) => void
  onStopTrack: (trackId: string) => void
  onAddTrack?: () => void
  onGenerateBGM?: () => void
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
  /** Optional leading channel rendered before the 4 standard channels (e.g. AI Voice) */
  leadingChannel?: React.ReactNode
  /** Whether to show the cue list panel */
  showCueList?: boolean
  /** Cue list event handlers */
  onPlayNextCue?: () => void
  onRemoveFromCueList?: (cueItemId: string) => void
  onResetCueList?: () => void
  onClearCueList?: () => void
  /** When true, only show SFX and Music channels (015-DD-001 AI mode layout) */
  aiMode?: boolean
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
  onGenerateBGM,
  onEditTrack,
  onDeleteTrack,
  leadingChannel,
  showCueList = false,
  onPlayNextCue,
  onRemoveFromCueList,
  onResetCueList,
  onClearCueList,
  aiMode = false,
}: ChannelBoardProps) {
  const tracks = useMagicDJStore(s => s.tracks)
  const addToChannel = useMagicDJStore(s => s.addToChannel)
  const reorderChannel = useMagicDJStore(s => s.reorderChannel)
  const addToCueList = useMagicDJStore(s => s.addToCueList)
  const reorderCueList = useMagicDJStore(s => s.reorderCueList)
  const reorderTracks = useMagicDJStore(s => s.reorderTracks)
  const cueList = useMagicDJStore(selectCueList)
  const remainingCount = useMagicDJStore(selectCueListRemainingCount)
  const [draggedTrack, setDraggedTrack] = useState<Track | null>(null)

  // In AI mode, only show SFX and Music channels (015-DD-001)
  const AI_MODE_CHANNELS: ChannelType[] = ['sfx', 'music']
  const visibleChannels = aiMode
    ? CHANNEL_CONFIGS.filter((c) => AI_MODE_CHANNELS.includes(c.type))
    : CHANNEL_CONFIGS

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

    // Case 1: Dragging from library
    if (activeData?.source === 'library' && activeData.track) {
      const track = activeData.track as Track

      // Case 1a: Library → Library reorder (T059 FR-019)
      if (overData?.source === 'library' && overData.track && active.id !== over.id) {
        const overTrack = overData.track as Track
        reorderTracks(track.id, overTrack.id)
        return
      }

      // Case 1b: Library → Cue List
      if (
        over.id === 'cue-list-drop-zone' ||
        overData?.type === 'cue-list' ||
        overData?.type === 'cue-item'
      ) {
        addToCueList(track.id)
        return
      }

      // Case 1c: Library → Channel
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

    // Case 2: Reordering within cue list
    if (activeData?.type === 'cue-item' && active.id !== over.id) {
      const cueItems = useMagicDJStore.getState().cueList.items
      const hasActive = cueItems.some((item) => item.id === active.id)
      const hasOver = cueItems.some((item) => item.id === over.id)

      if (hasActive && hasOver) {
        reorderCueList(active.id as string, over.id as string)
        return
      }
    }

    // Case 3: Reordering within a channel
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
        {/* Leading Channel (e.g. AI Voice, only in AI mode) */}
        {leadingChannel}


        {/* Channel Strips (all 4 in normal mode, SFX+Music in AI mode) */}
        <div className="flex gap-2">
          {visibleChannels.map((config) => (
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
          onGenerateBGM={onGenerateBGM}
          onEditTrack={onEditTrack}
          onDeleteTrack={onDeleteTrack}
        />

        {/* Cue List Panel (T040: prerecorded mode dual-panel) */}
        {showCueList && (
          <div className="w-64 shrink-0">
            <CueListPanel
              cueList={cueList}
              remainingCount={remainingCount}
              onRemove={onRemoveFromCueList ?? (() => {})}
              onPlayNext={onPlayNextCue ?? (() => {})}
              onReset={onResetCueList ?? (() => {})}
              onClear={onClearCueList ?? (() => {})}
              onPlayTrack={onPlayTrack}
              isAtEnd={
                cueList.items.length > 0 &&
                cueList.currentPosition >= cueList.items.length - 1
              }
            />
          </div>
        )}
      </div>

      {/* Drag Overlay */}
      <DragOverlay>
        <DragOverlayContent track={draggedTrack} />
      </DragOverlay>
    </DndContext>
  )
}

export default ChannelBoard
