/**
 * AI Voice Channel Strip Component
 * Feature: 010-magic-dj-controller
 *
 * A channel strip for AI real-time voice controls.
 * Visually consistent with ChannelStrip (w-48, border, bg-card, header/footer)
 * but contains AI control buttons and a microphone audio visualizer.
 */

import {
  Send,
  StopCircle,
  AudioLines,
  Clock,
  XCircle,
  Mic,
  MicOff,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { AudioVisualizer } from '@/components/interaction/AudioVisualizer'
import type { ConnectionStatus } from '@/types/interaction'

// =============================================================================
// Types
// =============================================================================

export interface AIVoiceChannelStripProps {
  wsStatus: ConnectionStatus
  isSessionActive: boolean
  isWaitingForAI: boolean
  isAITimeout: boolean
  onForceSubmit: () => void
  onInterrupt: () => void
  onFillerSound: () => void
  onRescueWait: () => void
  onRescueEnd: () => void
  /** Microphone volume level (0-1) */
  micVolume?: number
  /** Whether the microphone is actively capturing audio */
  isListening?: boolean
  /** Toggle microphone on/off */
  onToggleListening?: () => void
}

// =============================================================================
// Helpers
// =============================================================================

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

// =============================================================================
// Component
// =============================================================================

export function AIVoiceChannelStrip({
  wsStatus,
  isSessionActive,
  isWaitingForAI,
  isAITimeout,
  onForceSubmit,
  onInterrupt,
  onFillerSound,
  onRescueWait,
  onRescueEnd,
  micVolume = 0,
  isListening = false,
  onToggleListening,
}: AIVoiceChannelStripProps) {
  const isConnected = wsStatus === 'connected'
  const canControl = isSessionActive && isConnected

  return (
    <div className="flex h-full w-48 shrink-0 flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="border-b p-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">AI 即時語音</h3>
          <StatusDot status={wsStatus} />
        </div>
        <p className="text-xs text-muted-foreground">Gemini Realtime</p>
      </div>

      {/* Audio Input Indicator */}
      <div className="border-b px-2 py-2">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-muted-foreground">
            {isListening ? '收音中' : '未收音'}
          </span>
          {onToggleListening && (
            <button
              onClick={onToggleListening}
              disabled={!isConnected}
              className={cn(
                'flex h-6 w-6 items-center justify-center rounded-full transition-colors',
                !isConnected
                  ? 'cursor-not-allowed bg-muted text-muted-foreground'
                  : isListening
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80',
              )}
              title={isListening ? '關閉麥克風' : '開啟麥克風'}
            >
              {isListening ? (
                <Mic className="h-3.5 w-3.5" />
              ) : (
                <MicOff className="h-3.5 w-3.5" />
              )}
            </button>
          )}
        </div>
        <AudioVisualizer
          level={micVolume}
          isActive={isListening}
          mode="bars"
          barCount={16}
          height={32}
          activeColor="#22c55e"
          inactiveColor="#6B7280"
          backgroundColor="transparent"
        />
      </div>

      {/* Main Controls */}
      <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-2">
        {/* Force Submit */}
        <button
          onClick={onForceSubmit}
          disabled={!canControl}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            !canControl
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : isWaitingForAI
                ? 'animate-pulse bg-blue-500 text-white'
                : 'bg-blue-500/10 text-blue-700 hover:bg-blue-500/20 active:scale-[0.97]',
          )}
        >
          <Send className="h-4 w-4 shrink-0" />
          <span className="truncate">強制送出</span>
        </button>

        {/* Interrupt */}
        <button
          onClick={onInterrupt}
          disabled={!isSessionActive}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            !isSessionActive
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-orange-500/10 text-orange-700 hover:bg-orange-500/20 active:scale-[0.97]',
          )}
        >
          <StopCircle className="h-4 w-4 shrink-0" />
          <span className="truncate">中斷 AI</span>
        </button>

        {/* Filler Sound */}
        <button
          onClick={onFillerSound}
          disabled={!isSessionActive}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            !isSessionActive
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-purple-500/10 text-purple-700 hover:bg-purple-500/20 active:scale-[0.97]',
          )}
        >
          <AudioLines className="h-4 w-4 shrink-0" />
          <span className="truncate">思考音效</span>
        </button>

        {/* Rescue Section Divider */}
        <div className="my-1 flex items-center gap-2">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs text-muted-foreground">救場</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        {/* Rescue: Wait */}
        <button
          onClick={onRescueWait}
          disabled={!isSessionActive}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            !isSessionActive
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : isAITimeout
                ? 'animate-pulse bg-yellow-500/20 text-yellow-700'
                : 'bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20 active:scale-[0.97]',
          )}
        >
          <Clock className="h-4 w-4 shrink-0" />
          <span className="truncate">等待填補</span>
        </button>

        {/* Rescue: Emergency End */}
        <button
          onClick={onRescueEnd}
          disabled={!isSessionActive}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
            !isSessionActive
              ? 'cursor-not-allowed bg-muted text-muted-foreground'
              : 'bg-red-500/10 text-red-700 hover:bg-red-500/20 active:scale-[0.97]',
          )}
        >
          <XCircle className="h-4 w-4 shrink-0" />
          <span className="truncate">緊急結束</span>
        </button>
      </div>

      {/* Footer: Hotkey Hints */}
      <div className="border-t p-2">
        <div className="grid grid-cols-2 gap-1 text-[10px] text-muted-foreground">
          <div>
            <kbd className="rounded bg-muted px-1 py-0.5">Space</kbd> 送出
          </div>
          <div>
            <kbd className="rounded bg-muted px-1 py-0.5">Esc</kbd> 中斷
          </div>
          <div>
            <kbd className="rounded bg-muted px-1 py-0.5">F</kbd> 音效
          </div>
          <div>
            <kbd className="rounded bg-muted px-1 py-0.5">W</kbd> 等待
          </div>
          <div>
            <kbd className="rounded bg-muted px-1 py-0.5">E</kbd> 結束
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIVoiceChannelStrip
