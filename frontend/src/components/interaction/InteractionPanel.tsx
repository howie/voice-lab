/**
 * InteractionPanel Component
 * Feature: 004-interaction-module
 * T037: Main component for real-time voice interaction.
 *
 * Integrates microphone input, audio playback, transcripts, and status indicators.
 */

import { useEffect, useCallback, useState, useRef } from 'react'

import { AudioVisualizer } from './AudioVisualizer'
import { LatencyDisplay } from './LatencyDisplay'
import { ModeSelector } from './ModeSelector'
import { PerformanceSettings } from './PerformanceSettings'
import { TranscriptDisplay } from './TranscriptDisplay'
import { RoleScenarioEditor } from './RoleScenarioEditor'
import { ScenarioTemplateSelector } from './ScenarioTemplateSelector'

import { useInteractionStore } from '@/stores/interactionStore'
import type { ScenarioTemplate, TurnLatencyData } from '@/types/interaction'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useMicrophone } from '@/hooks/useMicrophone'
import { useAudioPlayback } from '@/hooks/useAudioPlayback'
import { buildWebSocketUrl } from '@/services/interactionApi'
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

  // T087: Track when an interruption just occurred for the indicator
  const [wasInterrupted, setWasInterrupted] = useState(false)

  // Turn timing debug info
  interface TurnTiming {
    speakingStartedAt: number | null
    endTurnSentAt: number | null
    responseStartedAt: number | null
    firstAudioAt: number | null
    responseEndedAt: number | null
  }
  const [turnTiming, setTurnTiming] = useState<TurnTiming>({
    speakingStartedAt: null,
    endTurnSentAt: null,
    responseStartedAt: null,
    firstAudioAt: null,
    responseEndedAt: null,
  })
  const firstAudioReceivedRef = useRef(false) // Track if we've received first audio in this turn

  // Ref to track if we're in the connecting phase
  const isConnectingRef = useRef(false)

  // Ref for turn counter
  const turnCounterRef = useRef(0)

  // Ref to avoid spamming sample rate log
  const audioSampleRateLoggedRef = useRef(false)

  // VAD (Voice Activity Detection) state machine for auto end_turn
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastSpeakingTimeRef = useRef<number>(Date.now())
  const speakingStartTimeRef = useRef<number | null>(null) // Track when user started speaking
  const hasSentEndTurnRef = useRef(false)
  const hasUserSpokenRef = useRef(false) // Track if user has spoken in current turn
  const speakingFrameCountRef = useRef(0) // Hysteresis: count consecutive frames above threshold
  const interactionStateRef = useRef<InteractionState>('idle') // Track state in ref to avoid stale closure
  const sessionStartTimeRef = useRef<number>(0) // For relative timestamp logging
  const inputVolumeRef = useRef<number>(0) // Track input volume for audio gating

  // Logging utility with relative timestamps
  const log = useCallback((category: string, message: string, data?: unknown) => {
    const elapsed = sessionStartTimeRef.current
      ? ((Date.now() - sessionStartTimeRef.current) / 1000).toFixed(3)
      : '0.000'
    if (data !== undefined) {
      console.log(`[+${elapsed}s] [${category}] ${message}`, data)
    } else {
      console.log(`[+${elapsed}s] [${category}] ${message}`)
    }
  }, [])

  // VAD Configuration - Tuned for natural conversation with hysteresis
  // Note: These values should be adjusted based on microphone sensitivity and environment
  const SILENCE_THRESHOLD = 0.15 // Volume below this is considered silence (raised to reduce false triggers)
  const SPEAKING_THRESHOLD = 0.22 // Volume above this confirms speaking (needs clear speech signal)
  const SILENCE_DURATION_MS = 1000 // Auto send end_turn after 1s of silence (allow natural pauses)
  const MIN_SPEAKING_DURATION_MS = 500 // User must speak for at least 500ms before silence detection activates
  const SPEAKING_FRAMES_REQUIRED = 4 // Require 4 consecutive frames above threshold to confirm speaking

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
    currentTurnLatency,
    sessionStats,
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
    setCurrentTurnLatency,
    setMode,
    setProviderConfig,
    setError,
    resetSession,
    // US4: Role and scenario configuration
    setUserRole,
    setAiRole,
    setScenarioContext,
    // US5: Barge-in configuration
    setBargeInEnabled,
    // Performance optimization
    setLightweightMode,
  } = useInteractionStore()

  // Determine WebSocket URL (must include user_id query parameter)
  // Use buildWebSocketUrl to get the correct backend API URL (not frontend domain)
  const resolvedWsUrl = wsUrl || buildWebSocketUrl(options.mode, userId)

  // Audio playback hook - must be before handleMessage which uses queueAudioChunk
  // Note: Both OpenAI and Gemini 2.5 return audio at 24000 Hz (default)
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

      // Debug: log all incoming WebSocket messages (except audio which is too frequent)
      if (type !== 'audio' && type !== 'pong') {
        log('WS_RECV', type, data)
      }

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
          // Record when AI response started
          setTurnTiming((prev) => ({ ...prev, responseStartedAt: Date.now() }))
          firstAudioReceivedRef.current = false
          log('TURN', 'response_started')
          break

        case 'text_delta':
          // Handle both 'delta' and 'text' field names for compatibility
          appendAIResponse((data.delta as string) || (data.text as string) || '')
          break

        case 'audio':
          // Decode base64 audio and queue for playback
          if (data.audio) {
            // Record first audio timing and calculate latency
            if (!firstAudioReceivedRef.current) {
              firstAudioReceivedRef.current = true
              const firstAudioAt = Date.now()
              setTurnTiming((prev) => {
                const latency = prev.endTurnSentAt ? firstAudioAt - prev.endTurnSentAt : null
                log('TURN', `first_audio (latency=${latency}ms)`)
                return { ...prev, firstAudioAt }
              })
            }
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
          // Record response end timing
          const responseEndedAt = Date.now()
          setTurnTiming((prev) => {
            const totalDuration = prev.speakingStartedAt ? responseEndedAt - prev.speakingStartedAt : null
            log('TURN', `response_ended (total_turn=${totalDuration}ms)`)
            return { ...prev, responseEndedAt }
          })

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

          // Reset silence detection and timing for next turn
          hasSentEndTurnRef.current = false
          lastSpeakingTimeRef.current = Date.now()
          firstAudioReceivedRef.current = false
          // Don't reset turnTiming here - we want to keep it for display until next turn starts

          // T065: Parse detailed latency data from response_ended message
          const latencyData = data.latency as TurnLatencyData | undefined
          if (latencyData) {
            setCurrentLatency(latencyData.total_ms)
            setCurrentTurnLatency(latencyData)
          } else if (data.latency_ms) {
            // Fallback for backward compatibility
            setCurrentLatency(data.latency_ms as number)
            setCurrentTurnLatency(null)
          }
          break
        }

        case 'interrupted':
          // T085: Stop audio playback immediately on interrupt
          stopAudio()
          setInteractionState('listening')
          // T087: Show interrupt indicator briefly
          setWasInterrupted(true)
          setTimeout(() => setWasInterrupted(false), 2000)
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
      setCurrentTurnLatency,
      setError,
      queueAudioChunk,
      stopAudio,
      userId,
      options.mode,
      options.providerConfig,
      options.systemPrompt,
      log,
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
    startRecording,
    stopRecording,
    error: micError,
  } = useMicrophone({
    onAudioChunk: (chunk: Float32Array, actualSampleRate: number) => {
      // 只在以下情況發送音訊：
      // 1. WebSocket 已連線
      // 2. 狀態為 'listening'（用戶輪次）
      // 3. 或者音量足夠大（可能是打斷 AI）
      const currentState = interactionStateRef.current
      const currentVolume = inputVolumeRef.current
      const shouldSend =
        wsStatus === 'connected' &&
        (currentState === 'listening' || currentVolume > SPEAKING_THRESHOLD)

      if (shouldSend) {
        // Debug: Log sample rate on first chunk to help diagnose audio issues
        if (!audioSampleRateLoggedRef.current) {
          log('AUDIO', `sample_rate=${actualSampleRate}Hz`)
          audioSampleRateLoggedRef.current = true
        }

        // Convert Float32 to PCM16
        const pcm16Buffer = float32ToPCM16(chunk)

        // Binary format: [4 bytes sample_rate (uint32 LE)] + [PCM16 audio data]
        // This is more efficient than Base64 JSON (~33% smaller, no encode/decode overhead)
        const headerSize = 4
        const binaryMessage = new ArrayBuffer(headerSize + pcm16Buffer.byteLength)
        const view = new DataView(binaryMessage)

        // Write sample rate as uint32 little-endian
        view.setUint32(0, actualSampleRate, true)

        // Copy PCM16 audio data after header
        new Uint8Array(binaryMessage, headerSize).set(new Uint8Array(pcm16Buffer))

        sendBinary(binaryMessage)
      }
    },
    onVolumeChange: (vol: number) => {
      setInputVolume(vol)
      inputVolumeRef.current = vol // Update ref for audio gating in onAudioChunk

      // VAD state machine: auto send end_turn when user stops speaking
      // Use ref for interactionState to avoid stale closure
      const currentState = interactionStateRef.current
      if (wsStatus === 'connected' && currentState === 'listening') {
        const now = Date.now()

        // Hysteresis: Use higher threshold to confirm speaking, lower threshold to confirm silence
        if (vol > SPEAKING_THRESHOLD) {
          // Volume clearly above speaking threshold
          speakingFrameCountRef.current++

          // Require consecutive frames above threshold to confirm speaking (debounce)
          if (speakingFrameCountRef.current >= SPEAKING_FRAMES_REQUIRED) {
            if (!hasUserSpokenRef.current) {
              // First time confirming user is speaking
              hasUserSpokenRef.current = true
              speakingStartTimeRef.current = now
              // Record timing for debug display and reset previous turn timing
              setTurnTiming({
                speakingStartedAt: now,
                endTurnSentAt: null,
                responseStartedAt: null,
                firstAudioAt: null,
                responseEndedAt: null,
              })
              log('VAD', 'user_started_speaking')
            }
            lastSpeakingTimeRef.current = now

            // Clear any pending silence timer
            if (silenceTimerRef.current) {
              clearTimeout(silenceTimerRef.current)
              silenceTimerRef.current = null
            }
          }
        } else if (vol > SILENCE_THRESHOLD) {
          // In the hysteresis zone - maintain current state but update speaking time if already speaking
          if (hasUserSpokenRef.current) {
            lastSpeakingTimeRef.current = now
            // Don't reset frame count - allow small dips during speech
          }
        } else {
          // Volume below silence threshold
          speakingFrameCountRef.current = 0 // Reset hysteresis counter

          // Only start silence detection if:
          // 1. User has spoken (hasUserSpokenRef)
          // 2. User has spoken for minimum duration (MIN_SPEAKING_DURATION_MS)
          // 3. We haven't already sent end_turn
          // 4. No timer is already running
          const speakingDuration = speakingStartTimeRef.current
            ? now - speakingStartTimeRef.current
            : 0

          if (
            hasUserSpokenRef.current &&
            speakingDuration >= MIN_SPEAKING_DURATION_MS &&
            !hasSentEndTurnRef.current &&
            !silenceTimerRef.current
          ) {
            // Start silence timer
            silenceTimerRef.current = setTimeout(() => {
              const silenceDuration = Date.now() - lastSpeakingTimeRef.current

              // Double-check all conditions before sending
              if (
                silenceDuration >= SILENCE_DURATION_MS &&
                !hasSentEndTurnRef.current &&
                hasUserSpokenRef.current &&
                interactionStateRef.current === 'listening'
              ) {
                const endTurnTime = Date.now()
                const totalSpeakingDuration = speakingStartTimeRef.current
                  ? endTurnTime - speakingStartTimeRef.current
                  : 0
                log('VAD', `silence=${silenceDuration}ms, spoke=${totalSpeakingDuration}ms → end_turn`)
                hasSentEndTurnRef.current = true
                // Record end_turn timing
                setTurnTiming((prev) => ({ ...prev, endTurnSentAt: endTurnTime }))
                stopRecording()
                sendMessage('end_turn', {})
                setInteractionState('processing')
              }
              silenceTimerRef.current = null
            }, SILENCE_DURATION_MS)
          }
        }
      }
    },
  })

  // Sync microphone state with store
  useEffect(() => {
    setIsRecording(micRecording)
  }, [micRecording, setIsRecording])

  // Sync interactionState to ref for use in closures (avoids stale state)
  useEffect(() => {
    interactionStateRef.current = interactionState
    // Reset VAD state when returning to listening state for next turn
    if (interactionState === 'listening') {
      hasSentEndTurnRef.current = false
      hasUserSpokenRef.current = false
      speakingStartTimeRef.current = null
      speakingFrameCountRef.current = 0
    }
  }, [interactionState])

  // Handle connection
  const handleConnect = async () => {
    setError(null)
    isConnectingRef.current = true
    // Reset session start time for logging
    sessionStartTimeRef.current = Date.now()
    log('SESSION', 'connecting...')

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
      // T084: Include barge_in_enabled configuration
      // T089: Include lightweight_mode for lower latency V2V
      sendMessage('config', {
        config: options.providerConfig,
        system_prompt: options.systemPrompt,
        user_role: options.userRole,
        ai_role: options.aiRole,
        scenario_context: options.scenarioContext,
        barge_in_enabled: options.bargeInEnabled,
        lightweight_mode: options.lightweightMode ?? true,
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
    // Clear silence detection timer
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
    hasSentEndTurnRef.current = false

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

  // Handle manual end of user speech (backup for when VAD doesn't detect silence)
  const handleEndTurn = () => {
    stopRecording()
    sendMessage('end_turn', {})
    setInteractionState('processing')
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

      {/* Performance Settings (V2V Feature Toggles) */}
      {options.mode === 'realtime' && (
        <PerformanceSettings
          lightweightMode={options.lightweightMode}
          onLightweightModeChange={setLightweightMode}
          disabled={isConnected}
        />
      )}

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
          <div className="flex items-center gap-3">
            {/* T087: Interrupt indicator */}
            {wasInterrupted && (
              <span className="flex items-center gap-1 text-xs text-orange-600">
                <span className="h-2 w-2 animate-pulse rounded-full bg-orange-500" />
                已打斷
              </span>
            )}
            {isRecording && (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
                收音中
              </span>
            )}
          </div>
        </div>
        <AudioVisualizer level={inputVolume} isActive={isRecording} mode="bars" height={60} showLevel />

        {/* VAD Threshold Debug Display */}
        {isRecording && (
          <div className="mt-3 space-y-2">
            {/* Volume bar with threshold markers */}
            <div className="relative h-6 rounded bg-gray-700">
              {/* Current volume bar */}
              <div
                className={`absolute left-0 top-0 h-full rounded transition-all duration-75 ${
                  inputVolume > SPEAKING_THRESHOLD
                    ? 'bg-green-500'
                    : inputVolume > SILENCE_THRESHOLD
                      ? 'bg-yellow-500'
                      : 'bg-gray-500'
                }`}
                style={{ width: `${Math.min(inputVolume * 100 * 2, 100)}%` }}
              />
              {/* Silence threshold marker */}
              <div
                className="absolute top-0 h-full w-0.5 bg-orange-400"
                style={{ left: `${SILENCE_THRESHOLD * 100 * 2}%` }}
                title={`靜音閾值: ${SILENCE_THRESHOLD}`}
              />
              {/* Speaking threshold marker */}
              <div
                className="absolute top-0 h-full w-0.5 bg-green-400"
                style={{ left: `${SPEAKING_THRESHOLD * 100 * 2}%` }}
                title={`說話閾值: ${SPEAKING_THRESHOLD}`}
              />
              {/* Labels */}
              <div className="absolute inset-0 flex items-center justify-between px-2 text-xs text-white">
                <span>
                  音量: {(inputVolume * 100).toFixed(1)}%
                </span>
                <span
                  className={`rounded px-1 ${
                    inputVolume > SPEAKING_THRESHOLD
                      ? 'bg-green-600'
                      : inputVolume > SILENCE_THRESHOLD
                        ? 'bg-yellow-600'
                        : 'bg-gray-600'
                  }`}
                >
                  {inputVolume > SPEAKING_THRESHOLD
                    ? '說話中'
                    : inputVolume > SILENCE_THRESHOLD
                      ? '過渡區'
                      : '靜音'}
                </span>
              </div>
            </div>
            {/* Threshold legend */}
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>
                <span className="mr-1 inline-block h-2 w-2 rounded-full bg-orange-400" />
                靜音閾值: {(SILENCE_THRESHOLD * 100).toFixed(0)}%
              </span>
              <span>
                <span className="mr-1 inline-block h-2 w-2 rounded-full bg-green-400" />
                說話閾值: {(SPEAKING_THRESHOLD * 100).toFixed(0)}%
              </span>
              <span>靜音時長: {SILENCE_DURATION_MS}ms</span>
            </div>
          </div>
        )}

        {/* T086: Barge-in toggle and interrupt button */}
        <div className="mt-4 flex items-center justify-between">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={options.bargeInEnabled}
              onChange={(e) => setBargeInEnabled(e.target.checked)}
              disabled={isConnected}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
            />
            <span className="text-sm text-muted-foreground">允許打斷 AI 回應</span>
          </label>

          <div className="flex gap-2">
            {/* End Turn Button - manually signal end of speech when VAD doesn't detect silence */}
            {interactionState === 'listening' && isRecording && (
              <button
                onClick={handleEndTurn}
                className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
              >
                結束發言
              </button>
            )}

            {/* Interrupt Button - only shown when AI is speaking and barge-in enabled */}
            {interactionState === 'speaking' && options.bargeInEnabled && (
              <button
                onClick={handleInterrupt}
                className="rounded-lg bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600"
              >
                打斷回應
              </button>
            )}
          </div>
        </div>
      </div>

      {/* T065-T067: Latency Display */}
      {options.showLatencyMetrics && (currentTurnLatency || sessionStats) && (
        <LatencyDisplay
          turnLatency={currentTurnLatency}
          sessionStats={sessionStats}
          mode={options.mode}
          showBreakdown={true}
          showSessionStats={!!sessionStats}
        />
      )}

      {/* Transcripts - T078a: Show role names instead of fixed labels */}
      <TranscriptDisplay
        turnHistory={turnHistory}
        currentUserTranscript={userTranscript}
        currentAIResponse={aiResponseText}
        isTranscriptFinal={isTranscriptFinal}
        userRoleLabel={options.userRole}
        aiRoleLabel={options.aiRole}
      />

      {/* Turn Timing Debug Display */}
      {isConnected && turnTiming.speakingStartedAt && (
        <div className="rounded-lg border border-dashed border-gray-600 bg-gray-900/50 p-4">
          <div className="mb-2 text-xs font-medium text-gray-400">Turn Timing Debug</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs font-mono">
            {/* Timeline events */}
            <div className="text-gray-500">說話開始:</div>
            <div className="text-gray-300">
              {new Date(turnTiming.speakingStartedAt).toLocaleTimeString('zh-TW', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
              .{String(turnTiming.speakingStartedAt % 1000).padStart(3, '0')}
            </div>

            <div className="text-gray-500">送出 end_turn:</div>
            <div className="text-gray-300">
              {turnTiming.endTurnSentAt ? (
                <>
                  +{turnTiming.endTurnSentAt - turnTiming.speakingStartedAt}ms
                  <span className="ml-2 text-yellow-500">
                    (說話 {turnTiming.endTurnSentAt - turnTiming.speakingStartedAt - SILENCE_DURATION_MS}ms + 靜音 {SILENCE_DURATION_MS}ms)
                  </span>
                </>
              ) : (
                <span className="text-gray-600">等待中...</span>
              )}
            </div>

            <div className="text-gray-500">AI 開始回應:</div>
            <div className="text-gray-300">
              {turnTiming.responseStartedAt ? (
                <>
                  +{turnTiming.responseStartedAt - turnTiming.speakingStartedAt}ms
                  {turnTiming.endTurnSentAt && (
                    <span className="ml-2 text-blue-400">
                      (等待 {turnTiming.responseStartedAt - turnTiming.endTurnSentAt}ms)
                    </span>
                  )}
                </>
              ) : turnTiming.endTurnSentAt ? (
                <span className="animate-pulse text-yellow-500">處理中...</span>
              ) : (
                <span className="text-gray-600">-</span>
              )}
            </div>

            <div className="text-gray-500">首個音訊:</div>
            <div className="text-gray-300">
              {turnTiming.firstAudioAt ? (
                <>
                  +{turnTiming.firstAudioAt - turnTiming.speakingStartedAt}ms
                  {turnTiming.responseStartedAt && (
                    <span className="ml-2 text-green-400">
                      (音訊延遲 {turnTiming.firstAudioAt - turnTiming.responseStartedAt}ms)
                    </span>
                  )}
                </>
              ) : turnTiming.responseStartedAt ? (
                <span className="animate-pulse text-blue-400">串流中...</span>
              ) : (
                <span className="text-gray-600">-</span>
              )}
            </div>

            <div className="text-gray-500">回應結束:</div>
            <div className="text-gray-300">
              {turnTiming.responseEndedAt ? (
                <>
                  +{turnTiming.responseEndedAt - turnTiming.speakingStartedAt}ms
                  <span className="ml-2 text-purple-400">
                    (總延遲 {turnTiming.endTurnSentAt ? turnTiming.responseEndedAt - turnTiming.endTurnSentAt : '-'}ms)
                  </span>
                </>
              ) : turnTiming.firstAudioAt ? (
                <span className="animate-pulse text-green-400">播放中...</span>
              ) : (
                <span className="text-gray-600">-</span>
              )}
            </div>
          </div>

          {/* Summary metrics */}
          {turnTiming.endTurnSentAt && turnTiming.responseStartedAt && (
            <div className="mt-3 border-t border-gray-700 pt-2">
              <div className="flex flex-wrap gap-3 text-xs">
                <span className="rounded bg-yellow-900/50 px-2 py-0.5 text-yellow-400">
                  API 延遲: {turnTiming.responseStartedAt - turnTiming.endTurnSentAt}ms
                </span>
                {turnTiming.firstAudioAt && (
                  <span className="rounded bg-green-900/50 px-2 py-0.5 text-green-400">
                    首音延遲: {turnTiming.firstAudioAt - turnTiming.endTurnSentAt}ms
                  </span>
                )}
                {turnTiming.responseEndedAt && (
                  <span className="rounded bg-purple-900/50 px-2 py-0.5 text-purple-400">
                    總回應: {turnTiming.responseEndedAt - turnTiming.endTurnSentAt}ms
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default InteractionPanel
