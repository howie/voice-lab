/**
 * TranscriptDisplay Component
 * Feature: 003-stt-testing-module
 * T033: Create TranscriptDisplay component
 *
 * Displays transcription results with confidence score and word timings.
 */

import type { TranscriptionResponse, WordTiming } from '@/types/stt'

interface TranscriptDisplayProps {
  result: TranscriptionResponse | null
  isLoading?: boolean
  error?: string | null
}

export function TranscriptDisplay({
  result,
  isLoading = false,
  error = null,
}: TranscriptDisplayProps) {
  if (error) {
    return (
      <div className="rounded-lg bg-red-50 dark:bg-red-950 p-4">
        <div className="flex items-center">
          <svg
            className="h-5 w-5 text-red-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <span className="ml-2 text-red-700 dark:text-red-300">{error}</span>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-6">
        <div className="animate-pulse space-y-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">Transcribing...</span>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="mt-2 text-gray-500">
          Upload an audio file and click "Transcribe" to see results
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Main Transcript */}
      <div className="rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
          Transcript
        </h3>
        <p className="text-lg text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
          {result.transcript || '(No speech detected)'}
        </p>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Provider"
          value={result.provider.toUpperCase()}
          icon={
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
              />
            </svg>
          }
        />
        <MetricCard
          label="Confidence"
          value={result.confidence != null ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A'}
          variant={result.confidence != null ? (result.confidence >= 0.9 ? 'success' : result.confidence >= 0.7 ? 'warning' : 'error') : 'default'}
          icon={
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />
        <MetricCard
          label="Latency"
          value={`${result.latency_ms} ms`}
          icon={
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />
        <MetricCard
          label="Language"
          value={result.language}
          icon={
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
              />
            </svg>
          }
        />
      </div>

      {/* Word Timings (if available) */}
      {result.words && result.words.length > 0 && (
        <WordTimingsSection words={result.words} />
      )}
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: string
  icon?: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error'
}

function MetricCard({ label, value, icon, variant = 'default' }: MetricCardProps) {
  const variantStyles = {
    default: 'bg-gray-50 dark:bg-gray-800',
    success: 'bg-green-50 dark:bg-green-950',
    warning: 'bg-yellow-50 dark:bg-yellow-950',
    error: 'bg-red-50 dark:bg-red-950',
  }

  const valueStyles = {
    default: 'text-gray-900 dark:text-gray-100',
    success: 'text-green-700 dark:text-green-300',
    warning: 'text-yellow-700 dark:text-yellow-300',
    error: 'text-red-700 dark:text-red-300',
  }

  return (
    <div className={`rounded-lg p-3 ${variantStyles[variant]}`}>
      <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className={`mt-1 text-lg font-semibold ${valueStyles[variant]}`}>{value}</p>
    </div>
  )
}

interface WordTimingsSectionProps {
  words: WordTiming[]
}

function WordTimingsSection({ words }: WordTimingsSectionProps) {
  return (
    <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Word Timings
      </h4>
      <div className="flex flex-wrap gap-2">
        {words.map((word, index) => (
          <span
            key={index}
            className="inline-flex items-center px-2 py-1 rounded text-sm bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700"
            title={`${word.start_ms}ms - ${word.end_ms}ms${word.confidence ? ` (${(word.confidence * 100).toFixed(0)}%)` : ''}`}
          >
            <span className="text-gray-900 dark:text-gray-100">{word.word}</span>
            <span className="ml-1 text-xs text-gray-400">
              {(word.start_ms / 1000).toFixed(1)}s
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
