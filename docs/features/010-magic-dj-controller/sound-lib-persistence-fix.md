# Sound Library Persistence Fix

**Date**: 2026-02-01
**Status**: In Progress
**Related Issue**: Sound library audio disappears on page refresh / SPA navigation

## Problem Statement

Magic DJ Sound Library 中的音效（音檔）在 page refresh 或 SPA 換頁後消失，無法播放。

## Architecture Overview

Sound Library 使用三層儲存架構：

| Layer | Technology | Content | Lifecycle |
|---|---|---|---|
| L1 | Zustand + `localStorage` | Track metadata, settings, channel queues | 跨 refresh 持久 |
| L2 | IndexedDB (`magic-dj-audio`) | Audio blob 二進位檔 | 跨 refresh 持久 |
| L3 | Backend PostgreSQL + GCS | 完整 preset + 音檔（需登入） | 永久 |

Blob URL (`blob:http://...`) 是運行時暫態，僅存活於當前 Document context，無法序列化。

## Root Cause Analysis

### BUG-1: `restoreTracks()` 是死程式碼 [CRITICAL]

**Location**: `magicDJStore.ts:259-270` vs `magicDJStore.ts:1237`

- `partialize()` 在每次 persist 時移除 `audioBase64`（`audioBase64: undefined`）
- `restoreTracks()` 的唯一復原路徑依賴 `track.isCustom && track.audioBase64`
- 條件永遠為 `false` → 函式等同 no-op
- **所有 custom track 在 rehydration 後 `url = ''`**

### BUG-2: `addTrack` 對 TTS 音軌不設 `hasLocalAudio` [HIGH]

**Location**: `magicDJStore.ts:293`

```typescript
hasLocalAudio: track.source === 'upload',  // TTS → false
```

- TTS 音軌的 `hasLocalAudio` 被強制為 `false`
- 需依賴後續 `updateTrack` 補設，兩次 `set()` 之間有時序風險
- 若中間觸發 persist，TTS track 以 `hasLocalAudio: false` 寫入 localStorage

### BUG-3: Rehydration 與 IndexedDB 初始化競態條件 [HIGH]

**Location**: `magicDJStore.ts:1248-1274` + `MagicDJPage.tsx:342-375`

```
T0: Zustand rehydrate → merge() → restoreTracks() → url='' (BUG-1)
T1: useEffect → initializeStorage() → IndexedDB async open → restore URLs
```

T0→T1 窗口期所有 tracks 的 `url = ''`。

### BUG-4: IndexedDB 失敗時無重試或降級 [MEDIUM]

**Location**: `magicDJStore.ts:1141-1147`

IndexedDB 初始化失敗後只設 `storageError`，無重試、無 fallback。

### BUG-5: 幽靈音軌 — metadata 存在但 blob 遺失 [MEDIUM]

**Location**: `magicDJStore.ts:1128-1136`

Track 的 `hasLocalAudio: true` 但 IndexedDB 中無對應 blob 時，track 永久 `url = ''` 且
`hasLocalAudio` 不被修正。

### BUG-6: Blob URL 記憶體洩漏 [LOW]

`initializeStorage()` 重複執行時（SPA 換頁回來）建立新 blob URL 但未清理舊的。

## Fix Plan

### Phase 1: Core persistence fixes

1. **Remove dead `restoreTracks()`** — rehydration 不再嘗試復原 blob URL
2. **Fix `addTrack` `hasLocalAudio`** — 尊重傳入值 `track.hasLocalAudio ?? (track.source === 'upload')`
3. **Fix `handleSaveTrack`** — 新增 TTS track 時直接設定 `hasLocalAudio: true`，移除冗餘 `updateTrack`
4. **Add `onRehydrateStorage`** — rehydration 完成後自動觸發 `initializeStorage()`
5. **Ghost track integrity check** — blob 遺失時重設 `hasLocalAudio: false`
6. **IndexedDB retry** — 最多重試 2 次，間隔指數遞增
7. **Blob URL cleanup** — 建立新 URL 前清理舊的

## Files Changed

- `frontend/src/stores/magicDJStore.ts` — core fixes
- `frontend/src/routes/magic-dj/MagicDJPage.tsx` — handleSaveTrack cleanup
