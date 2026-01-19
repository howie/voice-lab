# Data Model: STT Speech-to-Text Testing Module

**Date**: 2026-01-18
**Feature Branch**: `003-stt-testing-module`

## Entity Relationship Diagram

```
┌─────────────────────┐         ┌─────────────────────┐
│    AudioFile        │         │   GroundTruth       │
├─────────────────────┤         ├─────────────────────┤
│ id: UUID (PK)       │◄───────►│ id: UUID (PK)       │
│ user_id: UUID (FK)  │    1:1  │ audio_file_id: UUID │
│ filename: str       │         │ text: str           │
│ format: AudioFormat │         │ language: str       │
│ duration_ms: int    │         │ created_at: datetime│
│ sample_rate: int    │         └─────────────────────┘
│ file_size_bytes: int│
│ storage_path: str   │
│ created_at: datetime│
└─────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────┐         ┌─────────────────────┐
│ TranscriptionRequest│         │     STTProvider     │
├─────────────────────┤         ├─────────────────────┤
│ id: UUID (PK)       │         │ name: str (PK)      │
│ audio_file_id: UUID │◄───────►│ display_name: str   │
│ provider: str (FK)  │    N:1  │ supports_streaming: │
│ language: str       │         │   bool              │
│ child_mode: bool    │         │ max_duration_sec:int│
│                     │         │ max_file_size_mb:int│
│ status: RequestStatus         │ supported_formats:  │
│ created_at: datetime│         │   list[AudioFormat] │
└─────────────────────┘         └─────────────────────┘
          │
          │ 1:1
          ▼
┌─────────────────────┐
│ TranscriptionResult │
├─────────────────────┤
│ id: UUID (PK)       │
│ request_id: UUID(FK)│
│ transcript: str     │
│ confidence: float   │
│ latency_ms: int     │
│ metadata: JSON      │
│ created_at: datetime│
└─────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────┐
│     WordTiming      │
├─────────────────────┤
│ id: UUID (PK)       │
│ result_id: UUID(FK) │
│ word: str           │
│ start_ms: int       │
│ end_ms: int         │
│ confidence: float   │
└─────────────────────┘

┌─────────────────────┐
│    WERAnalysis      │
├─────────────────────┤
│ id: UUID (PK)       │
│ result_id: UUID(FK) │
│ ground_truth_id:UUID│
│ error_rate: float   │
│ error_type: str     │  # "WER" or "CER"
│ insertions: int     │
│ deletions: int      │
│ substitutions: int  │
│ alignment: JSON     │  # Visual diff data
│ created_at: datetime│
└─────────────────────┘
```

## Entity Definitions

### AudioFile

音檔實體，代表使用者上傳或錄製的音訊檔案。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | 唯一識別碼 |
| `user_id` | UUID | FK → User, NOT NULL | 擁有者 |
| `filename` | str | NOT NULL, max 255 | 原始檔名 |
| `format` | AudioFormat | NOT NULL | 音檔格式 (MP3/WAV/M4A/FLAC/WEBM) |
| `duration_ms` | int | NOT NULL, >= 0 | 音檔長度（毫秒） |
| `sample_rate` | int | NOT NULL, >= 8000 | 取樣率 (Hz) |
| `file_size_bytes` | int | NOT NULL, > 0 | 檔案大小 |
| `storage_path` | str | NOT NULL | 儲存路徑 |
| `source` | str | NOT NULL | "upload" or "recording" |
| `created_at` | datetime | NOT NULL, DEFAULT NOW | 建立時間 |

**Validation Rules**:
- `duration_ms` 必須 > 0 且 <= 600000 (10 分鐘)
- `sample_rate` 建議 >= 16000 Hz
- `format` 必須在支援清單中

---

### GroundTruth

正確答案實體，用於 WER/CER 計算。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | 唯一識別碼 |
| `audio_file_id` | UUID | FK → AudioFile, UNIQUE | 關聯音檔 |
| `text` | str | NOT NULL, max 10000 | 正確轉錄文字 |
| `language` | str | NOT NULL | 語言代碼 (zh-TW, en-US, etc.) |
| `created_at` | datetime | NOT NULL, DEFAULT NOW | 建立時間 |

**Validation Rules**:
- `text` 不可為空白
- 一個 AudioFile 最多只有一個 GroundTruth

---

### TranscriptionRequest

轉錄請求實體，代表一次 STT 辨識任務。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | 唯一識別碼 |
| `audio_file_id` | UUID | FK → AudioFile, NOT NULL | 來源音檔 |
| `provider` | str | FK → STTProvider, NOT NULL | STT 服務提供者 |
| `language` | str | NOT NULL, DEFAULT 'zh-TW' | 辨識語言 |
| `child_mode` | bool | NOT NULL, DEFAULT FALSE | 兒童語音模式 |
| `status` | RequestStatus | NOT NULL, DEFAULT 'pending' | 請求狀態 |
| `created_at` | datetime | NOT NULL, DEFAULT NOW | 建立時間 |

**RequestStatus Enum**:
- `pending`: 等待處理
- `processing`: 處理中
- `completed`: 完成
- `failed`: 失敗

**Validation Rules**:
- `language` 必須在 Provider 支援清單中

---

### TranscriptionResult

轉錄結果實體，儲存 STT 辨識輸出。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | 唯一識別碼 |
| `request_id` | UUID | FK → TranscriptionRequest, UNIQUE | 對應請求 |
| `transcript` | str | NOT NULL | 辨識文字結果 |
| `confidence` | float | NOT NULL, 0.0-1.0 | 整體信心分數 |
| `latency_ms` | int | NOT NULL, >= 0 | 辨識延遲（毫秒） |
| `metadata` | JSON | NULLABLE | Provider 特定資訊 |
| `created_at` | datetime | NOT NULL, DEFAULT NOW | 建立時間 |

**Metadata 欄位範例**:
```json
{
  "provider_version": "2.0",
  "model": "latest_long",
  "alternatives": [...]
}
```

---

### WordTiming

詞級時間戳實體，記錄每個詞的時間位置。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | 唯一識別碼 |
| `result_id` | UUID | FK → TranscriptionResult, NOT NULL | 對應結果 |
| `word` | str | NOT NULL | 詞/字元 |
| `start_ms` | int | NOT NULL, >= 0 | 起始時間（毫秒） |
| `end_ms` | int | NOT NULL, > start_ms | 結束時間（毫秒） |
| `confidence` | float | NULLABLE, 0.0-1.0 | 詞級信心分數 |

**Validation Rules**:
- `end_ms` > `start_ms`
- 時間戳不應重疊

---

### WERAnalysis

錯誤率分析實體，儲存 WER/CER 計算結果。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | 唯一識別碼 |
| `result_id` | UUID | FK → TranscriptionResult, NOT NULL | 對應辨識結果 |
| `ground_truth_id` | UUID | FK → GroundTruth, NOT NULL | 對應正確答案 |
| `error_rate` | float | NOT NULL, 0.0-1.0+ | 錯誤率 |
| `error_type` | str | NOT NULL | "WER" or "CER" |
| `insertions` | int | NOT NULL, >= 0 | 插入錯誤數 |
| `deletions` | int | NOT NULL, >= 0 | 刪除錯誤數 |
| `substitutions` | int | NOT NULL, >= 0 | 替換錯誤數 |
| `alignment` | JSON | NULLABLE | 對齊視覺化資料 |
| `created_at` | datetime | NOT NULL, DEFAULT NOW | 建立時間 |

**Alignment JSON 範例**:
```json
{
  "reference_tokens": ["你", "好", "嗎"],
  "hypothesis_tokens": ["你", "號", "嗎"],
  "operations": ["match", "substitute", "match"]
}
```

---

### STTProvider (Configuration)

STT 服務提供者配置，靜態定義。

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | 識別碼 (azure, gcp, whisper) |
| `display_name` | str | 顯示名稱 |
| `supports_streaming` | bool | 是否支援串流 |
| `max_duration_sec` | int | 最大音檔長度（秒） |
| `max_file_size_mb` | int | 最大檔案大小 (MB) |
| `supported_formats` | list | 支援的音檔格式 |
| `supported_languages` | list | 支援的語言 |

**預設配置**:
```python
STT_PROVIDERS = {
    "azure": {
        "display_name": "Azure Speech Services",
        "supports_streaming": True,
        "max_duration_sec": 600,  # 10 min via segmentation
        "max_file_size_mb": 200,
        "supported_formats": ["mp3", "wav", "ogg", "flac", "webm"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]
    },
    "gcp": {
        "display_name": "Google Cloud STT",
        "supports_streaming": True,
        "max_duration_sec": 600,
        "max_file_size_mb": 480,
        "supported_formats": ["mp3", "wav", "ogg", "flac", "webm"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]
    },
    "whisper": {
        "display_name": "OpenAI Whisper",
        "supports_streaming": False,  # ❌ No streaming
        "max_duration_sec": 600,
        "max_file_size_mb": 25,
        "supported_formats": ["mp3", "mp4", "wav", "webm", "m4a"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]
    },
    "deepgram": {
        "display_name": "Deepgram Nova-2",
        "supports_streaming": True,
        "max_duration_sec": 3600,
        "max_file_size_mb": 2000,
        "supported_formats": ["mp3", "wav", "ogg", "flac", "webm", "m4a"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]
    },
    "assemblyai": {
        "display_name": "AssemblyAI",
        "supports_streaming": True,
        "max_duration_sec": 3600,
        "max_file_size_mb": 2000,
        "supported_formats": ["mp3", "wav", "ogg", "flac", "webm", "m4a"],
        "supported_languages": ["zh-TW", "en-US", "ja-JP", "ko-KR"]
    },
    "elevenlabs": {
        "display_name": "ElevenLabs Scribe",
        "supports_streaming": False,
        "max_duration_sec": 600,
        "max_file_size_mb": 25,
        "supported_formats": ["mp3", "wav", "flac", "m4a"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]
    },
    "speechmatics": {
        "display_name": "Speechmatics",
        "supports_streaming": True,
        "max_duration_sec": 7200,
        "max_file_size_mb": 2000,
        "supported_formats": ["mp3", "wav", "ogg", "flac"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]
    }
}
```

---

## Enums

### AudioFormat

```python
class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    FLAC = "flac"
    WEBM = "webm"
    OGG = "ogg"
```

### RequestStatus

```python
class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### ErrorType

```python
class ErrorType(str, Enum):
    WER = "WER"  # Word Error Rate (English)
    CER = "CER"  # Character Error Rate (CJK)
```

---

## State Transitions

### TranscriptionRequest Lifecycle

```
[created] ──► pending ──► processing ──► completed
                │                            │
                │                            ▼
                └─────────────► failed ◄─────┘
```

| From | To | Trigger |
|------|----|---------|
| - | pending | Request created |
| pending | processing | Worker picks up |
| processing | completed | Transcription success |
| processing | failed | API error / timeout |
| pending | failed | Validation error |

---

## Indexes

```sql
-- 常用查詢優化
CREATE INDEX idx_audio_file_user_id ON audio_files(user_id);
CREATE INDEX idx_audio_file_created ON audio_files(created_at DESC);
CREATE INDEX idx_transcription_request_audio ON transcription_requests(audio_file_id);
CREATE INDEX idx_transcription_request_status ON transcription_requests(status);
CREATE INDEX idx_transcription_result_request ON transcription_results(request_id);
CREATE INDEX idx_wer_analysis_result ON wer_analyses(result_id);
```

---

## Migration Notes

- 現有 `STTRequest` 和 `STTResult` domain entities 已存在於 `backend/src/domain/entities/stt.py`
- 需擴展加入持久化欄位 (`id`, `created_at`, etc.)
- `WERAnalysis` 和 `GroundTruth` 為新增實體
- 使用 Alembic 建立 migration scripts
