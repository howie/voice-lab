/**
 * ErrorDisplay Component
 * T048: Enhanced error handling with friendly messages and retry support
 */

import { AlertCircle, RefreshCw, FileText, Wifi, Server } from 'lucide-react'

interface ErrorDisplayProps {
  error: string | null
  onRetry?: () => void
  showFormatHint?: boolean
}

// Error categories with friendly messages
const ERROR_PATTERNS: Array<{
  pattern: RegExp
  category: 'network' | 'parse' | 'api' | 'validation'
  icon: React.ElementType
  title: string
  getMessage: (error: string) => string
  hint?: string
}> = [
  {
    pattern: /network|fetch|timeout|連線|ERR_NETWORK/i,
    category: 'network',
    icon: Wifi,
    title: '網路連線問題',
    getMessage: () => '無法連接到伺服器，請檢查網路連線後重試。',
    hint: '如果問題持續，請確認 API 伺服器正在運行。',
  },
  {
    pattern: /說話者數量|超過.*限制|max.*speaker|speaker.*limit/i,
    category: 'validation',
    icon: AlertCircle,
    title: '說話者數量超過限制',
    getMessage: (error) => error,
    hint: '請減少對話中的說話者數量，或選擇支援更多說話者的 Provider。',
  },
  {
    pattern: /字數|character.*limit|text.*too.*long/i,
    category: 'validation',
    icon: FileText,
    title: '字數超過限制',
    getMessage: (error) => error,
    hint: '請減少對話文字長度，或選擇字數上限較高的 Provider。',
  },
  {
    pattern: /解析|parse|invalid.*format|格式錯誤/i,
    category: 'parse',
    icon: FileText,
    title: '對話格式解析失敗',
    getMessage: () => '無法解析對話格式，請確認格式是否正確。',
    hint: '支援格式：「A: 文字」或「[說話者名稱]: 文字」',
  },
  {
    pattern: /api.*key|credential|unauthorized|401|403/i,
    category: 'api',
    icon: Server,
    title: 'API 認證問題',
    getMessage: () => '目前選擇的 Provider API 金鑰無效或已過期。',
    hint: '請至「API 金鑰」頁面確認金鑰設定。',
  },
  {
    pattern: /500|internal.*server|伺服器錯誤/i,
    category: 'api',
    icon: Server,
    title: '伺服器錯誤',
    getMessage: () => 'Provider 伺服器暫時無法處理請求。',
    hint: '請稍後重試，如果問題持續請聯繫支援。',
  },
]

function categorizeError(error: string) {
  for (const errorType of ERROR_PATTERNS) {
    if (errorType.pattern.test(error)) {
      return errorType
    }
  }
  // Default fallback
  return {
    category: 'api' as const,
    icon: AlertCircle,
    title: '發生錯誤',
    getMessage: (err: string) => err,
    hint: undefined,
  }
}

export function ErrorDisplay({ error, onRetry, showFormatHint }: ErrorDisplayProps) {
  if (!error) return null

  const errorInfo = categorizeError(error)
  const Icon = errorInfo.icon

  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
        <div className="flex-1 space-y-2">
          <h4 className="font-medium text-destructive">{errorInfo.title}</h4>
          <p className="text-sm text-destructive/90">{errorInfo.getMessage(error)}</p>

          {/* Hint */}
          {errorInfo.hint && (
            <p className="text-xs text-muted-foreground">{errorInfo.hint}</p>
          )}

          {/* Format hint for parse errors */}
          {(showFormatHint || errorInfo.category === 'parse') && (
            <div className="mt-3 rounded-md bg-muted/50 p-3">
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                支援的對話格式：
              </p>
              <pre className="text-xs text-muted-foreground">
{`A: 你好，今天天氣真好
B: 是啊，很適合出門

[主持人]: 歡迎收聽本節目
[來賓]: 謝謝邀請`}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Retry button */}
      {onRetry && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 rounded-md bg-destructive/10 px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/20 transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            重試
          </button>
        </div>
      )}
    </div>
  )
}
