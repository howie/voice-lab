/**
 * Magic DJ Page
 * Feature: 010-magic-dj-controller
 *
 * T007: Main page container for Magic DJ Controller.
 * T018: Track preloading on mount.
 * Enhanced: Dynamic track management with TTS integration.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import { DJControlPanel } from '@/components/magic-dj/DJControlPanel'
import { TrackEditorModal } from '@/components/magic-dj/TrackEditorModal'
import { BGMGeneratorModal } from '@/components/magic-dj/BGMGeneratorModal'
import { PromptTemplateEditor } from '@/components/magic-dj/PromptTemplateEditor'
import { useMagicDJStore } from '@/stores/magicDJStore'
import { useAuthStore } from '@/stores/authStore'
import { useInteractionStore } from '@/stores/interactionStore'
import { useMultiTrackPlayer } from '@/hooks/useMultiTrackPlayer'
import { useDJHotkeys } from '@/hooks/useDJHotkeys'
import { useCueList } from '@/hooks/useCueList'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useMicrophone } from '@/hooks/useMicrophone'
import { buildWebSocketUrl } from '@/services/interactionApi'
import type { PromptTemplate, PromptTemplateColor, Track } from '@/types/magic-dj'

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

  // Track Editor Modal state
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [editingTrack, setEditingTrack] = useState<Track | null>(null)

  // BGM Generator Modal state
  const [isBGMGeneratorOpen, setIsBGMGeneratorOpen] = useState(false)

  // Prompt Template Editor Modal state (015)
  const [isPromptEditorOpen, setIsPromptEditorOpen] = useState(false)
  const [editingPromptTemplate, setEditingPromptTemplate] = useState<PromptTemplate | null>(null)

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
  const addTrack = useMagicDJStore(s => s.addTrack)
  const removeTrack = useMagicDJStore(s => s.removeTrack)
  const updateTrack = useMagicDJStore(s => s.updateTrack)
  const initializeStorage = useMagicDJStore(s => s.initializeStorage)
  const saveAudioToStorage = useMagicDJStore(s => s.saveAudioToStorage)

  // Prompt template store actions (015)
  const setLastSentPrompt = useMagicDJStore(s => s.setLastSentPrompt)
  const addPromptTemplate = useMagicDJStore(s => s.addPromptTemplate)
  const updatePromptTemplate = useMagicDJStore(s => s.updatePromptTemplate)
  const removePromptTemplate = useMagicDJStore(s => s.removePromptTemplate)

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
  } = useMultiTrackPlayer()

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


  // WebSocket for Gemini
  const wsUrl = buildWebSocketUrl('realtime', userId)

  const handleWSMessage = useCallback(
    (message: { type: string; data: unknown }) => {
      if (message.type === 'response_started') {
        stopAIWaiting()
      } else if (message.type === 'response_ended') {
        // Response complete
      } else if (message.type === 'error') {
        console.error('WebSocket error:', message.data)
      }
    },
    [stopAIWaiting]
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

    // Stop all tracks
    stopAll()

    // Stop AI waiting
    stopAIWaiting()
  }, [logOperation, sendMessage, stopAll, stopAIWaiting])

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

  const handleAddPromptTemplate = useCallback(() => {
    setEditingPromptTemplate(null)
    setIsPromptEditorOpen(true)
  }, [])

  const handleEditPromptTemplate = useCallback((template: PromptTemplate) => {
    setEditingPromptTemplate(template)
    setIsPromptEditorOpen(true)
  }, [])

  const handleDeletePromptTemplate = useCallback(
    (template: PromptTemplate) => {
      if (template.isDefault) return
      if (confirm(`確定要刪除「${template.name}」嗎？`)) {
        removePromptTemplate(template.id)
      }
    },
    [removePromptTemplate]
  )

  const handleSavePromptTemplate = useCallback(
    (data: { name: string; prompt: string; color: PromptTemplateColor }) => {
      if (editingPromptTemplate) {
        updatePromptTemplate(editingPromptTemplate.id, data)
      } else {
        addPromptTemplate({
          name: data.name,
          prompt: data.prompt,
          color: data.color,
          order: useMagicDJStore.getState().promptTemplates.length + 1,
          isDefault: false,
        })
      }
    },
    [editingPromptTemplate, updatePromptTemplate, addPromptTemplate]
  )

  const handleClosePromptEditor = useCallback(() => {
    setIsPromptEditorOpen(false)
    setEditingPromptTemplate(null)
  }, [])

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
      playTrack(trackId)
      logOperation('play_track', { trackId })
    },
    [playTrack, logOperation]
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

    const initAndLoad = async () => {
      setIsLoading(true)

      // Ensure storage is initialized (idempotent — may already be done
      // by onRehydrateStorage, but safe to call again on SPA re-navigation)
      if (!useMagicDJStore.getState().isStorageReady) {
        await initializeStorage()
      }

      // Get tracks with restored URLs (initializeStorage updated the store)
      const restoredTracks = useMagicDJStore.getState().tracks

      await loadTracks(restoredTracks)

      // Update progress periodically
      interval = setInterval(() => {
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
      if (interval) clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // === Track Editor Handlers ===

  const handleAddTrack = useCallback(() => {
    setEditingTrack(null)
    setIsEditorOpen(true)
  }, [])

  const handleEditTrack = useCallback((track: Track) => {
    setEditingTrack(track)
    setIsEditorOpen(true)
  }, [])

  const handleDeleteTrack = useCallback(
    (trackId: string) => {
      if (confirm('確定要刪除這個音軌嗎？')) {
        unloadTrack(trackId)
        removeTrack(trackId)
      }
    },
    [unloadTrack, removeTrack]
  )

  const handleSaveTrack = useCallback(
    async (track: Track, audioBlob: Blob) => {
      // Create blob URL for the audio (for immediate playback)
      const blobUrl = URL.createObjectURL(audioBlob)

      // Convert blob to base64 for localStorage persistence
      const arrayBuffer = await audioBlob.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)
      let binary = ''
      for (let i = 0; i < uint8Array.length; i++) {
        binary += String.fromCharCode(uint8Array[i])
      }
      const audioBase64 = `data:${audioBlob.type || 'audio/mpeg'};base64,${btoa(binary)}`

      // Persist audio to IndexedDB so it survives page reloads
      await saveAudioToStorage(track.id, audioBlob)

      if (editingTrack) {
        // Update existing track
        updateTrack(track.id, {
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
          hasLocalAudio: true,
        })

        // Reload the track in the player
        await loadTrack({
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
          hasLocalAudio: true,
        })
      } else {
        // Add new track — set hasLocalAudio directly so addTrack persists it
        // in a single atomic state update (no separate updateTrack needed)
        const newTrack: Track = {
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
          hasLocalAudio: true,
        }
        addTrack(newTrack)

        // Load the new track in the player
        await loadTrack(newTrack)
      }
    },
    [editingTrack, updateTrack, addTrack, loadTrack, saveAudioToStorage]
  )

  const handleCloseEditor = useCallback(() => {
    setIsEditorOpen(false)
    setEditingTrack(null)
  }, [])

  // === BGM Generator Handlers ===

  const handleOpenBGMGenerator = useCallback(() => {
    setIsBGMGeneratorOpen(true)
  }, [])

  const handleCloseBGMGenerator = useCallback(() => {
    setIsBGMGeneratorOpen(false)
  }, [])

  const handleSaveBGMTrack = useCallback(
    async (track: Track, audioBlob: Blob) => {
      // Create blob URL for the audio (for immediate playback)
      const blobUrl = URL.createObjectURL(audioBlob)

      // Convert blob to base64 for localStorage persistence
      const arrayBuffer = await audioBlob.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)
      let binary = ''
      for (let i = 0; i < uint8Array.length; i++) {
        binary += String.fromCharCode(uint8Array[i])
      }
      const audioBase64 = `data:${audioBlob.type || 'audio/mpeg'};base64,${btoa(binary)}`

      // Persist audio to IndexedDB so it survives page reloads
      await saveAudioToStorage(track.id, audioBlob)

      // Add new BGM track
      const newTrack: Track = {
        ...track,
        url: blobUrl,
        isCustom: true,
        audioBase64,
      }
      addTrack(newTrack)
      // Mark hasLocalAudio after addTrack (addTrack only sets it for source=upload)
      updateTrack(track.id, { hasLocalAudio: true })

      // Load the new track in the player
      await loadTrack(newTrack)
    },
    [addTrack, loadTrack, saveAudioToStorage, updateTrack]
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
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <div className="text-lg font-medium">載入音軌中...</div>
        <div className="h-2 w-64 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${loadProgress * 100}%` }}
          />
        </div>
        <div className="text-sm text-muted-foreground">
          {Math.round(loadProgress * 100)}%
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
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
    </div>
  )
}

export default MagicDJPage
