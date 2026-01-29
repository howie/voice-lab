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
```

**Validation Rules**:
- `id` 必須唯一
- `url` 必須是有效路徑
- `hotkey` 若設定，必須是單一字元或特殊鍵名
- `channel` 必須是 'voice' | 'music' | 'sfx' 之一

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
- 播放新聲音時，自動停止該頻道正在播放的聲音（即時中斷）
- 每個頻道獨立控制，互不影響
- 最多同時播放 3 個聲音（每頻道最多 1 個）

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
}
```

---

## Default Sound Library

預設聲音庫提供常用的聲音項目，RD 可自由新增更多。

```typescript
const DEFAULT_SOUND_LIBRARY: SoundItem[] = [
  // Voice 頻道 - 說話類
  { id: 'voice_intro', name: '開場白', channel: 'voice', url: '/audio/intro.mp3', hotkey: '1' },
  { id: 'voice_wait', name: '等待填補', channel: 'voice', url: '/audio/wait.mp3', hotkey: 'w' },
  { id: 'voice_end', name: '緊急結束', channel: 'voice', url: '/audio/end.mp3', hotkey: 'e' },

  // Music 頻道 - 音樂類
  { id: 'music_cleanup', name: '收玩具歌', channel: 'music', url: '/audio/cleanup.mp3', hotkey: '2', loop: true },
  { id: 'music_book', name: '魔法書過場', channel: 'music', url: '/audio/book.mp3', hotkey: '4' },
  { id: 'music_forest', name: '迷霧森林', channel: 'music', url: '/audio/forest.mp3', hotkey: '5' },

  // SFX 頻道 - 音效類
  { id: 'sfx_thinking', name: '思考音效', channel: 'sfx', url: '/audio/thinking.mp3', hotkey: 'f' },
  { id: 'sfx_success', name: '成功獎勵', channel: 'sfx', url: '/audio/success.mp3', hotkey: '3' },
]
```

**說明**：
- 以上僅為預設範例，RD 可新增任意數量的聲音項目
- 聲音庫沒有數量上限
- 熱鍵為可選設定，RD 可自行配置

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
