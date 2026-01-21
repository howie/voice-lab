/**
 * ConversationHistory Component
 * Feature: 004-interaction-module
 * T095 [US6]: Display conversation turns with audio playback.
 */

import { useState, useRef } from 'react'
import type { ConversationTurn, InteractionSession, LatencyStats } from '@/types/interaction'
import { getTurnAudioUrl, formatLatency, formatDuration } from '@/services/interactionApi'

interface ConversationHistoryProps {
  /** Session details */
  session: InteractionSession
  /** List of conversation turns */
  turns: ConversationTurn[]
  /** Latency statistics for the session */
  latencyStats?: LatencyStats | null
  /** Callback when session delete is requested */
  onDeleteRequest?: () => void
  /** Additional CSS classes */
  className?: string
}

// Audio player component for a single turn
function TurnAudioPlayer({
  sessionId,
  turn,
  audioType,
  label,
}: {
  sessionId: string
  turn: ConversationTurn
  audioType: 'user' | 'ai'
  label: string
}) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const audioPath = audioType === 'user' ? turn.user_audio_path : turn.ai_audio_path
  if (!audioPath) return null

  const audioUrl = getTurnAudioUrl(sessionId, turn.id, audioType)

  const handlePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play().catch((e) => {
          setError(`無法播放: ${e.message}`)
        })
      }
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handlePlay}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary hover:bg-primary/20"
        title={`播放${label}音訊`}
      >
        {isPlaying ? (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
            <path fillRule="evenodd" d="M6.75 5.25a.75.75 0 01.75-.75H9a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H7.5a.75.75 0 01-.75-.75V5.25zm7.5 0A.75.75 0 0115 4.5h1.5a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H15a.75.75 0 01-.75-.75V5.25z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
            <path fillRule="evenodd" d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z" clipRule="evenodd" />
          </svg>
        )}
      </button>
      <span className="text-xs text-muted-foreground">{label}</span>
      <audio
        ref={audioRef}
        src={audioUrl}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
        onError={() => setError('音訊載入失敗')}
      />
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  )
}

export function ConversationHistory({
  session,
  turns,
  latencyStats,
  onDeleteRequest,
  className = '',
}: ConversationHistoryProps) {
  const [expandedTurns, setExpandedTurns] = useState<Set<string>>(new Set())

  const toggleTurn = (turnId: string) => {
    setExpandedTurns((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(turnId)) {
        newSet.delete(turnId)
      } else {
        newSet.add(turnId)
      }
      return newSet
    })
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Session Header */}
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold">對話詳情</h3>
            <p className="text-sm text-muted-foreground">
              {new Date(session.started_at).toLocaleString('zh-TW')}
            </p>
          </div>
          {onDeleteRequest && (
            <button
              onClick={onDeleteRequest}
              className="rounded-lg border border-destructive/50 px-3 py-1.5 text-sm text-destructive hover:bg-destructive/10"
            >
              刪除對話
            </button>
          )}
        </div>

        {/* Session Info Grid */}
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div>
            <span className="text-muted-foreground">模式</span>
            <p className="font-medium">
              {session.mode === 'realtime' ? 'Realtime API' : 'Cascade Mode'}
            </p>
          </div>
          <div>
            <span className="text-muted-foreground">持續時間</span>
            <p className="font-medium">{formatDuration(session.started_at, session.ended_at)}</p>
          </div>
          <div>
            <span className="text-muted-foreground">對話輪數</span>
            <p className="font-medium">{turns.length}</p>
          </div>
          <div>
            <span className="text-muted-foreground">狀態</span>
            <p className="font-medium">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${
                  session.status === 'completed'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : session.status === 'active'
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                      : 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
                }`}
              >
                {session.status === 'completed' ? '已完成' : session.status === 'active' ? '進行中' : '已斷開'}
              </span>
            </p>
          </div>
        </div>

        {/* Latency Stats */}
        {latencyStats && latencyStats.total_turns > 0 && (
          <div className="mt-4 border-t pt-4">
            <h4 className="mb-2 text-sm font-medium">延遲統計</h4>
            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
              <div>
                <span className="text-muted-foreground">平均</span>
                <p className="font-medium">{formatLatency(latencyStats.avg_total_ms)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">最小</span>
                <p className="font-medium">{formatLatency(latencyStats.min_total_ms)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">最大</span>
                <p className="font-medium">{formatLatency(latencyStats.max_total_ms)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">P95</span>
                <p className="font-medium">{formatLatency(latencyStats.p95_total_ms)}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Conversation Turns */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-muted-foreground">對話內容 ({turns.length} 輪)</h4>

        {turns.length === 0 ? (
          <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
            此對話沒有任何輪次記錄
          </div>
        ) : (
          <div className="space-y-2">
            {turns.map((turn) => {
              const isExpanded = expandedTurns.has(turn.id)
              return (
                <div
                  key={turn.id}
                  className="rounded-lg border bg-card overflow-hidden"
                >
                  {/* Turn Header */}
                  <button
                    onClick={() => toggleTurn(turn.id)}
                    className="flex w-full items-center justify-between p-4 text-left hover:bg-accent/50"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                        {turn.turn_number}
                      </span>
                      <div>
                        <p className="text-sm font-medium">
                          {turn.user_transcript
                            ? turn.user_transcript.slice(0, 50) + (turn.user_transcript.length > 50 ? '...' : '')
                            : '(無轉錄文字)'}
                        </p>
                        {turn.interrupted && (
                          <span className="text-xs text-orange-600">已打斷</span>
                        )}
                      </div>
                    </div>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      className={`h-5 w-5 text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    >
                      <path fillRule="evenodd" d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75 0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06 1.06l-7.5 7.5z" clipRule="evenodd" />
                    </svg>
                  </button>

                  {/* Turn Details (Expanded) */}
                  {isExpanded && (
                    <div className="border-t p-4 space-y-4">
                      {/* User Section */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">使用者</span>
                          <TurnAudioPlayer
                            sessionId={session.id}
                            turn={turn}
                            audioType="user"
                            label="使用者音訊"
                          />
                        </div>
                        <p className="text-sm text-foreground bg-blue-50 dark:bg-blue-950/20 rounded-lg p-3">
                          {turn.user_transcript || '(無轉錄文字)'}
                        </p>
                      </div>

                      {/* AI Section */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-purple-600 dark:text-purple-400">AI 回應</span>
                          <TurnAudioPlayer
                            sessionId={session.id}
                            turn={turn}
                            audioType="ai"
                            label="AI 音訊"
                          />
                        </div>
                        <p className="text-sm text-foreground bg-purple-50 dark:bg-purple-950/20 rounded-lg p-3">
                          {turn.ai_response_text || '(無回應文字)'}
                        </p>
                      </div>

                      {/* Turn Metadata */}
                      <div className="text-xs text-muted-foreground flex gap-4">
                        <span>開始: {new Date(turn.started_at).toLocaleTimeString('zh-TW')}</span>
                        {turn.ended_at && (
                          <span>結束: {new Date(turn.ended_at).toLocaleTimeString('zh-TW')}</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationHistory
