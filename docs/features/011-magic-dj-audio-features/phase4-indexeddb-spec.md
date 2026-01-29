# Phase 4: IndexedDB 本地音檔儲存

## 概述

將音檔從 localStorage (base64) 遷移到 IndexedDB (Blob)，解決容量限制問題並提升效能。

## 問題分析

### 現況問題

| 問題 | 影響 |
|------|------|
| localStorage 容量限制 5-10MB | 用戶只能存 3-5 個音檔 |
| base64 編碼增加 33% 大小 | 10MB 檔案變成 13.3MB |
| 同步操作阻塞 UI | 載入時頁面卡頓 |
| 無法顯示剩餘容量 | 用戶不知道何時會滿 |
| 錯誤訊息不友善 | "QuotaExceededError" 難以理解 |

### 目標

1. **擴大容量**：從 ~7MB → 50MB+
2. **提升效能**：非同步操作，不阻塞 UI
3. **友善體驗**：清楚的容量警告和錯誤訊息
4. **平滑遷移**：自動遷移舊 localStorage 資料

---

## 技術規格

### 1. AudioStorageService

```typescript
// frontend/src/lib/audioStorage.ts

interface StoredAudio {
  trackId: string
  blob: Blob
  size: number
  mimeType: string
  savedAt: number
  checksum?: string
}

interface StorageQuota {
  used: number      // 已使用 bytes
  total: number     // 總容量 bytes
  percentage: number // 使用百分比
}

interface AudioStorageError {
  code: 'QUOTA_EXCEEDED' | 'NOT_FOUND' | 'CORRUPTED' | 'BROWSER_NOT_SUPPORTED' | 'UNKNOWN'
  message: string
  userMessage: string  // 友善的中文訊息
  trackId?: string
}

class AudioStorageService {
  // 初始化
  init(): Promise<void>

  // CRUD 操作
  save(trackId: string, blob: Blob): Promise<void>
  get(trackId: string): Promise<Blob | null>
  delete(trackId: string): Promise<void>
  deleteAll(): Promise<void>

  // 批次操作
  getMultiple(trackIds: string[]): Promise<Map<string, Blob>>

  // 容量查詢
  getQuota(): Promise<StorageQuota>
  getUsedSpace(): Promise<number>

  // 驗證
  verify(trackId: string): Promise<boolean>

  // 遷移
  migrateFromLocalStorage(): Promise<MigrationResult>
}
```

### 2. 容量警告等級

| 等級 | 使用率 | 顏色 | 訊息 |
|------|--------|------|------|
| 正常 | 0-70% | 綠色 | 無 |
| 警告 | 70-90% | 黃色 | "儲存空間即將不足，建議上傳至雲端" |
| 危險 | 90-100% | 紅色 | "儲存空間幾乎已滿，請刪除或上傳音檔" |
| 已滿 | 100% | 紅色 | "儲存空間已滿，無法儲存新音檔" |

### 3. 錯誤訊息對照表

| 錯誤碼 | 技術訊息 | 使用者訊息 |
|--------|----------|-----------|
| `QUOTA_EXCEEDED` | QuotaExceededError | 儲存空間已滿。請刪除部分音檔或上傳至雲端後再試。 |
| `NOT_FOUND` | Audio not found | 找不到音檔「{name}」，可能已被刪除。 |
| `CORRUPTED` | Checksum mismatch | 音檔「{name}」已損壞，請重新產生或上傳。 |
| `BROWSER_NOT_SUPPORTED` | IndexedDB not available | 您的瀏覽器不支援本地儲存。請使用 Chrome、Firefox 或 Edge。 |
| `UNKNOWN` | Unknown error | 儲存音檔時發生錯誤，請重試。如問題持續，請嘗試重新整理頁面。 |

---

## UI 設計

### 1. 儲存空間指示器 (StorageIndicator)

```
位置：DJControlPanel 標題列右側

顯示樣式：
┌─────────────────────────────────────┐
│  💾 本機儲存: 35.2 MB / 50 MB (70%) │
│  [████████████████░░░░░░░░]         │
└─────────────────────────────────────┘

警告樣式 (>70%):
┌─────────────────────────────────────┐
│  ⚠️ 本機儲存: 42.5 MB / 50 MB (85%) │
│  [██████████████████████░░░]        │
│  儲存空間即將不足                     │
└─────────────────────────────────────┘

危險樣式 (>90%):
┌─────────────────────────────────────┐
│  🔴 本機儲存: 48.2 MB / 50 MB (96%) │
│  [██████████████████████████]       │
│  儲存空間幾乎已滿！                   │
│  [上傳至雲端]                        │
└─────────────────────────────────────┘
```

### 2. 錯誤 Toast 訊息

```
錯誤 Toast 樣式：
┌─────────────────────────────────────┐
│ ❌ 無法儲存音檔                      │
│                                     │
│ 儲存空間已滿。請刪除部分音檔或上傳     │
│ 至雲端後再試。                       │
│                                     │
│ [刪除音檔] [上傳至雲端] [關閉]        │
└─────────────────────────────────────┘
```

### 3. 遷移對話框

```
首次偵測到舊資料時顯示：
┌─────────────────────────────────────┐
│ 🔄 升級本地儲存                      │
│                                     │
│ 偵測到 3 個使用舊格式儲存的音檔。     │
│ 升級後可支援更大的儲存空間。           │
│                                     │
│ 音檔：                               │
│ • 開場 (2.3 MB)                     │
│ • 思考音效 (1.5 MB)                  │
│ • 緊急結束 (0.8 MB)                  │
│                                     │
│ [立即升級] [稍後再說]                 │
└─────────────────────────────────────┘
```

---

## 資料結構

### IndexedDB Schema

```typescript
// Database: magic-dj-audio
// Version: 1

// Object Store: audio-blobs
interface AudioBlobRecord {
  trackId: string       // Primary Key
  blob: Blob
  size: number
  mimeType: string
  checksum: string      // MD5 hash for verification
  savedAt: number       // Unix timestamp
  version: number       // Schema version for future migrations
}

// Object Store: metadata
interface MetadataRecord {
  key: string           // Primary Key
  value: unknown
  updatedAt: number
}
```

### Store State 擴展

```typescript
// types/magic-dj.ts

interface MagicDJState {
  // ... existing fields ...

  // === Local Storage (Phase 4) ===
  /** 本地儲存容量資訊 */
  storageQuota: StorageQuota | null
  /** 是否正在遷移舊資料 */
  isMigrating: boolean
  /** 需要遷移的音軌數量 */
  migrationPending: number
}

interface Track {
  // ... existing fields ...

  // 移除
  // audioBase64?: string

  // 新增
  /** 是否有本地 IndexedDB 音檔 */
  hasLocalAudio: boolean
  /** 本地音檔大小 (bytes) */
  localAudioSize?: number
}
```

---

## 測試計畫

### 1. 單元測試 (AudioStorageService)

```typescript
// __tests__/lib/audioStorage.test.ts

describe('AudioStorageService', () => {
  describe('save/get', () => {
    it('should save and retrieve audio blob', async () => {
      const blob = new Blob(['test'], { type: 'audio/mpeg' })
      await audioStorage.save('track-1', blob)
      const retrieved = await audioStorage.get('track-1')
      expect(retrieved).toEqual(blob)
    })

    it('should return null for non-existent track', async () => {
      const result = await audioStorage.get('non-existent')
      expect(result).toBeNull()
    })

    it('should overwrite existing audio', async () => {
      const blob1 = new Blob(['v1'], { type: 'audio/mpeg' })
      const blob2 = new Blob(['v2'], { type: 'audio/mpeg' })
      await audioStorage.save('track-1', blob1)
      await audioStorage.save('track-1', blob2)
      const retrieved = await audioStorage.get('track-1')
      expect(await retrieved.text()).toBe('v2')
    })
  })

  describe('delete', () => {
    it('should delete existing audio', async () => {
      const blob = new Blob(['test'], { type: 'audio/mpeg' })
      await audioStorage.save('track-1', blob)
      await audioStorage.delete('track-1')
      const result = await audioStorage.get('track-1')
      expect(result).toBeNull()
    })

    it('should not throw when deleting non-existent audio', async () => {
      await expect(audioStorage.delete('non-existent')).resolves.not.toThrow()
    })
  })

  describe('getQuota', () => {
    it('should return storage quota information', async () => {
      const quota = await audioStorage.getQuota()
      expect(quota).toHaveProperty('used')
      expect(quota).toHaveProperty('total')
      expect(quota).toHaveProperty('percentage')
      expect(quota.percentage).toBeGreaterThanOrEqual(0)
      expect(quota.percentage).toBeLessThanOrEqual(100)
    })

    it('should update after saving audio', async () => {
      const before = await audioStorage.getQuota()
      const blob = new Blob(['x'.repeat(1000)], { type: 'audio/mpeg' })
      await audioStorage.save('track-1', blob)
      const after = await audioStorage.getQuota()
      expect(after.used).toBeGreaterThan(before.used)
    })
  })

  describe('error handling', () => {
    it('should throw QUOTA_EXCEEDED when storage is full', async () => {
      // Mock storage to be full
      // ...
    })

    it('should throw BROWSER_NOT_SUPPORTED when IndexedDB unavailable', async () => {
      // Mock IndexedDB to be unavailable
      // ...
    })
  })
})
```

### 2. 整合測試 (Store Integration)

```typescript
// __tests__/stores/magicDJStore.indexeddb.test.ts

describe('magicDJStore IndexedDB Integration', () => {
  describe('saveTrackAudio', () => {
    it('should save audio and update track.hasLocalAudio', async () => {
      const { saveTrackAudio, tracks } = useMagicDJStore.getState()
      const blob = createTestAudioBlob()

      await saveTrackAudio('track_01_intro', blob)

      const track = tracks.find(t => t.id === 'track_01_intro')
      expect(track?.hasLocalAudio).toBe(true)
      expect(track?.localAudioSize).toBe(blob.size)
    })

    it('should update storageQuota after save', async () => {
      const store = useMagicDJStore.getState()
      const before = store.storageQuota

      await store.saveTrackAudio('track_01', createTestAudioBlob(1024 * 1024))

      const after = useMagicDJStore.getState().storageQuota
      expect(after.used).toBeGreaterThan(before?.used ?? 0)
    })
  })

  describe('loadTrackAudio', () => {
    it('should create blob URL from stored audio', async () => {
      const store = useMagicDJStore.getState()
      const blob = createTestAudioBlob()
      await store.saveTrackAudio('track_01', blob)

      const url = await store.loadTrackAudio('track_01')

      expect(url).toMatch(/^blob:/)
    })

    it('should return null for track without audio', async () => {
      const url = await useMagicDJStore.getState().loadTrackAudio('no-audio')
      expect(url).toBeNull()
    })
  })

  describe('migration', () => {
    it('should migrate base64 audio to IndexedDB', async () => {
      // Setup old localStorage data
      const oldData = {
        tracks: [{
          id: 'track_01',
          audioBase64: btoa('test audio data'),
          // ...
        }]
      }
      localStorage.setItem('magic-dj-store', JSON.stringify(oldData))

      const result = await useMagicDJStore.getState().migrateFromLocalStorage()

      expect(result.migratedCount).toBe(1)
      expect(result.errors).toHaveLength(0)

      // Verify stored in IndexedDB
      const blob = await audioStorage.get('track_01')
      expect(blob).not.toBeNull()
    })
  })
})
```

### 3. UI 測試 (StorageIndicator)

```typescript
// __tests__/components/StorageIndicator.test.tsx

describe('StorageIndicator', () => {
  it('should show normal state when under 70%', () => {
    render(<StorageIndicator quota={{ used: 30, total: 100, percentage: 30 }} />)
    expect(screen.getByText('30%')).toHaveClass('text-green-600')
    expect(screen.queryByText(/即將不足/)).not.toBeInTheDocument()
  })

  it('should show warning when 70-90%', () => {
    render(<StorageIndicator quota={{ used: 80, total: 100, percentage: 80 }} />)
    expect(screen.getByText('80%')).toHaveClass('text-yellow-600')
    expect(screen.getByText(/即將不足/)).toBeInTheDocument()
  })

  it('should show danger when over 90%', () => {
    render(<StorageIndicator quota={{ used: 95, total: 100, percentage: 95 }} />)
    expect(screen.getByText('95%')).toHaveClass('text-red-600')
    expect(screen.getByText(/幾乎已滿/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /上傳至雲端/ })).toBeInTheDocument()
  })

  it('should show upload button when quota is critical', () => {
    render(<StorageIndicator quota={{ used: 95, total: 100, percentage: 95 }} />)
    fireEvent.click(screen.getByRole('button', { name: /上傳至雲端/ }))
    // Verify upload dialog opens
  })
})
```

### 4. E2E 測試場景

```typescript
// e2e/magic-dj-storage.spec.ts

describe('Magic DJ Local Storage', () => {
  test('user can save and load audio locally', async ({ page }) => {
    await page.goto('/magic-dj')

    // Upload audio file
    await page.click('[data-testid="track-01-edit"]')
    await page.setInputFiles('[data-testid="audio-upload"]', 'test-audio.mp3')
    await page.click('[data-testid="save-track"]')

    // Verify storage indicator updates
    await expect(page.locator('[data-testid="storage-indicator"]')).toContainText('MB')

    // Reload page and verify audio persists
    await page.reload()
    await expect(page.locator('[data-testid="track-01-audio"]')).toBeEnabled()
  })

  test('shows warning when storage is nearly full', async ({ page }) => {
    // Fill storage to 85%
    // ...

    await expect(page.locator('[data-testid="storage-warning"]')).toContainText('即將不足')
  })

  test('shows error and alternatives when storage is full', async ({ page }) => {
    // Fill storage to 100%
    // ...

    // Try to save another audio
    await page.click('[data-testid="track-02-edit"]')
    await page.setInputFiles('[data-testid="audio-upload"]', 'large-audio.mp3')
    await page.click('[data-testid="save-track"]')

    // Verify error message
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('儲存空間已滿')
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('上傳至雲端')
  })

  test('migrates old localStorage data on first load', async ({ page }) => {
    // Setup old localStorage data
    await page.evaluate(() => {
      localStorage.setItem('magic-dj-store', JSON.stringify({
        tracks: [{ id: 'track_01', audioBase64: '...' }]
      }))
    })

    await page.goto('/magic-dj')

    // Verify migration dialog
    await expect(page.locator('[data-testid="migration-dialog"]')).toBeVisible()
    await page.click('[data-testid="migrate-now"]')

    // Verify migration success
    await expect(page.locator('[data-testid="migration-dialog"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="track-01-audio"]')).toBeEnabled()
  })
})
```

---

## 實作順序

### Step 1: AudioStorageService (核心)
1. 建立 `lib/audioStorage.ts`
2. 實作 IndexedDB 初始化
3. 實作 CRUD 操作
4. 實作容量查詢
5. 實作錯誤處理

### Step 2: 錯誤訊息系統
1. 建立錯誤類型定義
2. 建立錯誤訊息對照表
3. 建立 Toast 通知元件

### Step 3: Store 整合
1. 擴展 Track 類型
2. 新增 storage actions
3. 修改 persist 設定

### Step 4: UI 元件
1. StorageIndicator 元件
2. MigrationDialog 元件
3. 整合到 DJControlPanel

### Step 5: 遷移邏輯
1. 偵測舊資料
2. 批次遷移
3. 清理舊資料

### Step 6: 測試
1. 單元測試
2. 整合測試
3. E2E 測試

---

## 瀏覽器相容性

| 瀏覽器 | IndexedDB 支援 | 預設容量 |
|--------|---------------|----------|
| Chrome 88+ | ✅ | 60% 磁碟空間 |
| Firefox 78+ | ✅ | 50% 磁碟空間 |
| Safari 14+ | ✅ | 1GB |
| Edge 88+ | ✅ | 60% 磁碟空間 |
| IE 11 | ⚠️ 有限 | 250MB |

### Fallback 策略

```typescript
if (!window.indexedDB) {
  // 降級到 localStorage (顯示容量警告)
  console.warn('IndexedDB not supported, falling back to localStorage')
  return new LocalStorageFallback()
}
```

---

## 風險與緩解

| 風險 | 緩解措施 |
|------|----------|
| IndexedDB 操作失敗 | 完整的錯誤處理 + 重試機制 |
| 遷移中斷 | 記錄遷移進度，支援斷點續傳 |
| 資料損壞 | Checksum 驗證 + 自動修復提示 |
| 隱私模式限制 | 偵測並提示用戶 |

---

## 時程估計

| 階段 | 工作項目 | 估計時間 |
|------|----------|----------|
| 1 | AudioStorageService | 2 小時 |
| 2 | 錯誤訊息系統 | 1 小時 |
| 3 | Store 整合 | 2 小時 |
| 4 | UI 元件 | 2 小時 |
| 5 | 遷移邏輯 | 1.5 小時 |
| 6 | 測試 | 2 小時 |
| **總計** | | **~10.5 小時** |
