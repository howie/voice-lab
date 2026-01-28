/**
 * Session Timer
 * Feature: 010-magic-dj-controller
 *
 * T032: SessionTimer component showing elapsed time, warning at 25 min, alert at 30 min.
 * T033: Session timing logic with start/stop/reset actions.
 */

import { useEffect, useRef } from 'react'
import { Play, Pause, RotateCcw, Clock, AlertTriangle } from 'lucide-react'

import {
  useMagicDJStore,
  selectIsTimeWarning,
  selectIsTimeLimit,
} from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface SessionTimerProps {
  onStartSession: () => void
  onStopSession: () => void
}

// =============================================================================
// Helpers
// =============================================================================

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// =============================================================================
// Component
// =============================================================================

export function SessionTimer({ onStartSession, onStopSession }: SessionTimerProps) {
  const {
    isSessionActive,
    elapsedTime,
    sessionStartTime,
    updateElapsedTime,
    resetSession,
    settings,
  } = useMagicDJStore()

  const isTimeWarning = useMagicDJStore(selectIsTimeWarning)
  const isTimeLimit = useMagicDJStore(selectIsTimeLimit)

  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Update elapsed time every second
  useEffect(() => {
    if (isSessionActive && sessionStartTime) {
      intervalRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000)
        updateElapsedTime(elapsed)
      }, 1000)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isSessionActive, sessionStartTime, updateElapsedTime])

  const handleToggle = () => {
    if (isSessionActive) {
      onStopSession()
    } else {
      onStartSession()
    }
  }

  const handleReset = () => {
    if (isSessionActive) {
      onStopSession()
    }
    resetSession()
  }

  // Calculate remaining time for display
  const remainingTime = Math.max(0, settings.sessionTimeLimit - elapsedTime)

  return (
    <div className="flex items-center gap-4">
      {/* Timer Display */}
      <div
        className={cn(
          'flex items-center gap-2 rounded-lg px-4 py-2 font-mono text-2xl font-bold transition-colors',
          isTimeLimit
            ? 'animate-pulse bg-destructive/20 text-destructive'
            : isTimeWarning
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-muted'
        )}
      >
        <Clock className="h-6 w-6" />
        <span>{formatTime(elapsedTime)}</span>
        {(isTimeWarning || isTimeLimit) && (
          <AlertTriangle className="h-5 w-5" />
        )}
      </div>

      {/* Remaining Time */}
      {isSessionActive && (
        <div className="text-sm text-muted-foreground">
          剩餘 {formatTime(remainingTime)}
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleToggle}
          className={cn(
            'flex items-center gap-2 rounded-lg px-4 py-2 font-medium transition-colors',
            isSessionActive
              ? 'bg-yellow-500 text-white hover:bg-yellow-600'
              : 'bg-green-500 text-white hover:bg-green-600'
          )}
        >
          {isSessionActive ? (
            <>
              <Pause className="h-4 w-4" />
              <span>暫停</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              <span>開始測試</span>
            </>
          )}
        </button>

        <button
          onClick={handleReset}
          className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2 font-medium hover:bg-muted/80"
          title="重置計時器"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {/* Time Limit Warning */}
      {isTimeLimit && (
        <div className="rounded-lg bg-destructive/20 px-3 py-1 text-sm font-medium text-destructive">
          已超過 30 分鐘！
        </div>
      )}

      {isTimeWarning && !isTimeLimit && (
        <div className="rounded-lg bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-700">
          剩餘不到 5 分鐘
        </div>
      )}
    </div>
  )
}

export default SessionTimer
