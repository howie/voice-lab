/**
 * TranscriptDisplay Component
 * Feature: 004-interaction-module
 * T042b: Real-time conversation transcript display.
 *
 * Shows full conversation history with current turn in progress.
 */

import { useEffect, useRef } from 'react'

import type { ConversationTurn } from '@/types/interaction'

interface TranscriptDisplayProps {
  /** Completed conversation turns */
  turnHistory: ConversationTurn[]
  /** Current user transcript (in progress) */
  currentUserTranscript: string
  /** Current AI response text (in progress) */
  currentAIResponse: string
  /** Whether the current user transcript is final */
  isTranscriptFinal: boolean
  /** User role label (default: "您") */
  userRoleLabel?: string
  /** AI role label (default: "AI") */
  aiRoleLabel?: string
  /** Additional CSS classes */
  className?: string
}

// Single turn display component
function TurnDisplay({
  userTranscript,
  aiResponse,
  userRoleLabel,
  aiRoleLabel,
  isInProgress = false,
}: {
  userTranscript: string | null
  aiResponse: string | null
  userRoleLabel: string
  aiRoleLabel: string
  isInProgress?: boolean
}) {
  return (
    <div className="space-y-2">
      {/* User message */}
      {userTranscript && (
        <div className="flex justify-end">
          <div className="max-w-[80%] rounded-lg bg-primary/10 p-3">
            <div className="mb-1 text-xs font-medium text-primary">{userRoleLabel}</div>
            <div className="text-sm text-foreground">
              {userTranscript}
              {isInProgress && !aiResponse && (
                <span className="ml-1 inline-block h-3 w-1 animate-pulse bg-primary" />
              )}
            </div>
          </div>
        </div>
      )}

      {/* AI response */}
      {aiResponse && (
        <div className="flex justify-start">
          <div className="max-w-[80%] rounded-lg bg-muted p-3">
            <div className="mb-1 text-xs font-medium text-muted-foreground">{aiRoleLabel}</div>
            <div className="text-sm text-foreground">
              {aiResponse}
              {isInProgress && (
                <span className="ml-1 inline-block h-3 w-1 animate-pulse bg-muted-foreground" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export function TranscriptDisplay({
  turnHistory,
  currentUserTranscript,
  currentAIResponse,
  isTranscriptFinal,
  userRoleLabel = '您',
  aiRoleLabel = 'AI',
  className = '',
}: TranscriptDisplayProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when content changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [turnHistory, currentUserTranscript, currentAIResponse])

  const hasContent =
    turnHistory.length > 0 || currentUserTranscript || currentAIResponse

  return (
    <div className={`rounded-lg border bg-card p-4 ${className}`}>
      <div className="mb-2 text-sm font-medium text-foreground">對話內容</div>

      <div
        ref={scrollRef}
        className="max-h-[400px] space-y-4 overflow-y-auto scroll-smooth"
      >
        {/* History turns */}
        {turnHistory.map((turn) => (
          <TurnDisplay
            key={turn.id}
            userTranscript={turn.user_transcript}
            aiResponse={turn.ai_response_text}
            userRoleLabel={userRoleLabel}
            aiRoleLabel={aiRoleLabel}
          />
        ))}

        {/* Current turn in progress */}
        {(currentUserTranscript || currentAIResponse) && (
          <TurnDisplay
            userTranscript={currentUserTranscript || null}
            aiResponse={currentAIResponse || null}
            userRoleLabel={userRoleLabel}
            aiRoleLabel={aiRoleLabel}
            isInProgress={!isTranscriptFinal || !!currentAIResponse}
          />
        )}

        {/* Empty state */}
        {!hasContent && (
          <div className="py-8 text-center text-sm text-muted-foreground">
            對話開始後，文字記錄會顯示在這裡
          </div>
        )}
      </div>
    </div>
  )
}

export default TranscriptDisplay
