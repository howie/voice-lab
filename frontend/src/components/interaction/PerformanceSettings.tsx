/**
 * PerformanceSettings Component
 * Feature: 004-interaction-module
 *
 * Displays V2V performance feature toggles for A/B testing.
 * Allows users to enable/disable optimizations and see trade-offs.
 */

import { useCallback, useEffect, useState } from 'react'

interface FeatureFlag {
  enabled: boolean
  description: string
  trade_off: string
}

interface FeatureFlags {
  lightweight_mode: FeatureFlag
  ws_compression: FeatureFlag
  batch_audio_upload: FeatureFlag
  skip_latency_tracking: FeatureFlag
}

interface PerformanceSettingsProps {
  /** Current lightweight mode setting from store */
  lightweightMode?: boolean
  /** Callback when lightweight mode changes */
  onLightweightModeChange?: (enabled: boolean) => void
  /** Whether settings are disabled (e.g., during active session) */
  disabled?: boolean
  /** Additional CSS classes */
  className?: string
}

export function PerformanceSettings({
  lightweightMode = true,
  onLightweightModeChange,
  disabled = false,
  className = '',
}: PerformanceSettingsProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [serverFlags, setServerFlags] = useState<FeatureFlags | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch feature flags from server
  const fetchFlags = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/v1/interaction/v2v/feature-flags')
      if (!response.ok) throw new Error('Failed to fetch feature flags')
      const data = await response.json()
      setServerFlags(data.feature_flags)
    } catch (err) {
      setError('無法載入效能設定')
      console.error('Failed to fetch feature flags:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isExpanded && !serverFlags && !loading) {
      fetchFlags()
    }
  }, [isExpanded, serverFlags, loading, fetchFlags])

  return (
    <div className={`rounded-lg border bg-card p-4 ${className}`}>
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-sm font-medium text-foreground"
      >
        <div className="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="h-5 w-5 text-primary"
          >
            <path
              fillRule="evenodd"
              d="M14.615 1.595a.75.75 0 01.359.852L12.982 9.75h7.268a.75.75 0 01.548 1.262l-10.5 11.25a.75.75 0 01-1.272-.71l1.992-7.302H3.75a.75.75 0 01-.548-1.262l10.5-11.25a.75.75 0 01.913-.143z"
              clipRule="evenodd"
            />
          </svg>
          <span>效能優化設定</span>
          {lightweightMode && (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400">
              低延遲模式
            </span>
          )}
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className={`h-5 w-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        >
          <path
            fillRule="evenodd"
            d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75 0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06 1.06l-7.5 7.5z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-4 text-muted-foreground">
              <svg
                className="mr-2 h-4 w-4 animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              載入中...
            </div>
          ) : error ? (
            <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
              {error}
              <button
                type="button"
                onClick={fetchFlags}
                className="ml-2 underline hover:no-underline"
              >
                重試
              </button>
            </div>
          ) : (
            <>
              {/* Lightweight Mode Toggle */}
              <div className="rounded-lg border p-3">
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    checked={lightweightMode}
                    onChange={(e) => onLightweightModeChange?.(e.target.checked)}
                    disabled={disabled}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">輕量級模式 (低延遲)</span>
                      {serverFlags?.lightweight_mode.enabled && (
                        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                          伺服器預設
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {serverFlags?.lightweight_mode.description || '跳過即時音訊儲存，減少延遲'}
                    </p>
                    <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                      Trade-off: {serverFlags?.lightweight_mode.trade_off || '音訊需在對話結束後批次上傳'}
                    </p>
                  </div>
                </label>
              </div>

              {/* Info about other server-side flags */}
              {serverFlags && (
                <div className="rounded-lg bg-muted/50 p-3">
                  <h4 className="text-xs font-medium text-muted-foreground">伺服器端設定</h4>
                  <div className="mt-2 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span>WebSocket 壓縮</span>
                      <span
                        className={
                          serverFlags.ws_compression.enabled
                            ? 'text-green-600'
                            : 'text-muted-foreground'
                        }
                      >
                        {serverFlags.ws_compression.enabled ? '已啟用' : '已停用'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>批次音訊上傳</span>
                      <span
                        className={
                          serverFlags.batch_audio_upload.enabled
                            ? 'text-green-600'
                            : 'text-muted-foreground'
                        }
                      >
                        {serverFlags.batch_audio_upload.enabled ? '已啟用' : '已停用'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>跳過延遲追蹤</span>
                      <span
                        className={
                          serverFlags.skip_latency_tracking.enabled
                            ? 'text-green-600'
                            : 'text-muted-foreground'
                        }
                      >
                        {serverFlags.skip_latency_tracking.enabled ? '已啟用' : '已停用'}
                      </span>
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    這些設定由環境變數控制，需在伺服器端修改
                  </p>
                </div>
              )}

              {/* Performance Tips */}
              <div className="rounded-lg border-l-4 border-primary bg-primary/5 p-3">
                <h4 className="text-sm font-medium text-primary">效能建議</h4>
                <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                  <li>- 啟用輕量級模式可減少約 50-100ms 延遲</li>
                  <li>- 使用 Gemini 2.5 Flash 可獲得更自然的語音</li>
                  <li>- 網路品質對延遲影響最大，建議使用有線網路</li>
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default PerformanceSettings
