/**
 * Quota Display Component
 * Feature: 012-music-generation
 *
 * Display user's music generation quota status.
 */

import { useEffect } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'
import { useMusicStore, selectQuotaUsagePercent } from '@/stores/musicStore'

export function QuotaDisplay() {
  const { quota, fetchQuota } = useMusicStore()
  const usagePercent = useMusicStore(selectQuotaUsagePercent)

  useEffect(() => {
    fetchQuota()
    // Refresh quota every minute
    const interval = setInterval(fetchQuota, 60000)
    return () => clearInterval(interval)
  }, [fetchQuota])

  if (!quota) {
    return (
      <div className="animate-pulse rounded-lg border bg-muted/50 p-4">
        <div className="h-4 w-24 rounded bg-muted" />
        <div className="mt-2 h-3 w-full rounded bg-muted" />
      </div>
    )
  }

  const isWarning = usagePercent >= 80
  const isExceeded = !quota.can_submit

  return (
    <div
      className={`rounded-lg border p-4 ${
        isExceeded
          ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
          : isWarning
            ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20'
            : 'bg-card'
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">配額使用</h3>
        {isExceeded ? (
          <AlertCircle className="h-4 w-4 text-red-500" />
        ) : quota.can_submit ? (
          <CheckCircle className="h-4 w-4 text-green-500" />
        ) : null}
      </div>

      <div className="space-y-3">
        {/* Daily usage */}
        <div>
          <div className="mb-1 flex justify-between text-xs">
            <span className="text-muted-foreground">今日</span>
            <span className={isWarning ? 'font-medium text-yellow-600 dark:text-yellow-400' : ''}>
              {quota.daily_used} / {quota.daily_limit}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full transition-all ${
                usagePercent >= 100
                  ? 'bg-red-500'
                  : isWarning
                    ? 'bg-yellow-500'
                    : 'bg-primary'
              }`}
              style={{ width: `${Math.min(usagePercent, 100)}%` }}
            />
          </div>
        </div>

        {/* Monthly usage */}
        <div>
          <div className="mb-1 flex justify-between text-xs">
            <span className="text-muted-foreground">本月</span>
            <span>
              {quota.monthly_used} / {quota.monthly_limit}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-secondary transition-all"
              style={{
                width: `${Math.min((quota.monthly_used / quota.monthly_limit) * 100, 100)}%`,
              }}
            />
          </div>
        </div>

        {/* Concurrent jobs */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">同時處理中</span>
          <span
            className={
              quota.concurrent_jobs >= quota.max_concurrent_jobs
                ? 'font-medium text-red-600 dark:text-red-400'
                : ''
            }
          >
            {quota.concurrent_jobs} / {quota.max_concurrent_jobs}
          </span>
        </div>
      </div>

      {isExceeded && (
        <p className="mt-3 text-xs text-red-600 dark:text-red-400">
          {quota.concurrent_jobs >= quota.max_concurrent_jobs
            ? '已達同時處理上限，請等待現有任務完成'
            : quota.daily_used >= quota.daily_limit
              ? '今日配額已用完，請明天再試'
              : '本月配額已用完，請聯繫管理員'}
        </p>
      )}
    </div>
  )
}

export default QuotaDisplay
