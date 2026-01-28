# Data Model: Magic DJ Controller

**Date**: 2026-01-28
**Feature**: 010-magic-dj-controller

## Overview

Magic DJ Controller 的資料模型專注於音軌管理和播放控制。所有狀態為即時運行狀態，無需持久化儲存。

---

## Entities

### Track (音軌)

代表一個預錄音檔的配置。

```typescript
interface Track {
  id: string                    // 唯一識別碼，如 'track_01_intro'
  name: string                  // 顯示名稱，如 '開場'
  type: TrackType               // 類型分類
  url: string                   // 音檔 URL，如 '/audio/intro.mp3'
  hotkey?: string               // 熱鍵，如 '1'
  loop?: boolean                // 是否循環播放
  duration?: number             // 時長（毫秒），載入後填入
}

type TrackType =
  | 'intro'       // 開場
  | 'transition'  // 過場
  | 'effect'      // 音效
  | 'song'        // 歌曲
  | 'filler'      // 填補音效（思考中）
  | 'rescue'      // 救場語音
```

**Validation Rules**:
- `id` 必須唯一
- `url` 必須是有效路徑
- `hotkey` 若設定，必須是單一字元或特殊鍵名

---

### TrackPlaybackState (音軌播放狀態)

追蹤單一音軌的即時播放狀態。

```typescript
interface TrackPlaybackState {
  trackId: string
  isPlaying: boolean
  isLoaded: boolean
  currentTime: number           // 當前播放位置（毫秒）
  volume: number                // 音量 0-1
}
```

---

### OperationMode (操作模式)

控制台的當前模式。

```typescript
type OperationMode = 'prerecorded' | 'ai-conversation'
```

---

## State Management (Zustand Store)

### magicDJStore

```typescript
interface MagicDJState {
  // === 音軌管理 ===
  tracks: Track[]
  trackStates: Map<string, TrackPlaybackState>
  masterVolume: number

  // === 操作模式 ===
  currentMode: OperationMode
  isAIConnected: boolean

  // === 計時器 ===
  isSessionActive: boolean
  elapsedTime: number           // 經過秒數

  // === 設定 ===
  settings: DJSettings
}

interface DJSettings {
  sessionTimeLimit: number      // 預設 30 分鐘（1800 秒）
  timeWarningAt: number         // 警告時間，預設 25 分鐘（1500 秒）
  autoPlayFillerOnSubmit: boolean  // 強制送出時自動播放思考音效
  hotkeys: Record<string, string>
  childFriendlyPrompt: string   // Gemini System Prompt
}
```

---

## Default Track Configuration

```typescript
const DEFAULT_TRACKS: Track[] = [
  { id: 'track_01_intro', name: '開場', type: 'intro', url: '/audio/intro.mp3', hotkey: '1' },
  { id: 'track_02_cleanup', name: '收玩具歌', type: 'song', url: '/audio/cleanup.mp3', hotkey: '2' },
  { id: 'track_03_success', name: '成功獎勵', type: 'effect', url: '/audio/success.mp3', hotkey: '3' },
  { id: 'track_04_book', name: '魔法書過場', type: 'transition', url: '/audio/book.mp3', hotkey: '4' },
  { id: 'track_05_forest', name: '迷霧森林', type: 'transition', url: '/audio/forest.mp3', hotkey: '5' },
  { id: 'sound_thinking', name: '思考音效', type: 'filler', url: '/audio/thinking.mp3', hotkey: 'f' },
  { id: 'filler_wait', name: '等待填補', type: 'rescue', url: '/audio/wait.mp3', hotkey: 'w' },
  { id: 'track_end', name: '緊急結束', type: 'rescue', url: '/audio/end.mp3', hotkey: 'e' },
]
```

---

## Hotkey Mapping

```typescript
const DEFAULT_HOTKEYS = {
  // 控制
  forceSubmit: ' ',           // 空白鍵 - 強制送出
  interrupt: 'Escape',        // ESC - 中斷 AI
  toggleMode: 'm',            // M - 切換模式

  // 音效
  fillerSound: 'f',           // F - 思考音效
  rescueWait: 'w',            // W - 等待填補
  rescueEnd: 'e',             // E - 緊急結束

  // 音軌
  track1: '1',
  track2: '2',
  track3: '3',
  track4: '4',
  track5: '5',
}
```
