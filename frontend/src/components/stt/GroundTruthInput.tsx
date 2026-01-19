/**
 * GroundTruthInput Component
 * Feature: 003-stt-testing-module - User Story 3
 * T053: Create GroundTruthInput component
 *
 * Allows users to input the ground truth (correct) text for WER/CER calculation.
 * Supports both manual input and file upload for longer texts.
 */

import { useState, type ChangeEvent } from 'react'

interface GroundTruthInputProps {
  value: string
  onChange: (value: string) => void
  onCalculate?: () => void
  isCalculating?: boolean
  disabled?: boolean
  language?: string
}

export function GroundTruthInput({
  value,
  onChange,
  onCalculate,
  isCalculating = false,
  disabled = false,
  language = 'zh-TW',
}: GroundTruthInputProps) {
  const [charCount, setCharCount] = useState(value.length)

  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    onChange(newValue)
    setCharCount(newValue.length)
  }

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      onChange(text)
      setCharCount(text.length)
    } catch (error) {
      console.error('Failed to read file:', error)
      alert('Failed to read file. Please try again.')
    }

    // Reset input so the same file can be uploaded again
    e.target.value = ''
  }

  const handleClear = () => {
    onChange('')
    setCharCount(0)
  }

  const isCJK = ['zh-TW', 'zh-CN', 'ja-JP', 'ko-KR'].includes(language)
  const metricType = isCJK ? 'CER' : 'WER'
  const unitLabel = isCJK ? 'characters' : 'words'

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <label
            htmlFor="ground-truth"
            className="text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Ground Truth Text
          </label>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
            {metricType}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {/* File Upload */}
          <label
            htmlFor="file-upload"
            className="cursor-pointer inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-md text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              className="h-4 w-4 mr-1.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            Upload
            <input
              id="file-upload"
              type="file"
              accept=".txt"
              onChange={handleFileUpload}
              disabled={disabled || isCalculating}
              className="sr-only"
            />
          </label>

          {/* Clear Button */}
          {value && (
            <button
              type="button"
              onClick={handleClear}
              disabled={disabled || isCalculating}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-md text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className="h-4 w-4 mr-1.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Text Area */}
      <div className="relative">
        <textarea
          id="ground-truth"
          value={value}
          onChange={handleTextChange}
          disabled={disabled || isCalculating}
          placeholder={`Enter the correct ${unitLabel} for accuracy calculation...`}
          rows={4}
          className="block w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        />

        {/* Character/Word Count */}
        <div className="absolute bottom-2 right-2 text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-900 px-2 py-1 rounded">
          {charCount} {charCount === 1 ? 'character' : 'characters'}
        </div>
      </div>

      {/* Helper Text */}
      <div className="flex items-start space-x-2 text-xs text-gray-600 dark:text-gray-400">
        <svg
          className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div>
          <p>
            Enter the correct transcription to calculate {metricType} (
            {metricType === 'WER' ? 'Word' : 'Character'} Error Rate).
          </p>
          {isCJK && (
            <p className="mt-1">
              Note: For {language}, CER is used instead of WER for better accuracy measurement.
            </p>
          )}
        </div>
      </div>

      {/* Calculate Button */}
      {onCalculate && (
        <button
          type="button"
          onClick={onCalculate}
          disabled={!value.trim() || disabled || isCalculating}
          className="w-full inline-flex items-center justify-center px-4 py-2.5 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-700 dark:hover:bg-blue-600"
        >
          {isCalculating ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
              Calculating {metricType}...
            </>
          ) : (
            <>
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
                  d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              Calculate {metricType}
            </>
          )}
        </button>
      )}
    </div>
  )
}
