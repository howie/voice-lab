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
import { useMagicDJStore } from '@/stores/magicDJStore'
import { useAuthStore } from '@/stores/authStore'
import { useMultiTrackPlayer } from '@/hooks/useMultiTrackPlayer'
import { useDJHotkeys } from '@/hooks/useDJHotkeys'
import { useCueList } from '@/hooks/useCueList'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useMicrophone } from '@/hooks/useMicrophone'
import { buildWebSocketUrl } from '@/services/interactionApi'
import type { Track } from '@/types/magic-dj'

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

  // Stores
  const {
    tracks,
    currentMode,
    setMode,
    settings,
    startSession,
    stopSession,
    isSessionActive,
    logOperation,
    startAIWaiting,
    stopAIWaiting,
    setAIConnected,
    addTrack,
    removeTrack,
    updateTrack,
  } = useMagicDJStore()

  // Note: interactionOptions available for future Gemini integration
  // const { options: interactionOptions } = useInteractionStore()

  // Multi-track player
  const {
    loadTracks,
    loadTrack,
    playTrack,
    stopTrack,
    stopAll,
    getLoadingProgress,
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

  const {
    isRecording: isListening,
    startRecording: startListening,
    stopRecording: stopListening,
  } = useMicrophone({
    onAudioChunk: (chunk: Float32Array, actualSampleRate: number) => {
      if (wsStatus !== 'connected') return

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

  // Auto-start listening when WebSocket connects in AI mode
  useEffect(() => {
    if (wsStatus === 'connected' && currentMode === 'ai-conversation' && !isListening) {
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

  useEffect(() => {
    const loadAllTracks = async () => {
      setIsLoading(true)

      await loadTracks(tracks)

      // Update progress periodically
      const interval = setInterval(() => {
        const progress = getLoadingProgress()
        setLoadProgress(progress)

        if (progress >= 1) {
          clearInterval(interval)
          setIsLoading(false)
        }
      }, 100)

      // Cleanup
      return () => clearInterval(interval)
    }

    loadAllTracks()
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
        removeTrack(trackId)
      }
    },
    [removeTrack]
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

      if (editingTrack) {
        // Update existing track
        updateTrack(track.id, {
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
        })

        // Reload the track in the player
        await loadTrack({
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
        })
      } else {
        // Add new track
        const newTrack: Track = {
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
        }
        addTrack(newTrack)

        // Load the new track in the player
        await loadTrack(newTrack)
      }
    },
    [editingTrack, updateTrack, addTrack, loadTrack]
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

      // Add new BGM track
      const newTrack: Track = {
        ...track,
        url: blobUrl,
        isCustom: true,
        audioBase64,
      }
      addTrack(newTrack)

      // Load the new track in the player
      await loadTrack(newTrack)
    },
    [addTrack, loadTrack]
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
    </div>
  )
}

export default MagicDJPage
