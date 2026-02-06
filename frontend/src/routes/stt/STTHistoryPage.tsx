/**
 * STT History Page
 * Feature: 003-stt-testing-module - Phase 7
 * T070: Create STTHistory page
 *
 * Page for viewing and managing transcription history.
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TranscriptionHistory } from '@/components/stt/TranscriptionHistory'

interface HistoryItem {
  id: string
  provider: string
  language: string
  transcript: string
  confidence: number | null
  created_at: string
  audio_filename?: string
}

interface HistoryPage {
  items: HistoryItem[]
  total: number
  page: number
  page_size: number
}

export function STTHistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryPage>({
    items: [],
    total: 0,
    page: 1,
    page_size: 20,
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedLanguage, setSelectedLanguage] = useState<string>('')

  const fetchHistory = async (page: number = 1) => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: history.page_size.toString(),
      })

      if (selectedProvider) {
        params.append('provider', selectedProvider)
      }

      if (selectedLanguage) {
        params.append('language', selectedLanguage)
      }

      const response = await fetch(`/api/v1/stt/history?${params}`)

      if (!response.ok) {
        throw new Error('Failed to fetch history')
      }

      const data = await response.json()
      setHistory(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProvider, selectedLanguage])

  const handlePageChange = (newPage: number) => {
    fetchHistory(newPage)
  }

  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/stt/history/${id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete history item')
      }

      // Refresh history after deletion
      fetchHistory(history.page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
    }
  }

  const handleView = (id: string) => {
    // Navigate to detail view
    navigate(`/stt/history/${id}`)
  }

  const handleClearFilters = () => {
    setSelectedProvider('')
    setSelectedLanguage('')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">轉錄歷史記錄</h1>
        <p className="mt-1 text-muted-foreground">
          查看與管理您的語音辨識歷史記錄
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-xl border bg-card p-6">
        <h2 className="text-lg font-semibold mb-4">篩選條件</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Provider Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Provider
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部</option>
              <option value="azure">Azure</option>
              <option value="gcp">Google Cloud</option>
              <option value="whisper">Whisper</option>
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              語言
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部</option>
              <option value="zh-TW">繁體中文</option>
              <option value="zh-CN">簡體中文</option>
              <option value="en-US">英語</option>
              <option value="ja-JP">日語</option>
            </select>
          </div>

          {/* Clear Filters */}
          <div className="flex items-end">
            <button
              onClick={handleClearFilters}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              清除篩選
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 p-4">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                載入錯誤
              </h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* History List */}
      <div className="rounded-xl border bg-card p-6">
        <TranscriptionHistory
          items={history.items}
          total={history.total}
          page={history.page}
          pageSize={history.page_size}
          isLoading={isLoading}
          onPageChange={handlePageChange}
          onDelete={handleDelete}
          onView={handleView}
        />
      </div>

      {/* Back to Test Button */}
      <div className="flex justify-center">
        <button
          onClick={() => navigate('/stt')}
          className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg
            className="h-5 w-5 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
          返回 STT 測試
        </button>
      </div>
    </div>
  )
}
