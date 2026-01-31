/**
 * Direct Gemini Live API WebSocket hook.
 *
 * Connects the browser directly to Google's Gemini Live API WebSocket
 * without going through the backend proxy. Used for benchmarking
 * the best-case v2v latency.
 *
 * Audio format:
 * - Input:  PCM16 mono @ 16kHz (base64 encoded)
 * - Output: PCM16 mono @ 24kHz (base64 encoded)
 */

import { useCallback, useEffect, useRef, useState } from 'react'

// =============================================================================
// Types
// =============================================================================

export interface GeminiLiveConfig {
  apiKey: string
  wsUrl: string
  model: string
  voice: string
  systemPrompt?: string
}

export type GeminiConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'setup_sent'
  | 'connected'
  | 'error'

export interface GeminiLatencyMetrics {
  /** Time from user stop speaking to first audio byte received (ms) */
  firstAudioByteMs: number | null
  /** Time from first audio byte to turn complete (ms) */
  audioStreamDurationMs: number | null
  /** Total round-trip time (ms) */
  totalRoundTripMs: number | null
  /** WebSocket open to setup complete (ms) */
  setupLatencyMs: number | null
  /** Number of audio chunks received */
  audioChunksReceived: number
  /** All recorded first-byte latencies for averaging */
  firstByteHistory: number[]
}

export interface UseGeminiLiveOptions {
  /** Called when audio data is received (base64 PCM16 @ 24kHz) */
  onAudioData?: (base64Audio: string) => void
  /** Called when input transcript is received */
  onInputTranscript?: (text: string) => void
  /** Called when output transcript is received */
  onOutputTranscript?: (text: string) => void
  /** Called when model turn completes */
  onTurnComplete?: () => void
  /** Called when interrupted */
  onInterrupted?: () => void
  /** Called on connection status change */
  onStatusChange?: (status: GeminiConnectionStatus) => void
}

export interface UseGeminiLiveReturn {
  /** Current connection status */
  status: GeminiConnectionStatus
  /** Latency metrics */
  metrics: GeminiLatencyMetrics
  /** Connect to Gemini Live API */
  connect: (config: GeminiLiveConfig) => void
  /** Disconnect from Gemini Live API */
  disconnect: () => void
  /** Send audio chunk (Float32Array from microphone) */
  sendAudio: (chunk: Float32Array) => void
  /** Send text message */
  sendText: (text: string) => void
  /** Error message if any */
  error: string | null
  /** Whether the model is currently generating a response */
  isModelSpeaking: boolean
}

// =============================================================================
// Helpers
// =============================================================================

/** Convert Float32Array (microphone) to PCM16 Int16Array */
function float32ToPcm16(float32: Float32Array): Int16Array {
  const int16 = new Int16Array(float32.length)
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]))
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return int16
}

/** Convert ArrayBuffer to base64 string */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

// =============================================================================
// Hook
// =============================================================================

const INITIAL_METRICS: GeminiLatencyMetrics = {
  firstAudioByteMs: null,
  audioStreamDurationMs: null,
  totalRoundTripMs: null,
  setupLatencyMs: null,
  audioChunksReceived: 0,
  firstByteHistory: [],
}

export function useGeminiLive(
  options: UseGeminiLiveOptions = {}
): UseGeminiLiveReturn {
  const {
    onAudioData,
    onInputTranscript,
    onOutputTranscript,
    onTurnComplete,
    onInterrupted,
    onStatusChange,
  } = options

  const [status, setStatus] = useState<GeminiConnectionStatus>('disconnected')
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<GeminiLatencyMetrics>(INITIAL_METRICS)
  const [isModelSpeaking, setIsModelSpeaking] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const statusRef = useRef<GeminiConnectionStatus>('disconnected')

  // Timing refs for latency measurement
  const connectStartRef = useRef<number>(0)
  const lastAudioSentRef = useRef<number>(0)
  const firstAudioReceivedRef = useRef<number>(0)
  const audioChunkCountRef = useRef<number>(0)

  // Stable callback refs
  const onAudioDataRef = useRef(onAudioData)
  const onInputTranscriptRef = useRef(onInputTranscript)
  const onOutputTranscriptRef = useRef(onOutputTranscript)
  const onTurnCompleteRef = useRef(onTurnComplete)
  const onInterruptedRef = useRef(onInterrupted)
  const onStatusChangeRef = useRef(onStatusChange)

  useEffect(() => {
    onAudioDataRef.current = onAudioData
    onInputTranscriptRef.current = onInputTranscript
    onOutputTranscriptRef.current = onOutputTranscript
    onTurnCompleteRef.current = onTurnComplete
    onInterruptedRef.current = onInterrupted
    onStatusChangeRef.current = onStatusChange
  }, [
    onAudioData,
    onInputTranscript,
    onOutputTranscript,
    onTurnComplete,
    onInterrupted,
    onStatusChange,
  ])

  const updateStatus = useCallback((newStatus: GeminiConnectionStatus) => {
    statusRef.current = newStatus
    setStatus(newStatus)
    onStatusChangeRef.current?.(newStatus)
  }, [])

  // Parse a single JSON message from Gemini
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const processMessage = useCallback(
    (msg: any) => {
      // Setup complete
      if (msg.setupComplete !== undefined) {
          const setupMs = performance.now() - connectStartRef.current
          setMetrics((prev) => ({ ...prev, setupLatencyMs: Math.round(setupMs) }))
          updateStatus('connected')
          console.log(`[GeminiLive] Setup complete in ${setupMs.toFixed(0)}ms`)
          return
        }

        // Server content
        if (msg.serverContent) {
          const sc = msg.serverContent

          // Input transcription
          if (sc.inputTranscription?.text) {
            onInputTranscriptRef.current?.(sc.inputTranscription.text)
          }

          // Output transcription
          if (sc.outputTranscription?.text) {
            onOutputTranscriptRef.current?.(sc.outputTranscription.text)
          }

          // Model turn - audio/text content
          if (sc.modelTurn?.parts) {
            for (const part of sc.modelTurn.parts) {
              if (part.inlineData?.data) {
                const now = performance.now()
                audioChunkCountRef.current++

                // Track first audio byte latency
                if (audioChunkCountRef.current === 1) {
                  firstAudioReceivedRef.current = now
                  const firstByteMs = now - lastAudioSentRef.current
                  setMetrics((prev) => ({
                    ...prev,
                    firstAudioByteMs: Math.round(firstByteMs),
                    audioChunksReceived: 1,
                    firstByteHistory: [
                      ...prev.firstByteHistory,
                      Math.round(firstByteMs),
                    ],
                  }))
                  setIsModelSpeaking(true)
                  console.log(
                    `[GeminiLive] First audio byte: ${firstByteMs.toFixed(0)}ms`
                  )
                } else {
                  setMetrics((prev) => ({
                    ...prev,
                    audioChunksReceived: audioChunkCountRef.current,
                  }))
                }

                onAudioDataRef.current?.(part.inlineData.data)
              }
              if (part.text) {
                onOutputTranscriptRef.current?.(part.text)
              }
            }
          }

          // Turn complete
          if (sc.turnComplete) {
            const now = performance.now()
            const totalMs = now - lastAudioSentRef.current
            const streamMs = firstAudioReceivedRef.current
              ? now - firstAudioReceivedRef.current
              : null

            setMetrics((prev) => ({
              ...prev,
              totalRoundTripMs: Math.round(totalMs),
              audioStreamDurationMs: streamMs ? Math.round(streamMs) : null,
            }))

            setIsModelSpeaking(false)
            audioChunkCountRef.current = 0
            onTurnCompleteRef.current?.()
            console.log(
              `[GeminiLive] Turn complete: total=${totalMs.toFixed(0)}ms`
            )
          }

          // Interrupted
          if (sc.interrupted) {
            setIsModelSpeaking(false)
            audioChunkCountRef.current = 0
            onInterruptedRef.current?.()
            console.log('[GeminiLive] Response interrupted')
          }
        }

        // Usage metadata (log only)
        if (msg.usageMetadata) {
          console.log('[GeminiLive] Usage:', msg.usageMetadata)
        }
    },
    [updateStatus]
  )

  // Handle incoming WebSocket messages (may be text, Blob, or ArrayBuffer)
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      const { data } = event

      // Text frame — parse directly
      if (typeof data === 'string') {
        try {
          processMessage(JSON.parse(data))
        } catch (err) {
          console.error('[GeminiLive] Failed to parse text message:', err)
        }
        return
      }

      // Binary frame (Blob) — most common from Gemini
      if (data instanceof Blob) {
        data.text().then((text) => {
          try {
            processMessage(JSON.parse(text))
          } catch (err) {
            console.error('[GeminiLive] Failed to parse Blob message:', err)
          }
        })
        return
      }

      // ArrayBuffer (if binaryType were set to 'arraybuffer')
      if (data instanceof ArrayBuffer) {
        try {
          const text = new TextDecoder().decode(data)
          processMessage(JSON.parse(text))
        } catch (err) {
          console.error('[GeminiLive] Failed to parse ArrayBuffer message:', err)
        }
        return
      }

      console.warn('[GeminiLive] Unknown message type:', typeof data)
    },
    [processMessage]
  )

  // Connect to Gemini Live API
  const connect = useCallback(
    (config: GeminiLiveConfig) => {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }

      setError(null)
      setMetrics(INITIAL_METRICS)
      updateStatus('connecting')
      connectStartRef.current = performance.now()

      const url = `${config.wsUrl}?key=${config.apiKey}`

      try {
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('[GeminiLive] WebSocket connected, sending setup...')
          updateStatus('setup_sent')

          // Send setup message
          const setupMsg = {
            setup: {
              model: `models/${config.model}`,
              generationConfig: {
                responseModalities: ['AUDIO'],
                speechConfig: {
                  voiceConfig: {
                    prebuiltVoiceConfig: {
                      voiceName: config.voice,
                    },
                  },
                },
                thinkingConfig: { thinkingBudget: 0 },
              },
              inputAudioTranscription: {},
              outputAudioTranscription: {},
              ...(config.systemPrompt
                ? {
                    systemInstruction: {
                      parts: [{ text: config.systemPrompt }],
                    },
                  }
                : {}),
            },
          }

          ws.send(JSON.stringify(setupMsg))
          console.log(
            `[GeminiLive] Setup sent: model=${config.model}, voice=${config.voice}`
          )
        }

        ws.onmessage = handleMessage

        ws.onerror = (ev) => {
          console.error('[GeminiLive] WebSocket error:', ev)
          setError('WebSocket connection error')
          updateStatus('error')
        }

        ws.onclose = (ev) => {
          console.log(
            `[GeminiLive] WebSocket closed: code=${ev.code}, reason=${ev.reason}`
          )
          if (statusRef.current !== 'error') {
            updateStatus('disconnected')
          }
          wsRef.current = null
        }
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : 'Failed to connect'
        setError(msg)
        updateStatus('error')
      }
    },
    [handleMessage, updateStatus]
  )

  // Disconnect
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    updateStatus('disconnected')
    setIsModelSpeaking(false)
    audioChunkCountRef.current = 0
  }, [updateStatus])

  // Send audio chunk (Float32Array from microphone → PCM16 base64)
  const sendAudio = useCallback((chunk: Float32Array) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    const pcm16 = float32ToPcm16(chunk)
    const base64 = arrayBufferToBase64(pcm16.buffer as ArrayBuffer)

    // Track the time of last audio sent (for latency measurement)
    lastAudioSentRef.current = performance.now()

    const msg = {
      realtimeInput: {
        mediaChunks: [
          {
            mimeType: 'audio/pcm;rate=16000',
            data: base64,
          },
        ],
      },
    }

    wsRef.current.send(JSON.stringify(msg))
  }, [])

  // Send text message
  const sendText = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    const msg = {
      clientContent: {
        turns: [
          {
            role: 'user',
            parts: [{ text }],
          },
        ],
        turnComplete: true,
      },
    }

    lastAudioSentRef.current = performance.now()
    audioChunkCountRef.current = 0
    wsRef.current.send(JSON.stringify(msg))
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  return {
    status,
    metrics,
    connect,
    disconnect,
    sendAudio,
    sendText,
    error,
    isModelSpeaking,
  }
}
