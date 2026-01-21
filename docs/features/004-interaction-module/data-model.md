# Data Model: Real-time Voice Interaction Testing Module

**Date**: 2026-01-19
**Feature**: 004-interaction-module

## Entity Relationship Diagram

```
┌─────────────────────────┐       ┌─────────────────────────┐
│   InteractionSession    │       │    ScenarioTemplate     │
├─────────────────────────┤       ├─────────────────────────┤
│ id: UUID (PK)           │       │ id: UUID (PK)           │
│ user_id: UUID (FK)      │       │ name: str               │
│ mode: InteractionMode   │       │ description: str        │
│ provider_config: JSON   │       │ user_role: str          │
│ user_role: str          │◀──────│ ai_role: str            │
│ ai_role: str            │       │ scenario_context: text  │
│ scenario_context: text  │       │ category: str           │
│ started_at: datetime    │       │ is_default: bool        │
│ ended_at: datetime?     │       │ created_at: datetime    │
│ status: SessionStatus   │       │ updated_at: datetime    │
│ created_at: datetime    │       └─────────────────────────┘
│ updated_at: datetime    │
└───────────┬─────────────┘
            │ 1
            │
            │ *
┌───────────▼─────────────┐
│    ConversationTurn     │
├─────────────────────────┤
│ id: UUID (PK)           │
│ session_id: UUID (FK)   │
│ turn_number: int        │
│ user_audio_path: str?   │
│ user_transcript: text?  │
│ ai_response_text: text? │
│ ai_audio_path: str?     │
│ interrupted: bool       │
│ started_at: datetime    │
│ ended_at: datetime?     │
│ created_at: datetime    │
└───────────┬─────────────┘
            │ 1
            │
            │ 1
┌───────────▼─────────────┐
│     LatencyMetrics      │
├─────────────────────────┤
│ id: UUID (PK)           │
│ turn_id: UUID (FK)      │
│ total_latency_ms: int   │
│ stt_latency_ms: int?    │
│ llm_ttft_ms: int?       │
│ tts_ttfb_ms: int?       │
│ realtime_latency_ms: int?│
│ created_at: datetime    │
└─────────────────────────┘
```

## Entities

### InteractionSession

代表一次完整的語音互動會話，包含角色設定和情境描述。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 唯一識別碼 |
| user_id | UUID | FK → users.id | 使用者識別碼 |
| mode | Enum | NOT NULL | 互動模式 (realtime/cascade) |
| provider_config | JSONB | NOT NULL | 提供者配置（見下方結構） |
| user_role | VARCHAR(100) | NOT NULL, DEFAULT '使用者' | 使用者角色名稱（如：顧客、病患、學生） |
| ai_role | VARCHAR(100) | NOT NULL, DEFAULT 'AI 助理' | AI 角色名稱（如：客服、醫生、老師） |
| scenario_context | TEXT | DEFAULT '' | 對話情境描述（情境說明和限制條件） |
| started_at | TIMESTAMP | NOT NULL | 會話開始時間 |
| ended_at | TIMESTAMP | NULLABLE | 會話結束時間 |
| status | Enum | NOT NULL, DEFAULT 'active' | 會話狀態 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 建立時間 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新時間 |

**Indexes**:
- `idx_session_user_id` ON (user_id)
- `idx_session_status` ON (status)
- `idx_session_started_at` ON (started_at DESC)

**provider_config JSON 結構**:
```json
{
  "mode": "cascade",
  "stt_provider": "deepgram",
  "stt_model": "nova-2",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "tts_provider": "elevenlabs",
  "tts_voice": "rachel"
}
```

或 Realtime 模式：
```json
{
  "mode": "realtime",
  "realtime_provider": "openai",
  "realtime_model": "gpt-realtime",
  "voice": "alloy"
}
```

**角色與情境說明**:
- `user_role`: 在對話記錄中用來標示使用者發言（取代固定的「您」）
- `ai_role`: 在對話記錄中用來標示 AI 回應（取代固定的「AI」），同時用於生成 system prompt
- `scenario_context`: 描述對話的情境、目標和限制，會被組合成 system prompt 發送給 LLM

---

### ConversationTurn

代表一個對話回合（使用者說話 + AI 回應）。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 唯一識別碼 |
| session_id | UUID | FK → interaction_sessions.id, ON DELETE CASCADE | 所屬會話 |
| turn_number | INTEGER | NOT NULL | 回合序號（從 1 開始） |
| user_audio_path | VARCHAR(500) | NULLABLE | 使用者音訊檔案路徑 |
| user_transcript | TEXT | NULLABLE | 使用者語音轉文字結果 |
| ai_response_text | TEXT | NULLABLE | AI 回應文字 |
| ai_audio_path | VARCHAR(500) | NULLABLE | AI 回應音訊檔案路徑 |
| interrupted | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否被打斷 |
| started_at | TIMESTAMP | NOT NULL | 回合開始時間 |
| ended_at | TIMESTAMP | NULLABLE | 回合結束時間 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 建立時間 |

**Indexes**:
- `idx_turn_session_id` ON (session_id)
- `idx_turn_session_number` ON (session_id, turn_number)

**Constraints**:
- UNIQUE (session_id, turn_number)

---

### LatencyMetrics

記錄每個對話回合的延遲測量數據。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 唯一識別碼 |
| turn_id | UUID | FK → conversation_turns.id, ON DELETE CASCADE, UNIQUE | 所屬回合 |
| total_latency_ms | INTEGER | NOT NULL | 端對端總延遲（毫秒） |
| stt_latency_ms | INTEGER | NULLABLE | STT 處理延遲（僅 Cascade 模式） |
| llm_ttft_ms | INTEGER | NULLABLE | LLM 首 Token 時間（僅 Cascade 模式） |
| tts_ttfb_ms | INTEGER | NULLABLE | TTS 首音訊時間（僅 Cascade 模式） |
| realtime_latency_ms | INTEGER | NULLABLE | Realtime API 延遲（僅 Realtime 模式） |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 建立時間 |

**Indexes**:
- `idx_latency_turn_id` ON (turn_id)

---

### ScenarioTemplate

預設的場景模板，包含角色設定和情境描述。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | 唯一識別碼 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 模板名稱 |
| description | VARCHAR(500) | NOT NULL | 模板說明（給使用者看的描述） |
| user_role | VARCHAR(100) | NOT NULL | 預設使用者角色名稱 |
| ai_role | VARCHAR(100) | NOT NULL | 預設 AI 角色名稱 |
| scenario_context | TEXT | NOT NULL | 預設對話情境描述 |
| category | VARCHAR(50) | NOT NULL | 分類（如 customer_service, education, medical） |
| is_default | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否為預設模板 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 建立時間 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新時間 |

**Indexes**:
- `idx_template_category` ON (category)
- `idx_template_is_default` ON (is_default) WHERE is_default = TRUE

---

## Enums

### InteractionMode

```python
class InteractionMode(str, Enum):
    REALTIME = "realtime"  # OpenAI Realtime API 模式
    CASCADE = "cascade"    # STT → LLM → TTS 串聯模式
```

### SessionStatus

```python
class SessionStatus(str, Enum):
    ACTIVE = "active"          # 進行中
    COMPLETED = "completed"    # 正常結束
    DISCONNECTED = "disconnected"  # 連線中斷
    ERROR = "error"            # 錯誤終止
```

---

## State Transitions

### InteractionSession 狀態轉換

```
                    ┌──────────────────┐
                    │                  │
     start_session  │     ACTIVE       │
    ──────────────▶ │                  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
      ┌───────────┐  ┌───────────┐  ┌───────────┐
      │ COMPLETED │  │DISCONNECTED│  │   ERROR   │
      │(end_session)│ │(ws_close) │  │(exception)│
      └───────────┘  └───────────┘  └───────────┘
```

**轉換規則**:
- `ACTIVE` → `COMPLETED`: 使用者主動結束會話
- `ACTIVE` → `DISCONNECTED`: WebSocket 連線中斷
- `ACTIVE` → `ERROR`: 發生未預期錯誤

---

## Validation Rules

### InteractionSession
- `started_at` 必須早於或等於 `ended_at`（若 `ended_at` 非 NULL）
- `provider_config` 必須包含與 `mode` 相符的必要欄位

### ConversationTurn
- `turn_number` 必須從 1 開始連續遞增
- `started_at` 必須在所屬 session 的 `started_at` 之後
- 若 `interrupted` 為 TRUE，則 `ended_at` 可能早於預期

### LatencyMetrics
- 所有 `*_latency_ms` 值必須 >= 0
- Cascade 模式：`total_latency_ms` ≈ `stt_latency_ms` + `llm_ttft_ms` + `tts_ttfb_ms` + 傳輸開銷
- Realtime 模式：`realtime_latency_ms` ≈ `total_latency_ms`

---

## Audio File Storage

音訊檔案儲存於本地檔案系統：

```
storage/
└── interactions/
    └── {session_id}/
        ├── turn_001_user.webm
        ├── turn_001_ai.mp3
        ├── turn_002_user.webm
        ├── turn_002_ai.mp3
        └── ...
```

**命名規則**:
- 使用者音訊：`turn_{turn_number:03d}_user.{format}`
- AI 回應音訊：`turn_{turn_number:03d}_ai.{format}`

**保留策略**:
- 預設保留 30 天
- 使用者可手動刪除特定會話的音訊

---

## Default Data

### 預設場景模板

| Name | Category | User Role | AI Role | Description |
|------|----------|-----------|---------|-------------|
| 客服諮詢 | customer_service | 顧客 | 客服專員 | 模擬客戶服務場景，處理產品詢問和問題反映 |
| 醫療諮詢 | medical | 病患 | 醫療助理 | 模擬醫療諮詢場景，進行症狀詢問和衛教說明 |
| 語言教學 | education | 學生 | 語言老師 | 模擬語言學習場景，進行對話練習和糾錯指導 |
| 技術支援 | technical | 用戶 | 技術工程師 | 模擬 IT 支援場景，解答技術問題和故障排除 |
| 一般對話 | general | 使用者 | AI 助理 | 通用對話場景，無特定角色限制 |

### 場景模板範例

**醫療諮詢模板**:
```
user_role: "病患"
ai_role: "醫療助理"
scenario_context: |
  你是一位專業的醫療諮詢助理。請以關懷的態度詢問病患的症狀，
  提供基本的衛教資訊，但不進行診斷或開立處方。
  如果症狀嚴重，請建議病患儘速就醫。
  對話應簡潔清晰，避免使用過於專業的醫學術語。
```
