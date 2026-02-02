import { useEffect, useState } from 'react'
import { AlertTriangle, Clock, ExternalLink, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { QuotaErrorDetails } from '@/lib/error-types'
import { formatRetryAfter } from '@/lib/error-messages'

interface QuotaErrorAlertProps {
  message: string
  details: QuotaErrorDetails
  className?: string
}

function CountdownTimer({ seconds }: { seconds: number }) {
  const [remaining, setRemaining] = useState(seconds)

  useEffect(() => {
    setRemaining(seconds)
    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [seconds])

  if (remaining <= 0) {
    return <span className="text-green-600 dark:text-green-400">可以重試了</span>
  }

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  return (
    <span className="tabular-nums">
      {mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs} 秒`}
    </span>
  )
}

export function QuotaErrorAlert({ message, details, className }: QuotaErrorAlertProps) {
  const ctx = details.usage_context

  return (
    <div
      className={cn(
        'space-y-3 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
        <div className="min-w-0">
          <p className="font-medium text-amber-800 dark:text-amber-200">{message}</p>
          {details.retry_after && (
            <div className="mt-1 flex items-center gap-1.5 text-sm text-amber-700 dark:text-amber-300">
              <Clock className="h-3.5 w-3.5" />
              <span>{formatRetryAfter(details.retry_after)}</span>
              <span className="text-muted-foreground">—</span>
              <CountdownTimer seconds={details.retry_after} />
            </div>
          )}
        </div>
      </div>

      {/* Usage Context */}
      {ctx && (
        <div className="rounded-md bg-amber-100/50 p-3 dark:bg-amber-900/30">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-amber-800 dark:text-amber-200">
            <TrendingUp className="h-3.5 w-3.5" />
            本次工作階段用量
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <div className="text-lg font-bold text-amber-900 dark:text-amber-100">
                {ctx.minute_requests}
              </div>
              <div className="text-amber-600 dark:text-amber-400">本分鐘</div>
            </div>
            <div>
              <div className="text-lg font-bold text-amber-900 dark:text-amber-100">
                {ctx.hour_requests}
              </div>
              <div className="text-amber-600 dark:text-amber-400">本小時</div>
            </div>
            <div>
              <div className="text-lg font-bold text-amber-900 dark:text-amber-100">
                {ctx.day_requests}
              </div>
              <div className="text-amber-600 dark:text-amber-400">今日</div>
            </div>
          </div>
          {ctx.estimated_rpm_limit && (
            <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
              預估 RPM 上限：~{ctx.estimated_rpm_limit} 次/分鐘
            </p>
          )}
          {ctx.quota_hits_today > 1 && (
            <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
              今日已觸發 {ctx.quota_hits_today} 次配額限制
            </p>
          )}
          {ctx.usage_warning && (
            <p className="mt-1 text-xs font-medium text-amber-800 dark:text-amber-200">
              {ctx.usage_warning}
            </p>
          )}
        </div>
      )}

      {/* Suggestions */}
      {details.suggestions && details.suggestions.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-amber-800 dark:text-amber-200">建議</p>
          <ul className="space-y-0.5 text-xs text-amber-700 dark:text-amber-300">
            {details.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="mt-0.5">•</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Help Link */}
      {details.help_url && (
        <a
          href={details.help_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-amber-700 underline transition-colors hover:text-amber-900 dark:text-amber-300 dark:hover:text-amber-100"
        >
          <ExternalLink className="h-3 w-3" />
          查看配額管理頁面
        </a>
      )}
    </div>
  )
}
