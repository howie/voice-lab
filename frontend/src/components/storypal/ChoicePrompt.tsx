/**
 * Choice Prompt
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Interactive choice UI displayed when the story reaches a decision point.
 * Children tap/click a button or speak their choice.
 */

import { Sparkles } from 'lucide-react'
import type { ChoicePromptData } from '@/types/storypal'
import { cn } from '@/lib/utils'

interface ChoicePromptProps {
  choice: ChoicePromptData
  onSelect: (choice: string) => void
  disabled?: boolean
}

const OPTION_COLORS = [
  'hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 focus:ring-blue-400',
  'hover:border-pink-400 hover:bg-pink-50 dark:hover:bg-pink-950/30 focus:ring-pink-400',
  'hover:border-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30 focus:ring-amber-400',
]

export function ChoicePrompt({ choice, onSelect, disabled }: ChoicePromptProps) {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 mx-auto max-w-lg space-y-4 duration-500">
      {/* Prompt text */}
      <div className="flex items-start gap-2 rounded-lg border border-primary/20 bg-primary/5 p-3">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p className="text-sm font-medium">{choice.prompt}</p>
      </div>

      {/* Choice buttons */}
      <div className="space-y-2">
        {choice.options.map((option, idx) => (
          <button
            key={option}
            onClick={() => onSelect(option)}
            disabled={disabled}
            className={cn(
              'w-full rounded-lg border-2 border-border bg-card p-3 text-left text-sm font-medium',
              'transition-all focus:outline-none focus:ring-2 focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              OPTION_COLORS[idx % OPTION_COLORS.length]
            )}
          >
            <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-muted text-[10px] font-bold">
              {idx + 1}
            </span>
            {option}
          </button>
        ))}
      </div>

      {/* Hint */}
      <p className="text-center text-xs text-muted-foreground">
        點選按鈕或用說的告訴我你的選擇
      </p>
    </div>
  )
}
