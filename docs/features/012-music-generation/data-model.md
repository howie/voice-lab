# Data Model: Music Generation

**Feature**: 012-music-generation
**Date**: 2026-01-29

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     MusicGenerationJob                          │
├─────────────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                                   │
│ user_id: UUID (FK -> users.id)                                  │
│ type: MusicGenerationType                                       │
│ status: MusicGenerationStatus                                   │
│                                                                 │
│ # Input                                                         │
│ prompt: string (nullable)         # 風格/場景描述               │
│ lyrics: string (nullable)         # 歌詞內容                    │
│ model: string = "auto"            # Mureka 模型選擇             │
│                                                                 │
│ # External tracking                                             │
│ mureka_task_id: string (nullable) # Mureka API task ID          │
│                                                                 │
│ # Output                                                        │
│ result_url: string (nullable)     # 本地儲存 URL                │
│ original_url: string (nullable)   # Mureka 原始 MP3 URL         │
│ cover_url: string (nullable)      # 封面圖片 URL                │
│ generated_lyrics: string (nullable) # 生成的歌詞               │
│ duration_ms: integer (nullable)   # 音樂時長（毫秒）            │
│ title: string (nullable)          # 生成的標題                  │
│                                                                 │
│ # Timestamps                                                    │
│ created_at: datetime                                            │
│ started_at: datetime (nullable)                                 │
│ completed_at: datetime (nullable)                               │
│                                                                 │
│ # Error handling                                                │
│ error_message: string (nullable)                                │
│ retry_count: integer = 0                                        │
└─────────────────────────────────────────────────────────────────┘
         │
         │ FK
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                          User                                   │
│                     (existing entity)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Enumerations

### MusicGenerationType

音樂生成類型

| Value | Description |
|-------|-------------|
| `song` | 歌曲生成（含人聲） |
| `instrumental` | 純音樂/BGM 生成 |
| `lyrics` | 歌詞生成 |

### MusicGenerationStatus

任務狀態（對應 Mureka API 狀態）

| Value | Description | Mureka Mapping |
|-------|-------------|----------------|
| `pending` | 等待處理 | - |
| `processing` | 生成中 | `preparing`, `processing` |
| `completed` | 已完成 | `completed` |
| `failed` | 失敗 | `failed` |

---

## Entity Details

### MusicGenerationJob

代表一個音樂生成請求任務。

#### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID | No | auto-generated | 主鍵 |
| `user_id` | UUID | No | - | 關聯用戶 |
| `type` | enum | No | - | 生成類型 |
| `status` | enum | No | `pending` | 任務狀態 |
| `prompt` | string | Yes | - | 風格/場景描述 |
| `lyrics` | string | Yes | - | 輸入歌詞（歌曲生成用） |
| `model` | string | No | `"auto"` | Mureka 模型選擇 |
| `mureka_task_id` | string | Yes | - | Mureka API 返回的 task ID |
| `result_url` | string | Yes | - | 本地儲存後的音檔 URL |
| `original_url` | string | Yes | - | Mureka 原始 MP3 URL |
| `cover_url` | string | Yes | - | 封面圖片 URL |
| `generated_lyrics` | text | Yes | - | AI 生成的歌詞 |
| `duration_ms` | integer | Yes | - | 音樂時長（毫秒） |
| `title` | string | Yes | - | 生成的標題 |
| `created_at` | datetime | No | now() | 建立時間 |
| `started_at` | datetime | Yes | - | 開始處理時間 |
| `completed_at` | datetime | Yes | - | 完成時間 |
| `error_message` | string | Yes | - | 錯誤訊息 |
| `retry_count` | integer | No | `0` | 重試次數 |

#### Validation Rules

1. `type` 必須是有效的 `MusicGenerationType` 值
2. `status` 必須是有效的 `MusicGenerationStatus` 值
3. 當 `type = song` 時，`prompt` 或 `lyrics` 至少需要一個
4. 當 `type = instrumental` 時，`prompt` 必填
5. 當 `type = lyrics` 時，`prompt` 必填（主題描述）
6. `model` 必須是 `auto`, `mureka-01`, `v7.5`, `v6` 之一
7. `retry_count` 不得超過 3

#### State Transitions

```
     ┌──────────────┐
     │   pending    │ ←── 初始狀態
     └──────┬───────┘
            │ worker 取得任務
            ▼
     ┌──────────────┐
     │  processing  │ ←── 呼叫 Mureka API
     └──────┬───────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐  ┌─────────┐
│completed│  │ failed  │
└─────────┘  └────┬────┘
                  │ retry (if retry_count < 3)
                  │
                  └───────► pending
```

#### Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `ix_music_jobs_user_id` | `user_id` | B-tree | 查詢用戶的任務 |
| `ix_music_jobs_status` | `status` | B-tree | 查詢特定狀態的任務 |
| `ix_music_jobs_user_status` | `user_id, status` | B-tree | 用戶並發任務檢查 |
| `ix_music_jobs_created_at` | `created_at` | B-tree | 歷史記錄排序 |

---

## Domain Services

### MusicGenerationService

核心業務邏輯服務。

#### Methods

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `submit_instrumental` | prompt, model | MusicGenerationJob | 提交純音樂生成 |
| `submit_song` | prompt, lyrics?, model | MusicGenerationJob | 提交歌曲生成 |
| `submit_lyrics` | prompt | MusicGenerationJob | 提交歌詞生成 |
| `extend_lyrics` | lyrics, prompt? | MusicGenerationJob | 延伸歌詞 |
| `get_job` | job_id | MusicGenerationJob | 查詢任務 |
| `list_jobs` | user_id, status?, limit, offset | List[MusicGenerationJob] | 列出任務 |
| `retry_job` | job_id | MusicGenerationJob | 重試失敗任務 |

### QuotaService

配額管理服務。

#### Methods

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `check_quota` | user_id | QuotaStatus | 檢查配額 |
| `get_concurrent_count` | user_id | int | 取得並發任務數 |
| `can_submit` | user_id | bool | 是否可提交新任務 |
| `increment_usage` | user_id | void | 增加使用量 |
| `get_usage_stats` | user_id | UsageStats | 取得用量統計 |

---

## Quota Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `DAILY_LIMIT_PER_USER` | 10 | 每用戶每日限制 |
| `MONTHLY_LIMIT_PER_USER` | 100 | 每用戶每月限制 |
| `MAX_CONCURRENT_JOBS` | 3 | 每用戶最大並發任務 |
| `JOB_TIMEOUT_MINUTES` | 5 | 任務逾時時間 |
| `MAX_RETRY_COUNT` | 3 | 最大重試次數 |
| `HISTORY_RETENTION_DAYS` | 30 | 歷史記錄保留天數 |

---

## Migration Notes

### New Table

```sql
CREATE TABLE music_generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    prompt TEXT,
    lyrics TEXT,
    model VARCHAR(20) NOT NULL DEFAULT 'auto',
    mureka_task_id VARCHAR(100),
    result_url TEXT,
    original_url TEXT,
    cover_url TEXT,
    generated_lyrics TEXT,
    duration_ms INTEGER,
    title VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX ix_music_jobs_user_id ON music_generation_jobs(user_id);
CREATE INDEX ix_music_jobs_status ON music_generation_jobs(status);
CREATE INDEX ix_music_jobs_user_status ON music_generation_jobs(user_id, status);
CREATE INDEX ix_music_jobs_created_at ON music_generation_jobs(created_at);
```

---

*Last updated: 2026-01-29*
