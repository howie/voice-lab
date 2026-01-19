/**
 * AudioUploader Component
 * Feature: 003-stt-testing-module
 * T031: Create AudioUploader component
 *
 * Handles audio file upload with drag-and-drop support and format validation.
 */

import { useCallback, useState } from 'react'
import { useSTTStore } from '@/stores/sttStore'
import type { STTProvider, AudioFormat } from '@/types/stt'

interface AudioUploaderProps {
  provider?: STTProvider | null
  disabled?: boolean
  onFileSelected?: (file: File) => void
}

const ACCEPTED_FORMATS: AudioFormat[] = ['mp3', 'wav', 'm4a', 'flac', 'webm', 'ogg']

export function AudioUploader({
  provider,
  disabled = false,
  onFileSelected,
}: AudioUploaderProps) {
  const { audioFile, audioUrl, setAudioFile, clearAudio } = useSTTStore()
  const [isDragging, setIsDragging] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file type
      const extension = file.name.split('.').pop()?.toLowerCase() as AudioFormat
      if (!ACCEPTED_FORMATS.includes(extension)) {
        return `Unsupported format. Accepted: ${ACCEPTED_FORMATS.join(', ')}`
      }

      // Check provider-specific limits
      if (provider) {
        // Format check
        if (!provider.supported_formats.includes(extension)) {
          return `${provider.display_name} does not support .${extension} format`
        }

        // Size check
        const maxBytes = provider.max_file_size_mb * 1024 * 1024
        if (file.size > maxBytes) {
          return `File size exceeds ${provider.max_file_size_mb}MB limit for ${provider.display_name}`
        }
      }

      return null
    },
    [provider]
  )

  const handleFile = useCallback(
    (file: File) => {
      setValidationError(null)

      const error = validateFile(file)
      if (error) {
        setValidationError(error)
        return
      }

      setAudioFile(file)
      onFileSelected?.(file)
    },
    [validateFile, setAudioFile, onFileSelected]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragging(false)

      if (disabled) return

      const files = e.dataTransfer.files
      if (files.length > 0) {
        handleFile(files[0])
      }
    },
    [disabled, handleFile]
  )

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      if (!disabled) {
        setIsDragging(true)
      }
    },
    [disabled]
  )

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleFile(files[0])
      }
      // Reset input value to allow re-selecting same file
      e.target.value = ''
    },
    [handleFile]
  )

  const handleClear = useCallback(() => {
    clearAudio()
    setValidationError(null)
  }, [clearAudio])

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : 'border-gray-300 dark:border-gray-600'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gray-400'}
        `}
      >
        <input
          type="file"
          accept={ACCEPTED_FORMATS.map((f) => `.${f}`).join(',')}
          onChange={handleFileInput}
          disabled={disabled}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />

        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div className="text-gray-600 dark:text-gray-400">
            <span className="font-medium text-blue-600 dark:text-blue-400">
              Upload an audio file
            </span>{' '}
            or drag and drop
          </div>
          <p className="text-xs text-gray-500">
            {provider
              ? `${provider.supported_formats.map((f) => f.toUpperCase()).join(', ')} up to ${provider.max_file_size_mb}MB`
              : 'MP3, WAV, M4A, FLAC, WEBM, OGG'}
          </p>
        </div>
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="text-red-600 text-sm bg-red-50 dark:bg-red-950 p-3 rounded-md">
          {validationError}
        </div>
      )}

      {/* Selected File Info */}
      {audioFile && (
        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded">
              <svg
                className="h-5 w-5 text-blue-600 dark:text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                />
              </svg>
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-xs">
                {audioFile.name}
              </p>
              <p className="text-sm text-gray-500">{formatFileSize(audioFile.size)}</p>
            </div>
          </div>
          <button
            onClick={handleClear}
            className="text-gray-400 hover:text-red-500 transition-colors"
            title="Remove file"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      )}

      {/* Audio Preview */}
      {audioUrl && (
        <div className="mt-4">
          <audio controls src={audioUrl} className="w-full" />
        </div>
      )}
    </div>
  )
}
