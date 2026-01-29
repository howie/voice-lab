# Data Model: Magic DJ Audio Features Enhancement

**Date**: 2026-01-29
**Feature**: 011-magic-dj-audio-features

## Overview

本文件定義 Magic DJ Audio Features 的資料模型，涵蓋 Phase 1-3 的擴充。

---

## Phase 1-2: Frontend Types (TypeScript)

### TrackSource (新增)

```typescript
/**
 * 音軌來源類型
 * - tts: 透過 TTS 服務生成
 * - upload: 使用者上傳的音檔
 */
type TrackSource = 'tts' | 'upload';
```

### Track (擴充)

```typescript
interface Track {
  // === 現有欄位 ===
  id: string;                       // 唯一識別碼，格式: 'track_01_intro'
  name: string;                     // 顯示名稱
  type: TrackType;                  // 音軌類型
  url: string;                      // 音訊 URL (blob URL 或 remote URL)
  hotkey?: string;                  // 快捷鍵 (1-5, f, w, e)
  loop?: boolean;                   // 是否循環播放
  duration?: number;                // 時長 (毫秒)
  isCustom?: boolean;               // 是否為自訂音軌
  textContent?: string;             // TTS 原始文字
  audioBase64?: string;             // base64 編碼的音訊資料 (用於 localStorage 持久化)

  // === Phase 1 新增 ===
  source: TrackSource;              // 音軌來源：'tts' | 'upload'
  originalFileName?: string;        // 上傳時的原始檔名 (僅 upload 類型)

  // === Phase 2 新增 ===
  volume: number;                   // 音量 0.0 ~ 1.0，預設 1.0
}
```

### TrackType (現有，無變更)

```typescript
type TrackType =
  | 'intro'       // 開場
  | 'transition'  // 過場
  | 'effect'      // 音效
  | 'song'        // 歌曲
  | 'filler'      // 填補音效
  | 'rescue';     // 緊急音效
```

### TrackPlaybackState (擴充)

```typescript
interface TrackPlaybackState {
  trackId: string;
  isPlaying: boolean;
  isLoaded: boolean;
  isLoading: boolean;
  error: string | null;
  currentTime: number;              // 目前播放位置 (毫秒)
  volume: number;                   // 目前播放音量 0-1

  // === Phase 2 新增 ===
  isMuted: boolean;                 // 是否靜音
  previousVolume: number;           // 靜音前的音量 (用於恢復)
}
```

### FileUploadState (新增，Phase 1)

```typescript
/**
 * 檔案上傳狀態
 */
interface FileUploadState {
  file: File | null;                // 原始 File 物件
  fileName: string;                 // 檔案名稱
  fileSize: number;                 // 檔案大小 (bytes)
  audioUrl: string | null;          // blob URL (用於預覽)
  audioBase64: string | null;       // base64 編碼 (用於儲存)
  duration: number | null;          // 音訊時長 (毫秒)
  error: string | null;             // 錯誤訊息
  isProcessing: boolean;            // 是否處理中
}
```

### 常數定義

```typescript
// 支援的音訊 MIME 類型
const SUPPORTED_AUDIO_TYPES = [
  'audio/mpeg',      // MP3
  'audio/wav',       // WAV
  'audio/ogg',       // OGG
  'audio/webm',      // WebM
] as const;

// 檔案大小上限 (10MB)
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 同時播放上限
const MAX_CONCURRENT_TRACKS = 5;

// 音量圖示對應
const VOLUME_ICONS = {
  muted: '🔇',      // 0%
  low: '🔈',        // 1-33%
  medium: '🔉',     // 34-66%
  high: '🔊',       // 67-100%
} as const;
```

---

## Phase 3: Backend Models (Python)

### Enums

```python
from enum import Enum

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
```

### DJSettings

```python
from pydantic import BaseModel, Field

class DJSettings(BaseModel):
    """預設組全域設定"""
    master_volume: float = Field(default=1.0, ge=0.0, le=1.0)
    time_warning_at: int = Field(default=1500)      # 25 分鐘警告
    session_time_limit: int = Field(default=1800)   # 30 分鐘上限
    ai_response_timeout: int = Field(default=10)    # AI 回應逾時 (秒)
    auto_play_filler: bool = Field(default=True)    # 自動播放填補音效
```

### DJPreset

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class DJPreset(BaseModel):
    """DJ 預設組"""
    id: UUID
    user_id: UUID
    name: str                           # 預設組名稱，同一使用者內唯一
    description: str | None = None
    is_default: bool = False            # 是否為預設選取
    settings: DJSettings
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### DJTrack

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class DJTrack(BaseModel):
    """DJ 音軌"""
    id: UUID
    preset_id: UUID

    # 基本資訊
    name: str
    type: TrackType
    hotkey: str | None = None
    loop: bool = False
    sort_order: int = 0

    # 音源資訊
    source: TrackSource

    # TTS 相關 (source = 'tts')
    text_content: str | None = None
    tts_provider: str | None = None
    tts_voice_id: str | None = None
    tts_speed: Decimal = Decimal("1.0")

    # 上傳相關 (source = 'upload')
    original_filename: str | None = None

    # 音檔資訊
    audio_storage_path: str | None = None   # GCS path
    audio_url: str | None = None            # Signed URL (動態生成)
    duration_ms: int | None = None
    file_size_bytes: int | None = None
    content_type: str = "audio/mpeg"

    # 音量
    volume: float = Field(default=1.0, ge=0.0, le=1.0)

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

## Database Schema (Phase 3)

### dj_presets

```sql
CREATE TABLE dj_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, name)
);

-- 索引
CREATE INDEX idx_dj_presets_user_id ON dj_presets(user_id);
```

### dj_tracks

```sql
CREATE TABLE dj_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preset_id UUID NOT NULL REFERENCES dj_presets(id) ON DELETE CASCADE,

    -- 基本資訊
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    hotkey VARCHAR(10),
    loop BOOLEAN DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,

    -- 音源資訊
    source VARCHAR(20) NOT NULL,

    -- TTS 相關
    text_content TEXT,
    tts_provider VARCHAR(50),
    tts_voice_id VARCHAR(100),
    tts_speed DECIMAL(3,2) DEFAULT 1.0,

    -- 上傳相關
    original_filename VARCHAR(255),

    -- 音檔資訊
    audio_storage_path VARCHAR(500),
    audio_url VARCHAR(1000),
    duration_ms INTEGER,
    file_size_bytes INTEGER,
    content_type VARCHAR(100) DEFAULT 'audio/mpeg',

    -- 音量
    volume DECIMAL(3,2) DEFAULT 1.0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_dj_tracks_preset_id ON dj_tracks(preset_id);
CREATE INDEX idx_dj_tracks_sort_order ON dj_tracks(preset_id, sort_order);
```

---

## Entity Relationships

```
┌─────────────┐       1:N       ┌─────────────┐
│   User      │────────────────>│  DJPreset   │
└─────────────┘                 └──────┬──────┘
                                       │
                                       │ 1:N
                                       ▼
                                ┌─────────────┐
                                │   DJTrack   │
                                └──────┬──────┘
                                       │
                                       │ 1:1 (optional)
                                       ▼
                                ┌─────────────┐
                                │ GCS Audio   │
                                │   File      │
                                └─────────────┘
```

**關係說明**:
- User : DJPreset = 1 : N（每位使用者可有多個預設組）
- DJPreset : DJTrack = 1 : N（每個預設組包含多個音軌）
- DJTrack : GCS File = 1 : 1（每個上傳音軌對應一個 GCS 檔案，TTS 音軌無 GCS 檔案）

---

## Data Migration

### Phase 1-2: localStorage 資料遷移

```typescript
/**
 * 遷移舊版 Track 資料
 * - 補上 source 預設值 'tts'
 * - 補上 volume 預設值 1.0
 */
const migrateTrackData = (track: Partial<Track>): Track => ({
  ...track,
  source: track.source ?? 'tts',
  volume: track.volume ?? 1.0,
} as Track);
```

### Phase 3: localStorage → Backend 遷移

```typescript
/**
 * 匯入 localStorage 資料到後端
 */
interface LocalStorageImportPayload {
  preset_name: string;
  data: {
    settings: DJSettings;
    masterVolume: number;
    tracks: Array<{
      id: string;
      name: string;
      type: TrackType;
      source: TrackSource;
      volume: number;
      audioBase64?: string;  // 將上傳到 GCS
      textContent?: string;
      // ... other fields
    }>;
  };
}
```

---

## Validation Rules

### Track Validation

| Field | Rule |
|-------|------|
| name | 必填，1-200 字元 |
| type | 必填，必須是有效的 TrackType |
| source | 必填，必須是 'tts' 或 'upload' |
| volume | 0.0 ~ 1.0 |
| hotkey | 可選，1 字元 |
| duration | 正整數（毫秒） |

### File Upload Validation

| Rule | Value |
|------|-------|
| 檔案大小上限 | 10MB |
| 支援格式 | audio/mpeg, audio/wav, audio/ogg, audio/webm |
| 檔名長度上限 | 255 字元 |

### Preset Validation

| Field | Rule |
|-------|------|
| name | 必填，1-100 字元，同一使用者內唯一 |
| 每使用者預設組上限 | 10 個 |
| 每預設組音軌上限 | 20 個 |
