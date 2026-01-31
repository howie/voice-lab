/**
 * Gemini Live API Direct Test Page
 *
 * Connects the browser directly to Google's Gemini Live API WebSocket
 * to benchmark the best-case v2v (voice-to-voice) latency without
 * going through the backend proxy.
 *
 * Architecture: Browser → Gemini WebSocket (direct, no backend hop)
 * Audio: Mic 16kHz PCM16 → base64 → Gemini → 24kHz PCM16 base64 → Speaker
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useMicrophone } from '@/hooks/useMicrophone'
import { useAudioPlayback } from '@/hooks/useAudioPlayback'
import { useGeminiLive } from '@/hooks/useGeminiLive'
import type { GeminiLiveConfig, GeminiConnectionStatus } from '@/hooks/useGeminiLive'

// =============================================================================
// Types
// =============================================================================

interface GeminiConfig {
  api_key: string
  ws_url: string
  model: string
  default_voice: string
  available_models: string[]
  available_voices: string[]
}

// =============================================================================
// Status helpers
// =============================================================================

function statusLabel(status: GeminiConnectionStatus): string {
  const labels: Record<GeminiConnectionStatus, string> = {
    disconnected: '未連線',
    connecting: '連線中...',
    setup_sent: '初始化中...',
    connected: '已連線',
    error: '錯誤',
  }
  return labels[status]
}

function statusColor(status: GeminiConnectionStatus): string {
  const colors: Record<GeminiConnectionStatus, string> = {
    disconnected: 'bg-gray-400',
    connecting: 'bg-yellow-400 animate-pulse',
    setup_sent: 'bg-yellow-400 animate-pulse',
    connected: 'bg-green-500',
    error: 'bg-red-500',
  }
  return colors[status]
}

// =============================================================================
// Component
// =============================================================================

export function GeminiLiveTestPage() {
  // ---------------------------------------------------------------------------
  // Backend config
  // ---------------------------------------------------------------------------
  const [config, setConfig] = useState<GeminiConfig | null>(null)
  const [configError, setConfigError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // ---------------------------------------------------------------------------
  // User settings
  // ---------------------------------------------------------------------------
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedVoice, setSelectedVoice] = useState('')
  const [systemPrompt, setSystemPrompt] = useState(
    '你是一個親切的助手，請用繁體中文回答。回答盡量簡短。'
  )

  // ---------------------------------------------------------------------------
  // Transcript state
  // ---------------------------------------------------------------------------
  const [inputTranscript, setInputTranscript] = useState('')
  const [outputTranscript, setOutputTranscript] = useState('')
  const [conversationLog, setConversationLog] = useState<
    { role: 'user' | 'ai'; text: string; timestamp: number }[]
  >([])
  const logEndRef = useRef<HTMLDivElement>(null)

  // ---------------------------------------------------------------------------
  // Text input
  // ---------------------------------------------------------------------------
  const [textInput, setTextInput] = useState('')

  // ---------------------------------------------------------------------------
  // Audio playback (24kHz PCM16 from Gemini)
  // ---------------------------------------------------------------------------
  const audioPlayback = useAudioPlayback({
    sampleRate: 24000,
    channelCount: 1,
    onPlaybackEnd: () => {
      console.log('[TestPage] Playback ended')
    },
  })

  // Base64 → ArrayBuffer helper
  const base64ToArrayBuffer = useCallback((base64: string): ArrayBuffer => {
    const binary = atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return bytes.buffer
  }, [])

  // ---------------------------------------------------------------------------
  // Gemini Live connection
  // ---------------------------------------------------------------------------
  const gemini = useGeminiLive({
    onAudioData: useCallback(
      (base64Audio: string) => {
        const pcm16 = base64ToArrayBuffer(base64Audio)
        audioPlayback.queueAudioChunk(pcm16, 'pcm16')
      },
      [base64ToArrayBuffer, audioPlayback]
    ),
    onInputTranscript: useCallback((text: string) => {
      setInputTranscript((prev) => prev + text)
    }, []),
    onOutputTranscript: useCallback((text: string) => {
      setOutputTranscript((prev) => prev + text)
    }, []),
    onTurnComplete: useCallback(() => {
      // Save transcripts to conversation log
      setInputTranscript((prev) => {
        if (prev.trim()) {
          setConversationLog((log) => [
            ...log,
            { role: 'user', text: prev.trim(), timestamp: Date.now() },
          ])
        }
        return ''
      })
      setOutputTranscript((prev) => {
        if (prev.trim()) {
          setConversationLog((log) => [
            ...log,
            { role: 'ai', text: prev.trim(), timestamp: Date.now() },
          ])
        }
        return ''
      })
    }, []),
    onInterrupted: useCallback(() => {
      audioPlayback.stop()
    }, [audioPlayback]),
  })

  // ---------------------------------------------------------------------------
  // Microphone (16kHz PCM16)
  // ---------------------------------------------------------------------------
  const microphone = useMicrophone({
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
    onAudioChunk: useCallback(
      (chunk: Float32Array) => {
        gemini.sendAudio(chunk)
      },
      [gemini]
    ),
  })

  // ---------------------------------------------------------------------------
  // Fetch config from backend
  // ---------------------------------------------------------------------------
  useEffect(() => {
    async function fetchConfig() {
      try {
        const res = await api.get<GeminiConfig>('/gemini-live-test/config')
        setConfig(res.data)
        setSelectedModel(res.data.model)
        setSelectedVoice(res.data.default_voice)
      } catch (err) {
        const msg =
          err instanceof Error
            ? err.message
            : 'Failed to fetch Gemini config'
        setConfigError(msg)
      } finally {
        setLoading(false)
      }
    }
    fetchConfig()
  }, [])

  // Auto-scroll conversation log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversationLog, inputTranscript, outputTranscript])

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  const handleConnect = useCallback(() => {
    if (!config) return

    const liveConfig: GeminiLiveConfig = {
      apiKey: config.api_key,
      wsUrl: config.ws_url,
      model: selectedModel,
      voice: selectedVoice,
      systemPrompt,
    }

    gemini.connect(liveConfig)
  }, [config, selectedModel, selectedVoice, systemPrompt, gemini])

  const handleDisconnect = useCallback(() => {
    microphone.stopRecording()
    audioPlayback.stop()
    gemini.disconnect()
  }, [microphone, audioPlayback, gemini])

  const handleToggleMic = useCallback(async () => {
    if (microphone.isRecording) {
      microphone.stopRecording()
    } else {
      await microphone.startRecording()
    }
  }, [microphone])

  const handleSendText = useCallback(() => {
    if (!textInput.trim()) return
    gemini.sendText(textInput.trim())
    setConversationLog((prev) => [
      ...prev,
      { role: 'user', text: textInput.trim(), timestamp: Date.now() },
    ])
    setTextInput('')
  }, [textInput, gemini])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSendText()
      }
    },
    [handleSendText]
  )

  // ---------------------------------------------------------------------------
  // Compute average first-byte latency
  // ---------------------------------------------------------------------------
  const avgFirstByte =
    gemini.metrics.firstByteHistory.length > 0
      ? Math.round(
          gemini.metrics.firstByteHistory.reduce((a, b) => a + b, 0) /
            gemini.metrics.firstByteHistory.length
        )
      : null

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-muted-foreground">載入設定中...</div>
      </div>
    )
  }

  if (configError) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-6">
        <h1 className="text-2xl font-bold">Gemini Live API 直連測試</h1>
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          <p className="font-medium">無法取得 Gemini 設定</p>
          <p className="mt-1 text-sm">{configError}</p>
          <p className="mt-2 text-sm">
            請確認已設定 <code className="rounded bg-red-100 px-1 dark:bg-red-900">GOOGLE_AI_API_KEY</code> 環境變數。
          </p>
        </div>
      </div>
    )
  }

  const isConnected = gemini.status === 'connected'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Gemini Live API 直連測試</h1>
        <p className="mt-1 text-muted-foreground">
          瀏覽器直接連線 Gemini WebSocket，不經過 Backend Proxy —— 測試最佳 v2v 延遲
        </p>
      </div>

      <div className="mx-auto grid max-w-5xl gap-6 lg:grid-cols-[1fr_320px]">
        {/* Main panel */}
        <div className="space-y-4">
          {/* Connection status bar */}
          <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
            <div className={cn('h-3 w-3 rounded-full', statusColor(gemini.status))} />
            <span className="text-sm font-medium">{statusLabel(gemini.status)}</span>
            {gemini.error && (
              <span className="text-sm text-red-500">{gemini.error}</span>
            )}
            <div className="flex-1" />
            {!isConnected ? (
              <button
                onClick={handleConnect}
                disabled={gemini.status === 'connecting' || gemini.status === 'setup_sent'}
                className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                連線
              </button>
            ) : (
              <button
                onClick={handleDisconnect}
                className="rounded-md bg-destructive px-4 py-1.5 text-sm font-medium text-destructive-foreground hover:bg-destructive/90"
              >
                斷線
              </button>
            )}
          </div>

          {/* Mic + volume */}
          {isConnected && (
            <div className="flex items-center gap-4 rounded-lg border bg-card p-3">
              <button
                onClick={handleToggleMic}
                className={cn(
                  'flex h-12 w-12 items-center justify-center rounded-full text-white transition-all',
                  microphone.isRecording
                    ? 'bg-red-500 shadow-lg shadow-red-500/30'
                    : 'bg-gray-500 hover:bg-gray-600'
                )}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" x2="12" y1="19" y2="22" />
                </svg>
              </button>

              <div className="flex-1">
                <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{microphone.isRecording ? '錄音中 (16kHz)' : '點擊開始錄音'}</span>
                  <span>音量: {Math.round(microphone.volume * 100)}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-green-500 transition-all duration-75"
                    style={{ width: `${microphone.volume * 100}%` }}
                  />
                </div>
              </div>

              {gemini.isModelSpeaking && (
                <div className="flex items-center gap-1.5 text-sm text-blue-500">
                  <div className="flex gap-0.5">
                    <div className="h-3 w-1 animate-pulse rounded-full bg-blue-500" style={{ animationDelay: '0ms' }} />
                    <div className="h-4 w-1 animate-pulse rounded-full bg-blue-500" style={{ animationDelay: '150ms' }} />
                    <div className="h-3 w-1 animate-pulse rounded-full bg-blue-500" style={{ animationDelay: '300ms' }} />
                    <div className="h-5 w-1 animate-pulse rounded-full bg-blue-500" style={{ animationDelay: '100ms' }} />
                  </div>
                  <span>AI 回覆中</span>
                </div>
              )}
            </div>
          )}

          {/* Text input (alternative to voice) */}
          {isConnected && (
            <div className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="或直接輸入文字測試..."
                className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
              />
              <button
                onClick={handleSendText}
                disabled={!textInput.trim()}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                發送
              </button>
            </div>
          )}

          {/* Conversation log */}
          <div className="rounded-lg border bg-card">
            <div className="border-b px-4 py-2">
              <h3 className="text-sm font-medium">對話紀錄</h3>
            </div>
            <div className="h-[400px] overflow-y-auto p-4">
              {conversationLog.length === 0 &&
                !inputTranscript &&
                !outputTranscript && (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    {isConnected
                      ? '開始說話或輸入文字...'
                      : '連線後即可開始對話'}
                  </div>
                )}

              {conversationLog.map((entry, i) => (
                <div
                  key={i}
                  className={cn(
                    'mb-3 rounded-lg px-3 py-2 text-sm',
                    entry.role === 'user'
                      ? 'ml-8 bg-primary/10 text-right'
                      : 'mr-8 bg-muted'
                  )}
                >
                  <div className="mb-0.5 text-[10px] font-medium uppercase text-muted-foreground">
                    {entry.role === 'user' ? 'You' : 'Gemini'}
                  </div>
                  {entry.text}
                </div>
              ))}

              {/* Live transcripts */}
              {inputTranscript && (
                <div className="mb-3 ml-8 rounded-lg bg-primary/10 px-3 py-2 text-right text-sm opacity-70">
                  <div className="mb-0.5 text-[10px] font-medium uppercase text-muted-foreground">
                    You (即時)
                  </div>
                  {inputTranscript}
                </div>
              )}
              {outputTranscript && (
                <div className="mb-3 mr-8 rounded-lg bg-muted px-3 py-2 text-sm opacity-70">
                  <div className="mb-0.5 text-[10px] font-medium uppercase text-muted-foreground">
                    Gemini (即時)
                  </div>
                  {outputTranscript}
                </div>
              )}

              <div ref={logEndRef} />
            </div>
          </div>
        </div>

        {/* Sidebar - config + metrics */}
        <div className="space-y-4">
          {/* Configuration */}
          <div className="rounded-lg border bg-card p-4">
            <h3 className="mb-3 text-sm font-medium">連線設定</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">
                  模型
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={isConnected}
                  className="w-full rounded-md border bg-background px-2 py-1.5 text-xs disabled:opacity-50"
                >
                  {config?.available_models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs text-muted-foreground">
                  語音
                </label>
                <select
                  value={selectedVoice}
                  onChange={(e) => setSelectedVoice(e.target.value)}
                  disabled={isConnected}
                  className="w-full rounded-md border bg-background px-2 py-1.5 text-xs disabled:opacity-50"
                >
                  {config?.available_voices.map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs text-muted-foreground">
                  System Prompt
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  disabled={isConnected}
                  rows={3}
                  className="w-full rounded-md border bg-background px-2 py-1.5 text-xs disabled:opacity-50"
                />
              </div>
            </div>
          </div>

          {/* Latency Metrics */}
          <div className="rounded-lg border bg-card p-4">
            <h3 className="mb-3 text-sm font-medium">延遲指標</h3>
            <div className="space-y-2 text-xs">
              <MetricRow
                label="Setup 延遲"
                value={gemini.metrics.setupLatencyMs}
                unit="ms"
              />
              <MetricRow
                label="首個音訊 Byte"
                value={gemini.metrics.firstAudioByteMs}
                unit="ms"
                highlight
              />
              <MetricRow
                label="音訊串流時長"
                value={gemini.metrics.audioStreamDurationMs}
                unit="ms"
              />
              <MetricRow
                label="總回應時間"
                value={gemini.metrics.totalRoundTripMs}
                unit="ms"
              />
              <MetricRow
                label="音訊 Chunks"
                value={gemini.metrics.audioChunksReceived}
                unit=""
              />
              <div className="border-t pt-2">
                <MetricRow
                  label="平均首 Byte"
                  value={avgFirstByte}
                  unit="ms"
                  highlight
                />
                <MetricRow
                  label="測量次數"
                  value={gemini.metrics.firstByteHistory.length}
                  unit=""
                />
              </div>
            </div>
          </div>

          {/* Architecture info */}
          <div className="rounded-lg border bg-card p-4">
            <h3 className="mb-2 text-sm font-medium">架構說明</h3>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="rounded bg-muted p-2 font-mono">
                Browser → Gemini WS
              </div>
              <p>
                <strong>直連模式：</strong>
                瀏覽器直接與 Gemini Live API WebSocket 通訊，無 Backend 中繼。
              </p>
              <p>
                <strong>音訊格式：</strong>
                輸入 PCM16 16kHz / 輸出 PCM16 24kHz
              </p>
              <p>
                <strong>目的：</strong>
                測試 Gemini v2v 原生延遲下限，作為架構優化的參考基準。
              </p>
            </div>
          </div>

          {/* First-byte history chart */}
          {gemini.metrics.firstByteHistory.length > 0 && (
            <div className="rounded-lg border bg-card p-4">
              <h3 className="mb-2 text-sm font-medium">首 Byte 延遲歷史</h3>
              <div className="flex items-end gap-1" style={{ height: 80 }}>
                {gemini.metrics.firstByteHistory.map((ms, i) => {
                  const max = Math.max(...gemini.metrics.firstByteHistory, 1)
                  const height = (ms / max) * 100
                  return (
                    <div
                      key={i}
                      className="flex flex-1 flex-col items-center gap-0.5"
                    >
                      <span className="text-[9px] text-muted-foreground">
                        {ms}
                      </span>
                      <div
                        className={cn(
                          'w-full min-w-[4px] rounded-t',
                          ms < 800
                            ? 'bg-green-500'
                            : ms < 1500
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                        )}
                        style={{ height: `${height}%` }}
                      />
                    </div>
                  )
                })}
              </div>
              <div className="mt-1 flex justify-between text-[9px] text-muted-foreground">
                <span>Turns</span>
                <span>
                  &lt;800ms{' '}
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />{' '}
                  &lt;1.5s{' '}
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-yellow-500" />{' '}
                  &gt;1.5s{' '}
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500" />
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Sub-components
// =============================================================================

function MetricRow({
  label,
  value,
  unit,
  highlight,
}: {
  label: string
  value: number | null
  unit: string
  highlight?: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={cn(
          'font-mono tabular-nums',
          highlight && value !== null ? 'font-semibold text-blue-500' : ''
        )}
      >
        {value !== null ? `${value}${unit}` : '—'}
      </span>
    </div>
  )
}

export default GeminiLiveTestPage
