/**
 * DJ Control Panel
 * Feature: 010-magic-dj-controller
 *
 * T015, T021, T026, T031, T034, T035, T036, T045: Main control panel assembling
 * all US1-US4 components into cohesive layout with DJ-style interface.
 */

import { useEffect, useRef, useState } from 'react'

import { ForceSubmitButton } from './ForceSubmitButton'
import { InterruptButton } from './InterruptButton'
import { FillerSoundTrigger } from './FillerSoundTrigger'
import { TrackList } from './TrackList'
import { ModeSwitch } from './ModeSwitch'
import { RescuePanel } from './RescuePanel'
import { SessionTimer } from './SessionTimer'
import { ExportPanel } from './ExportPanel'
import { TrackConfigPanel } from './TrackConfigPanel'
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
  onEditTrack?: (track: Track) => void
  onDeleteTrack?: (trackId: string) => void
  wsStatus: ConnectionStatus
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
  onEditTrack,
  onDeleteTrack,
  wsStatus,
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
      {/* Header: Session Timer + Mode Switch */}
      <div className="flex items-center justify-between rounded-lg border bg-card p-4">
        <SessionTimer
          onStartSession={onStartSession}
          onStopSession={onStopSession}
        />

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
      <div className="flex flex-1 gap-4">
        {/* Left: Track List */}
        <div className="w-80 shrink-0 rounded-lg border bg-card p-4 overflow-y-auto">
          <h2 className="mb-4 text-lg font-semibold">音軌列表</h2>
          <TrackList
            onPlayTrack={onPlayTrack}
            onStopTrack={onStopTrack}
            onAddTrack={onAddTrack}
            onEditTrack={onEditTrack}
            onDeleteTrack={onDeleteTrack}
          />
        </div>

        {/* Center: Main Controls */}
        <div className="flex flex-1 flex-col gap-4">
          {/* AI Control Buttons */}
          {currentMode === 'ai-conversation' && (
            <div className="rounded-lg border bg-card p-4">
              <h2 className="mb-4 text-lg font-semibold">AI 控制</h2>
              <div className="flex flex-wrap gap-4">
                <ForceSubmitButton
                  onClick={onForceSubmit}
                  disabled={!isSessionActive || wsStatus !== 'connected'}
                />
                <InterruptButton
                  onClick={onInterrupt}
                  disabled={!isSessionActive}
                />
                <FillerSoundTrigger
                  onClick={onFillerSound}
                  disabled={!isSessionActive}
                />
              </div>
            </div>
          )}

          {/* Rescue Panel */}
          <div className="rounded-lg border bg-card p-4">
            <h2 className="mb-4 text-lg font-semibold">救場語音</h2>
            <RescuePanel
              onRescueWait={onRescueWait}
              onRescueEnd={onRescueEnd}
              isAITimeout={isAITimeout}
              disabled={!isSessionActive}
              onEditRescue={onEditTrack}
            />
          </div>

          {/* Keyboard Shortcuts Reference (T037) */}
          <div className="rounded-lg border bg-muted/50 p-4">
            <h3 className="mb-2 text-sm font-medium text-muted-foreground">
              快捷鍵
            </h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <kbd className="rounded bg-muted px-2 py-1">Space</kbd> 強制送出
              </div>
              <div>
                <kbd className="rounded bg-muted px-2 py-1">Esc</kbd> 中斷 AI
              </div>
              <div>
                <kbd className="rounded bg-muted px-2 py-1">M</kbd> 切換模式
              </div>
              <div>
                <kbd className="rounded bg-muted px-2 py-1">F</kbd> 思考音效
              </div>
              <div>
                <kbd className="rounded bg-muted px-2 py-1">W</kbd> 等待填補
              </div>
              <div>
                <kbd className="rounded bg-muted px-2 py-1">E</kbd> 緊急結束
              </div>
              <div>
                <kbd className="rounded bg-muted px-2 py-1">1-5</kbd> 播放音軌
              </div>
            </div>
          </div>
        </div>
      </div>

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
