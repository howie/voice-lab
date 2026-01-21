# Data Model: Async Job Management

**Feature**: 007-async-job-mgmt
**Date**: 2026-01-20

---

## Entity Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                          Job                                │
├─────────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                               │
│ user_id: UUID (FK → users)                                  │
│ job_type: JobType                                           │
│ status: JobStatus                                           │
│ provider: str                                               │
│ input_params: JSONB                                         │
│ audio_file_id: UUID? (FK → audio_files)                     │
│ result_metadata: JSONB?                                     │
│ error_message: str?                                         │
│ retry_count: int                                            │
│ created_at: datetime                                        │
│ started_at: datetime?                                       │
│ completed_at: datetime?                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 1:1 (optional)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      AudioFile                              │
│                   (existing entity)                         │
├─────────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                               │
│ storage_path: str                                           │
│ format: AudioFileFormat                                     │
│ duration_ms: int                                            │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Entities

### Job（工作）

代表一個 TTS 合成請求的完整生命週期。

#### 屬性

| 屬性 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `id` | UUID | ✅ | 主鍵，工作識別碼 |
| `user_id` | UUID | ✅ | 關聯使用者（FK → users） |
| `job_type` | JobType | ✅ | 工作類型（目前僅 `multi_role_tts`） |
| `status` | JobStatus | ✅ | 工作狀態 |
| `provider` | str | ✅ | TTS Provider 名稱 |
| `input_params` | JSONB | ✅ | 合成輸入參數（見下方結構） |
| `audio_file_id` | UUID | ❌ | 完成後關聯的音檔（FK → audio_files） |
| `result_metadata` | JSONB | ❌ | 執行結果元資料（見下方結構） |
| `error_message` | str | ❌ | 失敗時的錯誤訊息 |
| `retry_count` | int | ✅ | 重試次數，預設 0 |
| `created_at` | datetime | ✅ | 建立時間（UTC） |
| `started_at` | datetime | ❌ | 開始執行時間（UTC） |
| `completed_at` | datetime | ❌ | 完成/失敗時間（UTC） |

#### 驗證規則

- `provider` 必須是有效的 TTS Provider 名稱
- `retry_count` 最大值為 3
- `started_at` 只能在 `status` 為 `processing` 或之後狀態時設定
- `completed_at` 只能在 `status` 為 `completed` 或 `failed` 時設定
- `audio_file_id` 只能在 `status` 為 `completed` 時設定
- `error_message` 只能在 `status` 為 `failed` 時設定

---

### JobStatus（工作狀態）

```python
class JobStatus(str, Enum):
    PENDING = "pending"        # 等待中
    PROCESSING = "processing"  # 處理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失敗
    CANCELLED = "cancelled"    # 已取消
```

#### 狀態轉換圖

```
            ┌──────────────────────────────────────┐
            │                                      │
            ▼                                      │
       ┌─────────┐    pick up    ┌────────────┐   │ timeout/error
       │ PENDING │──────────────▶│ PROCESSING │───┤
       └─────────┘               └────────────┘   │
            │                          │          │
            │ cancel                   │ success  │
            ▼                          ▼          ▼
       ┌───────────┐            ┌───────────┐ ┌────────┐
       │ CANCELLED │            │ COMPLETED │ │ FAILED │
       └───────────┘            └───────────┘ └────────┘
```

**轉換規則**：
- `PENDING` → `PROCESSING`：工作被 worker 領取
- `PENDING` → `CANCELLED`：使用者取消
- `PROCESSING` → `COMPLETED`：TTS 合成成功
- `PROCESSING` → `FAILED`：發生錯誤或逾時

---

### JobType（工作類型）

```python
class JobType(str, Enum):
    MULTI_ROLE_TTS = "multi_role_tts"  # 多角色 TTS 合成
```

未來可擴展：`SINGLE_TTS`、`STT_TRANSCRIPTION` 等。

---

## JSONB 結構

### input_params（輸入參數）

儲存 Multi-Role TTS 請求的完整參數。

```json
{
  "turns": [
    {"speaker": "A", "text": "你好", "index": 0},
    {"speaker": "B", "text": "嗨！", "index": 1}
  ],
  "voice_assignments": [
    {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural", "voice_name": "曉雨"},
    {"speaker": "B", "voice_id": "zh-TW-YunJheNeural", "voice_name": "雲哲"}
  ],
  "language": "zh-TW",
  "output_format": "mp3",
  "gap_ms": 300,
  "crossfade_ms": 50
}
```

### result_metadata（結果元資料）

儲存執行結果的詳細資訊。

```json
{
  "duration_ms": 5200,
  "latency_ms": 1850,
  "synthesis_mode": "segmented",
  "turn_timings": [
    {"turn_index": 0, "start_ms": 0, "end_ms": 2500},
    {"turn_index": 1, "start_ms": 2800, "end_ms": 5200}
  ]
}
```

---

## 索引策略

```sql
-- 主要查詢索引
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- 背景任務索引
CREATE INDEX idx_jobs_pending ON jobs(status, created_at)
    WHERE status = 'pending';
CREATE INDEX idx_jobs_processing_timeout ON jobs(status, started_at)
    WHERE status = 'processing';

-- 清理任務索引
CREATE INDEX idx_jobs_completed_cleanup ON jobs(status, completed_at)
    WHERE status IN ('completed', 'failed', 'cancelled');
```

---

## 與現有 Entity 的關係

### AudioFile（現有）

- Job 完成後會建立 AudioFile 記錄
- 透過 `audio_file_id` 外鍵關聯
- 1:1 關係（一個 Job 對應一個 AudioFile）

### User（假設存在）

- 透過 `user_id` 關聯
- 1:N 關係（一個 User 可有多個 Job）

---

## 資料保留策略

| 狀態 | 保留期限 | 清理行為 |
|------|----------|----------|
| `completed` | 30 天 | 刪除 Job 記錄和關聯 AudioFile |
| `failed` | 30 天 | 刪除 Job 記錄 |
| `cancelled` | 7 天 | 刪除 Job 記錄 |
| `pending` | 24 小時 | 自動標記為 `failed`（孤立工作） |
| `processing` | 10 分鐘 | 自動標記為 `failed`（逾時） |

---

## SQLAlchemy Model 範例

```python
from sqlalchemy import Column, String, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    provider = Column(String(50), nullable=False)
    input_params = Column(JSONB, nullable=False)
    audio_file_id = Column(UUID(as_uuid=True), ForeignKey("audio_files.id"), nullable=True)
    result_metadata = Column(JSONB, nullable=True)
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    audio_file = relationship("AudioFile", lazy="joined")
```
