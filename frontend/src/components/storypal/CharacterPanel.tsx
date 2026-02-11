/**
 * Character Panel
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Shows active characters with voice assignments and speaking indicator.
 */

import { Volume2 } from 'lucide-react'
import type { StoryCharacter } from '@/types/storypal'
import { cn } from '@/lib/utils'

interface CharacterPanelProps {
  characters: StoryCharacter[]
  speakingCharacter: string | null
}

// Character-specific colors for visual distinction
const CHARACTER_COLORS = [
  'border-blue-400 bg-blue-50 dark:bg-blue-950/30',
  'border-pink-400 bg-pink-50 dark:bg-pink-950/30',
  'border-amber-400 bg-amber-50 dark:bg-amber-950/30',
  'border-green-400 bg-green-50 dark:bg-green-950/30',
  'border-purple-400 bg-purple-50 dark:bg-purple-950/30',
]

const CHARACTER_TEXT_COLORS = [
  'text-blue-600 dark:text-blue-400',
  'text-pink-600 dark:text-pink-400',
  'text-amber-600 dark:text-amber-400',
  'text-green-600 dark:text-green-400',
  'text-purple-600 dark:text-purple-400',
]

export function CharacterPanel({ characters, speakingCharacter }: CharacterPanelProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-medium text-muted-foreground">故事角色</h3>
      <div className="flex flex-wrap gap-2">
        {characters.map((char, idx) => {
          const isSpeaking = speakingCharacter === char.name
          const colorClass = CHARACTER_COLORS[idx % CHARACTER_COLORS.length]
          const textColor = CHARACTER_TEXT_COLORS[idx % CHARACTER_TEXT_COLORS.length]

          return (
            <div
              key={char.name}
              className={cn(
                'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-all',
                colorClass,
                isSpeaking && 'ring-2 ring-primary/50 shadow-sm'
              )}
            >
              {isSpeaking && (
                <Volume2 className="h-3 w-3 animate-pulse text-primary" />
              )}
              <span className={cn('font-medium', textColor)}>{char.name}</span>
              {char.emotion !== 'neutral' && (
                <span className="text-[10px] text-muted-foreground">({char.emotion})</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Get a consistent color class for a character by name */
export function getCharacterColor(name: string, characters: StoryCharacter[]): string {
  const idx = characters.findIndex((c) => c.name === name)
  return CHARACTER_TEXT_COLORS[idx >= 0 ? idx % CHARACTER_TEXT_COLORS.length : 0]
}
