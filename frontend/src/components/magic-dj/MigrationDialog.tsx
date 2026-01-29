/**
 * Migration Dialog
 * Feature: 011-magic-dj-audio-features Phase 4
 *
 * Dialog to migrate audio data from localStorage (base64) to IndexedDB (blob).
 */

import { useState } from 'react'
import { RefreshCw, CheckCircle, XCircle, Loader2 } from 'lucide-react'

import { audioStorage, type MigrationResult } from '@/lib/audioStorage'

// =============================================================================
// Types
// =============================================================================

export interface MigrationDialogProps {
  /** Whether dialog is open */
  isOpen: boolean
  /** Number of tracks pending migration */
  pendingCount: number
  /** Callback when migration is complete */
  onComplete: (result: MigrationResult) => void
  /** Callback to dismiss dialog */
  onDismiss: () => void
}

type MigrationState = 'idle' | 'migrating' | 'success' | 'error'

// =============================================================================
// Component
// =============================================================================

export function MigrationDialog({
  isOpen,
  pendingCount,
  onComplete,
  onDismiss,
}: MigrationDialogProps) {
  const [state, setState] = useState<MigrationState>('idle')
  const [result, setResult] = useState<MigrationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleMigrate = async () => {
    setState('migrating')
    setError(null)

    try {
      const migrationResult = await audioStorage.migrateFromLocalStorage()
      setResult(migrationResult)

      if (migrationResult.errors.length > 0) {
        setState('error')
      } else {
        setState('success')
        // Auto-close after success
        setTimeout(() => {
          onComplete(migrationResult)
        }, 2000)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '遷移時發生未知錯誤')
      setState('error')
    }
  }

  const handleDismiss = () => {
    if (state === 'migrating') return // Don't allow dismiss during migration
    onDismiss()
  }

  const handleRetry = () => {
    setState('idle')
    setResult(null)
    setError(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-96 rounded-lg bg-background p-6 shadow-xl">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          {state === 'migrating' ? (
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          ) : state === 'success' ? (
            <CheckCircle className="h-6 w-6 text-green-500" />
          ) : state === 'error' ? (
            <XCircle className="h-6 w-6 text-red-500" />
          ) : (
            <RefreshCw className="h-6 w-6 text-primary" />
          )}
          <h2 className="text-lg font-semibold">
            {state === 'migrating'
              ? '正在升級...'
              : state === 'success'
              ? '升級完成'
              : state === 'error'
              ? '升級失敗'
              : '升級本地儲存'}
          </h2>
        </div>

        {/* Content based on state */}
        {state === 'idle' && (
          <>
            <p className="mb-4 text-sm text-muted-foreground">
              偵測到 <span className="font-semibold text-foreground">{pendingCount}</span>{' '}
              個使用舊格式儲存的音檔。升級後可支援更大的儲存空間（從 ~7MB 增加到 50MB+）。
            </p>

            <div className="mb-4 rounded-md bg-muted/50 p-3">
              <h3 className="mb-2 text-sm font-medium">升級內容：</h3>
              <ul className="space-y-1 text-xs text-muted-foreground">
                <li>• 將音檔從 localStorage 遷移到 IndexedDB</li>
                <li>• 移除 base64 編碼，節省 33% 空間</li>
                <li>• 原有音檔和設定將完整保留</li>
              </ul>
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={handleDismiss}
                className="rounded px-4 py-2 text-sm hover:bg-muted"
              >
                稍後再說
              </button>
              <button
                onClick={handleMigrate}
                className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                立即升級
              </button>
            </div>
          </>
        )}

        {state === 'migrating' && (
          <div className="py-4 text-center">
            <p className="text-sm text-muted-foreground">
              正在遷移音檔，請勿關閉頁面...
            </p>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full w-1/2 animate-pulse bg-primary" />
            </div>
          </div>
        )}

        {state === 'success' && result && (
          <>
            <div className="mb-4 rounded-md bg-green-50 p-4 text-green-800">
              <p className="text-sm">
                成功遷移 <span className="font-semibold">{result.migratedCount}</span> 個音檔，
                共 {audioStorage.formatBytes(result.totalSizeBytes)}。
              </p>
            </div>

            <p className="text-xs text-muted-foreground">
              此視窗將自動關閉...
            </p>
          </>
        )}

        {state === 'error' && (
          <>
            <div className="mb-4 rounded-md bg-red-50 p-4 text-red-800">
              <p className="text-sm font-medium mb-2">遷移時發生錯誤</p>
              {error && <p className="text-xs">{error}</p>}
              {result && result.errors.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium">失敗的音軌：</p>
                  <ul className="mt-1 text-xs">
                    {result.errors.slice(0, 3).map((err, i) => (
                      <li key={i}>• {err.trackId}: {err.error}</li>
                    ))}
                    {result.errors.length > 3 && (
                      <li>• 還有 {result.errors.length - 3} 個...</li>
                    )}
                  </ul>
                </div>
              )}
            </div>

            {result && result.migratedCount > 0 && (
              <p className="mb-4 text-xs text-muted-foreground">
                部分音檔已成功遷移：{result.migratedCount} 個
              </p>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={handleDismiss}
                className="rounded px-4 py-2 text-sm hover:bg-muted"
              >
                關閉
              </button>
              <button
                onClick={handleRetry}
                className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                重試
              </button>
            </div>
          </>
        )}
      </div>

      {/* Click outside to close (only in idle/success/error state) */}
      {state !== 'migrating' && (
        <div
          className="absolute inset-0 -z-10"
          onClick={handleDismiss}
        />
      )}
    </div>
  )
}

export default MigrationDialog
