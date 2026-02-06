/**
 * Magic DJ Page
 * Feature: 010-magic-dj-controller
 *
 * T007: Main page container for Magic DJ Controller.
 * T018: Track preloading on mount.
 * Enhanced: Dynamic track management with TTS integration.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import { ConfirmDialog } from '@/components/magic-dj/ConfirmDialog'
import { DJControlPanel } from '@/components/magic-dj/DJControlPanel'
import { TrackEditorModal } from '@/components/magic-dj/TrackEditorModal'
import { BGMGeneratorModal } from '@/components/magic-dj/BGMGeneratorModal'
import { PromptTemplateEditor } from '@/components/magic-dj/PromptTemplateEditor'
import { StoryPromptEditor } from '@/components/magic-dj/StoryPromptEditor'
import { useMagicDJStore } from '@/stores/magicDJStore'
import { useAuthStore } from '@/stores/authStore'
import { useInteractionStore } from '@/stores/interactionStore'
import { useMultiTrackPlayer } from '@/hooks/useMultiTrackPlayer'
import { useAudioPlayback } from '@/hooks/useAudioPlayback'
import { useMagicDJModals } from '@/hooks/useMagicDJModals'
import { useConfirmDialog } from '@/hooks/useConfirmDialog'
import { useDJHotkeys } from '@/hooks/useDJHotkeys'
import { useCueList } from '@/hooks/useCueList'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useMicrophone } from '@/hooks/useMicrophone'
import { buildWebSocketUrl } from '@/services/interactionApi'
import type { PromptTemplate } from '@/types/magic-dj'

// =============================================================================
// Utilities
// =============================================================================

/** Convert Float32 audio samples to PCM16 ArrayBuffer */
function float32ToPCM16(input: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(input.length * 2)
  const view = new DataView(buffer)
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  return buffer
}

// =============================================================================
// Component
// =============================================================================

export function MagicDJPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [loadProgress, setLoadProgress] = useState(0)

  // Floating notification state with severity support
  type NotificationSeverity = 'info' | 'warning' | 'error'
  const [notification, setNotification] = useState<{ message: string; severity: NotificationSeverity } | null>(null)
  const notificationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showNotification = useCallback((message: string, durationMs = 3000, severity: NotificationSeverity = 'warning') => {
    if (notificationTimerRef.current) clearTimeout(notificationTimerRef.current)
    setNotification({ message, severity })
    notificationTimerRef.current = setTimeout(() => setNotification(null), durationMs)
  }, [])

  // Confirm dialog (replaces window.confirm)
  const { confirm, dialogProps: confirmDialogProps } = useConfirmDialog()

  // Stores
  const tracks = useMagicDJStore(s => s.tracks)
  const currentMode = useMagicDJStore(s => s.currentMode)
  const setMode = useMagicDJStore(s => s.setMode)
  const settings = useMagicDJStore(s => s.settings)
  const startSession = useMagicDJStore(s => s.startSession)
  const stopSession = useMagicDJStore(s => s.stopSession)
  const isSessionActive = useMagicDJStore(s => s.isSessionActive)
  const logOperation = useMagicDJStore(s => s.logOperation)
  const startAIWaiting = useMagicDJStore(s => s.startAIWaiting)
  const stopAIWaiting = useMagicDJStore(s => s.stopAIWaiting)
  const setAIConnected = useMagicDJStore(s => s.setAIConnected)
  const removeTrack = useMagicDJStore(s => s.removeTrack)
  const initializeStorage = useMagicDJStore(s => s.initializeStorage)

  // Prompt template store actions (015)
  const setLastSentPrompt = useMagicDJStore(s => s.setLastSentPrompt)

  // Interaction options for Gemini AI config
  const interactionOptions = useInteractionStore(s => s.options)

  // Multi-track player
  const {
    loadTracks,
    loadTrack,
    playTrack,
    stopTrack,
    stopAll,
    getLoadingProgress,
    unloadTrack,
    canPlayMore,
  } = useMultiTrackPlayer()

  // Modal management (Track Editor, BGM Generator, Prompt Template Editor)
  const {
    isEditorOpen,
    editingTrack,
    handleAddTrack,
    handleEditTrack,
    handleSaveTrack,
    handleCloseEditor,
    isBGMGeneratorOpen,
    handleOpenBGMGenerator,
    handleCloseBGMGenerator,
    handleSaveBGMTrack,
    isPromptEditorOpen,
    editingPromptTemplate,
    handleAddPromptTemplate,
    handleEditPromptTemplate,
    handleDeletePromptTemplate,
    handleSavePromptTemplate,
    handleClosePromptEditor,
    isStoryEditorOpen,
    editingStoryPrompt,
    handleAddStoryPrompt,
    handleEditStoryPrompt,
    handleDeleteStoryPrompt,
    handleSaveStoryPrompt,
    handleCloseStoryEditor,
  } = useMagicDJModals({ loadTrack, showNotification, confirm })

  // Cue List (US3)
  const {
    playNextCue,
    removeFromCueList,
    resetCuePosition,
    clearCueList,
    advanceCuePosition,
    currentItem: currentCueItem,
  } = useCueList()

  // Auth store for user ID
  const user = useAuthStore((state) => state.user)
  const userId = user?.id || '00000000-0000-0000-0000-000000000001'


  // AI audio playback (Gemini voice responses)
  const { queueAudioChunk, stop: stopAIAudio } = useAudioPlayback()

  // WebSocket for Gemini
  const wsUrl = buildWebSocketUrl('realtime', userId)

  const handleWSMessage = useCallback(
    (message: { type: string; data: unknown }) => {
      if (message.type === 'response_started') {
        stopAIWaiting()
      } else if (message.type === 'audio') {
        // Decode base64 PCM16 audio from Gemini and queue for playback
        const data = message.data as Record<string, unknown>
        if (data.audio) {
          try {
            const binaryString = atob(data.audio as string)
            const bytes = new Uint8Array(binaryString.length)
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i)
            }
            queueAudioChunk(bytes.buffer, 'pcm16')
          } catch (e) {
            console.error('Failed to decode AI audio:', e)
          }
        }
      } else if (message.type === 'response_ended') {
        // Response complete
      } else if (message.type === 'error') {
        console.error('WebSocket error:', message.data)
      }
    },
    [stopAIWaiting, queueAudioChunk]
  )

  const handleWSStatusChange = useCallback(
    (status: 'connected' | 'disconnected' | 'connecting' | 'error') => {
      setAIConnected(status === 'connected')
    },
    [setAIConnected]
  )

  const { status: wsStatus, connect, disconnect, sendMessage, sendBinary } = useWebSocket({
    url: wsUrl,
    autoConnect: false,
    onMessage: handleWSMessage,
    onStatusChange: handleWSStatusChange,
  })

  // === Microphone for AI mode ===

  const [micVolume, setMicVolume] = useState(0)
  const audioSampleRateLoggedRef = useRef(false)
  const configSentRef = useRef(false)

  const {
    isRecording: isListening,
    startRecording: startListening,
    stopRecording: stopListening,
  } = useMicrophone({
    onAudioChunk: (chunk: Float32Array, actualSampleRate: number) => {
      if (wsStatus !== 'connected' || !configSentRef.current) return

      if (!audioSampleRateLoggedRef.current) {
        console.log(`[MagicDJ Audio] Sample rate: ${actualSampleRate}Hz`)
        audioSampleRateLoggedRef.current = true
      }

      // Convert Float32 to PCM16
      const pcm16Buffer = float32ToPCM16(chunk)

      // Binary format: [4 bytes sample_rate (uint32 LE)] + [PCM16 audio data]
      const headerSize = 4
      const binaryMessage = new ArrayBuffer(headerSize + pcm16Buffer.byteLength)
      const view = new DataView(binaryMessage)
      view.setUint32(0, actualSampleRate, true)
      new Uint8Array(binaryMessage, headerSize).set(new Uint8Array(pcm16Buffer))

      sendBinary(binaryMessage)
    },
    onVolumeChange: (vol: number) => {
      setMicVolume(vol)
    },
  })

  // Send config message when WebSocket connects (must run before microphone starts)
  useEffect(() => {
    if (wsStatus !== 'connected') {
      configSentRef.current = false
      return
    }
    if (currentMode === 'ai-conversation' && !configSentRef.current) {
      sendMessage('config', {
        config: interactionOptions.providerConfig,
        system_prompt: interactionOptions.systemPrompt,
        lightweight_mode: true,
      })
      configSentRef.current = true
    }
  }, [wsStatus, currentMode, sendMessage, interactionOptions])

  // Auto-start listening when WebSocket connects in AI mode (after config sent)
  useEffect(() => {
    if (wsStatus === 'connected' && currentMode === 'ai-conversation' && !isListening && configSentRef.current) {
      startListening()
    }
  }, [wsStatus, currentMode, isListening, startListening])

  const handleToggleListening = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  // === Hotkey Actions ===

  const handleForceSubmit = useCallback(() => {
    if (currentMode !== 'ai-conversation') return

    // Log operation
    logOperation('force_submit')

    // Send end_turn to Gemini
    sendMessage('end_turn', {})

    // Start waiting timer
    startAIWaiting()

    // Auto-play filler sound if enabled
    if (settings.autoPlayFillerOnSubmit) {
      playTrack('sound_thinking')
      logOperation('play_filler')
    }
  }, [
    currentMode,
    logOperation,
    sendMessage,
    startAIWaiting,
    settings.autoPlayFillerOnSubmit,
    playTrack,
  ])

  const handleInterrupt = useCallback(() => {
    // Log operation
    logOperation('interrupt')

    // Send interrupt to Gemini
    sendMessage('interrupt', {})

    // Stop all tracks and AI audio playback
    stopAll()
    stopAIAudio()

    // Stop AI waiting
    stopAIWaiting()
  }, [logOperation, sendMessage, stopAll, stopAIAudio, stopAIWaiting])

  const handleFillerSound = useCallback(() => {
    playTrack('sound_thinking')
    logOperation('play_filler')
  }, [playTrack, logOperation])

  const handleRescueWait = useCallback(() => {
    // Stop AI and play rescue wait
    sendMessage('interrupt', {})
    stopAll()
    playTrack('filler_wait')
    logOperation('play_rescue_wait')
    stopAIWaiting()
  }, [sendMessage, stopAll, playTrack, logOperation, stopAIWaiting])

  const handleRescueEnd = useCallback(() => {
    // Stop AI and play rescue end
    sendMessage('interrupt', {})
    stopAll()
    playTrack('track_end')
    logOperation('play_rescue_end')
    stopAIWaiting()

    // Optionally end session
    if (isSessionActive) {
      stopSession()
    }
  }, [sendMessage, stopAll, playTrack, logOperation, stopAIWaiting, isSessionActive, stopSession])

  // === Prompt Template Handlers (015) ===

  const handleSendPromptTemplate = useCallback(
    (template: PromptTemplate) => {
      if (wsStatus !== 'connected') return
      sendMessage('text_input', { text: template.prompt })
      setLastSentPrompt(template.id)
      logOperation('send_prompt_template', { templateId: template.id, name: template.name })
    },
    [wsStatus, sendMessage, setLastSentPrompt, logOperation]
  )

  const handleSendStoryPrompt = useCallback(
    (text: string) => {
      if (wsStatus !== 'connected' || !text.trim()) return
      sendMessage('text_input', { text: text.trim() })
      logOperation('send_story_prompt', { text: text.trim().slice(0, 50) })
    },
    [wsStatus, sendMessage, logOperation]
  )

  const handleToggleMode = useCallback(() => {
    const newMode = currentMode === 'prerecorded' ? 'ai-conversation' : 'prerecorded'
    setMode(newMode)

    // Connect/maintain WebSocket connection
    if (newMode === 'ai-conversation' && wsStatus !== 'connected') {
      connect()
    }
  }, [currentMode, setMode, wsStatus, connect])

  const handlePlayTrack = useCallback(
    (trackId: string) => {
      if (!canPlayMore()) {
        showNotification('最多只能同時播放 5 個音軌')
        return
      }
      playTrack(trackId)
      logOperation('play_track', { trackId })
    },
    [playTrack, logOperation, canPlayMore, showNotification]
  )

  // === Cue List Handlers (US3) ===

  const handlePlayNextCue = useCallback(() => {
    const cueItem = playNextCue()
    if (cueItem) {
      playTrack(cueItem.trackId)
      logOperation('play_track', { trackId: cueItem.trackId, source: 'cue_list' })
    }
  }, [playNextCue, playTrack, logOperation])

  // Auto-advance: when current cue item finishes playing (T035)
  useEffect(() => {
    if (!currentCueItem || currentCueItem.status !== 'playing') return

    const trackState = useMagicDJStore.getState().trackStates[currentCueItem.trackId]
    if (trackState && !trackState.isPlaying && trackState.isLoaded) {
      // Track finished playing - advance position
      advanceCuePosition()
    }
  }, [currentCueItem, advanceCuePosition])

  // Handle hotkey track play (by index)
  const handleHotkeyPlayTrack = useCallback(
    (trackIndex: number) => {
      // Filter main tracks (same as TrackList does)
      const mainTracks = tracks.filter(
        (track) => track.type !== 'filler' && track.type !== 'rescue'
      )
      const trackId = mainTracks[trackIndex]?.id
      if (trackId) {
        handlePlayTrack(trackId)
      }
    },
    [tracks, handlePlayTrack]
  )

  // Register hotkeys
  useDJHotkeys({
    onForceSubmit: handleForceSubmit,
    onInterrupt: handleInterrupt,
    onFillerSound: handleFillerSound,
    onRescueWait: handleRescueWait,
    onRescueEnd: handleRescueEnd,
    onToggleMode: handleToggleMode,
    onPlayTrack: handleHotkeyPlayTrack,
    onPlayNextCue: handlePlayNextCue,
  })

  // === Track Preloading (T018) ===
  // onRehydrateStorage triggers initializeStorage() automatically after
  // Zustand rehydration. This effect ensures storage is ready (idempotent)
  // and then preloads all tracks into the Web Audio player.

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null
    let unmounted = false

    const initAndLoad = async () => {
      setIsLoading(true)

      // Always call initializeStorage — it is idempotent and handles:
      // 1. Opening IndexedDB (safe to call multiple times)
      // 2. Revoking stale blob URLs before creating fresh ones
      // 3. Restoring audio URLs from IndexedDB blobs
      // This is required on SPA re-navigation where blob URLs from a
      // previous mount may have been invalidated.
      await initializeStorage()

      if (unmounted) return

      // Get tracks with restored URLs (initializeStorage updated the store)
      const restoredTracks = useMagicDJStore.getState().tracks

      await loadTracks(restoredTracks)

      if (unmounted) return

      // Update progress periodically
      interval = setInterval(() => {
        if (unmounted) {
          if (interval) clearInterval(interval)
          return
        }
        const progress = getLoadingProgress()
        setLoadProgress(progress)

        if (progress >= 1) {
          if (interval) clearInterval(interval)
          interval = null
          setIsLoading(false)
        }
      }, 100)
    }

    initAndLoad()

    return () => {
      unmounted = true
      if (interval) clearInterval(interval)
      // Note: blob URLs are NOT revoked here — initializeStorage() handles
      // revoking stale URLs when it creates fresh ones on next mount.
      // Revoking here would invalidate URLs still stored in Zustand,
      // causing ERR_FILE_NOT_FOUND on SPA re-navigation.
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleDeleteTrack = useCallback(
    async (trackId: string) => {
      const confirmed = await confirm({
        title: '刪除音軌',
        message: '確定要刪除這個音軌嗎？',
        confirmLabel: '刪除',
      })
      if (confirmed) {
        unloadTrack(trackId)
        removeTrack(trackId)
      }
    },
    [unloadTrack, removeTrack, confirm]
  )

  // === Session Management ===

  const handleStartSession = useCallback(() => {
    startSession()
  }, [startSession])

  const handleStopSession = useCallback(() => {
    stopSession()
    stopAll()
    stopListening()
    disconnect()
  }, [stopSession, stopAll, stopListening, disconnect])

  // === Render ===

  if (isLoading) {
    return (
      <div className="flex h-full flex-col gap-4 p-4">
        {/* Skeleton header */}
        <div className="flex items-center justify-between rounded-lg border bg-card p-4">
          <div className="h-8 w-32 animate-pulse rounded bg-muted" />
          <div className="h-8 w-24 animate-pulse rounded bg-muted" />
        </div>
        {/* Skeleton track list */}
        <div className="flex flex-1 flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-3 rounded-lg border p-3"
            >
              <div className="h-8 w-8 animate-pulse rounded bg-muted" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                <div className="h-3 w-16 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
        {/* Loading progress */}
        <div className="flex flex-col items-center gap-2 py-2">
          <div className="h-2 w-64 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${loadProgress * 100}%` }}
            />
          </div>
          <div className="text-sm text-muted-foreground">
            載入音軌中... {Math.round(loadProgress * 100)}%
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Floating notification with severity */}
      {notification && (
        <div className="fixed top-4 left-1/2 z-50 -translate-x-1/2 animate-in fade-in slide-in-from-top-2 duration-200">
          <div
            className={`rounded-lg border px-4 py-2 text-sm font-medium shadow-lg backdrop-blur ${
              notification.severity === 'error'
                ? 'border-destructive/50 bg-destructive/15 text-destructive'
                : notification.severity === 'info'
                  ? 'border-blue-500/50 bg-blue-500/15 text-blue-700 dark:text-blue-400'
                  : 'border-yellow-500/50 bg-yellow-500/15 text-yellow-700 dark:text-yellow-400'
            }`}
            role="alert"
          >
            {notification.message}
          </div>
        </div>
      )}

      <DJControlPanel
        onForceSubmit={handleForceSubmit}
        onInterrupt={handleInterrupt}
        onFillerSound={handleFillerSound}
        onRescueWait={handleRescueWait}
        onRescueEnd={handleRescueEnd}
        onToggleMode={handleToggleMode}
        onPlayTrack={handlePlayTrack}
        onStopTrack={stopTrack}
        onStartSession={handleStartSession}
        onStopSession={handleStopSession}
        onAddTrack={handleAddTrack}
        onGenerateBGM={handleOpenBGMGenerator}
        onEditTrack={handleEditTrack}
        onDeleteTrack={handleDeleteTrack}
        wsStatus={wsStatus}
        onPlayNextCue={handlePlayNextCue}
        onRemoveFromCueList={removeFromCueList}
        onResetCueList={resetCuePosition}
        onClearCueList={clearCueList}
        micVolume={micVolume}
        isListening={isListening}
        onToggleListening={handleToggleListening}
        onSendPromptTemplate={handleSendPromptTemplate}
        onSendStoryPrompt={handleSendStoryPrompt}
        onAddPromptTemplate={handleAddPromptTemplate}
        onEditPromptTemplate={handleEditPromptTemplate}
        onDeletePromptTemplate={handleDeletePromptTemplate}
        onAddStoryPrompt={handleAddStoryPrompt}
        onEditStoryPrompt={handleEditStoryPrompt}
        onDeleteStoryPrompt={handleDeleteStoryPrompt}
      />

      {/* Track Editor Modal */}
      <TrackEditorModal
        isOpen={isEditorOpen}
        onClose={handleCloseEditor}
        onSave={handleSaveTrack}
        editingTrack={editingTrack}
        existingText={editingTrack?.textContent}
      />

      {/* BGM Generator Modal */}
      <BGMGeneratorModal
        isOpen={isBGMGeneratorOpen}
        onClose={handleCloseBGMGenerator}
        onSave={handleSaveBGMTrack}
      />

      {/* Prompt Template Editor Modal (015) */}
      <PromptTemplateEditor
        isOpen={isPromptEditorOpen}
        onClose={handleClosePromptEditor}
        onSave={handleSavePromptTemplate}
        editingTemplate={editingPromptTemplate}
      />

      {/* Story Prompt Editor Modal */}
      <StoryPromptEditor
        isOpen={isStoryEditorOpen}
        onClose={handleCloseStoryEditor}
        onSave={handleSaveStoryPrompt}
        editingPrompt={editingStoryPrompt}
      />

      {/* Confirm Dialog (replaces window.confirm) */}
      <ConfirmDialog {...confirmDialogProps} />
    </div>
  )
}

export default MagicDJPage
