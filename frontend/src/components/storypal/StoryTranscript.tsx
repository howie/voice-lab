/**
 * Story Transcript
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Scrolling story text display with character-colored dialogue lines.
 */

import { useEffect, useRef } from 'react'
import { BookOpen, MessageCircle, HelpCircle, Sparkles } from 'lucide-react'
import type { StoryCharacter, StoryTurn } from '@/types/storypal'
import { getCharacterColor } from './CharacterPanel'
import { cn } from '@/lib/utils'

interface StoryTranscriptProps {
  turns: StoryTurn[]
  characters: StoryCharacter[]
  currentSegmentContent?: string | null
}

function TurnIcon({ turnType }: { turnType: string }) {
  switch (turnType) {
    case 'narration':
      return <BookOpen className="h-3 w-3 text-muted-foreground" />
    case 'dialogue':
      return <MessageCircle className="h-3 w-3 text-muted-foreground" />
    case 'choice_prompt':
      return <Sparkles className="h-3 w-3 text-primary" />
    case 'question':
    case 'answer':
      return <HelpCircle className="h-3 w-3 text-amber-500" />
    default:
      return null
  }
}

export function StoryTranscript({ turns, characters, currentSegmentContent }: StoryTranscriptProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns.length, currentSegmentContent])

  return (
    <div className="space-y-3">
      {turns.map((turn) => {
        const isDialogue = turn.turn_type === 'dialogue'
        const isChoice = turn.turn_type === 'choice_prompt'
        const isChildResponse = turn.turn_type === 'child_response'
        const charColor = turn.character_name
          ? getCharacterColor(turn.character_name, characters)
          : 'text-foreground'

        return (
          <div
            key={turn.id}
            className={cn(
              'animate-in fade-in slide-in-from-bottom-2 duration-300',
              isChildResponse && 'ml-auto max-w-[80%]'
            )}
          >
            {/* Character name for dialogue */}
            {isDialogue && turn.character_name && (
              <div className="mb-0.5 flex items-center gap-1">
                <TurnIcon turnType={turn.turn_type} />
                <span className={cn('text-xs font-semibold', charColor)}>
                  {turn.character_name}
                </span>
              </div>
            )}

            {/* Content */}
            <div
              className={cn(
                'rounded-lg px-3 py-2 text-sm leading-relaxed',
                turn.turn_type === 'narration' && 'bg-muted/50 italic text-muted-foreground',
                isDialogue && 'border-l-2 border-current bg-card pl-3',
                isDialogue && charColor,
                isChoice && 'border border-primary/20 bg-primary/5',
                isChildResponse && 'bg-primary text-primary-foreground',
                turn.turn_type === 'question' && 'bg-amber-50 dark:bg-amber-950/30',
                turn.turn_type === 'answer' && 'bg-card'
              )}
            >
              {!isDialogue && !isChildResponse && (
                <span className="mr-1 inline-block">
                  <TurnIcon turnType={turn.turn_type} />
                </span>
              )}
              {turn.content}
            </div>

            {/* Child's choice */}
            {turn.child_choice && (
              <div className="mt-1 ml-4 text-xs text-muted-foreground">
                你選了：「{turn.child_choice}」
              </div>
            )}
          </div>
        )
      })}

      {/* Streaming current segment */}
      {currentSegmentContent && (
        <div className="animate-pulse rounded-lg bg-muted/30 px-3 py-2 text-sm italic text-muted-foreground">
          {currentSegmentContent}
          <span className="ml-1 inline-block h-3 w-1 animate-blink bg-primary" />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
