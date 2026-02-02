import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Gauge,
  Loader2,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  quotaApi,
  type AppRateLimitStatus,
  type ProviderQuotaStatus,
  type QuotaDashboardResponse,
} from '@/services/quotaApi'
import { getProviderTheme } from '@/services/credentialService'

function UsageBar({ percent, className }: { percent: number; className?: string }) {
  const color =
    percent >= 90
      ? 'bg-red-500'
      : percent >= 70
        ? 'bg-yellow-500'
        : 'bg-green-500'

  return (
    <div className={cn('h-2 w-full rounded-full bg-muted', className)}>
      <div
        className={cn('h-2 rounded-full transition-all', color)}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  )
}

function ProviderQuotaCard({ status }: { status: ProviderQuotaStatus }) {
  const theme = getProviderTheme(status.provider)

  return (
    <div className="rounded-xl border bg-card p-5 transition-shadow hover:shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold"
            style={{ backgroundColor: theme.bgColor, color: theme.color }}
          >
            {status.display_name.charAt(0)}
          </div>
          <div>
            <h3 className="font-semibold">{status.display_name}</h3>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {status.has_credential ? (
                status.is_valid ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                    已設定
                  </>
                ) : (
                  <>
                    <XCircle className="h-3 w-3 text-red-500" />
                    金鑰無效
                  </>
                )
              ) : (
                <>
                  <ShieldAlert className="h-3 w-3 text-gray-400" />
                  未設定
                </>
              )}
            </div>
          </div>
        </div>
        {status.help_url && (
          <a
            href={status.help_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground transition-colors hover:text-primary"
            title="查看配額管理"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>

      {/* Tracked Usage (from in-memory tracker) */}
      {status.day_requests > 0 && (
        <div className="mt-4 rounded-md bg-muted/50 p-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">本次工作階段用量</p>
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <div className="text-lg font-bold">{status.minute_requests}</div>
              <div className="text-muted-foreground">本分鐘</div>
            </div>
            <div>
              <div className="text-lg font-bold">{status.hour_requests}</div>
              <div className="text-muted-foreground">本小時</div>
            </div>
            <div>
              <div className="text-lg font-bold">{status.day_requests}</div>
              <div className="text-muted-foreground">今日</div>
            </div>
          </div>
          {status.estimated_rpm_limit && (
            <p className="mt-2 text-xs text-muted-foreground">
              預估 RPM 上限：~{status.estimated_rpm_limit} 次/分鐘
            </p>
          )}
          {status.quota_hits_today > 0 && (
            <div className="mt-1 flex items-center gap-1 text-xs text-amber-600">
              <AlertTriangle className="h-3 w-3" />
              今日觸發 {status.quota_hits_today} 次配額限制
            </div>
          )}
          {status.usage_warning && (
            <p className="mt-1 text-xs font-medium text-amber-600">{status.usage_warning}</p>
          )}
        </div>
      )}

      {/* Quota Usage (from provider API, e.g. ElevenLabs) */}
      {status.character_count !== null && status.character_limit !== null && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">字元用量</span>
            <span className="font-medium">
              {status.character_count.toLocaleString()} / {status.character_limit.toLocaleString()}
            </span>
          </div>
          <UsageBar percent={status.usage_percent ?? 0} />
          {status.remaining_characters !== null && (
            <p className="text-xs text-muted-foreground">
              剩餘 {status.remaining_characters.toLocaleString()} 字元
            </p>
          )}
          {status.usage_percent !== null && status.usage_percent >= 80 && (
            <div className="flex items-center gap-1 text-xs text-yellow-600">
              <AlertTriangle className="h-3 w-3" />
              配額即將用盡
            </div>
          )}
        </div>
      )}

      {/* Rate Limit Reference */}
      {status.rate_limits && (
        <div className="mt-4 space-y-1.5">
          <p className="text-xs font-medium text-muted-foreground">速率限制參考</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {status.rate_limits.free_rpm !== null && (
              <>
                <span className="text-muted-foreground">Free</span>
                <span>{status.rate_limits.free_rpm} RPM</span>
              </>
            )}
            {status.rate_limits.tier1_rpm !== null && (
              <>
                <span className="text-muted-foreground">Tier 1</span>
                <span>{status.rate_limits.tier1_rpm} RPM</span>
              </>
            )}
            {status.rate_limits.tier2_rpm !== null && (
              <>
                <span className="text-muted-foreground">Tier 2</span>
                <span>{status.rate_limits.tier2_rpm} RPM</span>
              </>
            )}
          </div>
          {status.rate_limits.notes && (
            <p className="text-xs text-muted-foreground">{status.rate_limits.notes}</p>
          )}
        </div>
      )}

      {/* Tier Badge */}
      {status.tier && (
        <div className="mt-3">
          <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            {status.tier}
          </span>
        </div>
      )}

      {/* Last Validated */}
      {status.last_validated_at && (
        <p className="mt-3 text-xs text-muted-foreground">
          上次驗證：{new Date(status.last_validated_at).toLocaleString('zh-TW')}
        </p>
      )}
    </div>
  )
}

function AppRateLimitCard({ limits }: { limits: AppRateLimitStatus }) {
  const generalMinutePercent =
    ((limits.general_rpm - limits.general_minute_remaining) / limits.general_rpm) * 100
  const generalHourPercent =
    ((limits.general_rph - limits.general_hour_remaining) / limits.general_rph) * 100
  const ttsMinutePercent =
    ((limits.tts_rpm - limits.tts_minute_remaining) / limits.tts_rpm) * 100
  const ttsHourPercent =
    ((limits.tts_rph - limits.tts_hour_remaining) / limits.tts_rph) * 100

  return (
    <div className="rounded-xl border bg-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Gauge className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">應用程式速率限制</h2>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* General Limits */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium">一般 API</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">每分鐘</span>
              <span className="font-medium">
                {limits.general_minute_remaining} / {limits.general_rpm}
              </span>
            </div>
            <UsageBar percent={generalMinutePercent} />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">每小時</span>
              <span className="font-medium">
                {limits.general_hour_remaining} / {limits.general_rph}
              </span>
            </div>
            <UsageBar percent={generalHourPercent} />
          </div>
        </div>

        {/* TTS-Specific Limits */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium">TTS 合成</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">每分鐘</span>
              <span className="font-medium">
                {limits.tts_minute_remaining} / {limits.tts_rpm}
              </span>
            </div>
            <UsageBar percent={ttsMinutePercent} />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">每小時</span>
              <span className="font-medium">
                {limits.tts_hour_remaining} / {limits.tts_rph}
              </span>
            </div>
            <UsageBar percent={ttsHourPercent} />
          </div>
        </div>
      </div>
    </div>
  )
}

export function QuotaDashboardPage() {
  const [data, setData] = useState<QuotaDashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      const response = await quotaApi.getDashboard()
      setData(response)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch quota data:', err)
      setError('無法載入配額資訊')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const configuredProviders = data?.providers.filter((p) => p.has_credential) ?? []
  const unconfiguredProviders = data?.providers.filter((p) => !p.has_credential) ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">配額與速率限制</h1>
          <p className="mt-1 text-muted-foreground">
            查看各 Provider 的 API 配額和速率限制狀態
          </p>
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
        >
          <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
          重新整理
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">載入中...</span>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900 dark:bg-red-950">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      ) : data ? (
        <>
          {/* App Rate Limits */}
          <AppRateLimitCard limits={data.app_rate_limits} />

          {/* Configured Providers */}
          {configuredProviders.length > 0 && (
            <div>
              <div className="mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold">已設定的 Provider</h2>
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {configuredProviders.length}
                </span>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {configuredProviders.map((status) => (
                  <ProviderQuotaCard key={status.provider} status={status} />
                ))}
              </div>
            </div>
          )}

          {/* Unconfigured Providers */}
          {unconfiguredProviders.length > 0 && (
            <div>
              <h2 className="mb-4 text-lg font-semibold text-muted-foreground">
                未設定的 Provider
              </h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {unconfiguredProviders.map((status) => (
                  <ProviderQuotaCard key={status.provider} status={status} />
                ))}
              </div>
            </div>
          )}

          {/* Fetch timestamp */}
          <p className="text-right text-xs text-muted-foreground">
            資料更新時間：{new Date(data.fetched_at).toLocaleString('zh-TW')}
          </p>
        </>
      ) : null}
    </div>
  )
}
