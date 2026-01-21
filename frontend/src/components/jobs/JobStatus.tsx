/**
 * Job Status Badge Component
 * T041: Display job status with appropriate colors
 *
 * Feature: 007-async-job-mgmt
 */

import { Clock, Loader2, CheckCircle, XCircle, Ban } from 'lucide-react'
import type { JobStatus as JobStatusType } from '@/services/jobApi'

interface JobStatusProps {
  status: JobStatusType
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const STATUS_CONFIG: Record<
  JobStatusType,
  {
    label: string
    icon: typeof Clock
    bgColor: string
    textColor: string
    borderColor: string
  }
> = {
  pending: {
    label: '等待中',
    icon: Clock,
    bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
    textColor: 'text-yellow-700 dark:text-yellow-400',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
  },
  processing: {
    label: '處理中',
    icon: Loader2,
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    textColor: 'text-blue-700 dark:text-blue-400',
    borderColor: 'border-blue-200 dark:border-blue-800',
  },
  completed: {
    label: '已完成',
    icon: CheckCircle,
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    textColor: 'text-green-700 dark:text-green-400',
    borderColor: 'border-green-200 dark:border-green-800',
  },
  failed: {
    label: '失敗',
    icon: XCircle,
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    textColor: 'text-red-700 dark:text-red-400',
    borderColor: 'border-red-200 dark:border-red-800',
  },
  cancelled: {
    label: '已取消',
    icon: Ban,
    bgColor: 'bg-gray-50 dark:bg-gray-900/20',
    textColor: 'text-gray-700 dark:text-gray-400',
    borderColor: 'border-gray-200 dark:border-gray-800',
  },
}

const SIZE_CLASSES = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
  lg: 'text-base px-3 py-1.5',
}

const ICON_SIZES = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
}

export function JobStatusBadge({
  status,
  size = 'md',
  showLabel = true,
}: JobStatusProps) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${config.bgColor} ${config.textColor} ${config.borderColor} ${SIZE_CLASSES[size]}`}
    >
      <Icon
        className={`${ICON_SIZES[size]} ${status === 'processing' ? 'animate-spin' : ''}`}
      />
      {showLabel && <span>{config.label}</span>}
    </span>
  )
}

// Export for use in other components
export { STATUS_CONFIG }
