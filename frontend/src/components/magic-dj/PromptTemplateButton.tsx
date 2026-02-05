/**
 * Prompt Template Button Component
 * Feature: 015-magic-dj-ai-prompts (T011)
 *
 * A single clickable prompt template button with color badge,
 * click animation, and context menu for edit/delete.
 */

import { useState, useEffect, useCallback } from 'react'

import { cn } from '@/lib/utils'
import type { PromptTemplate } from '@/types/magic-dj'

// =============================================================================
// Color Mapping
// =============================================================================

const COLOR_CLASSES: Record<string, { bg: string; text: string; hover: string; active: string }> = {
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-700', hover: 'hover:bg-blue-500/20', active: 'bg-blue-500/30' },
  green: { bg: 'bg-green-500/10', text: 'text-green-700', hover: 'hover:bg-green-500/20', active: 'bg-green-500/30' },
  yellow: { bg: 'bg-yellow-500/10', text: 'text-yellow-700', hover: 'hover:bg-yellow-500/20', active: 'bg-yellow-500/30' },
  red: { bg: 'bg-red-500/10', text: 'text-red-700', hover: 'hover:bg-red-500/20', active: 'bg-red-500/30' },
  purple: { bg: 'bg-purple-500/10', text: 'text-purple-700', hover: 'hover:bg-purple-500/20', active: 'bg-purple-500/30' },
  orange: { bg: 'bg-orange-500/10', text: 'text-orange-700', hover: 'hover:bg-orange-500/20', active: 'bg-orange-500/30' },
  pink: { bg: 'bg-pink-500/10', text: 'text-pink-700', hover: 'hover:bg-pink-500/20', active: 'bg-pink-500/30' },
  cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-700', hover: 'hover:bg-cyan-500/20', active: 'bg-cyan-500/30' },
}

// =============================================================================
// Types
// =============================================================================

export interface PromptTemplateButtonProps {
  template: PromptTemplate
  disabled?: boolean
  /** Whether this button was just sent (for pulse feedback) */
  isJustSent?: boolean
  onSend: (template: PromptTemplate) => void
  onEdit?: (template: PromptTemplate) => void
  onDelete?: (template: PromptTemplate) => void
}

// =============================================================================
// Component
// =============================================================================

export function PromptTemplateButton({
  template,
  disabled = false,
  isJustSent = false,
  onSend,
  onEdit,
  onDelete,
}: PromptTemplateButtonProps) {
  const [isPulsing, setIsPulsing] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  const colors = COLOR_CLASSES[template.color] ?? COLOR_CLASSES.blue

  // Pulse animation on click
  const handleClick = useCallback(() => {
    if (disabled) return
    setIsPulsing(true)
    onSend(template)
  }, [disabled, onSend, template])

  // Reset pulse after animation
  useEffect(() => {
    if (isPulsing) {
      const timer = setTimeout(() => setIsPulsing(false), 300)
      return () => clearTimeout(timer)
    }
  }, [isPulsing])

  // External "just sent" feedback
  useEffect(() => {
    if (isJustSent) {
      setIsPulsing(true)
    }
  }, [isJustSent])

  // Context menu (right-click)
  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      if (onEdit || onDelete) {
        setShowMenu(true)
      }
    },
    [onEdit, onDelete]
  )

  // Close menu on blur
  useEffect(() => {
    if (showMenu) {
      const handleClick = () => setShowMenu(false)
      document.addEventListener('click', handleClick)
      return () => document.removeEventListener('click', handleClick)
    }
  }, [showMenu])

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        disabled={disabled}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-all',
          disabled
            ? 'cursor-not-allowed bg-muted text-muted-foreground'
            : cn(colors.bg, colors.text, colors.hover, 'active:scale-[0.97]'),
          isPulsing && !disabled && colors.active,
          isPulsing && !disabled && 'scale-[0.95]',
        )}
      >
        <span className="truncate">{template.name}</span>
      </button>

      {/* Context Menu */}
      {showMenu && (
        <div className="absolute left-0 top-full z-50 mt-1 w-32 rounded-md border bg-popover py-1 shadow-lg">
          {onEdit && (
            <button
              onClick={() => { setShowMenu(false); onEdit(template) }}
              className="flex w-full items-center px-3 py-1.5 text-sm hover:bg-accent"
            >
              編輯
            </button>
          )}
          {onDelete && !template.isDefault && (
            <button
              onClick={() => { setShowMenu(false); onDelete(template) }}
              className="flex w-full items-center px-3 py-1.5 text-sm text-destructive hover:bg-accent"
            >
              刪除
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default PromptTemplateButton
