/**
 * Story Controls
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Play/pause/restart controls and voice input toggle for the story player.
 */

import { Mic, MicOff, Pause, Play, RotateCcw, Square } from 'lucide-react'
import { cn } from '@/lib/utils'

type StoryPlayState = 'idle' | 'loading' | 'playing' | 'waiting_choice' | 'listening' | 'paused' | 'ended'

interface StoryControlsProps {
  playState: StoryPlayState
  isConnected: boolean
  isListening: boolean
  onToggleListening: () => void
  onPause: () => void
  onResume: () => void
  onStop: () => void
  onRestart: () => void
}

export function StoryControls({
  playState,
  isConnected,
  isListening,
  onToggleListening,
  onPause,
  onResume,
  onStop,
  onRestart,
}: StoryControlsProps) {
  const isPlaying = playState === 'playing' || playState === 'waiting_choice' || playState === 'listening'
  const canInteract = isConnected && playState !== 'idle' && playState !== 'ended'

  return (
    <div className="flex items-center justify-center gap-3">
      {/* Restart */}
      <button
        onClick={onRestart}
        disabled={playState === 'idle'}
        className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-30"
        title="重新開始"
      >
        <RotateCcw className="h-4 w-4" />
      </button>

      {/* Play/Pause */}
      {isPlaying ? (
        <button
          onClick={onPause}
          disabled={!canInteract}
          className="rounded-full bg-primary p-3 text-primary-foreground shadow-md transition-all hover:bg-primary/90 disabled:opacity-30"
          title="暫停"
        >
          <Pause className="h-5 w-5" />
        </button>
      ) : playState === 'paused' ? (
        <button
          onClick={onResume}
          className="rounded-full bg-primary p-3 text-primary-foreground shadow-md transition-all hover:bg-primary/90"
          title="繼續"
        >
          <Play className="h-5 w-5" />
        </button>
      ) : (
        <button
          disabled
          className="rounded-full bg-muted p-3 text-muted-foreground"
          title={playState === 'ended' ? '故事結束' : '等待中'}
        >
          {playState === 'loading' ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            <Play className="h-5 w-5" />
          )}
        </button>
      )}

      {/* Stop */}
      <button
        onClick={onStop}
        disabled={!canInteract}
        className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive disabled:opacity-30"
        title="結束故事"
      >
        <Square className="h-4 w-4" />
      </button>

      {/* Microphone */}
      <button
        onClick={onToggleListening}
        disabled={!canInteract}
        className={cn(
          'rounded-full p-2 transition-all',
          isListening
            ? 'bg-red-100 text-red-600 ring-2 ring-red-300 dark:bg-red-950/50 dark:text-red-400'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground',
          !canInteract && 'opacity-30'
        )}
        title={isListening ? '關閉麥克風' : '開啟麥克風'}
      >
        {isListening ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
      </button>
    </div>
  )
}
