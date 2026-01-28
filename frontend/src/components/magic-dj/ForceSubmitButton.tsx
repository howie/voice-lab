/**
 * Force Submit Button
 * Feature: 010-magic-dj-controller
 *
 * T010: ForceSubmitButton component that triggers end_turn via existing useWebSocket,
 * shows visual feedback on click/Space key.
 */

import { useState, useEffect } from 'react'
import { Send } from 'lucide-react'

import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface ForceSubmitButtonProps {
  onClick: () => void
  disabled?: boolean
}

// =============================================================================
// Component
// =============================================================================

export function ForceSubmitButton({ onClick, disabled }: ForceSubmitButtonProps) {
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
        'focus:outline-none focus:ring-4 focus:ring-primary/50',
        disabled
          ? 'cursor-not-allowed border-muted bg-muted/50 text-muted-foreground'
          : isPressed
            ? 'scale-95 border-green-600 bg-green-600 text-white shadow-lg'
            : 'border-green-500 bg-green-500/10 text-green-700 hover:bg-green-500/20 active:scale-95'
      )}
    >
      <Send className="h-8 w-8" />
      <span>強制送出</span>
      <span className="text-xs opacity-70">Space</span>
    </button>
  )
}

export default ForceSubmitButton
