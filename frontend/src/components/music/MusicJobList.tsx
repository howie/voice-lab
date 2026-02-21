/**
 * Music Job List Component
 * Feature: 012-music-generation
 *
 * Display list of music generation jobs with filtering.
 */

import { useEffect, useState } from 'react'
import { RefreshCw, ChevronLeft, ChevronRight, X, RotateCcw } from 'lucide-react'
import { useMusicStore } from '@/stores/musicStore'
import { MusicJobStatusBadge } from './MusicJobStatus'
import type { MusicGenerationStatus, MusicGenerationType, MusicJob } from '@/types/music'
import { MUSIC_TYPE_LABELS } from '@/types/music'

interface MusicJobListProps {
  onSelectJob?: (job: MusicJob) => void
  selectedJobId?: string | null
}

const STATUS_FILTERS: Array<{ value: MusicGenerationStatus | null; label: string }> = [
  { value: null, label: '全部' },
  { value: 'pending', label: '等待中' },
  { value: 'processing', label: '處理中' },
  { value: 'completed', label: '完成' },
  { value: 'failed', label: '失敗' },
  { value: 'cancelled', label: '已取消' },
]

const TYPE_FILTERS: Array<{ value: MusicGenerationType | null; label: string }> = [
  { value: null, label: '全部類型' },
  { value: 'instrumental', label: '純音樂' },
  { value: 'song', label: '歌曲' },
  { value: 'lyrics', label: '歌詞' },
]

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function MusicJobList({ onSelectJob, selectedJobId }: MusicJobListProps) {
  const {
    jobs,
    isLoading,
    error,
    fetchJobs,
    retryJob,
    cancelJob,
    restartJob,
    clearError,
    startPolling,
    stopPolling,
  } = useMusicStore()

  // Local filter state
  const [statusFilter, setStatusFilter] = useState<MusicGenerationStatus | null>(null)
  const [typeFilter, setTypeFilter] = useState<MusicGenerationType | null>(null)
  const [offset, setOffset] = useState(0)
  const limit = 20

  // Fetch and poll
  useEffect(() => {
    fetchJobs({ status: statusFilter ?? undefined, type: typeFilter ?? undefined, limit, offset })
  }, [fetchJobs, statusFilter, typeFilter, offset])

  // Start polling for pending/processing jobs
  useEffect(() => {
    const pendingJobs = jobs.filter((j) => j.status === 'pending' || j.status === 'processing')
    pendingJobs.forEach((job) => startPolling(job.id))

    return () => {
      pendingJobs.forEach((job) => stopPolling(job.id))
    }
  }, [jobs, startPolling, stopPolling])

  const handleRetry = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation()
    await retryJob(jobId)
  }

  const handleCancel = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation()
    if (confirm('確定要取消此任務？')) {
      await cancelJob(jobId)
    }
  }

  const handleRestart = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation()
    await restartJob(jobId)
  }

  // Pagination
  const currentPage = Math.floor(offset / limit) + 1
  const hasMore = jobs.length === limit

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">生成紀錄</h2>
        <button
          onClick={() => fetchJobs({ status: statusFilter ?? undefined, type: typeFilter ?? undefined, limit, offset })}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          重新整理
        </button>
      </div>

      {/* Filters */}
      <div className="space-y-2">
        {/* Status filter */}
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value ?? 'all'}
              onClick={() => {
                setStatusFilter(filter.value)
                setOffset(0)
              }}
              className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                statusFilter === filter.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {/* Type filter */}
        <div className="flex flex-wrap gap-2">
          {TYPE_FILTERS.map((filter) => (
            <button
              key={filter.value ?? 'all-type'}
              onClick={() => {
                setTypeFilter(filter.value)
                setOffset(0)
              }}
              className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                typeFilter === filter.value
                  ? 'bg-secondary text-secondary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center justify-between rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          <span>{error}</span>
          <button onClick={clearError} className="hover:text-red-900">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Job list */}
      <div className="divide-y rounded-lg border">
        {jobs.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-muted-foreground">
            {isLoading ? '載入中...' : '尚無生成紀錄'}
          </div>
        ) : (
          jobs.map((job) => (
            <MusicJobListItem
              key={job.id}
              job={job}
              isSelected={selectedJobId === job.id}
              onSelect={() => onSelectJob?.(job)}
              onRetry={(e) => handleRetry(e, job.id)}
              onCancel={(e) => handleCancel(e, job.id)}
              onRestart={(e) => handleRestart(e, job.id)}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {(offset > 0 || hasMore) && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">第 {currentPage} 頁</span>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              上一頁
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={!hasMore}
              className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
            >
              下一頁
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Job list item component
interface MusicJobListItemProps {
  job: MusicJob
  isSelected: boolean
  onSelect: () => void
  onRetry: (e: React.MouseEvent) => void
  onCancel: (e: React.MouseEvent) => void
  onRestart: (e: React.MouseEvent) => void
}

function MusicJobListItem({ job, isSelected, onSelect, onRetry, onCancel, onRestart }: MusicJobListItemProps) {
  const canCancel = job.status === 'pending' || job.status === 'processing'
  const canRetry = job.status === 'failed'
  const canRestart = job.status === 'cancelled'

  return (
    <div
      onClick={onSelect}
      className={`flex cursor-pointer items-center justify-between p-4 transition-colors hover:bg-muted/50 ${
        isSelected ? 'bg-muted' : ''
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {job.title || job.prompt?.slice(0, 30) || job.id.slice(0, 8)}...
          </span>
          <MusicJobStatusBadge status={job.status} size="sm" />
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          <span>{MUSIC_TYPE_LABELS[job.type]}</span>
          <span>{formatDateTime(job.created_at)}</span>
          {job.duration_ms && <span>{Math.round(job.duration_ms / 1000)}秒</span>}
        </div>
      </div>

      <div className="ml-2 flex items-center gap-1">
        {canCancel && (
          <button
            onClick={onCancel}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/30 dark:hover:text-red-400"
            title="取消任務"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        {canRetry && (
          <button
            onClick={onRetry}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            title="重新嘗試"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}

        {canRestart && (
          <button
            onClick={onRestart}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            title="重新建立"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

export default MusicJobList
