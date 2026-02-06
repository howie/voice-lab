/**
 * DJ Control Panel
 * Feature: 010-magic-dj-controller
 * Feature: 015-magic-dj-ai-prompts
 *
 * T015, T021, T026, T031, T034, T035, T036, T045: Main control panel assembling
 * all US1-US4 components into cohesive layout with DJ-style interface.
 * 015-T014~T016, T019~T022: AI prompt template integration with four-column layout.
 */

import { ChannelBoard } from './ChannelBoard'
import { AIControlBar } from './AIControlBar'
import { PromptTemplatePanel } from './PromptTemplatePanel'
import { StoryPromptPanel } from './StoryPromptPanel'
import { ModeSwitch } from './ModeSwitch'
import { SessionTimer } from './SessionTimer'
import { ExportPanel } from './ExportPanel'
import { TrackConfigPanel } from './TrackConfigPanel'
import { PresetSelector } from './PresetSelector'
import { useMagicDJStore, selectIsAITimeout } from '@/stores/magicDJStore'
import type { ConnectionStatus } from '@/types/interaction'
import type { PromptTemplate, Track } from '@/types/magic-dj'

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
  /** Prompt template handlers (015) */
  onSendPromptTemplate?: (template: PromptTemplate) => void
  onSendStoryPrompt?: (text: string) => void
  onAddPromptTemplate?: () => void
  onEditPromptTemplate?: (template: PromptTemplate) => void
  onDeletePromptTemplate?: (template: PromptTemplate) => void
}

// =============================================================================
// Component
// =============================================================================

export function DJControlPanel({
  onForceSubmit,
  onInterrupt,
  onFillerSound,
  onRescueWait: _onRescueWait,
  onRescueEnd: _onRescueEnd,
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
  onSendPromptTemplate,
  onSendStoryPrompt,
  onAddPromptTemplate,
  onEditPromptTemplate,
  onDeletePromptTemplate,
}: DJControlPanelProps) {
  const { currentMode, isSessionActive, isWaitingForAI, settings } =
    useMagicDJStore()
  const promptTemplates = useMagicDJStore(s => s.promptTemplates)
  const storyPrompts = useMagicDJStore(s => s.storyPrompts)
  const lastSentPromptId = useMagicDJStore(s => s.lastSentPromptId)
  const isAITimeout = useMagicDJStore(selectIsAITimeout)
  const isAIConnected = wsStatus === 'connected'

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

      {/* AI Control Bar — only in AI conversation mode (015-T009) */}
      {currentMode === 'ai-conversation' && (
        <AIControlBar
          wsStatus={wsStatus}
          isSessionActive={isSessionActive}
          isWaitingForAI={isWaitingForAI}
          onForceSubmit={onForceSubmit}
          onInterrupt={onInterrupt}
          onFillerSound={onFillerSound}
          micVolume={micVolume}
          isListening={isListening}
          onToggleListening={onToggleListening}
        />
      )}

      {/* AI Timeout Warning Banner (T029) — CSS animation with reduced-motion support */}
      {isAITimeout && isWaitingForAI && (
        <div
          className="animate-timeout-pulse rounded-lg border-2 border-destructive bg-destructive/20 p-3 text-center font-bold text-destructive"
          role="alert"
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
        /* AI Conversation Mode: Prompt Templates + Story Prompts + SFX + Music (015-DD-001) */
        <div className="flex flex-1 min-h-0">
          <ChannelBoard
            aiMode
            leadingChannel={
              <>
                {/* Column 1: Prompt Templates */}
                {onSendPromptTemplate && (
                  <PromptTemplatePanel
                    templates={promptTemplates}
                    disabled={!isAIConnected}
                    lastSentPromptId={lastSentPromptId}
                    onSendPrompt={onSendPromptTemplate}
                    onAddTemplate={onAddPromptTemplate}
                    onEditTemplate={onEditPromptTemplate}
                    onDeleteTemplate={onDeletePromptTemplate}
                  />
                )}
                {/* Column 2: Story Prompts */}
                {onSendStoryPrompt && (
                  <StoryPromptPanel
                    storyPrompts={storyPrompts}
                    disabled={!isAIConnected}
                    onSendStoryPrompt={onSendStoryPrompt}
                  />
                )}
              </>
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
