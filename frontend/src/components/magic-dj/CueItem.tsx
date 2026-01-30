/**
 * Cue Item Component
 * Feature: 010-magic-dj-controller
 *
 * T033: Individual cue list item with sequence number, play status,
 * drag handle for reorder, and remove button.
 */

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, X, AlertTriangle, Play, Check, Clock } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { CueItem as CueItemType } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface CueItemProps {
  item: CueItemType
  isCurrent: boolean
  onRemove: (cueItemId: string) => void
  onPlay?: (trackId: string) => void
}

// =============================================================================
// Status Icon
// =============================================================================

function StatusIcon({ status }: { status: CueItemType['status'] }) {
  switch (status) {
    case 'pending':
      return <Clock className="h-3.5 w-3.5 text-muted-foreground" />
    case 'playing':
      return <Play className="h-3.5 w-3.5 text-primary animate-pulse" />
    case 'played':
      return <Check className="h-3.5 w-3.5 text-green-500" />
    case 'invalid':
      return <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
  }
}

// =============================================================================
// Component
// =============================================================================

export function CueItemComponent({ item, isCurrent, onRemove, onPlay }: CueItemProps) {
  const tracks = useMagicDJStore((s) => s.tracks)
  const track = tracks.find((t) => t.id === item.trackId)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: item.id,
    data: {
      type: 'cue-item',
      cueItem: item,
    },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 rounded-md border px-2 py-1.5 text-sm transition-colors ${
        isDragging ? 'opacity-50' : ''
      } ${isCurrent ? 'border-primary bg-primary/10 ring-1 ring-primary' : 'border-border bg-card'} ${
        item.status === 'invalid' ? 'border-destructive/50 bg-destructive/5' : ''
      } ${item.status === 'played' ? 'opacity-60' : ''}`}
    >
      {/* Drag Handle */}
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab touch-none text-muted-foreground hover:text-foreground"
        aria-label="拖曳排序"
      >
        <GripVertical className="h-4 w-4" />
      </button>

      {/* Sequence Number */}
      <span className="w-5 text-center text-xs font-medium text-muted-foreground">
        {item.order}
      </span>

      {/* Status Icon */}
      <StatusIcon status={item.status} />

      {/* Track Name */}
      <button
        className="flex-1 truncate text-left"
        onClick={() => {
          if (item.status !== 'invalid' && onPlay) {
            onPlay(item.trackId)
          }
        }}
        title={item.status === 'invalid' ? '來源已刪除' : track?.name}
      >
        {item.status === 'invalid' ? (
          <span className="text-destructive line-through">來源已刪除</span>
        ) : (
          track?.name ?? '未知音軌'
        )}
      </button>

      {/* Remove Button */}
      <button
        onClick={() => onRemove(item.id)}
        className="rounded p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        aria-label="移除"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

export default CueItemComponent
