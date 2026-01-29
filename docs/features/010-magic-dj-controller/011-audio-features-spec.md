# Magic DJ Audio Features Enhancement

## Overview

增強 Magic DJ 的音軌管理功能，支援直接上傳 MP3 檔案以及調整各音軌音量。

**功能目標**：
1. **Phase 1**: MP3 上傳功能 - 讓使用者除了 TTS 生成外，可以直接上傳 MP3 檔案作為音軌
2. **Phase 2**: 音量控制功能 - 讓每個音軌可以獨立調整音量，方便同時播放時區分
3. **Phase 3**: 後端儲存支援 - 將資料從 localStorage 遷移到後端，支援跨裝置、多使用者

---

## Phase 1: MP3 上傳功能

### 需求描述

目前 Magic DJ 音軌只能透過 TTS 生成，需要增加直接上傳 MP3 檔案的選項，讓使用者可以使用自己準備的音效、音樂或錄音。

### 使用情境

1. RD 有預先錄製好的背景音樂想直接使用
2. 使用外部工具（如 Adobe Audition）製作的音效
3. 使用其他 TTS 服務生成的音檔
4. 版權音樂或特殊音效素材

### 技術規格

#### 1.1 Track 類型擴充

```typescript
// frontend/src/types/magic-dj.ts

// 新增音軌來源類型
type TrackSource = 'tts' | 'upload';

interface Track {
  id: string;
  name: string;
  type: TrackType;
  url: string;
  hotkey?: string;
  loop?: boolean;
  duration?: number;
  isCustom?: boolean;
  textContent?: string;
  audioBase64?: string;

  // 新增欄位
  source: TrackSource;           // 音軌來源：'tts' | 'upload'
  originalFileName?: string;     // 上傳時的原始檔名
}
```

#### 1.2 TrackEditorModal 修改

**UI 變更**:

```
┌─────────────────────────────────────────────────────┐
│  編輯音軌                                      [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  音軌名稱: [________________]                       │
│                                                     │
│  音軌類型: [下拉選單 ▼]                            │
│                                                     │
│  快捷鍵:   [1-5 或留空]                            │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  音源方式:  ○ TTS 生成    ● 上傳 MP3               │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  [TTS 設定區域 - 當選擇 TTS 時顯示]         │   │
│  │                                              │   │
│  │  文字內容: [多行輸入框______________]       │   │
│  │  TTS 供應商: [VoAI ▼]                       │   │
│  │  語音:      [小美 ▼]                        │   │
│  │  語速:      [1.0x ▼]                        │   │
│  │                                              │   │
│  │  [生成語音]                                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  [上傳區域 - 當選擇上傳時顯示]              │   │
│  │                                              │   │
│  │  ┌───────────────────────────────────────┐  │   │
│  │  │                                        │  │   │
│  │  │   拖放 MP3 檔案至此處                  │  │   │
│  │  │        或                              │  │   │
│  │  │   [選擇檔案]                           │  │   │
│  │  │                                        │  │   │
│  │  │   支援格式: MP3, WAV, OGG              │  │   │
│  │  │   檔案大小上限: 10MB                   │  │   │
│  │  │                                        │  │   │
│  │  └───────────────────────────────────────┘  │   │
│  │                                              │   │
│  │  已選擇: background_music.mp3 (2.3MB)       │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  音訊預覽:  [▶ 播放]  [⏹ 停止]   00:00 / 01:23    │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│                        [取消]    [儲存]             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 1.3 檔案處理邏輯

```typescript
// frontend/src/components/magic-dj/TrackEditorModal.tsx

interface FileUploadState {
  file: File | null;
  fileName: string;
  fileSize: number;
  audioUrl: string | null;      // blob URL for preview
  audioBase64: string | null;   // for persistence
  duration: number | null;
  error: string | null;
  isProcessing: boolean;
}

// 支援的音訊格式
const SUPPORTED_AUDIO_TYPES = [
  'audio/mpeg',      // MP3
  'audio/wav',       // WAV
  'audio/ogg',       // OGG
  'audio/webm',      // WebM
];

// 檔案大小限制 (10MB)
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 檔案處理流程
async function processUploadedFile(file: File): Promise<FileUploadState> {
  // 1. 驗證檔案類型
  if (!SUPPORTED_AUDIO_TYPES.includes(file.type)) {
    throw new Error('不支援的檔案格式');
  }

  // 2. 驗證檔案大小
  if (file.size > MAX_FILE_SIZE) {
    throw new Error('檔案大小超過 10MB 限制');
  }

  // 3. 讀取檔案為 ArrayBuffer
  const arrayBuffer = await file.arrayBuffer();

  // 4. 轉換為 base64
  const base64 = arrayBufferToBase64(arrayBuffer);

  // 5. 建立 blob URL 供預覽
  const blob = new Blob([arrayBuffer], { type: file.type });
  const blobUrl = URL.createObjectURL(blob);

  // 6. 取得音訊時長
  const duration = await getAudioDuration(blobUrl);

  return {
    file,
    fileName: file.name,
    fileSize: file.size,
    audioUrl: blobUrl,
    audioBase64: base64,
    duration,
    error: null,
    isProcessing: false,
  };
}
```

#### 1.4 拖放上傳元件

```typescript
// frontend/src/components/magic-dj/AudioDropzone.tsx

interface AudioDropzoneProps {
  onFileAccepted: (file: File) => void;
  onError: (error: string) => void;
  isProcessing: boolean;
  currentFile?: {
    name: string;
    size: number;
  };
}

// 使用原生 HTML5 drag-and-drop API
// 或整合 react-dropzone 套件
```

#### 1.5 資料遷移

既有音軌需要加上 `source: 'tts'` 預設值：

```typescript
// 在 store 初始化時處理
const migrateTrackData = (track: Track): Track => ({
  ...track,
  source: track.source || 'tts',
});
```

### 驗收標準 (Phase 1)

- [ ] 可以切換音源方式：TTS 生成 / 上傳 MP3
- [ ] 支援拖放上傳 MP3/WAV/OGG 檔案
- [ ] 支援點擊選擇檔案上傳
- [ ] 顯示已選擇的檔案名稱和大小
- [ ] 檔案大小超過 10MB 時顯示錯誤訊息
- [ ] 不支援的檔案格式顯示錯誤訊息
- [ ] 上傳的音訊可以預覽播放
- [ ] 上傳的音訊可以正確儲存並持久化（localStorage）
- [ ] 重新載入頁面後，上傳的音軌仍可正常播放
- [ ] TrackList 中顯示音軌來源圖示（TTS / 上傳）

---

## Phase 2: 音量控制功能

### 需求描述

目前雖然播放器內部支援音量控制，但沒有持久化且 UI 上沒有明顯的控制項。需要增加每個音軌的獨立音量控制，並持久化設定。

### 使用情境

1. 背景音樂需要比語音小聲，避免蓋過說話聲
2. 音效需要比對話聲大聲，確保兒童注意到
3. 不同來源的音軌錄音音量不一致，需要平衡
4. 同時播放多軌時，需要調整各軌平衡

### 技術規格

#### 2.1 Track 類型擴充

```typescript
// frontend/src/types/magic-dj.ts

interface Track {
  // ... 現有欄位

  // Phase 2 新增
  volume: number;  // 0.0 ~ 1.0，預設 1.0
}
```

#### 2.2 TrackPlayer UI 修改

```
┌─────────────────────────────────────────────────────────────┐
│ [▶]  開場白介紹                              [1] [✏] [🗑]   │
│      ──────────────────────────────── 00:15                │
│      🔊 ────────●──────── 80%                              │
└─────────────────────────────────────────────────────────────┘

Legend:
- [▶] 播放/暫停按鈕
- 進度條
- 🔊 音量圖示 + 滑桿 + 百分比顯示
- [1] 快捷鍵
- [✏] 編輯
- [🗑] 刪除
```

#### 2.3 音量滑桿元件

```typescript
// frontend/src/components/magic-dj/VolumeSlider.tsx

interface VolumeSliderProps {
  value: number;           // 0.0 ~ 1.0
  onChange: (value: number) => void;
  disabled?: boolean;
  size?: 'sm' | 'md';      // 緊湊版 vs 標準版
}

// 功能：
// - 滑桿拖動調整音量
// - 點擊音量圖示切換靜音
// - 顯示音量百分比
// - 音量圖示隨音量大小變化（🔇 🔈 🔉 🔊）
```

#### 2.4 音量圖示對應

| 音量範圍 | 圖示 |
|---------|------|
| 0%      | 🔇 (靜音) |
| 1-33%   | 🔈 (低音量) |
| 34-66%  | 🔉 (中音量) |
| 67-100% | 🔊 (高音量) |

#### 2.5 Store 更新

```typescript
// frontend/src/stores/magicDJStore.ts

interface MagicDJStore {
  // ... 現有欄位

  // Phase 2 新增 actions
  setTrackVolume: (trackId: string, volume: number) => void;
  toggleTrackMute: (trackId: string) => void;
}

// 音量值會自動持久化到 localStorage
```

#### 2.6 TrackEditorModal 音量設定

在編輯音軌時也可以設定預設音量：

```
┌─────────────────────────────────────────────────────┐
│  編輯音軌                                      [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ...（其他欄位）...                                 │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  預設音量:  🔊 ────────●──────── 80%               │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│                        [取消]    [儲存]             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 2.7 TrackList 整體佈局調整

```
┌─────────────────────────────────────────────────────────────────────┐
│  音軌列表                                              [+ 新增音軌] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ≡  [▶]  開場白介紹           🎤  🔊 ──●── 80%   [1]  [✏] [🗑]    │
│                                                                     │
│  ≡  [⏸]  背景音樂             📁  🔉 ●──── 40%   [2]  [✏] [🗑]    │
│       ████████░░░░░░░░░░░░░░░ 00:45 / 02:30                        │
│                                                                     │
│  ≡  [▶]  轉場音效             🎤  🔊 ────●  100%  [3]  [✏] [🗑]    │
│                                                                     │
│  ≡  [▶]  歡呼聲               📁  🔊 ───●─  90%   [4]  [✏] [🗑]    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Legend:
- ≡    拖動排序手柄
- [▶]  播放按鈕
- [⏸]  播放中（點擊停止）
- 🎤   TTS 生成的音軌
- 📁   上傳的音軌
- 🔊   音量滑桿
- [1]  快捷鍵
- [✏]  編輯
- [🗑]  刪除
```

### 驗收標準 (Phase 2)

- [ ] 每個音軌顯示音量滑桿
- [ ] 可以拖動滑桿調整音量 (0% ~ 100%)
- [ ] 點擊音量圖示可以切換靜音
- [ ] 音量圖示隨音量大小變化
- [ ] 音量設定自動持久化
- [ ] 重新載入頁面後音量設定保留
- [ ] 播放時音量設定即時生效
- [ ] 編輯音軌時可以設定預設音量
- [ ] 多軌同時播放時，各軌音量獨立控制
- [ ] Master volume 仍然可以控制整體音量

---

## 實作計畫

### Phase 1 任務分解

| 任務 | 預估複雜度 | 相依性 |
|-----|----------|--------|
| 1.1 擴充 Track 類型定義 | 低 | - |
| 1.2 實作 AudioDropzone 元件 | 中 | - |
| 1.3 修改 TrackEditorModal - 加入音源切換 | 中 | 1.1 |
| 1.4 實作檔案處理邏輯 | 中 | - |
| 1.5 整合 AudioDropzone 到 TrackEditorModal | 低 | 1.2, 1.3 |
| 1.6 處理資料遷移（舊資料相容） | 低 | 1.1 |
| 1.7 TrackList 顯示來源圖示 | 低 | 1.1 |
| 1.8 測試與除錯 | 中 | All |

### Phase 2 任務分解

| 任務 | 預估複雜度 | 相依性 |
|-----|----------|--------|
| 2.1 擴充 Track 類型 - 加入 volume | 低 | - |
| 2.2 實作 VolumeSlider 元件 | 中 | - |
| 2.3 修改 TrackPlayer 加入 VolumeSlider | 低 | 2.2 |
| 2.4 Store 新增 setTrackVolume action | 低 | 2.1 |
| 2.5 整合音量控制到播放器 hook | 低 | 2.4 |
| 2.6 TrackEditorModal 加入預設音量設定 | 低 | 2.2 |
| 2.7 處理資料遷移（舊資料預設音量 1.0） | 低 | 2.1 |
| 2.8 測試與除錯 | 中 | All |

---

## 技術考量

### 儲存空間

- 上傳的音檔會以 base64 存儲在 localStorage
- localStorage 通常限制 5-10MB
- 建議：
  - 單檔限制 10MB
  - 可考慮壓縮音訊或降低取樣率
  - 未來可考慮 IndexedDB 或後端儲存

### 效能

- base64 編碼會增加約 33% 的資料大小
- 大量音軌可能影響頁面載入速度
- 建議：延遲載入音訊資料，只在需要時解碼

### 瀏覽器相容性

- Web Audio API: 所有現代瀏覽器支援
- Drag and Drop API: 所有現代瀏覽器支援
- File API: 所有現代瀏覽器支援

### 向後相容

- 舊版資料自動遷移
- `source` 預設為 `'tts'`
- `volume` 預設為 `1.0`

---

## 未來擴充可能

1. **後端儲存**: 將音檔上傳至後端，解決 localStorage 限制
2. **音訊裁剪**: 上傳後可以裁剪音訊片段
3. **音訊效果**: 淡入淡出、迴音等效果
4. **波形顯示**: 顯示音訊波形圖
5. **音軌分組**: 將音軌分組管理（如：背景音樂、音效、對話）
6. **預設音量模板**: 儲存常用的音量配置

---

## 檔案變更清單

### Phase 1 新增/修改檔案

```
frontend/src/
├── types/
│   └── magic-dj.ts                    # 修改 - Track 類型擴充
├── components/magic-dj/
│   ├── AudioDropzone.tsx              # 新增 - 拖放上傳元件
│   ├── TrackEditorModal.tsx           # 修改 - 加入上傳功能
│   └── TrackList.tsx                  # 修改 - 顯示來源圖示
└── stores/
    └── magicDJStore.ts                # 修改 - 資料遷移處理
```

### Phase 2 新增/修改檔案

```
frontend/src/
├── types/
│   └── magic-dj.ts                    # 修改 - 加入 volume 欄位
├── components/magic-dj/
│   ├── VolumeSlider.tsx               # 新增 - 音量滑桿元件
│   ├── TrackPlayer.tsx                # 修改 - 加入音量控制
│   ├── TrackEditorModal.tsx           # 修改 - 加入預設音量設定
│   └── TrackList.tsx                  # 修改 - 調整佈局
├── hooks/
│   └── useMultiTrackPlayer.ts         # 修改 - 整合持久化音量
└── stores/
    └── magicDJStore.ts                # 修改 - 新增 setTrackVolume
```

---

## Phase 3: 後端儲存支援

### 需求描述

Phase 1-2 使用 localStorage 儲存，有以下限制需要解決：

| 問題 | 影響 |
|------|------|
| **無法跨裝置** | RD 換電腦要重新設定所有音軌 |
| **無法區分使用者** | 多人共用電腦會互相覆蓋設定 |
| **容量限制** | localStorage 5-10MB，多個音檔容易爆掉 |
| **資料易遺失** | 清快取就沒了 |

Phase 3 透過後端 API + 雲端儲存解決這些問題。

### 使用情境

1. RD 在公司設定好音軌，回家用筆電繼續使用
2. 多位 RD 各自有獨立的音軌設定
3. 上傳大量音檔不受 localStorage 限制
4. 重灌電腦、換瀏覽器資料不遺失

### 系統架構

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Magic DJ Controller                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │ TrackList   │  │ TrackEditor │  │ useMultiTrackPlayer     │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │   │
│  │         │                │                      │                │   │
│  │         └────────────────┼──────────────────────┘                │   │
│  │                          │                                       │   │
│  │                   ┌──────▼──────┐                               │   │
│  │                   │  DJ Store   │ ◄── Zustand (runtime only)    │   │
│  │                   └──────┬──────┘                               │   │
│  │                          │                                       │   │
│  └──────────────────────────┼───────────────────────────────────────┘   │
│                             │                                           │
│                      ┌──────▼──────┐                                   │
│                      │  API Client │                                   │
│                      └──────┬──────┘                                   │
│                             │                                           │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Backend                                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      FastAPI Application                          │  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │  │
│  │  │ /api/v1/dj/     │  │ /api/v1/dj/     │  │ /api/v1/dj/     │  │  │
│  │  │   presets       │  │   tracks        │  │   audio         │  │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │  │
│  │           │                    │                     │           │  │
│  │           └────────────────────┼─────────────────────┘           │  │
│  │                                │                                  │  │
│  │                         ┌──────▼──────┐                          │  │
│  │                         │  DJ Service │                          │  │
│  │                         └──────┬──────┘                          │  │
│  │                                │                                  │  │
│  └────────────────────────────────┼──────────────────────────────────┘  │
│                                   │                                     │
│            ┌──────────────────────┼──────────────────────┐             │
│            │                      │                      │             │
│     ┌──────▼──────┐        ┌──────▼──────┐       ┌──────▼──────┐      │
│     │ PostgreSQL  │        │    GCS      │       │   Redis     │      │
│     │ (metadata)  │        │  (audio)    │       │  (cache)    │      │
│     └─────────────┘        └─────────────┘       └─────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 技術規格

#### 3.1 資料庫 Schema

```sql
-- 使用者 DJ 設定預設組
CREATE TABLE dj_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    settings JSONB NOT NULL DEFAULT '{}',
    -- settings 包含: masterVolume, timeWarningAt, sessionTimeLimit, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, name)
);

-- 音軌資料
CREATE TABLE dj_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preset_id UUID NOT NULL REFERENCES dj_presets(id) ON DELETE CASCADE,

    -- 基本資訊
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'intro', 'transition', 'effect', 'song', 'filler', 'rescue'
    hotkey VARCHAR(10),
    loop BOOLEAN DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,

    -- 音源資訊
    source VARCHAR(20) NOT NULL,  -- 'tts' | 'upload'

    -- TTS 相關 (source = 'tts')
    text_content TEXT,
    tts_provider VARCHAR(50),
    tts_voice_id VARCHAR(100),
    tts_speed DECIMAL(3,2) DEFAULT 1.0,

    -- 上傳相關 (source = 'upload')
    original_filename VARCHAR(255),

    -- 音檔資訊
    audio_storage_path VARCHAR(500),  -- GCS path: gs://bucket/dj-audio/{user_id}/{track_id}.mp3
    audio_url VARCHAR(1000),          -- Signed URL (generated on read)
    duration_ms INTEGER,
    file_size_bytes INTEGER,
    content_type VARCHAR(100) DEFAULT 'audio/mpeg',

    -- Phase 2: 音量
    volume DECIMAL(3,2) DEFAULT 1.0,  -- 0.0 ~ 1.0

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_dj_presets_user_id ON dj_presets(user_id);
CREATE INDEX idx_dj_tracks_preset_id ON dj_tracks(preset_id);
CREATE INDEX idx_dj_tracks_sort_order ON dj_tracks(preset_id, sort_order);
```

#### 3.2 Domain Models

```python
# backend/src/domain/models/dj.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TrackType(str, Enum):
    INTRO = "intro"
    TRANSITION = "transition"
    EFFECT = "effect"
    SONG = "song"
    FILLER = "filler"
    RESCUE = "rescue"


class TrackSource(str, Enum):
    TTS = "tts"
    UPLOAD = "upload"


class DJSettings(BaseModel):
    master_volume: float = Field(default=1.0, ge=0.0, le=1.0)
    time_warning_at: int = Field(default=1500)  # 25 minutes in seconds
    session_time_limit: int = Field(default=1800)  # 30 minutes
    ai_response_timeout: int = Field(default=10)  # seconds
    auto_play_filler: bool = Field(default=True)


class DJPreset(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    is_default: bool = False
    settings: DJSettings
    created_at: datetime
    updated_at: datetime


class DJTrack(BaseModel):
    id: UUID
    preset_id: UUID
    name: str
    type: TrackType
    hotkey: str | None = None
    loop: bool = False
    sort_order: int = 0

    # Source
    source: TrackSource

    # TTS fields
    text_content: str | None = None
    tts_provider: str | None = None
    tts_voice_id: str | None = None
    tts_speed: Decimal = Decimal("1.0")

    # Upload fields
    original_filename: str | None = None

    # Audio info
    audio_storage_path: str | None = None
    audio_url: str | None = None  # Signed URL
    duration_ms: int | None = None
    file_size_bytes: int | None = None
    content_type: str = "audio/mpeg"

    # Volume
    volume: float = Field(default=1.0, ge=0.0, le=1.0)

    created_at: datetime
    updated_at: datetime
```

#### 3.3 API Endpoints

```yaml
# Preset 管理
GET    /api/v1/dj/presets                    # 列出使用者所有預設組
POST   /api/v1/dj/presets                    # 建立新預設組
GET    /api/v1/dj/presets/{preset_id}        # 取得預設組詳情（含所有音軌）
PUT    /api/v1/dj/presets/{preset_id}        # 更新預設組設定
DELETE /api/v1/dj/presets/{preset_id}        # 刪除預設組
POST   /api/v1/dj/presets/{preset_id}/clone  # 複製預設組

# Track 管理
GET    /api/v1/dj/presets/{preset_id}/tracks              # 列出預設組所有音軌
POST   /api/v1/dj/presets/{preset_id}/tracks              # 新增音軌
GET    /api/v1/dj/presets/{preset_id}/tracks/{track_id}   # 取得音軌詳情
PUT    /api/v1/dj/presets/{preset_id}/tracks/{track_id}   # 更新音軌
DELETE /api/v1/dj/presets/{preset_id}/tracks/{track_id}   # 刪除音軌
PUT    /api/v1/dj/presets/{preset_id}/tracks/reorder      # 重新排序音軌

# Audio 管理
POST   /api/v1/dj/audio/upload                # 上傳音檔（multipart/form-data）
GET    /api/v1/dj/audio/{track_id}            # 取得音檔（redirect to signed URL）
DELETE /api/v1/dj/audio/{track_id}            # 刪除音檔

# 資料遷移
POST   /api/v1/dj/import                      # 從 localStorage JSON 匯入
GET    /api/v1/dj/export/{preset_id}          # 匯出預設組為 JSON
```

#### 3.4 API Request/Response 範例

**建立預設組**
```http
POST /api/v1/dj/presets
Content-Type: application/json

{
  "name": "兒童互動測試",
  "description": "4-6歲兒童語音互動研究",
  "settings": {
    "master_volume": 0.8,
    "time_warning_at": 1500,
    "session_time_limit": 1800
  }
}
```

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid",
  "name": "兒童互動測試",
  "description": "4-6歲兒童語音互動研究",
  "is_default": false,
  "settings": {
    "master_volume": 0.8,
    "time_warning_at": 1500,
    "session_time_limit": 1800,
    "ai_response_timeout": 10,
    "auto_play_filler": true
  },
  "created_at": "2026-01-29T10:00:00Z",
  "updated_at": "2026-01-29T10:00:00Z"
}
```

**新增 TTS 音軌**
```http
POST /api/v1/dj/presets/{preset_id}/tracks
Content-Type: application/json

{
  "name": "開場白",
  "type": "intro",
  "hotkey": "1",
  "source": "tts",
  "text_content": "嗨！小朋友你好，我是魔法 DJ！",
  "tts_provider": "voai",
  "tts_voice_id": "voai-tw-female-1",
  "tts_speed": 1.0,
  "volume": 1.0
}
```

**上傳音檔**
```http
POST /api/v1/dj/audio/upload
Content-Type: multipart/form-data

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="background.mp3"
Content-Type: audio/mpeg

[binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="track_id"

550e8400-e29b-41d4-a716-446655440000
------WebKitFormBoundary--
```

```json
{
  "track_id": "550e8400-e29b-41d4-a716-446655440000",
  "storage_path": "gs://voice-lab-audio/dj-audio/user-123/550e8400.mp3",
  "audio_url": "https://storage.googleapis.com/...",
  "duration_ms": 180000,
  "file_size_bytes": 2457600,
  "content_type": "audio/mpeg"
}
```

**從 localStorage 匯入**
```http
POST /api/v1/dj/import
Content-Type: application/json

{
  "preset_name": "匯入的設定",
  "data": {
    "settings": { ... },
    "masterVolume": 0.8,
    "tracks": [
      {
        "id": "track_01",
        "name": "開場白",
        "type": "intro",
        "audioBase64": "data:audio/mpeg;base64,..."
      }
    ]
  }
}
```

#### 3.5 GCS 音檔儲存

```python
# backend/src/infrastructure/storage/gcs.py

from google.cloud import storage
from datetime import timedelta

class DJAudioStorage:
    BUCKET_NAME = "voice-lab-audio"
    PATH_PREFIX = "dj-audio"

    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.BUCKET_NAME)

    def upload(
        self,
        user_id: str,
        track_id: str,
        audio_data: bytes,
        content_type: str = "audio/mpeg"
    ) -> str:
        """上傳音檔，回傳 storage path"""
        path = f"{self.PATH_PREFIX}/{user_id}/{track_id}.mp3"
        blob = self.bucket.blob(path)
        blob.upload_from_string(audio_data, content_type=content_type)
        return f"gs://{self.BUCKET_NAME}/{path}"

    def get_signed_url(self, storage_path: str, expiration: int = 3600) -> str:
        """產生 signed URL for download"""
        # 解析 gs:// path
        path = storage_path.replace(f"gs://{self.BUCKET_NAME}/", "")
        blob = self.bucket.blob(path)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET"
        )

    def delete(self, storage_path: str) -> None:
        """刪除音檔"""
        path = storage_path.replace(f"gs://{self.BUCKET_NAME}/", "")
        blob = self.bucket.blob(path)
        blob.delete()
```

#### 3.6 Frontend 整合

```typescript
// frontend/src/lib/api/dj.ts

export interface DJPreset {
  id: string;
  userId: string;
  name: string;
  description?: string;
  isDefault: boolean;
  settings: DJSettings;
  createdAt: string;
  updatedAt: string;
}

export interface DJTrackDTO {
  id: string;
  presetId: string;
  name: string;
  type: TrackType;
  hotkey?: string;
  loop: boolean;
  sortOrder: number;
  source: 'tts' | 'upload';
  textContent?: string;
  ttsProvider?: string;
  ttsVoiceId?: string;
  ttsSpeed?: number;
  originalFilename?: string;
  audioUrl?: string;  // Signed URL from backend
  durationMs?: number;
  fileSizeBytes?: number;
  volume: number;
}

// API Client
export const djApi = {
  // Presets
  listPresets: () =>
    api.get<DJPreset[]>('/dj/presets'),

  getPreset: (presetId: string) =>
    api.get<DJPreset & { tracks: DJTrackDTO[] }>(`/dj/presets/${presetId}`),

  createPreset: (data: CreatePresetRequest) =>
    api.post<DJPreset>('/dj/presets', data),

  updatePreset: (presetId: string, data: UpdatePresetRequest) =>
    api.put<DJPreset>(`/dj/presets/${presetId}`, data),

  deletePreset: (presetId: string) =>
    api.delete(`/dj/presets/${presetId}`),

  // Tracks
  createTrack: (presetId: string, data: CreateTrackRequest) =>
    api.post<DJTrackDTO>(`/dj/presets/${presetId}/tracks`, data),

  updateTrack: (presetId: string, trackId: string, data: UpdateTrackRequest) =>
    api.put<DJTrackDTO>(`/dj/presets/${presetId}/tracks/${trackId}`, data),

  deleteTrack: (presetId: string, trackId: string) =>
    api.delete(`/dj/presets/${presetId}/tracks/${trackId}`),

  reorderTracks: (presetId: string, trackIds: string[]) =>
    api.put(`/dj/presets/${presetId}/tracks/reorder`, { trackIds }),

  // Audio
  uploadAudio: (trackId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('track_id', trackId);
    return api.post<AudioUploadResponse>('/dj/audio/upload', formData);
  },

  // Import/Export
  importFromLocalStorage: (presetName: string, data: LocalStorageData) =>
    api.post<DJPreset>('/dj/import', { preset_name: presetName, data }),

  exportPreset: (presetId: string) =>
    api.get<ExportData>(`/dj/export/${presetId}`),
};
```

#### 3.7 Store 改造

```typescript
// frontend/src/stores/magicDJStore.ts

// Phase 3: 改為 API-backed store（移除 persist middleware）

interface MagicDJStoreState {
  // Current loaded preset
  currentPreset: DJPreset | null;
  tracks: Track[];
  trackStates: Record<string, TrackPlaybackState>;

  // UI state (not persisted)
  masterVolume: number;
  currentMode: OperationMode;
  isLoading: boolean;
  error: string | null;

  // Session state (not persisted)
  isSessionActive: boolean;
  // ...

  // Actions
  loadPreset: (presetId: string) => Promise<void>;
  saveTrack: (track: Track) => Promise<void>;
  deleteTrack: (trackId: string) => Promise<void>;
  uploadAudio: (trackId: string, file: File) => Promise<void>;
  // ...
}

export const useMagicDJStore = create<MagicDJStoreState>()((set, get) => ({
  // ... state

  loadPreset: async (presetId) => {
    set({ isLoading: true, error: null });
    try {
      const preset = await djApi.getPreset(presetId);
      set({
        currentPreset: preset,
        tracks: preset.tracks.map(dtoToTrack),
        trackStates: createInitialTrackStates(preset.tracks),
        masterVolume: preset.settings.masterVolume,
        isLoading: false,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  saveTrack: async (track) => {
    const preset = get().currentPreset;
    if (!preset) return;

    try {
      const dto = await djApi.updateTrack(preset.id, track.id, trackToDto(track));
      set((state) => ({
        tracks: state.tracks.map(t => t.id === track.id ? dtoToTrack(dto) : t),
      }));
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // ... other actions
}));
```

#### 3.8 UI 變更

**Preset 選擇器**
```
┌────────────────────────────────────────────────────────────────────────┐
│  Magic DJ Controller                                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  預設組: [兒童互動測試 ▼]  [+ 新增]  [複製]  [刪除]  [匯入/匯出]       │
│                                                                        │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                        │
│  （現有的 TrackList + Controls）                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**匯入對話框**
```
┌─────────────────────────────────────────────────────┐
│  匯入設定                                      [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  偵測到本地設定：                                   │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │  8 個音軌                                      │ │
│  │  總計 4.2 MB 音檔                              │ │
│  │  最後修改: 2026-01-28 15:30                    │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  預設組名稱: [匯入的設定____________]              │
│                                                     │
│  ⚠️ 匯入後，本地設定將被清除                       │
│                                                     │
│                        [取消]    [匯入到雲端]       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 驗收標準 (Phase 3)

**後端 API**
- [ ] 可建立/讀取/更新/刪除預設組
- [ ] 可建立/讀取/更新/刪除音軌
- [ ] 可上傳音檔到 GCS
- [ ] 可產生有時效的 signed URL
- [ ] 音軌排序功能正常
- [ ] 資料存取有使用者權限驗證

**前端整合**
- [ ] 可選擇不同預設組
- [ ] 新增/編輯/刪除預設組
- [ ] 音軌 CRUD 透過 API
- [ ] 音檔上傳直接到後端
- [ ] 播放時使用 signed URL

**資料遷移**
- [ ] 可從 localStorage 匯入到後端
- [ ] 匯入包含音檔上傳
- [ ] 匯入成功後清除 localStorage
- [ ] 可匯出預設組為 JSON

**效能**
- [ ] Signed URL 有適當快取
- [ ] 音檔播放無明顯延遲
- [ ] 大量音軌列表載入流暢

### 實作任務分解

| 任務 | 預估複雜度 | 相依性 |
|-----|----------|--------|
| 3.1 設計並建立資料庫 Schema | 中 | - |
| 3.2 實作 Domain Models | 低 | 3.1 |
| 3.3 實作 GCS 音檔儲存服務 | 中 | - |
| 3.4 實作 Preset CRUD API | 中 | 3.2 |
| 3.5 實作 Track CRUD API | 中 | 3.2, 3.4 |
| 3.6 實作音檔上傳 API | 中 | 3.3, 3.5 |
| 3.7 實作匯入/匯出 API | 中 | 3.4, 3.5, 3.6 |
| 3.8 Frontend API Client | 低 | 3.4-3.7 |
| 3.9 改造 Store（移除 persist） | 中 | 3.8 |
| 3.10 Preset 選擇器 UI | 中 | 3.9 |
| 3.11 匯入對話框 UI | 中 | 3.9, 3.10 |
| 3.12 整合測試 | 高 | All |

### Phase 3 新增/修改檔案

```
backend/src/
├── domain/models/
│   └── dj.py                              # 新增 - DJ Domain Models
├── domain/services/
│   └── dj_service.py                      # 新增 - DJ 業務邏輯
├── infrastructure/
│   ├── persistence/
│   │   └── dj_repository.py               # 新增 - DB 存取
│   └── storage/
│       └── gcs.py                         # 修改 - 新增 DJ 音檔儲存
├── presentation/api/routes/
│   └── dj.py                              # 新增 - DJ API Routes
└── presentation/api/schemas/
    └── dj.py                              # 新增 - Request/Response Schemas

frontend/src/
├── lib/api/
│   └── dj.ts                              # 新增 - DJ API Client
├── components/magic-dj/
│   ├── PresetSelector.tsx                 # 新增 - 預設組選擇器
│   ├── ImportDialog.tsx                   # 新增 - 匯入對話框
│   └── ExportButton.tsx                   # 新增 - 匯出按鈕
├── stores/
│   └── magicDJStore.ts                    # 修改 - API-backed store
└── routes/magic-dj/
    └── MagicDJPage.tsx                    # 修改 - 整合 Preset 選擇

migrations/
└── versions/
    └── xxxx_add_dj_tables.py              # 新增 - Alembic migration
```
