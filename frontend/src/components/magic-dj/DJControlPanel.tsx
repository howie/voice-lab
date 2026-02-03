/**
 * DJ Control Panel
 * Feature: 010-magic-dj-controller
 *
 * T015, T021, T026, T031, T034, T035, T036, T045: Main control panel assembling
 * all US1-US4 components into cohesive layout with DJ-style interface.
 */

import { useEffect, useRef, useState } from 'react'

import { ChannelBoard } from './ChannelBoard'
import { AIVoiceChannelStrip } from './AIVoiceChannelStrip'
import { ModeSwitch } from './ModeSwitch'
import { SessionTimer } from './SessionTimer'
import { ExportPanel } from './ExportPanel'
import { TrackConfigPanel } from './TrackConfigPanel'
import { PresetSelector } from './PresetSelector'
import { useMagicDJStore, selectIsAITimeout } from '@/stores/magicDJStore'
import type { ConnectionStatus } from '@/types/interaction'
import type { Track } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface DJControlPanelProps {
  onForceSubmit: () => void
  onInterrupt: () => void
  onFillerSound: () => void
  onRescueWait: () => void
  onRescueEnd: () => void
  onToggleMode: () => void
  onPlayTrack: (trackId: string) => void
  onStopTrack: (trackId: string) => void
  onStartSession: () => void
  onStopSession: () => void
  onAddTrack?: () => void
  onGenerateBGM?: () => void
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
  wsStatus: ConnectionStatus
  /** Cue list handlers (US3) */
  onPlayNextCue?: () => void
  onRemoveFromCueList?: (cueItemId: string) => void
  onResetCueList?: () => void
  onClearCueList?: () => void
  /** Microphone audio input state (AI mode) */
  micVolume?: number
  isListening?: boolean
  onToggleListening?: () => void
}

// =============================================================================
// Component
// =============================================================================

export function DJControlPanel({
  onForceSubmit,
  onInterrupt,
  onFillerSound,
  onRescueWait,
  onRescueEnd,
  onToggleMode,
  onPlayTrack,
  onStopTrack,
  onStartSession,
  onStopSession,
  onAddTrack,
  onGenerateBGM,
  onEditTrack,
  onDeleteTrack,
  wsStatus,
  onPlayNextCue,
  onRemoveFromCueList,
  onResetCueList,
  onClearCueList,
  micVolume = 0,
  isListening = false,
  onToggleListening,
}: DJControlPanelProps) {
  const { currentMode, isSessionActive, isWaitingForAI, settings } =
    useMagicDJStore()
  const isAITimeout = useMagicDJStore(selectIsAITimeout)

  // AI timeout warning flash
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false)
  const timeoutIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Flash warning when AI timeout (T029)
  useEffect(() => {
    if (isAITimeout && isWaitingForAI) {
      // Start flashing
      timeoutIntervalRef.current = setInterval(() => {
        setShowTimeoutWarning((prev) => !prev)
      }, 500)
    } else {
      // Stop flashing
      if (timeoutIntervalRef.current) {
        clearInterval(timeoutIntervalRef.current)
        timeoutIntervalRef.current = null
      }
      setShowTimeoutWarning(false)
    }

    return () => {
      if (timeoutIntervalRef.current) {
        clearInterval(timeoutIntervalRef.current)
      }
    }
  }, [isAITimeout, isWaitingForAI])

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      {/* Header: Session Timer + Preset Selector + Mode Switch */}
      <div className="flex items-center justify-between rounded-lg border bg-card p-4">
        <div className="flex items-center gap-4">
          <SessionTimer
            onStartSession={onStartSession}
            onStopSession={onStopSession}
          />
          <PresetSelector />
        </div>

        <ModeSwitch onToggle={onToggleMode} wsStatus={wsStatus} />
      </div>

      {/* AI Timeout Warning Banner (T029) */}
      {isAITimeout && isWaitingForAI && (
        <div
          className={`rounded-lg border-2 p-3 text-center font-bold transition-colors ${
            showTimeoutWarning
              ? 'border-destructive bg-destructive/20 text-destructive'
              : 'border-yellow-500 bg-yellow-500/20 text-yellow-700'
          }`}
        >
          AI 回應超過 {settings.aiResponseTimeout} 秒！建議使用救場語音
        </div>
      )}

      {/* Main Control Area */}
      {currentMode === 'prerecorded' ? (
        /* Prerecorded Mode: 4-Channel Board + Sound Library + Cue List (DD-001, US3) */
        <div className="flex flex-1 min-h-0">
          <ChannelBoard
            onPlayTrack={onPlayTrack}
            onStopTrack={onStopTrack}
            onAddTrack={onAddTrack}
            onGenerateBGM={onGenerateBGM}
            onEditTrack={onEditTrack}
            onDeleteTrack={onDeleteTrack}
            showCueList
            onPlayNextCue={onPlayNextCue}
            onRemoveFromCueList={onRemoveFromCueList}
            onResetCueList={onResetCueList}
            onClearCueList={onClearCueList}
          />
        </div>
      ) : (
        /* AI Conversation Mode: AI Channel + 4 Channels + Sound Library (no CueList) */
        <div className="flex flex-1 min-h-0">
          <ChannelBoard
            leadingChannel={
              <AIVoiceChannelStrip
                wsStatus={wsStatus}
                isSessionActive={isSessionActive}
                isWaitingForAI={isWaitingForAI}
                isAITimeout={isAITimeout}
                onForceSubmit={onForceSubmit}
                onInterrupt={onInterrupt}
                onFillerSound={onFillerSound}
                onRescueWait={onRescueWait}
                onRescueEnd={onRescueEnd}
                micVolume={micVolume}
                isListening={isListening}
                onToggleListening={onToggleListening}
              />
            }
            onPlayTrack={onPlayTrack}
            onStopTrack={onStopTrack}
            onAddTrack={onAddTrack}
            onGenerateBGM={onGenerateBGM}
            onEditTrack={onEditTrack}
            onDeleteTrack={onDeleteTrack}
            showCueList={false}
          />
        </div>
      )}

      {/* Footer: Export Panels */}
      <div className="flex flex-col gap-4">
        {/* Track Config Export/Import (T055-T057) */}
        <div className="rounded-lg border bg-card p-4">
          <TrackConfigPanel />
        </div>

        {/* Session Export Panel (T045) */}
        <div className="rounded-lg border bg-card p-4">
          <ExportPanel />
        </div>
      </div>
    </div>
  )
}

export default DJControlPanel
