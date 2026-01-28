/**
 * Rescue Panel
 * Feature: 010-magic-dj-controller
 *
 * T027: RescuePanel component with two buttons: 「等待填補」(W key) and 「緊急結束」(E key).
 * T030: Ensure rescue sounds interrupt current AI playback and take priority.
 * Enhanced: Support editing rescue sound texts via TTS modal.
 */

import { useState, useEffect } from 'react'
import { Clock, XCircle, AlertTriangle, Pencil } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'
import type { Track } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface RescuePanelProps {
  onRescueWait: () => void
  onRescueEnd: () => void
  isAITimeout: boolean
  disabled?: boolean
  onEditRescue?: (track: Track) => void
}

// =============================================================================
// Component
// =============================================================================

export function RescuePanel({
  onRescueWait,
  onRescueEnd,
  isAITimeout,
  disabled,
  onEditRescue,
}: RescuePanelProps) {
  const [waitPressed, setWaitPressed] = useState(false)
  const [endPressed, setEndPressed] = useState(false)

  // Get rescue tracks from store
  const { tracks } = useMagicDJStore()
  const waitTrack = tracks.find((t) => t.id === 'filler_wait')
  const endTrack = tracks.find((t) => t.id === 'track_end')

  // Visual feedback on press
  useEffect(() => {
    if (waitPressed) {
      const timer = setTimeout(() => setWaitPressed(false), 200)
      return () => clearTimeout(timer)
    }
  }, [waitPressed])

  useEffect(() => {
    if (endPressed) {
      const timer = setTimeout(() => setEndPressed(false), 200)
      return () => clearTimeout(timer)
    }
  }, [endPressed])

  const handleWait = () => {
    if (disabled) return
    setWaitPressed(true)
    onRescueWait()
  }

  const handleEnd = () => {
    if (disabled) return
    setEndPressed(true)
    onRescueEnd()
  }

  // Get display text from track or use default
  const waitText = waitTrack?.textContent || '訊號有點不好，等等喔...'
  const endText = endTrack?.textContent || '天黑了，我們該回家了！'

  return (
    <div className="flex flex-col gap-4">
      {/* Timeout Warning */}
      {isAITimeout && (
        <div className="flex items-center gap-2 rounded-lg bg-yellow-100 p-3 text-yellow-800">
          <AlertTriangle className="h-5 w-5" />
          <span className="font-medium">AI 回應超時，建議使用救場語音</span>
        </div>
      )}

      <div className="flex gap-4">
        {/* Wait Filler Button */}
        <div className="relative flex-1">
          <button
            onClick={handleWait}
            disabled={disabled}
            className={cn(
              'flex w-full flex-col items-center justify-center gap-3 rounded-xl border-4 p-6 text-lg font-bold transition-all',
              'focus:outline-none focus:ring-4 focus:ring-yellow-500/50',
              disabled
                ? 'cursor-not-allowed border-muted bg-muted/50 text-muted-foreground'
                : waitPressed
                  ? 'scale-95 border-yellow-600 bg-yellow-600 text-white shadow-lg'
                  : isAITimeout
                    ? 'animate-pulse border-yellow-500 bg-yellow-500/20 text-yellow-700 hover:bg-yellow-500/30'
                    : 'border-yellow-500 bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20 active:scale-95'
            )}
          >
            <Clock className="h-10 w-10" />
            <span>等待填補</span>
            <span className="text-sm font-normal opacity-70 line-clamp-2">
              「{waitText}」
            </span>
            <kbd className="rounded bg-white/50 px-2 py-1 text-xs">W</kbd>
          </button>

          {/* Edit button */}
          {onEditRescue && waitTrack && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEditRescue(waitTrack)
              }}
              className="absolute right-2 top-2 rounded-md bg-white/80 p-1.5 text-muted-foreground hover:bg-white hover:text-foreground"
              title="編輯語音內容"
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Emergency End Button */}
        <div className="relative flex-1">
          <button
            onClick={handleEnd}
            disabled={disabled}
            className={cn(
              'flex w-full flex-col items-center justify-center gap-3 rounded-xl border-4 p-6 text-lg font-bold transition-all',
              'focus:outline-none focus:ring-4 focus:ring-red-500/50',
              disabled
                ? 'cursor-not-allowed border-muted bg-muted/50 text-muted-foreground'
                : endPressed
                  ? 'scale-95 border-red-700 bg-red-700 text-white shadow-lg'
                  : 'border-red-600 bg-red-600/10 text-red-700 hover:bg-red-600/20 active:scale-95'
            )}
          >
            <XCircle className="h-10 w-10" />
            <span>緊急結束</span>
            <span className="text-sm font-normal opacity-70 line-clamp-2">
              「{endText}」
            </span>
            <kbd className="rounded bg-white/50 px-2 py-1 text-xs">E</kbd>
          </button>

          {/* Edit button */}
          {onEditRescue && endTrack && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEditRescue(endTrack)
              }}
              className="absolute right-2 top-2 rounded-md bg-white/80 p-1.5 text-muted-foreground hover:bg-white hover:text-foreground"
              title="編輯語音內容"
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default RescuePanel
