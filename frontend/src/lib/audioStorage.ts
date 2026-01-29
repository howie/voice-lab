/**
 * Audio Storage Service
 * Feature: 011-magic-dj-audio-features Phase 4
 *
 * IndexedDB-based storage for audio blobs, replacing localStorage base64 storage.
 * Provides larger capacity (~50MB+) and better performance.
 */

// =============================================================================
// Types
// =============================================================================

export interface StoredAudio {
  trackId: string
  blob: Blob
  size: number
  mimeType: string
  savedAt: number
  version: number
}

export interface StorageQuota {
  /** Used space in bytes */
  used: number
  /** Total available space in bytes */
  total: number
  /** Usage percentage (0-100) */
  percentage: number
}

export type AudioStorageErrorCode =
  | 'QUOTA_EXCEEDED'
  | 'NOT_FOUND'
  | 'CORRUPTED'
  | 'BROWSER_NOT_SUPPORTED'
  | 'DB_ERROR'
  | 'UNKNOWN'

export interface AudioStorageError {
  code: AudioStorageErrorCode
  message: string
  userMessage: string
  trackId?: string
  originalError?: Error
}

export interface MigrationResult {
  migratedCount: number
  skippedCount: number
  errors: Array<{ trackId: string; error: string }>
  totalSizeBytes: number
}

// =============================================================================
// Constants
// =============================================================================

const DB_NAME = 'magic-dj-audio'
const DB_VERSION = 1
const STORE_NAME = 'audio-blobs'
const SCHEMA_VERSION = 1

// Storage warning thresholds
export const STORAGE_THRESHOLDS = {
  WARNING: 70, // 70% - show warning
  DANGER: 90, // 90% - show danger
  CRITICAL: 100, // 100% - prevent saves
} as const

// Default fallback quota (50MB) when browser doesn't report
const DEFAULT_QUOTA_BYTES = 50 * 1024 * 1024

// =============================================================================
// Error Messages (Chinese)
// =============================================================================

const ERROR_MESSAGES: Record<AudioStorageErrorCode, { message: string; userMessage: string }> = {
  QUOTA_EXCEEDED: {
    message: 'Storage quota exceeded',
    userMessage: '儲存空間已滿。請刪除部分音檔或上傳至雲端後再試。',
  },
  NOT_FOUND: {
    message: 'Audio not found',
    userMessage: '找不到音檔，可能已被刪除。',
  },
  CORRUPTED: {
    message: 'Audio data corrupted',
    userMessage: '音檔已損壞，請重新產生或上傳。',
  },
  BROWSER_NOT_SUPPORTED: {
    message: 'IndexedDB not supported',
    userMessage: '您的瀏覽器不支援本地儲存。請使用 Chrome、Firefox 或 Edge。',
  },
  DB_ERROR: {
    message: 'Database error',
    userMessage: '儲存音檔時發生資料庫錯誤，請重試。',
  },
  UNKNOWN: {
    message: 'Unknown error',
    userMessage: '儲存音檔時發生錯誤，請重試。如問題持續，請嘗試重新整理頁面。',
  },
}

// =============================================================================
// Helper Functions
// =============================================================================

function createError(
  code: AudioStorageErrorCode,
  trackId?: string,
  originalError?: Error
): AudioStorageError {
  const { message, userMessage } = ERROR_MESSAGES[code]
  return {
    code,
    message,
    userMessage: trackId ? userMessage.replace('音檔', `音檔「${trackId}」`) : userMessage,
    trackId,
    originalError,
  }
}

function isQuotaExceededError(error: unknown): boolean {
  if (error instanceof DOMException) {
    return (
      error.name === 'QuotaExceededError' ||
      error.code === 22 || // Legacy code
      error.message.toLowerCase().includes('quota')
    )
  }
  return false
}

// =============================================================================
// AudioStorageService Class
// =============================================================================

class AudioStorageService {
  private db: IDBDatabase | null = null
  private initPromise: Promise<void> | null = null

  /**
   * Check if IndexedDB is supported
   */
  isSupported(): boolean {
    return typeof indexedDB !== 'undefined' && indexedDB !== null
  }

  /**
   * Initialize the IndexedDB database
   */
  async init(): Promise<void> {
    // Return existing initialization promise if in progress
    if (this.initPromise) {
      return this.initPromise
    }

    // Already initialized
    if (this.db) {
      return Promise.resolve()
    }

    this.initPromise = this._initDB()
    return this.initPromise
  }

  private async _initDB(): Promise<void> {
    if (!this.isSupported()) {
      throw createError('BROWSER_NOT_SUPPORTED')
    }

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onerror = () => {
        this.initPromise = null
        reject(createError('DB_ERROR', undefined, request.error ?? undefined))
      }

      request.onsuccess = () => {
        this.db = request.result
        this.initPromise = null
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'trackId' })
          store.createIndex('savedAt', 'savedAt', { unique: false })
          store.createIndex('size', 'size', { unique: false })
        }
      }
    })
  }

  private async ensureDB(): Promise<IDBDatabase> {
    if (!this.db) {
      await this.init()
    }
    if (!this.db) {
      throw createError('DB_ERROR')
    }
    return this.db
  }

  // ===========================================================================
  // CRUD Operations
  // ===========================================================================

  /**
   * Save audio blob to IndexedDB
   */
  async save(trackId: string, blob: Blob): Promise<void> {
    const db = await this.ensureDB()

    const record: StoredAudio = {
      trackId,
      blob,
      size: blob.size,
      mimeType: blob.type || 'audio/mpeg',
      savedAt: Date.now(),
      version: SCHEMA_VERSION,
    }

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)

      const request = store.put(record)

      request.onerror = () => {
        if (isQuotaExceededError(request.error)) {
          reject(createError('QUOTA_EXCEEDED', trackId, request.error ?? undefined))
        } else {
          reject(createError('DB_ERROR', trackId, request.error ?? undefined))
        }
      }

      tx.oncomplete = () => resolve()
      tx.onerror = () => {
        if (isQuotaExceededError(tx.error)) {
          reject(createError('QUOTA_EXCEEDED', trackId, tx.error ?? undefined))
        } else {
          reject(createError('DB_ERROR', trackId, tx.error ?? undefined))
        }
      }
    })
  }

  /**
   * Get audio blob from IndexedDB
   */
  async get(trackId: string): Promise<Blob | null> {
    const db = await this.ensureDB()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.get(trackId)

      request.onsuccess = () => {
        const record = request.result as StoredAudio | undefined
        resolve(record?.blob ?? null)
      }

      request.onerror = () => {
        reject(createError('DB_ERROR', trackId, request.error ?? undefined))
      }
    })
  }

  /**
   * Get stored audio metadata (without blob)
   */
  async getMetadata(trackId: string): Promise<Omit<StoredAudio, 'blob'> | null> {
    const db = await this.ensureDB()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.get(trackId)

      request.onsuccess = () => {
        const record = request.result as StoredAudio | undefined
        if (record) {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { blob, ...metadata } = record
          resolve(metadata)
        } else {
          resolve(null)
        }
      }

      request.onerror = () => {
        reject(createError('DB_ERROR', trackId, request.error ?? undefined))
      }
    })
  }

  /**
   * Check if audio exists for a track
   */
  async exists(trackId: string): Promise<boolean> {
    const metadata = await this.getMetadata(trackId)
    return metadata !== null
  }

  /**
   * Delete audio for a track
   */
  async delete(trackId: string): Promise<void> {
    const db = await this.ensureDB()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const request = store.delete(trackId)

      tx.oncomplete = () => resolve()
      tx.onerror = () => {
        reject(createError('DB_ERROR', trackId, tx.error ?? undefined))
      }
      request.onerror = () => {
        reject(createError('DB_ERROR', trackId, request.error ?? undefined))
      }
    })
  }

  /**
   * Delete all stored audio
   */
  async deleteAll(): Promise<void> {
    const db = await this.ensureDB()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const request = store.clear()

      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(createError('DB_ERROR', undefined, tx.error ?? undefined))
      request.onerror = () => reject(createError('DB_ERROR', undefined, request.error ?? undefined))
    })
  }

  /**
   * Get multiple audio blobs at once
   */
  async getMultiple(trackIds: string[]): Promise<Map<string, Blob>> {
    const db = await this.ensureDB()
    const result = new Map<string, Blob>()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)

      let completed = 0

      for (const trackId of trackIds) {
        const request = store.get(trackId)
        request.onsuccess = () => {
          const record = request.result as StoredAudio | undefined
          if (record?.blob) {
            result.set(trackId, record.blob)
          }
          completed++
          if (completed === trackIds.length) {
            resolve(result)
          }
        }
        request.onerror = () => {
          reject(createError('DB_ERROR', trackId, request.error ?? undefined))
        }
      }

      // Handle empty array
      if (trackIds.length === 0) {
        resolve(result)
      }
    })
  }

  /**
   * Get all stored track IDs
   */
  async getAllTrackIds(): Promise<string[]> {
    const db = await this.ensureDB()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.getAllKeys()

      request.onsuccess = () => {
        resolve(request.result as string[])
      }

      request.onerror = () => {
        reject(createError('DB_ERROR', undefined, request.error ?? undefined))
      }
    })
  }

  // ===========================================================================
  // Storage Quota
  // ===========================================================================

  /**
   * Get storage quota information
   */
  async getQuota(): Promise<StorageQuota> {
    // Try to use Storage API if available
    if (navigator.storage && navigator.storage.estimate) {
      try {
        const estimate = await navigator.storage.estimate()
        const used = estimate.usage ?? 0
        const total = estimate.quota ?? DEFAULT_QUOTA_BYTES

        return {
          used,
          total,
          percentage: Math.round((used / total) * 100),
        }
      } catch {
        // Fall back to manual calculation
      }
    }

    // Fallback: calculate used space manually
    const used = await this.getUsedSpace()
    return {
      used,
      total: DEFAULT_QUOTA_BYTES,
      percentage: Math.round((used / DEFAULT_QUOTA_BYTES) * 100),
    }
  }

  /**
   * Get total used space in bytes
   */
  async getUsedSpace(): Promise<number> {
    const db = await this.ensureDB()

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.getAll()

      request.onsuccess = () => {
        const records = request.result as StoredAudio[]
        const total = records.reduce((sum, record) => sum + (record.size || 0), 0)
        resolve(total)
      }

      request.onerror = () => {
        reject(createError('DB_ERROR', undefined, request.error ?? undefined))
      }
    })
  }

  /**
   * Get warning level based on storage usage
   */
  getWarningLevel(percentage: number): 'normal' | 'warning' | 'danger' | 'critical' {
    if (percentage >= STORAGE_THRESHOLDS.CRITICAL) return 'critical'
    if (percentage >= STORAGE_THRESHOLDS.DANGER) return 'danger'
    if (percentage >= STORAGE_THRESHOLDS.WARNING) return 'warning'
    return 'normal'
  }

  /**
   * Get user-friendly warning message
   */
  getWarningMessage(level: 'normal' | 'warning' | 'danger' | 'critical'): string | null {
    switch (level) {
      case 'warning':
        return '儲存空間即將不足，建議上傳至雲端'
      case 'danger':
        return '儲存空間幾乎已滿，請刪除或上傳音檔'
      case 'critical':
        return '儲存空間已滿，無法儲存新音檔'
      default:
        return null
    }
  }

  // ===========================================================================
  // Migration from localStorage
  // ===========================================================================

  /**
   * Migrate audio data from localStorage (base64) to IndexedDB (blob)
   */
  async migrateFromLocalStorage(): Promise<MigrationResult> {
    const result: MigrationResult = {
      migratedCount: 0,
      skippedCount: 0,
      errors: [],
      totalSizeBytes: 0,
    }

    try {
      // Read old data from localStorage
      const oldDataStr = localStorage.getItem('magic-dj-store')
      if (!oldDataStr) {
        return result
      }

      const oldData = JSON.parse(oldDataStr)
      const tracks = oldData?.state?.tracks || oldData?.tracks || []

      for (const track of tracks) {
        if (!track.audioBase64) {
          result.skippedCount++
          continue
        }

        try {
          // Convert base64 to blob
          const blob = this.base64ToBlob(track.audioBase64, 'audio/mpeg')

          // Save to IndexedDB
          await this.save(track.id, blob)

          result.migratedCount++
          result.totalSizeBytes += blob.size
        } catch (error) {
          result.errors.push({
            trackId: track.id,
            error: error instanceof Error ? error.message : 'Unknown error',
          })
        }
      }

      // If all migrated successfully, clean up localStorage
      if (result.errors.length === 0 && result.migratedCount > 0) {
        // Remove audioBase64 from tracks but keep other data
        const cleanedTracks = tracks.map((track: Record<string, unknown>) => {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { audioBase64, ...rest } = track
          return { ...rest, hasLocalAudio: true }
        })

        if (oldData.state) {
          oldData.state.tracks = cleanedTracks
        } else {
          oldData.tracks = cleanedTracks
        }

        localStorage.setItem('magic-dj-store', JSON.stringify(oldData))
      }
    } catch (error) {
      console.error('Migration error:', error)
    }

    return result
  }

  /**
   * Check if there's data to migrate
   */
  hasPendingMigration(): boolean {
    try {
      const oldDataStr = localStorage.getItem('magic-dj-store')
      if (!oldDataStr) return false

      const oldData = JSON.parse(oldDataStr)
      const tracks = oldData?.state?.tracks || oldData?.tracks || []

      return tracks.some((track: Record<string, unknown>) => !!track.audioBase64)
    } catch {
      return false
    }
  }

  /**
   * Get count of tracks pending migration
   */
  getPendingMigrationCount(): number {
    try {
      const oldDataStr = localStorage.getItem('magic-dj-store')
      if (!oldDataStr) return 0

      const oldData = JSON.parse(oldDataStr)
      const tracks = oldData?.state?.tracks || oldData?.tracks || []

      return tracks.filter((track: Record<string, unknown>) => !!track.audioBase64).length
    } catch {
      return 0
    }
  }

  // ===========================================================================
  // Utility Methods
  // ===========================================================================

  /**
   * Convert base64 string to Blob
   */
  private base64ToBlob(base64: string, mimeType: string = 'audio/mpeg'): Blob {
    // Remove data URL prefix if present
    const base64Data = base64.replace(/^data:[^;]+;base64,/, '')

    const byteCharacters = atob(base64Data)
    const byteNumbers = new Array(byteCharacters.length)

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }

    const byteArray = new Uint8Array(byteNumbers)
    return new Blob([byteArray], { type: mimeType })
  }

  /**
   * Convert Blob to base64 string (for backwards compatibility if needed)
   */
  async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result as string
        // Remove data URL prefix
        const base64 = result.replace(/^data:[^;]+;base64,/, '')
        resolve(base64)
      }
      reader.onerror = () => reject(reader.error)
      reader.readAsDataURL(blob)
    })
  }

  /**
   * Create object URL for audio playback
   */
  createObjectURL(blob: Blob): string {
    return URL.createObjectURL(blob)
  }

  /**
   * Revoke object URL to free memory
   */
  revokeObjectURL(url: string): void {
    URL.revokeObjectURL(url)
  }

  /**
   * Format bytes to human-readable string
   */
  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'

    const units = ['B', 'KB', 'MB', 'GB']
    const k = 1024
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${units[i]}`
  }
}

// =============================================================================
// Singleton Export
// =============================================================================

export const audioStorage = new AudioStorageService()

// Also export the class for testing
export { AudioStorageService }
