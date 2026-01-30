# Data Model: Magic DJ Controller

**Date**: 2026-01-28
**Feature**: 010-magic-dj-controller

## Overview

Magic DJ Controller 的資料模型專注於**聲音庫管理**和**頻道播放控制**。

核心架構：
- **聲音庫 (Sound Library)**：可無限擴充的聲音項目集合，RD 可自由新增、編輯、刪除
- **播放頻道 (Playback Channels)**：固定 3 個頻道，限制同時播放的聲音數量

---

## Entities

### SoundItem (聲音項目)

代表聲音庫中的一個項目。聲音庫可無限擴充，沒有數量上限。

```typescript
interface SoundItem {
  id: string                    // 唯一識別碼，如 'sound_intro_01'
  name: string                  // 顯示名稱，如 '開場白'
  channel: ChannelType          // 播放時使用的頻道
  priority: SoundPriority       // 播放優先級
  url: string                   // 音檔 URL，如 '/audio/intro.mp3'
  hotkey?: string               // 熱鍵，如 '1'
  loop?: boolean                // 是否循環播放
  duration?: number             // 時長（毫秒），載入後填入
  tags?: string[]               // 標籤，用於分類篩選
}

// 頻道類型 - 決定聲音播放到哪個頻道
type ChannelType =
  | 'voice'     // 說話頻道：AI 回應、預錄台詞、救場語音
  | 'music'     // 音樂頻道：背景音樂、歌曲
  | 'sfx'       // 音效頻道：音效、提示音、思考音效

// 播放優先級 - 控制同頻道內的中斷規則
type SoundPriority =
  | 'rescue'    // 救場語音：可中斷任何 voice 內容，不會被一般語音中斷
  | 'normal'    // 一般語音：可互相中斷，但不能中斷正在播放的救場語音
```

**Validation Rules**:
- `id` 必須唯一
- `url` 必須是有效路徑
- `hotkey` 若設定，必須是單一字元或特殊鍵名
- `channel` 必須是 'voice' | 'music' | 'sfx' 之一
- `priority` 必須是 'rescue' | 'normal'

---

### PlaybackChannel (播放頻道)

系統固定的三個播放頻道。每個頻道同時只能播放一個聲音，但三個頻道可同時播放。

```typescript
interface PlaybackChannel {
  type: ChannelType             // 頻道類型
  currentSoundId: string | null // 當前播放的聲音 ID，null 表示沒有播放
  isPlaying: boolean
  currentTime: number           // 當前播放位置（毫秒）
  volume: number                // 頻道音量 0-1
}

// 系統固定的三個頻道
const CHANNELS: ChannelType[] = ['voice', 'music', 'sfx']
```

**播放規則**:
- 每個頻道獨立控制，互不影響
- 最多同時播放 3 個聲音（每頻道最多 1 個）
- **Voice 頻道優先級規則**：
  - `rescue` 優先：可無條件中斷當前 voice 內容
  - `normal` 優先：可中斷其他 `normal`，但不能中斷正在播放的 `rescue`
  - 當 `normal` 嘗試中斷 `rescue` 時，播放請求被忽略
- Music / SFX 頻道：播放新聲音時，自動停止該頻道正在播放的聲音（即時中斷）

---

### SoundItemLoadState (聲音載入狀態)

追蹤聲音庫中每個項目的載入狀態。

```typescript
interface SoundItemLoadState {
  soundId: string
  isLoaded: boolean
  loadError?: string            // 載入失敗時的錯誤訊息
}
```

---

### OperationMode (操作模式)

控制台的當前模式。

```typescript
type OperationMode = 'prerecorded' | 'ai-conversation'
```

---

## Default Sound Library

預設聲音庫提供常用的聲音項目，RD 可自由新增更多。

```typescript
const DEFAULT_SOUND_LIBRARY: SoundItem[] = [
  // Voice 頻道 - 救場語音（priority: 'rescue'）
  { id: 'voice_wait', name: '等待填補', channel: 'voice', priority: 'rescue', url: '/audio/wait.mp3', hotkey: 'w' },
  { id: 'voice_end', name: '緊急結束', channel: 'voice', priority: 'rescue', url: '/audio/end.mp3', hotkey: 'e' },

  // Voice 頻道 - 一般語音（priority: 'normal'）
  { id: 'voice_intro', name: '開場白', channel: 'voice', priority: 'normal', url: '/audio/intro.mp3', hotkey: '1' },

  // Music 頻道
  { id: 'music_cleanup', name: '收玩具歌', channel: 'music', priority: 'normal', url: '/audio/cleanup.mp3', hotkey: '2', loop: true },
  { id: 'music_book', name: '魔法書過場', channel: 'music', priority: 'normal', url: '/audio/book.mp3', hotkey: '4' },
  { id: 'music_forest', name: '迷霧森林', channel: 'music', priority: 'normal', url: '/audio/forest.mp3', hotkey: '5' },

  // SFX 頻道
  { id: 'sfx_thinking', name: '思考音效', channel: 'sfx', priority: 'normal', url: '/audio/thinking.mp3', hotkey: 'f' },
  { id: 'sfx_success', name: '成功獎勵', channel: 'sfx', priority: 'normal', url: '/audio/success.mp3', hotkey: '3' },
]
```

**說明**：
- 以上僅為預設範例，RD 可新增任意數量的聲音項目
- 聲音庫沒有數量上限
- 熱鍵為可選設定，RD 可自行配置

---

### CueItem (播放清單項目)

代表播放清單中的一個項目。參照聲音庫中的 SoundItem，同一個 SoundItem 可在播放清單中出現多次。

```typescript
interface CueItem {
  id: string                    // 唯一識別碼，如 'cue_001'
  soundId: string               // 參照的 SoundItem ID
  order: number                 // 播放順序（1-based）
  status: CueItemStatus         // 項目狀態
}

type CueItemStatus =
  | 'pending'                   // 等待播放
  | 'playing'                   // 正在播放
  | 'played'                    // 已播放完成
  | 'invalid'                   // 來源已刪除或無效

// 狀態轉換
// pending -> playing: 開始播放
// playing -> played: 播放完成或被停止
// any -> invalid: 當 SoundItem 被刪除時
```

**Validation Rules**:
- `id` 必須唯一
- `soundId` 必須參照有效的 SoundItem（但可標記為 invalid）
- `order` 必須為正整數，在清單中唯一

---

### CueList (播放清單)

預錄模式下的播放順序清單。儲存於 localStorage。

```typescript
interface CueList {
  id: string                    // 清單識別碼，如 'default'
  name: string                  // 清單名稱，如 '預設播放清單'
  items: CueItem[]              // 播放清單項目
  currentPosition: number       // 當前播放位置（0-based index，-1 表示未開始）
  createdAt: number             // 建立時間 (timestamp)
  updatedAt: number             // 更新時間 (timestamp)
}
```

**播放規則**:
- 點擊「播放下一個」時，播放 `items[currentPosition + 1]` 並更新 currentPosition
- 音軌播放結束時，自動將 currentPosition 移至下一項（但不自動播放）
- 當 currentPosition 到達最後一項且播放結束時，重設為 0
- 從聲音庫拖曳項目到播放清單時，加入 items 尾端

---

## State Management (Zustand Store)

### magicDJStore

```typescript
interface MagicDJState {
  // === 聲音庫管理 ===
  soundLibrary: SoundItem[]                    // 聲音庫（無數量上限）
  soundLoadStates: Map<string, SoundItemLoadState>

  // === 播放頻道狀態 ===
  channels: {
    voice: PlaybackChannel
    music: PlaybackChannel
    sfx: PlaybackChannel
  }
  masterVolume: number

  // === 播放清單 (Cue List) ===
  cueList: CueList                             // 當前播放清單
  isDragging: boolean                          // 是否正在拖曳

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

// === 播放控制 Actions ===
interface MagicDJActions {
  // 聲音庫管理
  addSound: (sound: SoundItem) => void
  updateSound: (id: string, updates: Partial<SoundItem>) => void
  deleteSound: (id: string) => void
  reorderSounds: (fromIndex: number, toIndex: number) => void

  // 播放控制
  playSound: (soundId: string) => void        // 播放聲音到對應頻道（自動停止該頻道當前聲音）
  stopChannel: (channel: ChannelType) => void // 停止指定頻道
  stopAllChannels: () => void                 // 停止所有頻道
  setChannelVolume: (channel: ChannelType, volume: number) => void

  // 播放清單控制
  addToCueList: (soundId: string) => void     // 將聲音加入播放清單尾端
  removeFromCueList: (cueItemId: string) => void  // 從播放清單移除項目
  reorderCueList: (fromIndex: number, toIndex: number) => void  // 重新排序
  playNextCue: () => void                     // 播放下一個 Cue
  resetCuePosition: () => void                // 重設播放位置
  clearCueList: () => void                    // 清空播放清單
}
```

---

## Hotkey Mapping

```typescript
const DEFAULT_HOTKEYS = {
  // 系統控制
  forceSubmit: ' ',           // 空白鍵 - 強制送出
  interrupt: 'Escape',        // ESC - 中斷 AI / 停止所有頻道
  toggleMode: 'm',            // M - 切換模式

  // 頻道控制
  stopVoice: 'q',             // Q - 停止說話頻道
  stopMusic: 'a',             // A - 停止音樂頻道
  stopSfx: 'z',               // Z - 停止音效頻道
  stopAll: 'Escape',          // ESC - 停止所有頻道

  // 聲音庫項目熱鍵由各 SoundItem.hotkey 定義
  // 例如：'1' -> voice_intro, 'f' -> sfx_thinking
}
```

**熱鍵特性**：
- 聲音庫項目的熱鍵可自由配置，無固定限制
- 播放聲音時會自動停止同頻道的當前聲音（即時中斷）
- ESC 鍵可一鍵停止所有播放
