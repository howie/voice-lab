/**
 * Cue List Panel Component
 * Feature: 010-magic-dj-controller
 *
 * T032: Displays ordered cue items with sequence numbers, current position
 * highlight, remove button, and drop zone for drag targets.
 * T034: PlayNextButton integration.
 * T035: Auto-advance on playback end.
 * T036: End-of-list reset.
 * T038: Same-sound-multiple-times support.
 */

import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { useDroppable } from '@dnd-kit/core'
import { ListMusic, RotateCcw, Trash2, SkipForward } from 'lucide-react'

import { CueItemComponent } from './CueItem'
import type { CueList } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface CueListPanelProps {
  cueList: CueList
  remainingCount: number
  onRemove: (cueItemId: string) => void
  onPlayNext: () => void
  onReset: () => void
  onClear: () => void
  onPlayTrack?: (trackId: string) => void
  isAtEnd: boolean
}

// =============================================================================
// Component
// =============================================================================

export function CueListPanel({
  cueList,
  remainingCount,
  onRemove,
  onPlayNext,
  onReset,
  onClear,
  onPlayTrack,
  isAtEnd,
}: CueListPanelProps) {
  const { items, currentPosition } = cueList
  const isEmpty = items.length === 0

  // Make the cue list panel a drop target
  const { setNodeRef, isOver } = useDroppable({
    id: 'cue-list-drop-zone',
    data: { type: 'cue-list' },
  })

  return (
    <div className="flex h-full flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="flex items-center gap-2">
          <ListMusic className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">播放清單</h3>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {items.length} 項
          </span>
        </div>

        <div className="flex items-center gap-1">
          {/* Reset Button */}
          <button
            onClick={onReset}
            disabled={isEmpty}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
            title="重設播放位置"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          {/* Clear Button */}
          <button
            onClick={onClear}
            disabled={isEmpty}
            className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
            title="清空播放清單"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Play Next Button (T034) */}
      <div className="border-b px-3 py-2">
        <button
          onClick={onPlayNext}
          disabled={isEmpty || (isAtEnd && currentPosition >= 0)}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          <SkipForward className="h-4 w-4" />
          播放下一個
          {remainingCount > 0 && (
            <span className="rounded-full bg-primary-foreground/20 px-2 py-0.5 text-xs">
              剩餘 {remainingCount}
            </span>
          )}
        </button>
        {/* N hotkey hint */}
        <p className="mt-1 text-center text-xs text-muted-foreground">
          按 <kbd className="rounded bg-muted px-1">N</kbd> 快速播放下一個
        </p>
      </div>

      {/* Cue Items List */}
      <div
        ref={setNodeRef}
        className={`flex-1 overflow-y-auto p-2 transition-colors ${
          isOver ? 'bg-primary/5 ring-2 ring-inset ring-primary/30' : ''
        } ${isEmpty ? 'flex items-center justify-center' : ''}`}
      >
        {isEmpty ? (
          <div className="text-center text-sm text-muted-foreground">
            <ListMusic className="mx-auto mb-2 h-8 w-8 opacity-30" />
            <p>播放清單為空</p>
            <p className="text-xs">從聲音庫拖曳項目到此處</p>
          </div>
        ) : (
          <SortableContext
            items={items.map((item) => item.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="flex flex-col gap-1">
              {items.map((item, index) => (
                <CueItemComponent
                  key={item.id}
                  item={item}
                  isCurrent={index === currentPosition}
                  onRemove={onRemove}
                  onPlay={onPlayTrack}
                />
              ))}
            </div>
          </SortableContext>
        )}
      </div>

      {/* End-of-list message (EC-007) */}
      {isAtEnd && currentPosition >= 0 && (
        <div className="border-t px-3 py-2 text-center text-xs text-muted-foreground">
          播放清單已結束
        </div>
      )}
    </div>
  )
}

export default CueListPanel
