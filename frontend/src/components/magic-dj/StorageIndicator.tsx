/**
 * Storage Indicator
 * Feature: 011-magic-dj-audio-features Phase 4
 *
 * Shows local storage usage with visual progress bar and warnings.
 */

import { useEffect, useState } from 'react'
import { HardDrive, AlertTriangle, XCircle, Cloud } from 'lucide-react'

import { cn } from '@/lib/utils'
import { audioStorage, type StorageQuota } from '@/lib/audioStorage'

// =============================================================================
// Types
// =============================================================================

export interface StorageIndicatorProps {
  /** Custom class name */
  className?: string
  /** Callback when user clicks "upload to cloud" */
  onUploadToCloud?: () => void
  /** Whether to show compact version */
  compact?: boolean
  /** Override quota for testing */
  quota?: StorageQuota
}

// =============================================================================
// Component
// =============================================================================

export function StorageIndicator({
  className,
  onUploadToCloud,
  compact = false,
  quota: propQuota,
}: StorageIndicatorProps) {
  const [quota, setQuota] = useState<StorageQuota | null>(propQuota ?? null)
  const [isLoading, setIsLoading] = useState(!propQuota)

  // Fetch quota on mount
  useEffect(() => {
    if (propQuota) {
      setQuota(propQuota)
      return
    }

    let mounted = true

    const fetchQuota = async () => {
      try {
        const q = await audioStorage.getQuota()
        if (mounted) {
          setQuota(q)
          setIsLoading(false)
        }
      } catch (error) {
        console.error('Failed to get storage quota:', error)
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    fetchQuota()

    // Refresh every 30 seconds
    const interval = setInterval(fetchQuota, 30000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [propQuota])

  // Don't render if not supported or loading
  if (isLoading || !quota) {
    return null
  }

  const level = audioStorage.getWarningLevel(quota.percentage)
  const warningMessage = audioStorage.getWarningMessage(level)

  // Color based on level
  const getColors = () => {
    switch (level) {
      case 'critical':
      case 'danger':
        return {
          text: 'text-red-600',
          bg: 'bg-red-500',
          bgLight: 'bg-red-100',
          icon: 'text-red-500',
        }
      case 'warning':
        return {
          text: 'text-yellow-600',
          bg: 'bg-yellow-500',
          bgLight: 'bg-yellow-100',
          icon: 'text-yellow-500',
        }
      default:
        return {
          text: 'text-green-600',
          bg: 'bg-green-500',
          bgLight: 'bg-green-100',
          icon: 'text-muted-foreground',
        }
    }
  }

  const colors = getColors()
  const usedFormatted = audioStorage.formatBytes(quota.used)
  const totalFormatted = audioStorage.formatBytes(quota.total)

  // Icon based on level
  const Icon = level === 'critical' || level === 'danger'
    ? XCircle
    : level === 'warning'
    ? AlertTriangle
    : HardDrive

  // Compact version (just icon + percentage)
  if (compact) {
    return (
      <div
        className={cn(
          'flex items-center gap-1.5 text-xs',
          colors.text,
          className
        )}
        title={`本機儲存: ${usedFormatted} / ${totalFormatted} (${quota.percentage}%)`}
      >
        <Icon className={cn('h-3.5 w-3.5', colors.icon)} />
        <span>{quota.percentage}%</span>
      </div>
    )
  }

  return (
    <div className={cn('space-y-2', className)}>
      {/* Header */}
      <div className="flex items-center justify-between text-sm">
        <div className={cn('flex items-center gap-2', colors.text)}>
          <Icon className={cn('h-4 w-4', colors.icon)} />
          <span className="font-medium">本機儲存</span>
        </div>
        <span className={cn('font-mono text-xs', colors.text)}>
          {usedFormatted} / {totalFormatted}
        </span>
      </div>

      {/* Progress bar */}
      <div className={cn('h-2 w-full rounded-full', colors.bgLight)}>
        <div
          className={cn('h-full rounded-full transition-all duration-300', colors.bg)}
          style={{ width: `${Math.min(quota.percentage, 100)}%` }}
        />
      </div>

      {/* Percentage */}
      <div className="flex items-center justify-between text-xs">
        <span className={cn(colors.text)}>{quota.percentage}%</span>

        {/* Warning message */}
        {warningMessage && (
          <span className={cn('font-medium', colors.text)}>
            {warningMessage}
          </span>
        )}
      </div>

      {/* Upload to cloud button (shown when critical/danger) */}
      {(level === 'critical' || level === 'danger') && onUploadToCloud && (
        <button
          onClick={onUploadToCloud}
          className={cn(
            'flex w-full items-center justify-center gap-2 rounded-md px-3 py-2 text-sm',
            'bg-primary text-primary-foreground hover:bg-primary/90',
            'transition-colors'
          )}
        >
          <Cloud className="h-4 w-4" />
          <span>上傳至雲端</span>
        </button>
      )}
    </div>
  )
}

// =============================================================================
// Storage Warning Toast Component
// =============================================================================

export interface StorageWarningToastProps {
  level: 'warning' | 'danger' | 'critical'
  onDismiss?: () => void
  onUploadToCloud?: () => void
  onDeleteAudio?: () => void
}

export function StorageWarningToast({
  level,
  onDismiss,
  onUploadToCloud,
  onDeleteAudio,
}: StorageWarningToastProps) {
  const message = audioStorage.getWarningMessage(level)

  const colors = {
    warning: 'border-yellow-500 bg-yellow-50 text-yellow-800',
    danger: 'border-red-500 bg-red-50 text-red-800',
    critical: 'border-red-600 bg-red-100 text-red-900',
  }

  const icons = {
    warning: AlertTriangle,
    danger: XCircle,
    critical: XCircle,
  }

  const Icon = icons[level]

  return (
    <div
      className={cn(
        'fixed bottom-4 right-4 z-50 w-80 rounded-lg border-2 p-4 shadow-lg',
        colors[level]
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1 space-y-3">
          <p className="font-medium">
            {level === 'critical' ? '無法儲存音檔' : '儲存空間警告'}
          </p>
          <p className="text-sm opacity-90">{message}</p>

          <div className="flex flex-wrap gap-2">
            {onDeleteAudio && (
              <button
                onClick={onDeleteAudio}
                className="rounded px-3 py-1.5 text-xs font-medium hover:bg-black/10"
              >
                刪除音檔
              </button>
            )}
            {onUploadToCloud && (
              <button
                onClick={onUploadToCloud}
                className="rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
              >
                上傳至雲端
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="rounded px-3 py-1.5 text-xs hover:bg-black/10"
              >
                關閉
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default StorageIndicator
