/**
 * Interrupt Button
 * Feature: 010-magic-dj-controller
 *
 * T011: InterruptButton component that sends interrupt message via WebSocket,
 * stops AI audio playback.
 */

import { useState, useEffect } from 'react'
import { StopCircle } from 'lucide-react'

import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface InterruptButtonProps {
  onClick: () => void
  disabled?: boolean
}

// =============================================================================
// Component
// =============================================================================

export function InterruptButton({ onClick, disabled }: InterruptButtonProps) {
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
        'focus:outline-none focus:ring-4 focus:ring-destructive/50',
        disabled
          ? 'cursor-not-allowed border-muted bg-muted/50 text-muted-foreground'
          : isPressed
            ? 'scale-95 border-red-600 bg-red-600 text-white shadow-lg'
            : 'border-red-500 bg-red-500/10 text-red-700 hover:bg-red-500/20 active:scale-95'
      )}
    >
      <StopCircle className="h-8 w-8" />
      <span>中斷</span>
      <span className="text-xs opacity-70">Esc</span>
    </button>
  )
}

export default InterruptButton
