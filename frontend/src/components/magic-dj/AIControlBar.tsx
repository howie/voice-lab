/**
 * AI Control Bar Component
 * Feature: 015-magic-dj-ai-prompts (T009)
 *
 * Horizontal control bar for AI mode header: mic toggle, connection status,
 * interrupt, force submit, filler sound. Extracted from AIVoiceChannelStrip.
 */

import {
  Send,
  StopCircle,
  AudioLines,
  Mic,
  MicOff,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { AudioVisualizer } from '@/components/interaction/AudioVisualizer'
import type { ConnectionStatus } from '@/types/interaction'

export interface AIControlBarProps {
  wsStatus: ConnectionStatus
  isSessionActive: boolean
  isWaitingForAI: boolean
  onForceSubmit: () => void
  onInterrupt: () => void
  onFillerSound: () => void
  micVolume?: number
  isListening?: boolean
  onToggleListening?: () => void
}

function StatusDot({ status }: { status: ConnectionStatus }) {
  return (
    <span
      className={cn(
        'inline-block h-2.5 w-2.5 rounded-full',
        status === 'connected' && 'bg-green-500',
        status === 'connecting' && 'animate-pulse bg-yellow-500',
        status === 'disconnected' && 'bg-gray-400',
        status === 'error' && 'bg-red-500',
      )}
      title={
        status === 'connected'
          ? '已連線'
          : status === 'connecting'
            ? '連線中...'
            : status === 'error'
              ? '連線錯誤'
              : '未連線'
      }
    />
  )
}

export function AIControlBar({
  wsStatus,
  isSessionActive,
  isWaitingForAI,
  onForceSubmit,
  onInterrupt,
  onFillerSound,
  micVolume = 0,
  isListening = false,
  onToggleListening,
}: AIControlBarProps) {
  const isConnected = wsStatus === 'connected'
  const canControl = isSessionActive && isConnected

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card px-4 py-2">
      {/* Connection Status */}
      <div className="flex items-center gap-2">
        <StatusDot status={wsStatus} />
        <span className="text-xs text-muted-foreground">
          {isConnected ? 'AI 已連線' : 'AI 未連線'}
        </span>
      </div>

      {/* Mic Toggle + Visualizer */}
      <div className="flex items-center gap-2 border-l pl-3">
        {onToggleListening && (
          <button
            onClick={onToggleListening}
            disabled={!isConnected}
            className={cn(
              'flex h-8 w-8 items-center justify-center rounded-full transition-colors',
              !isConnected
                ? 'cursor-not-allowed bg-muted text-muted-foreground'
                : isListening
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80',
            )}
            title={isListening ? '關閉麥克風' : '開啟麥克風'}
          >
            {isListening ? (
              <Mic className="h-4 w-4" />
            ) : (
              <MicOff className="h-4 w-4" />
            )}
          </button>
        )}
        <div className="w-24">
          <AudioVisualizer
            level={micVolume}
            isActive={isListening}
            mode="bars"
            barCount={12}
            height={24}
            activeColor="#22c55e"
            inactiveColor="#6B7280"
            backgroundColor="transparent"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2 border-l pl-3">
        {/* Force Submit */}
        <button
          onClick={onForceSubmit}
          disabled={!canControl}
          className={cn(
            'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            !canControl
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : isWaitingForAI
                ? 'animate-pulse bg-blue-500 text-white'
                : 'bg-blue-500/10 text-blue-700 hover:bg-blue-500/20 active:scale-[0.97]',
          )}
        >
          <Send className="h-3.5 w-3.5" />
          送出
        </button>

        {/* Interrupt */}
        <button
          onClick={onInterrupt}
          disabled={!isSessionActive}
          className={cn(
            'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            !isSessionActive
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-orange-500/10 text-orange-700 hover:bg-orange-500/20 active:scale-[0.97]',
          )}
        >
          <StopCircle className="h-3.5 w-3.5" />
          中斷
        </button>

        {/* Filler Sound */}
        <button
          onClick={onFillerSound}
          disabled={!isSessionActive}
          className={cn(
            'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
            !isSessionActive
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-purple-500/10 text-purple-700 hover:bg-purple-500/20 active:scale-[0.97]',
          )}
        >
          <AudioLines className="h-3.5 w-3.5" />
          思考音效
        </button>
      </div>

      {/* Hotkey Hints */}
      <div className="ml-auto flex items-center gap-3 text-[10px] text-muted-foreground">
        <span><kbd className="rounded bg-muted px-1 py-0.5">Space</kbd> 送出</span>
        <span><kbd className="rounded bg-muted px-1 py-0.5">Esc</kbd> 中斷</span>
      </div>
    </div>
  )
}

export default AIControlBar
