/**
 * Story Prompt Panel Component
 * Feature: 015-magic-dj-ai-prompts (T017)
 *
 * Upper section: story template cards (click to send).
 * Lower section: free text input + submit button.
 * Second column in AI conversation mode.
 */

import { useState, useCallback, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { StoryPrompt } from '@/types/magic-dj'

// =============================================================================
// Color Mapping for Story Categories
// =============================================================================

const CATEGORY_COLORS: Record<string, string> = {
  adventure: 'bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/20',
  activity: 'bg-amber-500/10 text-amber-700 hover:bg-amber-500/20',
  fantasy: 'bg-violet-500/10 text-violet-700 hover:bg-violet-500/20',
}

const DEFAULT_CATEGORY_COLOR = 'bg-sky-500/10 text-sky-700 hover:bg-sky-500/20'

// =============================================================================
// Types
// =============================================================================

export interface StoryPromptPanelProps {
  storyPrompts: StoryPrompt[]
  disabled?: boolean
  onSendStoryPrompt: (text: string) => void
}

// =============================================================================
// Component
// =============================================================================

export function StoryPromptPanel({
  storyPrompts,
  disabled = false,
  onSendStoryPrompt,
}: StoryPromptPanelProps) {
  const [customText, setCustomText] = useState('')
  const sorted = [...storyPrompts].sort((a, b) => a.order - b.order)

  const handleSubmitCustom = useCallback(() => {
    const trimmed = customText.trim()
    if (!trimmed || disabled) return
    onSendStoryPrompt(trimmed)
    setCustomText('')
  }, [customText, disabled, onSendStoryPrompt])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault()
        handleSubmitCustom()
      }
    },
    [handleSubmitCustom]
  )

  return (
    <div className="flex h-full w-48 shrink-0 flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="border-b p-3">
        <h3 className="text-sm font-semibold">Story Prompts</h3>
        <p className="text-xs text-muted-foreground">故事指令</p>
      </div>

      {/* Story Template Cards */}
      <div className="flex flex-1 flex-col gap-1.5 overflow-y-auto p-2">
        {sorted.map((sp) => (
          <button
            key={sp.id}
            onClick={() => !disabled && onSendStoryPrompt(sp.prompt)}
            disabled={disabled}
            className={cn(
              'flex w-full items-center rounded-md px-3 py-2 text-left text-sm font-medium transition-all active:scale-[0.97]',
              disabled
                ? 'cursor-not-allowed bg-muted text-muted-foreground'
                : CATEGORY_COLORS[sp.category] ?? DEFAULT_CATEGORY_COLOR,
            )}
          >
            <span className="truncate">{sp.name}</span>
          </button>
        ))}
      </div>

      {/* Custom Text Input */}
      <div className="border-t p-2">
        <textarea
          value={customText}
          onChange={(e) => setCustomText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="輸入自訂指令..."
          rows={2}
          className="w-full resize-none rounded-md border bg-background px-2 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          onClick={handleSubmitCustom}
          disabled={disabled || !customText.trim()}
          className={cn(
            'mt-1.5 flex w-full items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            disabled || !customText.trim()
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-primary text-primary-foreground hover:bg-primary/90 active:scale-[0.97]',
          )}
        >
          <Send className="h-3 w-3" />
          送出指令
        </button>
        <p className="mt-1 text-center text-[10px] text-muted-foreground">
          Shift+Enter 快速送出
        </p>
      </div>
    </div>
  )
}

export default StoryPromptPanel
