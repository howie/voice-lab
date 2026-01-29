# Feature Specification: Music Generation (Mureka AI)

**Feature Branch**: `012-music-generation`
**Created**: 2026-01-29
**Status**: Draft
**Research**: [Mureka AI 整合研究](../011-music-generation/research.md)
**Integration Guide**: [Mureka AI 整合文件](/docs/integrations/mureka-ai.md)

---

## Overview

整合 Mureka AI 平台為 Voice Lab 提供音樂和音效生成能力，支援歌曲、純音樂（BGM）和歌詞生成功能。

詳細的技術研究和平台分析請參閱 [Research Document](../011-music-generation/research.md)。

---

## Clarifications

### Session 2026-01-29

- Q: 音樂生成的主要使用場景為何？ → A: Magic DJ 預錄音檔生成、有聲書背景音樂、兒童互動內容配樂
- Q: 是否需要即時生成還是背景任務？ → A: 非同步背景任務，整合 007-async-job-mgmt
- Q: 生成的音樂是否需要儲存和管理？ → A: 與現有音檔儲存機制整合
- Q: API 配額管理策略為何？ → A: 設定每日/每月用量上限，避免超額消費
- Q: 音樂生成失敗時的使用者通知方式？ → A: 輪詢查詢，使用者需主動查詢任務狀態頁面得知失敗
- Q: SC-004 音樂品質標準如何量化驗證？ → A: 驗證音檔可正常播放（MP3 格式、無損壞），品質依賴 Mureka AI 服務保證
- Q: FR-008 與 007-async-job-mgmt 的整合方式？ → A: 模式借鑑，獨立的 MusicGenerationJob 表格，沿用 007 的 Worker 模式和 API 設計

---

## Problem Statement

目前 Voice Lab 專注於語音合成（TTS）功能，但在以下場景缺乏音樂/音效生成能力：

1. **Magic DJ Controller**：需要手動準備預錄音檔，無法動態生成配樂
2. **有聲書製作**：缺乏背景音樂生成能力，需要外部工具處理
3. **兒童互動內容**：無法根據情境即時生成適合的音效和歌曲
4. **創意限制**：依賴現有音檔庫，無法根據需求客製化音樂內容

根據 [研究文件](../011-music-generation/research.md#競品比較)，Mureka AI 是目前唯一提供官方 API 且商業授權明確的選項。

---

## User Scenarios & Testing

### User Story 1 - 生成背景音樂用於 Magic DJ (Priority: P1)

使用者可以根據情境描述生成適合的背景音樂（BGM），用於 Magic DJ Controller 的預錄音軌。

**Why this priority**: Magic DJ Controller 是目前活躍開發的功能，需要大量預錄音檔，自動生成可大幅減少內容準備時間。

**Independent Test**: 可透過描述情境生成 BGM，下載並在 Magic DJ 中使用來驗證。

**Acceptance Scenarios**:

1. **Given** 使用者在音樂生成頁面，**When** 使用者輸入情境描述如「magical fantasy forest, whimsical, children friendly」，**Then** 系統開始生成對應的純音樂
2. **Given** 音樂生成任務已提交，**When** 使用者查看任務狀態，**Then** 顯示進度（準備中、處理中、已完成）
3. **Given** 音樂生成完成，**When** 使用者點擊下載或預覽，**Then** 可以試聽和下載 MP3 檔案

---

### User Story 2 - 生成主題歌曲 (Priority: P1)

使用者可以根據歌詞和風格描述生成完整歌曲，包含人聲演唱。

**Why this priority**: 歌曲生成是 Mureka AI 的核心功能，可用於兒童互動內容（如收玩具歌、故事主題曲）。

**Independent Test**: 可透過提供歌詞和風格描述，驗證生成的歌曲是否符合預期。

**Acceptance Scenarios**:

1. **Given** 使用者在歌曲生成頁面，**When** 使用者輸入歌詞和風格（如「pop, cheerful, children, chinese, female vocal」），**Then** 系統開始生成歌曲
2. **Given** 使用者沒有歌詞，**When** 使用者選擇「AI 生成歌詞」並輸入主題，**Then** 系統先生成歌詞再生成歌曲
3. **Given** 歌曲生成完成，**When** 使用者檢視結果，**Then** 顯示歌曲預覽、封面、歌詞和下載選項

---

### User Story 3 - AI 輔助歌詞創作 (Priority: P2)

使用者可以透過 AI 根據主題/情境生成歌詞，再用於歌曲生成。

**Why this priority**: 歌詞創作是歌曲生成的前置步驟，提供 AI 輔助可降低使用門檻。

**Independent Test**: 可透過輸入主題（如「太空探險」）驗證生成的歌詞結構和內容。

**Acceptance Scenarios**:

1. **Given** 使用者在歌詞生成頁面，**When** 使用者輸入主題描述，**Then** 系統生成結構化歌詞（含 [Verse], [Chorus] 等標記）
2. **Given** 歌詞已生成，**When** 使用者點擊「延伸歌詞」，**Then** 系統可以增加新的段落
3. **Given** 歌詞已生成，**When** 使用者滿意結果，**Then** 可一鍵將歌詞送入歌曲生成

---

### User Story 4 - 音樂生成歷史管理 (Priority: P2)

使用者可以查看和管理過去生成的音樂，避免重複生成相同內容。

**Why this priority**: 與 007-async-job-mgmt 整合，提供一致的任務管理體驗。

**Independent Test**: 可透過查看歷史記錄，找到並重新下載之前生成的音樂。

**Acceptance Scenarios**:

1. **Given** 使用者有已完成的音樂生成任務，**When** 使用者查看歷史記錄，**Then** 顯示過去 30 天內的生成記錄
2. **Given** 使用者選擇一個歷史記錄，**When** 使用者檢視詳情，**Then** 顯示原始輸入參數、生成結果和下載選項
3. **Given** 使用者選擇一個歷史記錄，**When** 使用者點擊「重新生成」，**Then** 以相同參數提交新的生成任務

---

### User Story 5 - Magic DJ 快速音軌生成 (Priority: P1)

RD 可以直接從 Magic DJ 控制台生成新的音軌，無需離開控制介面。

**Why this priority**: 減少 RD 在測試準備階段的工具切換，提升效率。

**Independent Test**: 在 Magic DJ 控制台中點擊「生成新音軌」，填入描述後等待生成完成。

**Acceptance Scenarios**:

1. **Given** RD 在 Magic DJ 控制台，**When** 點擊「生成新音軌」按鈕，**Then** 彈出音樂生成對話框
2. **Given** 音樂生成對話框開啟，**When** 輸入描述並提交，**Then** 任務開始生成並顯示進度
3. **Given** 音樂生成完成，**When** 使用者確認加入，**Then** 新音軌自動加入 Magic DJ 音軌列表

---

### Edge Cases

- **EC-001 API 配額不足**：當 Mureka API 配額不足時，系統 MUST 顯示明確錯誤訊息「音樂生成配額不足，請聯繫管理員」，並阻止提交新任務
- **EC-002 生成任務逾時**：當生成任務超過 5 分鐘未完成時，系統 MUST 標記為逾時失敗，並允許使用者重新提交
- **EC-003 API 連線失敗**：當 Mureka API 無法連線時，系統 MUST 自動重試最多 3 次（間隔遞增），仍失敗則標記任務失敗
- **EC-004 歌詞過長**：當歌詞超過平台限制時，系統 MUST 在提交前驗證並提示使用者縮短歌詞
- **EC-005 不支援的語言**：當使用者輸入不支援語言的歌詞時，系統 SHOULD 提示支援的語言列表
- **EC-006 並發上限**：當使用者已有 3 個進行中的生成任務時，系統 MUST 阻止新任務提交並提示等待

---

## Requirements

### Functional Requirements

**音樂生成核心功能**

- **FR-001**: 系統 MUST 支援透過情境描述生成純音樂/背景音樂（BGM）
- **FR-002**: 系統 MUST 支援透過歌詞和風格描述生成完整歌曲（含人聲）
- **FR-003**: 系統 MUST 支援透過主題描述生成 AI 歌詞
- **FR-004**: 系統 MUST 支援延伸/修改已生成的歌詞

**非同步任務管理**

- **FR-005**: 系統 MUST 以非同步方式執行音樂生成，返回任務 ID 供查詢
- **FR-006**: 系統 MUST 支援查詢任務狀態（準備中、處理中、已完成、失敗），使用者透過輪詢方式得知狀態變更
- **FR-007**: 系統 MUST 在任務完成時保存生成結果（MP3 檔案、封面、歌詞）
- **FR-008**: 系統 MUST 採用 [007-async-job-mgmt](../007-async-job-mgmt/spec.md) 的 Worker 模式和 API 設計風格，使用獨立的 MusicGenerationJob 表格

**結果存取與管理**

- **FR-009**: 使用者 MUST 能夠線上預覽已生成的音樂
- **FR-010**: 使用者 MUST 能夠下載已生成的音樂（MP3 格式）
- **FR-011**: 系統 MUST 保留生成歷史記錄至少 30 天
- **FR-012**: 使用者 MUST 能夠查看歷史生成記錄及其原始參數

**配額與限制**

- **FR-013**: 系統 MUST 追蹤 Mureka API 使用量
- **FR-014**: 系統 SHOULD 支援設定每日/每月使用量上限
- **FR-015**: 系統 MUST 在配額不足時阻止新任務提交並顯示提示
- **FR-016**: 系統 MUST 限制每個使用者同時最多 3 個進行中的生成任務

**模型選擇**

- **FR-017**: 系統 SHOULD 支援選擇不同的 Mureka 模型（auto, mureka-01, v7.5, v6）
- **FR-018**: 系統 MUST 預設使用 `auto` 模型

**Magic DJ 整合**

- **FR-019**: 系統 MUST 在 Magic DJ 控制台提供「生成新音軌」入口
- **FR-020**: 系統 MUST 支援將生成完成的音樂直接加入 Magic DJ 音軌列表

### Key Entities

根據 [研究文件 - API 架構分析](../011-music-generation/research.md#api-架構分析)：

- **MusicGenerationJob（音樂生成任務）**: 代表一個音樂生成請求，包含類型（song/instrumental/lyrics）、輸入參數、狀態、輸出結果
- **GeneratedMusic（生成音樂）**: 代表生成完成的音樂，包含 MP3 URL、封面、歌詞、時長等資訊
- **MusicGenerationType（生成類型）**: 枚舉值：`song`（歌曲）、`instrumental`（純音樂/BGM）、`lyrics`（歌詞）

---

## Technical Design

### API 整合架構

根據 [研究文件 - 整合建議](../011-music-generation/research.md#整合選項)，採用直接 REST API 整合方式：

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Mureka API    │
│   (React)       │     │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │   (Job Queue)   │
                        └─────────────────┘
```

### 資料模型

```python
from enum import Enum
from datetime import datetime
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class MusicGenerationType(str, Enum):
    SONG = "song"
    INSTRUMENTAL = "instrumental"
    LYRICS = "lyrics"


class MusicGenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MusicGenerationJob(Base):
    __tablename__ = "music_generation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[MusicGenerationType]
    status: Mapped[MusicGenerationStatus] = mapped_column(
        default=MusicGenerationStatus.PENDING
    )

    # Input parameters
    prompt: Mapped[str | None]  # 風格/場景描述
    lyrics: Mapped[str | None]  # 歌詞內容
    model: Mapped[str] = mapped_column(default="auto")

    # Mureka task tracking
    mureka_task_id: Mapped[str | None]

    # Output
    result_url: Mapped[str | None]  # 儲存後的本地 URL
    original_url: Mapped[str | None]  # Mureka 原始 MP3 URL
    cover_url: Mapped[str | None]
    generated_lyrics: Mapped[str | None]
    duration_ms: Mapped[int | None]
    title: Mapped[str | None]

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]

    # Error handling
    error_message: Mapped[str | None]
    retry_count: Mapped[int] = mapped_column(default=0)
```

### API Endpoints

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/api/v1/music/song` | 提交歌曲生成任務 |
| POST | `/api/v1/music/instrumental` | 提交純音樂生成任務 |
| POST | `/api/v1/music/lyrics` | 提交歌詞生成任務 |
| POST | `/api/v1/music/lyrics/extend` | 延伸歌詞 |
| GET | `/api/v1/music/jobs` | 列出音樂生成任務 |
| GET | `/api/v1/music/jobs/{job_id}` | 查詢單一任務狀態 |
| GET | `/api/v1/music/jobs/{job_id}/download` | 下載生成結果 |
| POST | `/api/v1/music/jobs/{job_id}/retry` | 重新提交失敗任務 |
| GET | `/api/v1/music/quota` | 查詢配額使用狀況 |

### 背景任務流程

參考 [研究文件 - 非同步任務流程](../011-music-generation/research.md#非同步任務流程)：

```
1. 使用者提交生成請求
2. Backend 建立 MusicGenerationJob 記錄（status=pending）
3. Background worker 從佇列取出任務
4. Worker 呼叫 Mureka API 提交生成（約 45 秒完成）
5. Worker 取得 mureka_task_id，更新記錄（status=processing）
6. Worker 定期輪詢 Mureka API 查詢狀態（每 5 秒）
7. 生成完成後，下載 MP3 並儲存至 storage
8. 更新記錄（status=completed, result_url=...）
```

### 配額管理

根據 [研究文件 - 定價結構](../011-music-generation/research.md#定價結構)：

```python
class MusicQuotaConfig:
    # 每個使用者每日限制
    DAILY_LIMIT_PER_USER: int = 10

    # 每個使用者每月限制
    MONTHLY_LIMIT_PER_USER: int = 100

    # 同時進行中的任務限制
    MAX_CONCURRENT_JOBS: int = 3
```

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 使用者可以在提交任務後 3 秒內看到任務已受理的確認
- **SC-002**: 90% 的音樂生成任務應在 2 分鐘內完成（根據 [研究](../011-music-generation/research.md#技術規格) 平均 45 秒）
- **SC-003**: 使用者可以在任務完成後 30 天內下載音檔
- **SC-004**: 生成的音檔 MUST 可正常播放（MP3 格式、無損壞），品質依賴 Mureka AI 服務保證
- **SC-005**: 系統應支援每個使用者同時執行最多 3 個音樂生成任務
- **SC-006**: Magic DJ 整合後，RD 可在 3 步驟內完成新音軌生成和加入

---

## Scope Boundaries

### In Scope

- Mureka AI API 整合（歌曲、純音樂、歌詞生成）
- 非同步任務管理與狀態追蹤
- 生成結果的儲存與下載
- 歷史記錄查詢
- 基本的配額追蹤
- Magic DJ 控制台整合

### Out of Scope

- 音樂編輯功能（剪輯、混音）
- 語音克隆功能（雖然 Mureka 支援）
- 即時串流生成
- 批次提交多個任務
- 音樂版權管理（依賴 Mureka 的商業授權）
- 音樂風格的細緻調整（如 BPM、調性）
- 與其他音樂生成服務的整合

---

## Implementation Phases

根據 [研究文件 - 實作建議](../011-music-generation/research.md#實作建議)：

### Phase 1: MVP

1. 實作純音樂（BGM）生成功能
2. 整合 007-async-job-mgmt
3. 基本的狀態查詢和下載
4. Magic DJ 快速生成入口

### Phase 2: 完整功能

1. 加入歌曲生成（含人聲）
2. 加入歌詞生成
3. 歷史記錄管理
4. 配額追蹤

### Phase 3: 進階功能

1. 模型選擇 UI
2. 風格模板
3. 與 Magic DJ 深度整合（自動分析情境推薦音樂）

---

## Assumptions

- Mureka API 服務穩定可用
- API 配額充足（或已規劃配額管理策略）
- 使用者理解音樂生成需要時間（非即時）
- 生成的音樂將儲存在現有的 storage 機制中
- 007-async-job-mgmt 機制可擴展支援新的任務類型

---

## Dependencies

- **[007-async-job-mgmt](../007-async-job-mgmt/spec.md)**: 非同步任務管理機制
- **[002-provider-mgmt-interface](../002-provider-mgmt-interface/spec.md)**: Provider 憑證管理（儲存 Mureka API Key）
- **[010-magic-dj-controller](../010-magic-dj-controller/spec.md)**: Magic DJ 控制台整合
- **Mureka AI Platform**: 外部服務依賴

---

## Risks & Mitigations

根據 [研究文件 - 風險評估](../011-music-generation/research.md#風險評估)：

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Mureka API 變更 | API 整合失效 | 封裝 API 呼叫，便於適應變更 |
| 配額超額 | 服務中斷 | 實作配額追蹤和警示機制 |
| 生成品質不穩定 | 使用者體驗差 | 提供重新生成功能，允許模型選擇 |
| API 費用超支 | 營運成本增加 | 設定使用上限，監控用量 |
| API 服務中斷 | 功能不可用 | 實作重試機制、graceful degradation |

---

## References

- [Mureka AI 整合研究](../011-music-generation/research.md)
- [Mureka AI 整合文件](/docs/integrations/mureka-ai.md)
- [Mureka API Platform](https://platform.mureka.ai/)
- [Mureka API Documentation](https://platform.mureka.ai/docs/)
- [Mureka MCP Server](https://github.com/SkyworkAI/Mureka-mcp)

---

*Last updated: 2026-01-29*
