/**
 * WERDisplay Component
 * Feature: 003-stt-testing-module - User Story 3
 * T052: Create WERDisplay component
 *
 * Displays Word Error Rate (WER) or Character Error Rate (CER) analysis results
 * with detailed breakdown of errors and visual alignment.
 */

import type { WERAnalysis } from '@/types/stt'

interface WERDisplayProps {
  werAnalysis: WERAnalysis | null
  isCalculating?: boolean
}

export function WERDisplay({ werAnalysis, isCalculating = false }: WERDisplayProps) {
  if (isCalculating) {
    return (
      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-6">
        <div className="animate-pulse space-y-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">
              Calculating accuracy metrics...
            </span>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!werAnalysis) {
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
          Enter ground truth text to calculate accuracy metrics
        </p>
      </div>
    )
  }

  const errorRatePercentage = (werAnalysis.error_rate * 100).toFixed(2)
  const accuracy = (100 - werAnalysis.error_rate * 100).toFixed(2)
  const totalErrors =
    werAnalysis.insertions + werAnalysis.deletions + werAnalysis.substitutions

  // Determine quality based on error rate
  const getQualityInfo = (errorRate: number) => {
    if (errorRate < 0.05) {
      return {
        label: 'Excellent',
        color: 'green',
        bgClass: 'bg-green-50 dark:bg-green-950',
        textClass: 'text-green-700 dark:text-green-300',
        borderClass: 'border-green-200 dark:border-green-800',
      }
    } else if (errorRate < 0.15) {
      return {
        label: 'Good',
        color: 'blue',
        bgClass: 'bg-blue-50 dark:bg-blue-950',
        textClass: 'text-blue-700 dark:text-blue-300',
        borderClass: 'border-blue-200 dark:border-blue-800',
      }
    } else if (errorRate < 0.30) {
      return {
        label: 'Fair',
        color: 'yellow',
        bgClass: 'bg-yellow-50 dark:bg-yellow-950',
        textClass: 'text-yellow-700 dark:text-yellow-300',
        borderClass: 'border-yellow-200 dark:border-yellow-800',
      }
    } else {
      return {
        label: 'Poor',
        color: 'red',
        bgClass: 'bg-red-50 dark:bg-red-950',
        textClass: 'text-red-700 dark:text-red-300',
        borderClass: 'border-red-200 dark:border-red-800',
      }
    }
  }

  const quality = getQualityInfo(werAnalysis.error_rate)

  return (
    <div className="space-y-4">
      {/* Error Rate Summary */}
      <div
        className={`rounded-lg border p-6 ${quality.bgClass} ${quality.borderClass}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {werAnalysis.error_type === 'WER'
                  ? 'Word Error Rate (WER)'
                  : 'Character Error Rate (CER)'}
              </h3>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${quality.bgClass} ${quality.textClass}`}
              >
                {quality.label}
              </span>
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <p className={`text-4xl font-bold ${quality.textClass}`}>
                {errorRatePercentage}%
              </p>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                error rate
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Accuracy: {accuracy}% ({werAnalysis.total_reference - totalErrors}/
              {werAnalysis.total_reference} correct)
            </p>
          </div>
          <div className="ml-4">
            <svg
              className={`h-12 w-12 ${quality.textClass}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              {werAnalysis.error_rate < 0.15 ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              )}
            </svg>
          </div>
        </div>
      </div>

      {/* Error Breakdown */}
      <div className="grid grid-cols-3 gap-4">
        <ErrorMetric
          label="Substitutions"
          value={werAnalysis.substitutions}
          total={totalErrors}
          description="Incorrect words/characters"
          icon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
              />
            </svg>
          }
        />
        <ErrorMetric
          label="Insertions"
          value={werAnalysis.insertions}
          total={totalErrors}
          description="Extra words/characters"
          icon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
          }
        />
        <ErrorMetric
          label="Deletions"
          value={werAnalysis.deletions}
          total={totalErrors}
          description="Missing words/characters"
          icon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 12H4"
              />
            </svg>
          }
        />
      </div>

      {/* Alignment Visualization */}
      {werAnalysis.alignment && werAnalysis.alignment.length > 0 && (
        <AlignmentSection alignment={werAnalysis.alignment} />
      )}
    </div>
  )
}

interface ErrorMetricProps {
  label: string
  value: number
  total: number
  description: string
  icon: React.ReactNode
}

function ErrorMetric({ label, value, total, description, icon }: ErrorMetricProps) {
  const percentage = total > 0 ? ((value / total) * 100).toFixed(0) : '0'

  return (
    <div className="rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
          {label}
        </span>
        <div className="text-gray-400">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        {description} {total > 0 && `(${percentage}%)`}
      </p>
    </div>
  )
}

interface AlignmentSectionProps {
  alignment: Array<{
    ref: string | null
    hyp: string | null
    op: 'match' | 'substitute' | 'insert' | 'delete'
  }>
}

function AlignmentSection({ alignment }: AlignmentSectionProps) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center">
        <svg
          className="h-4 w-4 mr-2"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 10h16M4 14h16M4 18h16"
          />
        </svg>
        Alignment Visualization
      </h4>
      <div className="flex flex-wrap gap-1">
        {alignment.map((item, index) => {
          const getAlignmentStyle = (op: string) => {
            switch (op) {
              case 'match':
                return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border-green-200 dark:border-green-700'
              case 'substitute':
                return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 border-yellow-200 dark:border-yellow-700'
              case 'insert':
                return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 border-blue-200 dark:border-blue-700'
              case 'delete':
                return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border-red-200 dark:border-red-700'
              default:
                return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-600'
            }
          }

          const displayText = item.hyp || item.ref || '∅'
          const tooltipText = `${item.op}: "${item.ref || '∅'}" → "${item.hyp || '∅'}"`

          return (
            <span
              key={index}
              className={`inline-flex items-center px-2 py-1 rounded text-xs border ${getAlignmentStyle(item.op)}`}
              title={tooltipText}
            >
              {displayText}
            </span>
          )
        })}
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-400">
        <div className="flex items-center">
          <div className="w-3 h-3 rounded bg-green-100 dark:bg-green-900 border border-green-200 dark:border-green-700 mr-1.5"></div>
          Match
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded bg-yellow-100 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 mr-1.5"></div>
          Substitute
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded bg-blue-100 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 mr-1.5"></div>
          Insert
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded bg-red-100 dark:bg-red-900 border border-red-200 dark:border-red-700 mr-1.5"></div>
          Delete
        </div>
      </div>
    </div>
  )
}
