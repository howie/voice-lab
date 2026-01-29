/**
 * Audio Dropzone Component
 * Feature: 011-magic-dj-audio-features
 *
 * T010-T016: Drag and drop audio file upload component.
 * Supports MP3, WAV, OGG, WebM files up to 10MB.
 */

import { useCallback, useRef, useState } from 'react'
import { Upload, FileAudio, X, AlertCircle, Loader2 } from 'lucide-react'

import { cn } from '@/lib/utils'
import {
  SUPPORTED_AUDIO_TYPES,
  MAX_FILE_SIZE,
  type FileUploadState,
} from '@/types/magic-dj'
import { audioStorage, STORAGE_THRESHOLDS } from '@/lib/audioStorage'

// =============================================================================
// Types
// =============================================================================

export interface AudioDropzoneProps {
  /** Callback when file is accepted and processed */
  onFileAccepted: (state: FileUploadState) => void
  /** Callback when error occurs */
  onError?: (error: string) => void
  /** Whether file is being processed */
  isProcessing?: boolean
  /** Current uploaded file info */
  currentFile?: {
    fileName: string
    fileSize: number
    duration: number | null
  } | null
  /** Whether the component is disabled */
  disabled?: boolean
  /** Custom class name */
  className?: string
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Format file size to human-readable string
 */
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

/**
 * Format duration in milliseconds to mm:ss
 */
const formatDuration = (ms: number): string => {
  const seconds = Math.floor(ms / 1000)
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * Validate file type and size (T013)
 */
const validateFile = (file: File): string | null => {
  // Check file type
  if (!SUPPORTED_AUDIO_TYPES.includes(file.type as typeof SUPPORTED_AUDIO_TYPES[number])) {
    const supportedFormats = 'MP3, WAV, OGG, WebM'
    return `不支援的檔案格式。支援的格式：${supportedFormats}`
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const maxSizeMB = MAX_FILE_SIZE / (1024 * 1024)
    return `檔案大小超過上限 (${maxSizeMB}MB)`
  }

  return null
}

/**
 * Get audio duration (T015)
 */
const getAudioDuration = (url: string): Promise<number> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio()
    audio.onloadedmetadata = () => {
      resolve(Math.round(audio.duration * 1000)) // Convert to milliseconds
    }
    audio.onerror = () => reject(new Error('Failed to load audio'))
    audio.src = url
  })
}

/**
 * Check IndexedDB storage quota (T016, Phase 4)
 */
const checkStorageQuota = async (dataSize: number): Promise<{ hasSpace: boolean; percentage: number }> => {
  try {
    await audioStorage.init()
    const quota = await audioStorage.getQuota()

    // Calculate if there's space (IndexedDB stores raw blobs, no base64 overhead)
    const available = quota.total - quota.used
    const hasSpace = dataSize < available && quota.percentage < STORAGE_THRESHOLDS.CRITICAL

    return { hasSpace, percentage: quota.percentage }
  } catch {
    // If we can't check, assume it's okay
    return { hasSpace: true, percentage: 0 }
  }
}

// =============================================================================
// Component
// =============================================================================

export function AudioDropzone({
  onFileAccepted,
  onError,
  isProcessing = false,
  currentFile,
  disabled = false,
  className,
}: AudioDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [localProcessing, setLocalProcessing] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const processing = isProcessing || localProcessing

  /**
   * Process uploaded file (T014, T015, T016)
   */
  const processFile = useCallback(
    async (file: File) => {
      setLocalProcessing(true)
      setLocalError(null)

      try {
        // Validate file (T013)
        const validationError = validateFile(file)
        if (validationError) {
          setLocalError(validationError)
          onError?.(validationError)
          return
        }

        // Check storage quota (T016, Phase 4)
        const quotaCheck = await checkStorageQuota(file.size)
        if (!quotaCheck.hasSpace) {
          const error = quotaCheck.percentage >= STORAGE_THRESHOLDS.CRITICAL
            ? '儲存空間已滿，請刪除部分音檔或上傳至雲端'
            : '儲存空間不足，請刪除不需要的音軌後再試'
          setLocalError(error)
          onError?.(error)
          return
        }

        // Create blob URL for preview
        const audioUrl = URL.createObjectURL(file)

        // Get duration (T015)
        let duration: number | null = null
        try {
          duration = await getAudioDuration(audioUrl)
        } catch {
          // Duration is optional, continue without it
        }

        // Phase 4: No longer generate base64, use IndexedDB for blob storage
        const state: FileUploadState = {
          file, // Pass the File (Blob) for IndexedDB storage
          fileName: file.name,
          fileSize: file.size,
          audioUrl,
          audioBase64: null, // Deprecated in Phase 4
          duration,
          error: null,
          isProcessing: false,
        }

        onFileAccepted(state)
      } catch (err) {
        const error = err instanceof Error ? err.message : '處理檔案時發生錯誤'
        setLocalError(error)
        onError?.(error)
      } finally {
        setLocalProcessing(false)
      }
    },
    [onFileAccepted, onError]
  )

  /**
   * Handle drag events (T011)
   */
  const handleDragEnter = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (!disabled && !processing) {
        setIsDragging(true)
      }
    },
    [disabled, processing]
  )

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (!disabled && !processing) {
        setIsDragging(true)
      }
    },
    [disabled, processing]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      if (disabled || processing) return

      const files = e.dataTransfer.files
      if (files.length > 0) {
        processFile(files[0])
      }
    },
    [disabled, processing, processFile]
  )

  /**
   * Handle click to select file (T012)
   */
  const handleClick = useCallback(() => {
    if (disabled || processing) return
    fileInputRef.current?.click()
  }, [disabled, processing])

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        processFile(files[0])
      }
      // Reset input so the same file can be selected again
      e.target.value = ''
    },
    [processFile]
  )

  /**
   * Clear current file
   */
  const handleClear = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      setLocalError(null)
      onFileAccepted({
        file: null,
        fileName: '',
        fileSize: 0,
        audioUrl: null,
        audioBase64: null,
        duration: null,
        error: null,
        isProcessing: false,
      })
    },
    [onFileAccepted]
  )

  return (
    <div
      className={cn(
        'relative rounded-lg border-2 border-dashed transition-all',
        isDragging
          ? 'border-primary bg-primary/10'
          : localError
            ? 'border-destructive bg-destructive/5'
            : currentFile
              ? 'border-green-500 bg-green-500/5'
              : 'border-muted-foreground/30 hover:border-primary/50',
        disabled && 'opacity-50 cursor-not-allowed',
        !disabled && !processing && 'cursor-pointer',
        className
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={SUPPORTED_AUDIO_TYPES.join(',')}
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled || processing}
      />

      <div className="flex flex-col items-center justify-center gap-3 p-6">
        {processing ? (
          // Processing state
          <>
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">處理中...</p>
          </>
        ) : localError ? (
          // Error state
          <>
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-sm text-destructive text-center">{localError}</p>
            <button
              onClick={handleClear}
              className="text-sm text-muted-foreground hover:text-foreground underline"
            >
              重試
            </button>
          </>
        ) : currentFile ? (
          // File selected state
          <>
            <FileAudio className="h-10 w-10 text-green-500" />
            <div className="text-center">
              <p className="font-medium truncate max-w-[200px]">{currentFile.fileName}</p>
              <p className="text-sm text-muted-foreground">
                {formatFileSize(currentFile.fileSize)}
                {currentFile.duration && ` / ${formatDuration(currentFile.duration)}`}
              </p>
            </div>
            <button
              onClick={handleClear}
              className="flex items-center gap-1 text-sm text-muted-foreground hover:text-destructive"
            >
              <X className="h-4 w-4" />
              移除
            </button>
          </>
        ) : (
          // Default state
          <>
            <Upload className="h-10 w-10 text-muted-foreground" />
            <div className="text-center">
              <p className="font-medium">拖放音檔或點擊選擇</p>
              <p className="text-sm text-muted-foreground">
                支援 MP3, WAV, OGG, WebM (最大 10MB)
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default AudioDropzone
