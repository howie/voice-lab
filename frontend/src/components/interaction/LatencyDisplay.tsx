/**
 * LatencyDisplay Component
 * Feature: 004-interaction-module
 * T064-T066: Display latency metrics for voice interaction turns.
 *
 * Shows real-time latency breakdown including:
 * - Total latency
 * - STT, LLM TTFT, TTS TTFB segments for Cascade mode
 * - Realtime latency for Realtime mode
 */

import type { InteractionMode, LatencyStats, TurnLatencyData } from '@/types/interaction'

interface LatencyDisplayProps {
  /** Current turn latency data */
  turnLatency: TurnLatencyData | null
  /** Session-level statistics */
  sessionStats: LatencyStats | null
  /** Current interaction mode */
  mode: InteractionMode
  /** Whether to show the detailed breakdown */
  showBreakdown?: boolean
  /** Whether to show session statistics */
  showSessionStats?: boolean
  /** Additional CSS classes */
  className?: string
}

// Color mapping for different segments
const SEGMENT_COLORS = {
  stt: 'bg-blue-500',
  llm: 'bg-purple-500',
  tts: 'bg-green-500',
  realtime: 'bg-amber-500',
}

// Format milliseconds for display
function formatMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return '-'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// Calculate percentage for bar width
function calculatePercentage(value: number | null, total: number): number {
  if (!value || total === 0) return 0
  return Math.min(100, Math.round((value / total) * 100))
}

export function LatencyDisplay({
  turnLatency,
  sessionStats,
  mode,
  showBreakdown = true,
  showSessionStats = false,
  className = '',
}: LatencyDisplayProps) {
  const isCascadeMode = mode === 'cascade'
  const hasLatency = turnLatency !== null

  if (!hasLatency && !showSessionStats) {
    return null
  }

  return (
    <div className={`rounded-lg border bg-card p-4 ${className}`}>
      <h4 className="mb-3 text-sm font-medium text-foreground">延遲指標</h4>

      {/* Current Turn Latency */}
      {turnLatency && (
        <div className="space-y-3">
          {/* Total Latency */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">總延遲</span>
            <span className="text-lg font-semibold text-foreground">
              {formatMs(turnLatency.total_ms)}
            </span>
          </div>

          {/* Segment Breakdown for Cascade Mode (T066) */}
          {showBreakdown && isCascadeMode && turnLatency.total_ms > 0 && (
            <div className="space-y-2">
              {/* Visual Bar */}
              <div className="flex h-6 w-full overflow-hidden rounded-full bg-muted">
                {turnLatency.stt_ms !== null && (
                  <div
                    className={`${SEGMENT_COLORS.stt} flex items-center justify-center text-xs text-white`}
                    style={{
                      width: `${calculatePercentage(turnLatency.stt_ms, turnLatency.total_ms)}%`,
                    }}
                    title={`STT: ${formatMs(turnLatency.stt_ms)}`}
                  >
                    {calculatePercentage(turnLatency.stt_ms, turnLatency.total_ms) > 15 && 'STT'}
                  </div>
                )}
                {turnLatency.llm_ttft_ms !== null && (
                  <div
                    className={`${SEGMENT_COLORS.llm} flex items-center justify-center text-xs text-white`}
                    style={{
                      width: `${calculatePercentage(turnLatency.llm_ttft_ms, turnLatency.total_ms)}%`,
                    }}
                    title={`LLM: ${formatMs(turnLatency.llm_ttft_ms)}`}
                  >
                    {calculatePercentage(turnLatency.llm_ttft_ms, turnLatency.total_ms) > 15 &&
                      'LLM'}
                  </div>
                )}
                {turnLatency.tts_ttfb_ms !== null && (
                  <div
                    className={`${SEGMENT_COLORS.tts} flex items-center justify-center text-xs text-white`}
                    style={{
                      width: `${calculatePercentage(turnLatency.tts_ttfb_ms, turnLatency.total_ms)}%`,
                    }}
                    title={`TTS: ${formatMs(turnLatency.tts_ttfb_ms)}`}
                  >
                    {calculatePercentage(turnLatency.tts_ttfb_ms, turnLatency.total_ms) > 15 &&
                      'TTS'}
                  </div>
                )}
              </div>

              {/* Segment Details */}
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="flex items-center gap-1">
                  <span className={`h-2 w-2 rounded-full ${SEGMENT_COLORS.stt}`} />
                  <span className="text-muted-foreground">STT:</span>
                  <span className="font-medium">{formatMs(turnLatency.stt_ms)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className={`h-2 w-2 rounded-full ${SEGMENT_COLORS.llm}`} />
                  <span className="text-muted-foreground">LLM:</span>
                  <span className="font-medium">{formatMs(turnLatency.llm_ttft_ms)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className={`h-2 w-2 rounded-full ${SEGMENT_COLORS.tts}`} />
                  <span className="text-muted-foreground">TTS:</span>
                  <span className="font-medium">{formatMs(turnLatency.tts_ttfb_ms)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Realtime Mode Display */}
          {showBreakdown && !isCascadeMode && turnLatency.realtime_ms !== null && (
            <div className="flex items-center gap-2 text-xs">
              <span className={`h-2 w-2 rounded-full ${SEGMENT_COLORS.realtime}`} />
              <span className="text-muted-foreground">Realtime API:</span>
              <span className="font-medium">{formatMs(turnLatency.realtime_ms)}</span>
            </div>
          )}
        </div>
      )}

      {/* Session Statistics (T067) */}
      {showSessionStats && sessionStats && sessionStats.total_turns > 0 && (
        <div className={`${hasLatency ? 'mt-4 border-t pt-4' : ''}`}>
          <h5 className="mb-2 text-xs font-medium text-muted-foreground">
            對話統計 ({sessionStats.total_turns} 輪)
          </h5>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">平均</span>
              <span className="font-medium">{formatMs(sessionStats.avg_total_ms)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">最小</span>
              <span className="font-medium">{formatMs(sessionStats.min_total_ms)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">最大</span>
              <span className="font-medium">{formatMs(sessionStats.max_total_ms)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">P95</span>
              <span className="font-medium">{formatMs(sessionStats.p95_total_ms)}</span>
            </div>
          </div>

          {/* Cascade Mode Averages */}
          {isCascadeMode && (
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
              <div className="flex flex-col">
                <span className="text-muted-foreground">平均 STT</span>
                <span className="font-medium">{formatMs(sessionStats.avg_stt_ms)}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-muted-foreground">平均 LLM</span>
                <span className="font-medium">{formatMs(sessionStats.avg_llm_ttft_ms)}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-muted-foreground">平均 TTS</span>
                <span className="font-medium">{formatMs(sessionStats.avg_tts_ttfb_ms)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LatencyDisplay
