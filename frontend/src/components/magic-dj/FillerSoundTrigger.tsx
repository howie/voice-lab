/**
 * Filler Sound Trigger
 * Feature: 010-magic-dj-controller
 *
 * T012: FillerSoundTrigger component that plays thinking sound effect
 * via useMultiTrackPlayer on F key or click.
 */

import { useState, useEffect } from 'react'
import { Sparkles } from 'lucide-react'

import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface FillerSoundTriggerProps {
  onClick: () => void
  disabled?: boolean
}

// =============================================================================
// Component
// =============================================================================

export function FillerSoundTrigger({ onClick, disabled }: FillerSoundTriggerProps) {
  const [isPressed, setIsPressed] = useState(false)

  // Visual feedback on press
  useEffect(() => {
    if (isPressed) {
      const timer = setTimeout(() => setIsPressed(false), 200)
      return () => clearTimeout(timer)
    }
  }, [isPressed])

  const handleClick = () => {
    if (disabled) return
    setIsPressed(true)
    onClick()
  }

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        'flex h-24 w-32 flex-col items-center justify-center gap-2 rounded-xl border-4 text-lg font-bold transition-all',
        'focus:outline-none focus:ring-4 focus:ring-purple-500/50',
        disabled
          ? 'cursor-not-allowed border-muted bg-muted/50 text-muted-foreground'
          : isPressed
            ? 'scale-95 border-purple-600 bg-purple-600 text-white shadow-lg'
            : 'border-purple-500 bg-purple-500/10 text-purple-700 hover:bg-purple-500/20 active:scale-95'
      )}
    >
      <Sparkles className="h-8 w-8" />
      <span>思考音效</span>
      <span className="text-xs opacity-70">F</span>
    </button>
  )
}

export default FillerSoundTrigger
