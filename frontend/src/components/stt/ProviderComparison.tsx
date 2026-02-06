/**
 * ProviderComparison Component
 * Feature: 003-stt-testing-module - Phase 7
 * T068: Create ProviderComparison component
 *
 * Displays side-by-side comparison of transcription results from multiple providers.
 */

import type { TranscriptionResponse } from '@/types/stt'

interface ProviderComparisonProps {
  results: TranscriptionResponse[]
  groundTruth?: string
  isLoading?: boolean
}

export function ProviderComparison({
  results,
  groundTruth,
  isLoading = false,
}: ProviderComparisonProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-6">
        <div className="animate-pulse space-y-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">
              正在比較多個 provider...
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
                <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!results || results.length === 0) {
    return (
      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-6 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          選擇至少兩個 provider 進行比較
        </p>
      </div>
    )
  }

  // Sort by confidence (descending)
  const sortedResults = [...results].sort(
    (a, b) => (b.confidence || 0) - (a.confidence || 0)
  )

  return (
    <div className="space-y-6">
      {/* Comparison Summary */}
      <div className="rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 p-4">
        <div className="flex items-start gap-3">
          <svg
            className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100">
              比較 {results.length} 個 Provider
            </h3>
            <p className="mt-1 text-xs text-blue-700 dark:text-blue-300">
              最高信心度: {sortedResults[0].provider} ({sortedResults[0].confidence != null ? `${(sortedResults[0].confidence * 100).toFixed(1)}%` : 'N/A'})
            </p>
          </div>
        </div>
      </div>

      {/* Ground Truth Display */}
      {groundTruth && (
        <div className="rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            正確答案 (Ground Truth)
          </h4>
          <p className="text-sm text-gray-900 dark:text-gray-100">{groundTruth}</p>
        </div>
      )}

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedResults.map((result, index) => (
          <ProviderResultCard
            key={result.provider}
            result={result}
            rank={index + 1}
            isBest={index === 0}
          />
        ))}
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Provider
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                信心度
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                延遲
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                字數
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {sortedResults.map((result) => (
              <tr key={result.provider}>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                  {result.provider}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      result.confidence != null && result.confidence >= 0.9
                        ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        : result.confidence != null && result.confidence >= 0.7
                          ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                          : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                    }`}
                  >
                    {result.confidence != null ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {result.latency_ms}ms
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {result.transcript.split(/\s+/).length}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

interface ProviderResultCardProps {
  result: TranscriptionResponse
  rank: number
  isBest: boolean
}

function ProviderResultCard({ result, rank, isBest }: ProviderResultCardProps) {
  return (
    <div
      className={`rounded-lg border p-4 ${
        isBest
          ? 'border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-950'
          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {result.provider}
            </h3>
            {isBest && (
              <svg
                className="h-4 w-4 text-green-600 dark:text-green-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Rank #{rank}
          </p>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">信心度</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {result.confidence != null ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">延遲</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {result.latency_ms}ms
          </p>
        </div>
      </div>

      {/* Transcript */}
      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">轉錄文字</p>
        <p className="text-sm text-gray-900 dark:text-gray-100 line-clamp-3">
          {result.transcript || '(無轉錄結果)'}
        </p>
      </div>
    </div>
  )
}
