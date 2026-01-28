/**
 * Mode Switch
 * Feature: 010-magic-dj-controller
 *
 * T022: ModeSwitch component showing current mode (prerecorded/ai-conversation),
 * toggle button/indicator.
 */

import { Radio, Bot, Wifi, WifiOff } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'
import type { ConnectionStatus } from '@/types/interaction'

// =============================================================================
// Types
// =============================================================================

export interface ModeSwitchProps {
  onToggle: () => void
  wsStatus: ConnectionStatus
}

// =============================================================================
// Component
// =============================================================================

export function ModeSwitch({ onToggle, wsStatus }: ModeSwitchProps) {
  const { currentMode, isAIConnected } = useMagicDJStore()

  const isPrerecorded = currentMode === 'prerecorded'
  const isConnected = wsStatus === 'connected' || isAIConnected

  return (
    <div className="flex items-center gap-4">
      {/* Connection Status */}
      <div
        className={cn(
          'flex items-center gap-2 rounded-full px-3 py-1 text-sm',
          isConnected
            ? 'bg-green-100 text-green-700'
            : 'bg-muted text-muted-foreground'
        )}
      >
        {isConnected ? (
          <>
            <Wifi className="h-4 w-4" />
            <span>AI 已連線</span>
          </>
        ) : (
          <>
            <WifiOff className="h-4 w-4" />
            <span>AI 未連線</span>
          </>
        )}
      </div>

      {/* Mode Toggle */}
      <button
        onClick={onToggle}
        className={cn(
          'relative flex h-12 w-64 items-center rounded-full border-2 p-1 transition-all',
          'focus:outline-none focus:ring-4 focus:ring-primary/50'
        )}
      >
        {/* Background Indicator */}
        <div
          className={cn(
            'absolute h-10 w-1/2 rounded-full transition-all duration-300',
            isPrerecorded
              ? 'left-1 bg-amber-500'
              : 'left-[calc(50%-4px)] bg-blue-500'
          )}
        />

        {/* Prerecorded Option */}
        <div
          className={cn(
            'relative z-10 flex flex-1 items-center justify-center gap-2 text-sm font-medium transition-colors',
            isPrerecorded ? 'text-white' : 'text-muted-foreground'
          )}
        >
          <Radio className="h-4 w-4" />
          <span>預錄模式</span>
        </div>

        {/* AI Conversation Option */}
        <div
          className={cn(
            'relative z-10 flex flex-1 items-center justify-center gap-2 text-sm font-medium transition-colors',
            !isPrerecorded ? 'text-white' : 'text-muted-foreground'
          )}
        >
          <Bot className="h-4 w-4" />
          <span>AI 對話</span>
        </div>
      </button>

      {/* Hotkey hint */}
      <div className="text-sm text-muted-foreground">
        <kbd className="rounded bg-muted px-2 py-1">M</kbd>
      </div>
    </div>
  )
}

export default ModeSwitch
