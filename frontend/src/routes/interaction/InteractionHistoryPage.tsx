/**
 * InteractionHistoryPage
 * Feature: 004-interaction-module
 * T096-T101 [US6]: History page with session list, filters, and detail view.
 */

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ConversationHistory } from '@/components/interaction/ConversationHistory'
import {
  listSessions,
  getSession,
  deleteSession,
  listSessionTurns,
  getSessionLatencyStats,
  formatDuration,
} from '@/services/interactionApi'
import { useAuthStore } from '@/stores/authStore'
import type {
  InteractionSession,
  InteractionMode,
  ConversationTurn,
  LatencyStats,
} from '@/types/interaction'

// T101: Delete confirmation dialog
function DeleteConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  sessionDate,
}: {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
  sessionDate: string
}) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg bg-card p-6 shadow-xl">
        <h3 className="text-lg font-semibold">確認刪除</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          確定要刪除 {new Date(sessionDate).toLocaleString('zh-TW')} 的對話記錄嗎？
          此操作無法復原，相關的音訊檔案也會一併刪除。
        </p>
        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg border px-4 py-2 text-sm hover:bg-accent"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            className="rounded-lg bg-destructive px-4 py-2 text-sm text-destructive-foreground hover:bg-destructive/90"
          >
            確認刪除
          </button>
        </div>
      </div>
    </div>
  )
}

export function InteractionHistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const user = useAuthStore((state) => state.user)

  // State
  const [sessions, setSessions] = useState<InteractionSession[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters (T097, T098)
  const [modeFilter, setModeFilter] = useState<InteractionMode | ''>('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 10

  // Selected session detail (T099)
  const [selectedSession, setSelectedSession] = useState<InteractionSession | null>(null)
  const [selectedTurns, setSelectedTurns] = useState<ConversationTurn[]>([])
  const [selectedStats, setSelectedStats] = useState<LatencyStats | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Delete confirmation (T101)
  const [deleteTarget, setDeleteTarget] = useState<InteractionSession | null>(null)
  const [deleting, setDeleting] = useState(false)

  // Fetch sessions
  const fetchSessions = useCallback(async () => {
    if (!user?.id) return

    setLoading(true)
    setError(null)

    try {
      const result = await listSessions({
        user_id: user.id,
        mode: modeFilter || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        page_size: pageSize,
      })

      setSessions(result.sessions)
      setTotal(result.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : '載入失敗')
    } finally {
      setLoading(false)
    }
  }, [user?.id, modeFilter, startDate, endDate, page])

  // Fetch session detail (T099)
  const fetchSessionDetail = useCallback(async (sessionId: string) => {
    setLoadingDetail(true)
    setError(null)

    try {
      const [session, turns, stats] = await Promise.all([
        getSession(sessionId),
        listSessionTurns(sessionId),
        getSessionLatencyStats(sessionId),
      ])

      setSelectedSession(session)
      setSelectedTurns(turns)
      setSelectedStats(stats)
    } catch (e) {
      setError(e instanceof Error ? e.message : '載入詳情失敗')
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  // Handle session selection from URL
  useEffect(() => {
    const sessionId = searchParams.get('session')
    if (sessionId) {
      fetchSessionDetail(sessionId)
    } else {
      setSelectedSession(null)
      setSelectedTurns([])
      setSelectedStats(null)
    }
  }, [searchParams, fetchSessionDetail])

  // Fetch sessions on mount and filter change
  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  // Handle session click
  const handleSessionClick = (session: InteractionSession) => {
    setSearchParams({ session: session.id })
  }

  // Handle back to list
  const handleBackToList = () => {
    setSearchParams({})
  }

  // Handle delete (T101)
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return

    setDeleting(true)
    try {
      await deleteSession(deleteTarget.id)

      // If viewing the deleted session, go back to list
      if (selectedSession?.id === deleteTarget.id) {
        setSearchParams({})
      }

      // Refresh list
      await fetchSessions()
    } catch (e) {
      setError(e instanceof Error ? e.message : '刪除失敗')
    } finally {
      setDeleting(false)
      setDeleteTarget(null)
    }
  }

  // Render session list
  const renderSessionList = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">對話歷史</h1>
          <p className="mt-1 text-muted-foreground">
            查看和管理語音互動記錄
          </p>
        </div>
      </div>

      {/* Filters (T097, T098) */}
      <div className="flex flex-wrap gap-4">
        {/* Mode filter (T098) */}
        <select
          value={modeFilter}
          onChange={(e) => {
            setModeFilter(e.target.value as InteractionMode | '')
            setPage(1)
          }}
          className="rounded-lg border bg-background px-3 py-2 text-sm"
        >
          <option value="">所有模式</option>
          <option value="realtime">Realtime API</option>
          <option value="cascade">Cascade Mode</option>
        </select>

        {/* Date range filter (T097) */}
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value)
              setPage(1)
            }}
            className="rounded-lg border bg-background px-3 py-2 text-sm"
            placeholder="開始日期"
          />
          <span className="text-muted-foreground">-</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value)
              setPage(1)
            }}
            className="rounded-lg border bg-background px-3 py-2 text-sm"
            placeholder="結束日期"
          />
        </div>

        {/* Clear filters */}
        {(modeFilter || startDate || endDate) && (
          <button
            onClick={() => {
              setModeFilter('')
              setStartDate('')
              setEndDate('')
              setPage(1)
            }}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            清除篩選
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Session List */}
      {loading ? (
        <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground">
          載入中...
        </div>
      ) : sessions.length === 0 ? (
        <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground">
          尚無對話記錄
        </div>
      ) : (
        <div className="rounded-xl border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-muted-foreground">
                <th className="p-4 font-medium">時間</th>
                <th className="p-4 font-medium">模式</th>
                <th className="p-4 font-medium">持續時間</th>
                <th className="p-4 font-medium">狀態</th>
                <th className="p-4 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr
                  key={session.id}
                  className="border-b last:border-0 hover:bg-accent/50 cursor-pointer"
                  onClick={() => handleSessionClick(session)}
                >
                  <td className="p-4 text-sm">
                    {new Date(session.started_at).toLocaleString('zh-TW')}
                  </td>
                  <td className="p-4 text-sm">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${
                        session.mode === 'realtime'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                      }`}
                    >
                      {session.mode === 'realtime' ? 'Realtime' : 'Cascade'}
                    </span>
                  </td>
                  <td className="p-4 text-sm">
                    {formatDuration(session.started_at, session.ended_at)}
                  </td>
                  <td className="p-4 text-sm">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${
                        session.status === 'completed'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : session.status === 'active'
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                            : 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
                      }`}
                    >
                      {session.status === 'completed' ? '已完成' : session.status === 'active' ? '進行中' : '已斷開'}
                    </span>
                  </td>
                  <td className="p-4 text-sm">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setDeleteTarget(session)
                      }}
                      className="text-destructive hover:text-destructive/80"
                    >
                      刪除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            共 {total} 筆記錄
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border px-3 py-1.5 text-sm hover:bg-accent disabled:opacity-50"
            >
              上一頁
            </button>
            <span className="flex items-center px-3 text-sm">
              {page} / {Math.ceil(total / pageSize)}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
              disabled={page >= Math.ceil(total / pageSize)}
              className="rounded-lg border px-3 py-1.5 text-sm hover:bg-accent disabled:opacity-50"
            >
              下一頁
            </button>
          </div>
        </div>
      )}
    </div>
  )

  // Render session detail (T099, T100)
  const renderSessionDetail = () => (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={handleBackToList}
        className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
          <path fillRule="evenodd" d="M7.72 12.53a.75.75 0 010-1.06l7.5-7.5a.75.75 0 111.06 1.06L9.31 12l6.97 6.97a.75.75 0 11-1.06 1.06l-7.5-7.5z" clipRule="evenodd" />
        </svg>
        返回列表
      </button>

      {loadingDetail ? (
        <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground">
          載入中...
        </div>
      ) : selectedSession ? (
        <ConversationHistory
          session={selectedSession}
          turns={selectedTurns}
          latencyStats={selectedStats}
          onDeleteRequest={() => setDeleteTarget(selectedSession)}
        />
      ) : (
        <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground">
          找不到對話記錄
        </div>
      )}
    </div>
  )

  return (
    <div className="container mx-auto py-6">
      {selectedSession || searchParams.get('session') ? renderSessionDetail() : renderSessionList()}

      {/* Delete Confirmation Dialog (T101) */}
      <DeleteConfirmDialog
        isOpen={!!deleteTarget}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTarget(null)}
        sessionDate={deleteTarget?.started_at || ''}
      />

      {/* Deleting overlay */}
      {deleting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg bg-card p-6">
            <p className="text-sm">刪除中...</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default InteractionHistoryPage
