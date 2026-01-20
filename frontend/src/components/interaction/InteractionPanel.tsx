/**
 * InteractionPanel Component
 * Feature: 004-interaction-module
 * T037: Main component for real-time voice interaction.
 *
 * Integrates microphone input, audio playback, transcripts, and status indicators.
 */

import { useEffect, useCallback, useState, useRef } from 'react'

import { AudioVisualizer } from './AudioVisualizer'
import { ModeSelector } from './ModeSelector'

import { useInteractionStore } from '@/stores/interactionStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useMicrophone } from '@/hooks/useMicrophone'
import { useAudioPlayback } from '@/hooks/useAudioPlayback'
import type { ConnectionStatus, InteractionState, WSMessage } from '@/types/interaction'

interface InteractionPanelProps {
  /** User ID for the session */
  userId: string
  /** WebSocket URL for interaction */
  wsUrl?: string
  /** Additional CSS classes */
  className?: string
}

// Combined status for UI display
type DisplayStatus = 'idle' | 'connecting' | 'ready' | 'listening' | 'processing' | 'speaking' | 'error'

// Status indicator component
function StatusIndicator({
  connectionStatus,
  interactionState,
}: {
  connectionStatus: ConnectionStatus
  interactionState: InteractionState
}) {
  // Map connection status and interaction state to display status
  const getDisplayStatus = (): DisplayStatus => {
    if (connectionStatus === 'error') return 'error'
    if (connectionStatus === 'connecting') return 'connecting'
    if (connectionStatus === 'disconnected') return 'idle'
    // Connected - use interaction state
    return interactionState as DisplayStatus
  }

  const displayStatus = getDisplayStatus()

  const statusConfig: Record<DisplayStatus, { label: string; color: string; pulse: boolean }> = {
    idle: { label: '閒置', color: 'bg-gray-400', pulse: false },
    connecting: { label: '連接中...', color: 'bg-yellow-400', pulse: true },
    ready: { label: '已連線', color: 'bg-green-400', pulse: false },
    listening: { label: '聆聽中', color: 'bg-green-400', pulse: true },
    processing: { label: '處理中', color: 'bg-blue-400', pulse: true },
    speaking: { label: 'AI 回應中', color: 'bg-purple-400', pulse: true },
    error: { label: '錯誤', color: 'bg-red-400', pulse: false },
  }

  const config = statusConfig[displayStatus]

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-3 w-3">
        {config.pulse && (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full ${config.color} opacity-75`}
          />
        )}
        <span className={`relative inline-flex h-3 w-3 rounded-full ${config.color}`} />
      </span>
      <span className="text-sm text-muted-foreground">{config.label}</span>
    </div>
  )
}

// Helper to convert Float32 audio to PCM16 ArrayBuffer
function float32ToPCM16(input: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(input.length * 2)
  const view = new DataView(buffer)
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  return buffer
}

export function InteractionPanel({ userId, wsUrl, className = '' }: InteractionPanelProps) {
  const [permissionError, setPermissionError] = useState<string | null>(null)

  // Ref to track if we're in the connecting phase
  const isConnectingRef = useRef(false)

  // Store state
  const {
    connectionStatus,
    interactionState,
    options,
    userTranscript,
    aiResponseText,
    isRecording,
    inputVolume,
    currentLatency,
    error,
    setConnectionStatus,
    setInteractionState,
    setSession,
    setUserTranscript,
    appendAIResponse,
    clearTranscripts,
    setIsRecording,
    setInputVolume,
    setCurrentLatency,
    setMode,
    setProviderConfig,
    setError,
    resetSession,
  } = useInteractionStore()

  // Determine WebSocket URL
  const resolvedWsUrl =
    wsUrl ||
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/interaction/ws/${options.mode}`

  // Audio playback hook - must be before handleMessage which uses queueAudioChunk
  const { queueAudioChunk, stop: stopAudio } = useAudioPlayback({
    onPlaybackEnd: () => {
      // Audio playback ended - state already managed by response_ended message
    },
  })

  // WebSocket message handler
  const handleMessage = useCallback(
    (message: WSMessage) => {
      const { type } = message
      // Cast data to Record for easier access - actual type checking done per case
      const data = message.data as Record<string, unknown>

      switch (type) {
        case 'connected':
          if (data.session_id) {
            const now = new Date().toISOString()
            // Create minimal session object - full details come from API
            setSession({
              id: data.session_id as string,
              user_id: userId,
              mode: options.mode,
              provider_config: options.providerConfig,
              system_prompt: options.systemPrompt || '',
              status: 'active',
              started_at: now,
              ended_at: null,
              created_at: now,
              updated_at: now,
            })
            setInteractionState('listening')
            isConnectingRef.current = false
          }
          break

        case 'speech_started':
          setInteractionState('listening')
          clearTranscripts()
          break

        case 'speech_ended':
          setInteractionState('processing')
          break

        case 'transcript':
          setUserTranscript(data.text as string, data.is_final as boolean)
          break

        case 'response_started':
          setInteractionState('speaking')
          break

        case 'text_delta':
          // Handle both 'delta' and 'text' field names for compatibility
          appendAIResponse((data.delta as string) || (data.text as string) || '')
          break

        case 'audio':
          // Decode base64 audio and queue for playback
          if (data.audio) {
            try {
              const binaryString = atob(data.audio as string)
              const bytes = new Uint8Array(binaryString.length)
              for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i)
              }
              queueAudioChunk(bytes.buffer, 'pcm16')
            } catch (e) {
              console.error('Failed to decode audio:', e)
            }
          }
          break

        case 'response_ended':
          setInteractionState('listening')
          if (data.latency_ms) {
            setCurrentLatency(data.latency_ms as number)
          }
          break

        case 'interrupted':
          setInteractionState('listening')
          break

        case 'error':
          setError((data.message as string) || 'Unknown error')
          // Don't set interaction state to error - use connection status for that
          break

        case 'pong':
          // Heartbeat response, no action needed
          break
      }
    },
    [
      setSession,
      setInteractionState,
      clearTranscripts,
      setUserTranscript,
      appendAIResponse,
      setCurrentLatency,
      setError,
      queueAudioChunk,
      userId,
      options.mode,
      options.providerConfig,
      options.systemPrompt,
    ]
  )

  // WebSocket hook
  const {
    status: wsStatus,
    connect: wsConnect,
    disconnect: wsDisconnect,
    sendMessage,
    sendBinary,
    error: wsError,
  } = useWebSocket({
    url: resolvedWsUrl,
    onMessage: handleMessage,
    onStatusChange: setConnectionStatus,
  })

  // Microphone hook
  const {
    isRecording: micRecording,
    volume,
    startRecording,
    stopRecording,
    error: micError,
  } = useMicrophone({
    onAudioChunk: (chunk: Float32Array) => {
      if (wsStatus === 'connected') {
        // Convert Float32 to PCM16 and send as binary
        const pcm16Buffer = float32ToPCM16(chunk)
        sendBinary(pcm16Buffer)
      }
    },
    onVolumeChange: setInputVolume,
  })

  // Sync microphone state with store
  useEffect(() => {
    setIsRecording(micRecording)
  }, [micRecording, setIsRecording])

  // Update volume in store
  useEffect(() => {
    setInputVolume(volume)
  }, [volume, setInputVolume])

  // Handle connection
  const handleConnect = async () => {
    setError(null)
    isConnectingRef.current = true

    // Request microphone permission first
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
      setPermissionError(null)
    } catch {
      setPermissionError('需要麥克風權限才能使用語音互動功能')
      isConnectingRef.current = false
      return
    }

    // Connect WebSocket
    wsConnect()
  }

  // Handle start session after WebSocket connects
  useEffect(() => {
    if (wsStatus === 'connected' && isConnectingRef.current) {
      // Send config message to start session
      sendMessage('config', {
        config: options.providerConfig,
        system_prompt: options.systemPrompt,
      })
    }
  }, [wsStatus, sendMessage, options])

  // Handle disconnect
  const handleDisconnect = () => {
    stopRecording()
    stopAudio()
    wsDisconnect()
    resetSession()
    setInteractionState('idle')
    isConnectingRef.current = false
  }

  // Handle start/stop recording
  const handleToggleRecording = async () => {
    if (isRecording) {
      stopRecording()
      // Send end turn signal
      sendMessage('end_turn', {})
    } else {
      await startRecording()
    }
  }

  // Handle interrupt
  const handleInterrupt = () => {
    sendMessage('interrupt', {})
    stopAudio()
  }

  const isConnected = connectionStatus === 'connected'
  const canRecord = isConnected && interactionState === 'listening'
  const displayError = error || wsError || micError || permissionError

  return (
    <div className={`flex flex-col gap-6 ${className}`}>
      {/* Mode Selector */}
      <ModeSelector
        mode={options.mode}
        providerConfig={options.providerConfig}
        onModeChange={setMode}
        onProviderChange={setProviderConfig}
        disabled={isConnected}
      />

      {/* Status and Connection */}
      <div className="flex items-center justify-between rounded-lg border bg-card p-4">
        <StatusIndicator connectionStatus={connectionStatus} interactionState={interactionState} />

        <div className="flex items-center gap-4">
          {currentLatency && (
            <span className="text-sm text-muted-foreground">延遲: {currentLatency.toFixed(0)}ms</span>
          )}

          {!isConnected ? (
            <button
              onClick={handleConnect}
              disabled={connectionStatus === 'connecting'}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {connectionStatus === 'connecting' ? '連接中...' : '開始對話'}
            </button>
          ) : (
            <button
              onClick={handleDisconnect}
              className="rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90"
            >
              結束對話
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {displayError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {displayError}
        </div>
      )}

      {/* Audio Visualizer */}
      <div className="rounded-lg border bg-card p-4">
        <div className="mb-2 text-sm font-medium text-foreground">音訊輸入</div>
        <AudioVisualizer level={inputVolume} isActive={isRecording} mode="bars" height={60} showLevel />

        {/* Recording Button */}
        <div className="mt-4 flex justify-center">
          <button
            onClick={handleToggleRecording}
            disabled={!canRecord && !isRecording}
            className={`
              flex h-16 w-16 items-center justify-center rounded-full transition-all
              ${
                isRecording
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              }
              disabled:cursor-not-allowed disabled:opacity-50
            `}
          >
            {isRecording ? (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-8 w-8">
                <path
                  fillRule="evenodd"
                  d="M4.5 7.5a3 3 0 013-3h9a3 3 0 013 3v9a3 3 0 01-3 3h-9a3 3 0 01-3-3v-9z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-8 w-8">
                <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
                <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-7.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
              </svg>
            )}
          </button>
        </div>

        {/* Interrupt Button */}
        {interactionState === 'speaking' && (
          <div className="mt-4 flex justify-center">
            <button
              onClick={handleInterrupt}
              className="rounded-lg bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600"
            >
              打斷回應
            </button>
          </div>
        )}
      </div>

      {/* Transcripts */}
      <div className="rounded-lg border bg-card p-4">
        <div className="mb-2 text-sm font-medium text-foreground">對話內容</div>
        <div className="space-y-3">
          {/* User transcript */}
          {userTranscript && (
            <div className="rounded-lg bg-primary/10 p-3">
              <div className="mb-1 text-xs font-medium text-primary">您</div>
              <div className="text-sm text-foreground">{userTranscript}</div>
            </div>
          )}

          {/* AI response */}
          {aiResponseText && (
            <div className="rounded-lg bg-muted p-3">
              <div className="mb-1 text-xs font-medium text-muted-foreground">AI</div>
              <div className="text-sm text-foreground">{aiResponseText}</div>
            </div>
          )}

          {/* Empty state */}
          {!userTranscript && !aiResponseText && (
            <div className="py-8 text-center text-sm text-muted-foreground">
              {isConnected ? '開始說話以進行對話' : '點擊「開始對話」按鈕以連接'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default InteractionPanel
