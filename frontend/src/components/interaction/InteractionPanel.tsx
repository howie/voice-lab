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
import { TranscriptDisplay } from './TranscriptDisplay'
import { RoleScenarioEditor } from './RoleScenarioEditor'
import { ScenarioTemplateSelector } from './ScenarioTemplateSelector'

import { useInteractionStore } from '@/stores/interactionStore'
import type { ScenarioTemplate } from '@/types/interaction'
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

// T058: Fallback prompt component when Realtime API fails
interface FallbackPromptProps {
  isRealtimeMode: boolean
  hasError: boolean
  onSwitchToCascade: () => void
}

function FallbackPrompt({ isRealtimeMode, hasError, onSwitchToCascade }: FallbackPromptProps) {
  if (!isRealtimeMode || !hasError) return null

  return (
    <div className="rounded-lg border border-amber-500/50 bg-amber-50 p-4 dark:bg-amber-950/20">
      <div className="flex items-start gap-3">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600 dark:text-amber-400"
        >
          <path
            fillRule="evenodd"
            d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z"
            clipRule="evenodd"
          />
        </svg>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-amber-800 dark:text-amber-200">
            Realtime API 連線失敗
          </h4>
          <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">
            即時模式暫時無法使用。建議切換至串接模式 (STT → LLM → TTS)，可提供相似的互動體驗。
          </p>
          <button
            type="button"
            onClick={onSwitchToCascade}
            className="mt-3 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 dark:bg-amber-500 dark:hover:bg-amber-600"
          >
            切換至串接模式
          </button>
        </div>
      </div>
    </div>
  )
}

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

  // Ref for turn counter
  const turnCounterRef = useRef(0)

  // Store state
  const {
    connectionStatus,
    interactionState,
    options,
    turnHistory,
    userTranscript,
    aiResponseText,
    isTranscriptFinal,
    isRecording,
    inputVolume,
    currentLatency,
    error,
    setConnectionStatus,
    setInteractionState,
    setSession,
    addTurnToHistory,
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
    // US4: Role and scenario configuration
    setUserRole,
    setAiRole,
    setScenarioContext,
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

        case 'response_ended': {
          // Save current turn to history before clearing
          const currentUserTranscript = useInteractionStore.getState().userTranscript
          const currentAIResponse = useInteractionStore.getState().aiResponseText
          const currentSession = useInteractionStore.getState().session

          if ((currentUserTranscript || currentAIResponse) && currentSession) {
            turnCounterRef.current += 1
            const now = new Date().toISOString()
            addTurnToHistory({
              id: `${currentSession.id}-turn-${turnCounterRef.current}`,
              session_id: currentSession.id,
              turn_number: turnCounterRef.current,
              user_audio_path: null,
              user_transcript: currentUserTranscript || null,
              ai_response_text: currentAIResponse || null,
              ai_audio_path: null,
              interrupted: false,
              started_at: now,
              ended_at: now,
            })
          }

          // Clear current transcripts for next turn
          clearTranscripts()
          setInteractionState('listening')

          if (data.latency_ms) {
            setCurrentLatency(data.latency_ms as number)
          }
          break
        }

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
      addTurnToHistory,
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
      // T078: Send config message with role/scenario to start session
      sendMessage('config', {
        config: options.providerConfig,
        system_prompt: options.systemPrompt,
        user_role: options.userRole,
        ai_role: options.aiRole,
        scenario_context: options.scenarioContext,
      })
    }
  }, [wsStatus, sendMessage, options])

  // Auto-start recording when session is ready (一鍵開始對話)
  useEffect(() => {
    if (wsStatus === 'connected' && interactionState === 'listening' && !isRecording) {
      // Session is ready, auto-start recording
      startRecording()
    }
  }, [wsStatus, interactionState, isRecording, startRecording])

  // Handle disconnect
  const handleDisconnect = () => {
    stopRecording()
    stopAudio()
    wsDisconnect()
    resetSession()
    setInteractionState('idle')
    isConnectingRef.current = false
  }

  // Handle interrupt
  const handleInterrupt = () => {
    sendMessage('interrupt', {})
    stopAudio()
  }

  // T076: Handle template selection - fill role/scenario from template
  const handleTemplateSelect = useCallback(
    (template: ScenarioTemplate) => {
      setUserRole(template.user_role)
      setAiRole(template.ai_role)
      setScenarioContext(template.scenario_context)
    },
    [setUserRole, setAiRole, setScenarioContext]
  )

  const isConnected = connectionStatus === 'connected'
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

      {/* US4: Scenario Template Selector */}
      <ScenarioTemplateSelector
        onSelect={handleTemplateSelect}
        disabled={isConnected}
      />

      {/* US4: Role and Scenario Editor */}
      <RoleScenarioEditor
        userRole={options.userRole}
        aiRole={options.aiRole}
        scenarioContext={options.scenarioContext}
        onUserRoleChange={setUserRole}
        onAiRoleChange={setAiRole}
        onScenarioContextChange={setScenarioContext}
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

      {/* T058: Fallback prompt when Realtime fails */}
      <FallbackPrompt
        isRealtimeMode={options.mode === 'realtime'}
        hasError={connectionStatus === 'error' || !!wsError}
        onSwitchToCascade={() => {
          setError(null)
          setMode('cascade')
          setProviderConfig({
            stt_provider: 'azure',
            llm_provider: 'openai',
            tts_provider: 'azure',
            tts_voice: 'zh-TW-HsiaoChenNeural',
          })
        }}
      />

      {/* Audio Visualizer */}
      <div className="rounded-lg border bg-card p-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-foreground">音訊輸入</span>
          {isRecording && (
            <span className="flex items-center gap-1 text-xs text-green-600">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              收音中
            </span>
          )}
        </div>
        <AudioVisualizer level={inputVolume} isActive={isRecording} mode="bars" height={60} showLevel />

        {/* Interrupt Button - only shown when AI is speaking */}
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

      {/* Transcripts - T078a: Show role names instead of fixed labels */}
      <TranscriptDisplay
        turnHistory={turnHistory}
        currentUserTranscript={userTranscript}
        currentAIResponse={aiResponseText}
        isTranscriptFinal={isTranscriptFinal}
        userRoleLabel={options.userRole}
        aiRoleLabel={options.aiRole}
      />
    </div>
  )
}

export default InteractionPanel
