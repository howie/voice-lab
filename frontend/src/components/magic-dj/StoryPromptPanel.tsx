/**
 * Story Prompt Panel Component
 * Feature: 015-magic-dj-ai-prompts (T017)
 *
 * Upper section: story template cards (click to send).
 * Lower section: free text input + submit button.
 * Second column in AI conversation mode.
 */

import { useState, useCallback, type KeyboardEvent } from 'react'
import { Send, Plus, Pencil, Trash2 } from 'lucide-react'

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
  onAddStoryPrompt?: () => void
  onEditStoryPrompt?: (prompt: StoryPrompt) => void
  onDeleteStoryPrompt?: (prompt: StoryPrompt) => void
}

// =============================================================================
// Story Prompt Button (with inline edit/delete)
// =============================================================================

function StoryPromptButton({
  prompt,
  disabled,
  onSend,
  onEdit,
  onDelete,
}: {
  prompt: StoryPrompt
  disabled: boolean
  onSend: (text: string) => void
  onEdit?: (prompt: StoryPrompt) => void
  onDelete?: (prompt: StoryPrompt) => void
}) {
  return (
    <div
      className={cn(
        'group flex w-full items-center gap-1 rounded-md px-2 py-1.5 text-sm font-medium transition-all',
        disabled
          ? 'cursor-not-allowed bg-muted text-muted-foreground'
          : CATEGORY_COLORS[prompt.category] ?? DEFAULT_CATEGORY_COLOR,
      )}
    >
      <button
        onClick={() => !disabled && onSend(prompt.prompt)}
        disabled={disabled}
        className="min-w-0 flex-1 truncate text-left active:scale-[0.97]"
      >
        {prompt.name}
      </button>
      {!disabled && (onEdit || onDelete) && (
        <div className="flex shrink-0 items-center gap-0.5">
          {onEdit && (
            <button
              onClick={() => onEdit(prompt)}
              className="rounded p-0.5 opacity-0 transition-opacity hover:bg-black/10 group-hover:opacity-100"
              title="編輯"
            >
              <Pencil className="h-3 w-3" />
            </button>
          )}
          {onDelete && !prompt.isDefault && (
            <button
              onClick={() => onDelete(prompt)}
              className="rounded p-0.5 opacity-0 transition-opacity hover:bg-black/10 group-hover:opacity-100"
              title="刪除"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Component
// =============================================================================

export function StoryPromptPanel({
  storyPrompts,
  disabled = false,
  onSendStoryPrompt,
  onAddStoryPrompt,
  onEditStoryPrompt,
  onDeleteStoryPrompt,
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
      <div className="flex items-center justify-between border-b p-3">
        <div>
          <h3 className="text-sm font-semibold">Story Prompts</h3>
          <p className="text-xs text-muted-foreground">故事指令</p>
        </div>
        {onAddStoryPrompt && (
          <button
            onClick={onAddStoryPrompt}
            className="rounded-md p-1 hover:bg-accent"
            title="新增故事指令"
          >
            <Plus className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Story Template Cards */}
      <div className="flex flex-1 flex-col gap-1.5 overflow-y-auto p-2">
        {sorted.map((sp) => (
          <StoryPromptButton
            key={sp.id}
            prompt={sp}
            disabled={disabled}
            onSend={onSendStoryPrompt}
            onEdit={onEditStoryPrompt}
            onDelete={onDeleteStoryPrompt}
          />
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
