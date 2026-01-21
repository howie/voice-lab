/**
 * Job List Component
 * T042: Display list of jobs with status filter
 *
 * Feature: 007-async-job-mgmt
 */

import { useEffect } from 'react'
import { RefreshCw, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useJobStore } from '@/stores/jobStore'
import { JobStatusBadge } from './JobStatus'
import { formatDateTime, canCancel } from '@/services/jobApi'
import type { JobStatus, JobResponse } from '@/services/jobApi'

interface JobListProps {
  onSelectJob?: (jobId: string) => void
  selectedJobId?: string | null
}

const STATUS_FILTERS: Array<{ value: JobStatus | null; label: string }> = [
  { value: null, label: '全部' },
  { value: 'pending', label: '等待中' },
  { value: 'processing', label: '處理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失敗' },
  { value: 'cancelled', label: '已取消' },
]

export function JobList({ onSelectJob, selectedJobId }: JobListProps) {
  const {
    jobs,
    total,
    limit,
    offset,
    statusFilter,
    isLoading,
    error,
    fetchJobs,
    setStatusFilter,
    setPage,
    cancelJob,
    startPolling,
    stopPolling,
    clearError,
  } = useJobStore()

  // Initial load and polling
  useEffect(() => {
    fetchJobs()
    startPolling()

    return () => {
      stopPolling()
    }
  }, [fetchJobs, startPolling, stopPolling])

  // Handle cancel job
  const handleCancelJob = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation()
    if (confirm('確定要取消此工作嗎？')) {
      try {
        await cancelJob(jobId)
      } catch {
        // Error is handled in the store
      }
    }
  }

  // Pagination
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)

  const handlePrevPage = () => {
    if (offset >= limit) {
      setPage(offset - limit)
    }
  }

  const handleNextPage = () => {
    if (offset + limit < total) {
      setPage(offset + limit)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">工作列表</h2>
        <button
          onClick={() => fetchJobs()}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          重新整理
        </button>
      </div>

      {/* Status filter */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((filter) => (
          <button
            key={filter.value ?? 'all'}
            onClick={() => setStatusFilter(filter.value)}
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
            {isLoading ? '載入中...' : '尚無工作記錄'}
          </div>
        ) : (
          jobs.map((job) => (
            <JobListItem
              key={job.id}
              job={job}
              isSelected={selectedJobId === job.id}
              onSelect={() => onSelectJob?.(job.id)}
              onCancel={(e) => handleCancelJob(e, job.id)}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            共 {total} 筆，第 {currentPage} / {totalPages} 頁
          </span>
          <div className="flex gap-2">
            <button
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              上一頁
            </button>
            <button
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
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
interface JobListItemProps {
  job: JobResponse
  isSelected: boolean
  onSelect: () => void
  onCancel: (e: React.MouseEvent) => void
}

function JobListItem({ job, isSelected, onSelect, onCancel }: JobListItemProps) {
  return (
    <div
      onClick={onSelect}
      className={`flex cursor-pointer items-center justify-between p-4 transition-colors hover:bg-muted/50 ${
        isSelected ? 'bg-muted' : ''
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{job.id.slice(0, 8)}...</span>
          <JobStatusBadge status={job.status} size="sm" />
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="capitalize">{job.provider}</span>
          <span>{formatDateTime(job.created_at)}</span>
        </div>
      </div>

      {canCancel(job.status) && (
        <button
          onClick={onCancel}
          className="ml-2 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          title="取消工作"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
