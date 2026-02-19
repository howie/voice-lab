# Feature Specification: Gemini Lyria 音樂生成整合

**Feature Branch**: `016-integration-gemini-lyria-music`
**Created**: 2026-02-19
**Status**: Draft
**Research**: [Gemini / Lyria 音樂生成研究](/docs/research/2026-music-ai/gemini-lyria-music.md)
**Depends On**: [012-music-generation](../012-music-generation/spec.md)

---

## Overview

整合 Google Gemini Lyria 模型系列為 Voice Lab 新增器樂背景音樂（BGM）生成 provider。首發使用 Lyria 2 (`lyria-002`) 透過 Vertex AI REST API，補充現有 Mureka 在純器樂場景的能力，並為未來 Lyria 3 全功能整合（人聲+歌詞）預留架構。

詳細的技術研究和模型分析請參閱 [Research Document](/docs/research/2026-music-ai/gemini-lyria-music.md)。

---

## Clarifications

### Session 2026-02-19

- Q: 為何不直接整合 Lyria 3？ → A: `lyria-003-experimental` 仍為預覽版，API 可能變動；Lyria 2 (`lyria-002`) 已 GA 穩定
- Q: Lyria 僅支援器樂，如何與 Mureka 互補？ → A: Mureka 用於歌曲（含人聲+歌詞），Lyria 用於純器樂 BGM；使用者透過 provider 選擇切換
- Q: Google Cloud 認證如何處理？ → A: 複用現有 GCP Terraform 部署的 Service Account，透過 Application Default Credentials (ADC) 認證
- Q: 生成的 WAV 如何處理？ → A: 轉換為 MP3 後存至現有 storage 機制，與 Mureka 音檔統一管理
- Q: 配額管理是否需要獨立於 Mureka？ → A: 共用現有配額框架（每日/月限制），Lyria 的 Vertex AI 費用由 GCP billing 管控

---

## Problem Statement

目前 Voice Lab 的音樂生成僅依賴 Mureka AI 單一 provider：

1. **單點故障風險**：Mureka API 中斷時完全無法生成音樂
2. **器樂品質受限**：Mureka 側重歌曲生成，純器樂 BGM 並非其強項
3. **缺乏 IP 保障**：Mureka 無 IP 侵權賠償保障，企業使用有法律風險
4. **GCP 資源閒置**：專案已有 GCP 基礎設施（Terraform 部署），未利用 Google 的 AI 音樂能力

根據 [研究文件](/docs/research/2026-music-ai/gemini-lyria-music.md#十與現有方案比較)，Lyria 2 在器樂 BGM 場景提供 GA 穩定 API、$0.06/30s 低價、雙重 IP 賠償保障，是理想的互補選擇。

---

## User Scenarios & Testing

### User Story 1 — 使用 Lyria 生成器樂 BGM (Priority: P1)

使用者可以選擇 Lyria 作為 provider 生成純器樂背景音樂。

**Why this priority**: 核心功能，驗證端到端 Lyria 整合。

**Independent Test**: 在音樂生成頁面選擇 Lyria provider，輸入英文描述，驗證生成 MP3 可正常播放。

**Acceptance Scenarios**:

1. **Given** 使用者在音樂生成頁面，**When** 選擇 provider 為 "Lyria" 並輸入英文描述如 "calm acoustic folk with gentle guitar"，**Then** 系統提交 Vertex AI 生成任務並回傳任務 ID
2. **Given** 器樂生成任務已提交，**When** 生成完成，**Then** 系統將 WAV 轉為 MP3 並儲存，使用者可試聽和下載
3. **Given** 使用者輸入中文描述，**When** 提交至 Lyria，**Then** 系統顯示提示「Lyria 目前僅支援英文描述」

---

### User Story 2 — 使用 Negative Prompt 精確控制 (Priority: P1)

使用者可以指定不希望出現在音樂中的元素。

**Why this priority**: Lyria 2 的 negative prompt 是差異化功能，提升生成精確度。

**Independent Test**: 輸入 prompt 和 negative prompt，驗證生成結果排除了指定元素。

**Acceptance Scenarios**:

1. **Given** 使用者在 Lyria 器樂生成表單，**When** 填入 negative prompt 如 "drums, electric guitar"，**Then** 系統將 negative_prompt 傳送至 Vertex AI API
2. **Given** 使用者未填入 negative prompt，**When** 提交生成，**Then** 系統正常生成（negative_prompt 為空）

---

### User Story 3 — Lyria 與 Mureka Provider 切換 (Priority: P1)

使用者可以在音樂生成時自由選擇 Lyria 或 Mureka 作為 provider。

**Why this priority**: 確保 multi-provider 架構正常運作。

**Independent Test**: 分別用 Lyria 和 Mureka 生成同一描述的音樂，驗證兩者都正常運作。

**Acceptance Scenarios**:

1. **Given** 使用者在音樂生成頁面，**When** 選擇 provider 下拉選單，**Then** 顯示 "Mureka AI" 和 "Google Lyria" 選項
2. **Given** 使用者選擇 Lyria，**When** 表單只顯示 "器樂生成"（instrumental），**Then** 歌曲和歌詞生成選項 MUST 隱藏（Lyria 2 不支援）
3. **Given** 使用者的歷史記錄包含 Lyria 和 Mureka 任務，**When** 查看歷史記錄，**Then** 每筆記錄顯示其使用的 provider

---

### User Story 4 — 種子值可重現生成 (Priority: P2)

使用者可以指定 seed 值來重現相同的生成結果。

**Why this priority**: 進階功能，方便使用者微調 prompt 時保持音樂基調一致。

**Independent Test**: 使用相同 prompt + seed 生成兩次，驗證結果相同。

**Acceptance Scenarios**:

1. **Given** 使用者填入 seed 值，**When** 提交生成，**Then** 系統傳送 seed 至 Vertex AI API
2. **Given** 相同 prompt + 相同 seed，**When** 生成兩次，**Then** 產出相同的音樂
3. **Given** 使用者填入 seed 值，**When** 同時填入 sample_count > 1，**Then** 系統提示「seed 和 sample_count 不可同時使用」

---

### User Story 5 — 批量生成多首變體 (Priority: P2)

使用者可以一次生成多首變體，從中挑選最適合的。

**Why this priority**: 提升使用者找到理想 BGM 的效率。

**Independent Test**: 指定 sample_count=3 提交生成，驗證返回 3 首不同的音樂。

**Acceptance Scenarios**:

1. **Given** 使用者在 Lyria 生成表單，**When** 設定 sample_count 為 3，**Then** 系統一次生成 3 首變體
2. **Given** 批量生成完成，**When** 使用者查看結果，**Then** 可以逐一試聽並選擇下載

---

### Edge Cases

- **EC-001 Vertex AI 認證失敗**：當 GCP Service Account 無權限或 token 過期時，系統 MUST 顯示「Google Cloud 認證失敗，請檢查 Service Account 設定」
- **EC-002 Prompt 安全過濾**：當 Vertex AI 因安全過濾拒絕生成時，系統 MUST 顯示「您的描述被安全過濾器攔截，請修改內容」
- **EC-003 配額/費用上限**：當 GCP billing 配額不足時，系統 MUST 顯示「Google Cloud 配額不足」並阻止提交
- **EC-004 WAV 轉 MP3 失敗**：當音檔轉換失敗時，系統 SHOULD 直接提供 WAV 下載作為降級方案
- **EC-005 非英文 Prompt**：當使用者輸入非英文 prompt 時，系統 MUST 提示「Lyria 目前僅支援英文描述」
- **EC-006 Vertex AI 回應逾時**：當 API 回應超過 30 秒時，系統 MUST 標記任務失敗並允許重試

---

## Requirements

### Functional Requirements

**Lyria Provider 核心功能**

- **FR-001**: 系統 MUST 支援透過 Lyria 2 (Vertex AI) 生成器樂背景音樂
- **FR-002**: 系統 MUST 支援 Lyria prompt（英文情境描述）
- **FR-003**: 系統 MUST 支援 Lyria negative_prompt（排除不想要的元素）
- **FR-004**: 系統 MUST 將 Lyria 生成的 WAV (48 kHz) 轉換為 MP3 並儲存

**Provider 切換**

- **FR-005**: 使用者 MUST 能夠在 Lyria 和 Mureka 之間切換 provider
- **FR-006**: 系統 MUST 根據選擇的 provider 動態調整可用的生成類型（Lyria 僅器樂）
- **FR-007**: 系統 MUST 在歷史記錄中標示每筆任務使用的 provider

**進階參數**

- **FR-008**: 系統 SHOULD 支援 seed 參數以重現生成結果
- **FR-009**: 系統 SHOULD 支援 sample_count 參數以批量生成變體
- **FR-010**: 系統 MUST 驗證 seed 和 sample_count 不可同時使用

**認證與安全**

- **FR-011**: 系統 MUST 使用 Google Cloud Application Default Credentials (ADC) 認證
- **FR-012**: 系統 MUST 驗證 Vertex AI Lyria API 回應的 SynthID 浮水印標記
- **FR-013**: 系統 MUST 處理 Vertex AI 安全過濾器回傳的錯誤

**錯誤處理**

- **FR-014**: 系統 MUST 在認證失敗時提供明確的錯誤訊息
- **FR-015**: 系統 MUST 在 API 逾時 (30s) 時標記任務失敗
- **FR-016**: 系統 MUST 支援失敗任務重試（最多 3 次）

### Key Entities

複用 012-music-generation 既有實體，僅新增 enum 值：

- **MusicProvider enum**: 新增 `LYRIA = "lyria"` 值
- **MusicGenerationJob**: 無結構變更，`provider` 欄位可存放 `"lyria"` 值
- **LyriaVertexAIClient**: 新增 — Vertex AI REST API 客戶端
- **LyriaMusicProvider**: 新增 — 實作 `IMusicProvider` 介面

---

## Technical Design

### 整合架構

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Vertex AI API     │
│   (React)       │     │   (FastAPI)     │     │   (lyria-002)       │
└─────────────────┘     └─────────────────┘     └─────────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌─────────────────┐     ┌─────────────────────┐
                        │   PostgreSQL    │     │   Mureka API        │
                        │   (Job Queue)   │     │   (existing)        │
                        └─────────────────┘     └─────────────────────┘
```

### Provider Factory 整合

```python
# MusicProviderFactory 新增 lyria 分支
class MusicProviderFactory:
    SUPPORTED_PROVIDERS = ["mureka", "lyria"]

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> IMusicProvider:
        if provider_name == "lyria":
            from src.infrastructure.providers.music.lyria_music import LyriaMusicProvider
            return LyriaMusicProvider(**kwargs)
        elif provider_name == "mureka":
            ...
```

### Lyria API 呼叫流程

```
1. 使用者選擇 Lyria provider 並提交器樂生成請求
2. Backend 建立 MusicGenerationJob (provider="lyria", status=pending)
3. Background worker 取得任務
4. Worker 透過 LyriaVertexAIClient 呼叫 Vertex AI API
   POST https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/...
5. Vertex AI 同步回傳 base64 WAV 音訊（~10 秒）
6. Worker 解碼 base64 → WAV → 轉 MP3
7. Worker 儲存 MP3 至 storage
8. 更新 MusicGenerationJob (status=completed, result_url=...)
```

> **注意**：與 Mureka 的非同步輪詢模式不同，Lyria 2 Vertex AI 是同步 API（一次請求直接回傳結果）。Worker 提交後直接取得結果，不需要 polling。

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Lyria provider 可成功生成器樂並回傳可播放的 MP3 檔案
- **SC-002**: 95% 的 Lyria 生成請求應在 15 秒內完成（Vertex AI 回應 + WAV→MP3 轉換）
- **SC-003**: 使用者可在 UI 自由切換 Lyria / Mureka provider
- **SC-004**: Negative prompt 功能可有效排除指定元素
- **SC-005**: 生成的 MP3 品質不低於 128 kbps
- **SC-006**: 所有 Lyria 生成的音檔帶有 SynthID 浮水印標記

---

## Scope Boundaries

### In Scope

- Lyria 2 (`lyria-002`) Vertex AI REST API 整合
- 器樂/BGM 生成功能
- Negative prompt 支援
- Seed / sample_count 參數
- WAV → MP3 轉換與儲存
- UI provider 切換
- Contract tests + Unit tests

### Out of Scope

- Lyria 3 (`lyria-003-experimental`) 整合（待 GA 後獨立評估）
- Lyria RealTime WebSocket 串流整合
- 人聲/歌詞生成（Lyria 2 不支援）
- 多模態輸入（圖片/影片 prompt）
- 自動中英翻譯 prompt
- Lyria 專用配額計算（共用現有配額框架）

---

## Implementation Phases

### Phase 1: MVP

1. GCP 認證設定 + LyriaVertexAIClient 實作
2. LyriaMusicProvider (IMusicProvider) 實作
3. Factory 註冊 + enum 新增
4. WAV→MP3 轉換邏輯
5. Contract tests + Unit tests
6. Frontend provider 選擇 UI

### Phase 2: 進階功能

1. Negative prompt UI
2. Seed / sample_count 參數支援
3. 批量變體選擇 UI

### Phase 3: Lyria 3（待 API 發布）

1. 升級至 `lyria-003` 端點
2. 人聲 + 歌詞生成
3. 多模態輸入

---

## Assumptions

- GCP Service Account 已設定且有 Vertex AI 存取權限
- 本專案的 GCP Terraform 部署可擴展 Lyria API 所需的 IAM 權限
- Lyria 2 Vertex AI API 在部署區域（us-central1）可用
- 現有的 music_generation_jobs 表結構足以容納 Lyria 任務（無需 migration）
- pydub 或 ffmpeg 可用於 WAV → MP3 轉換

---

## Dependencies

- **[012-music-generation](../012-music-generation/spec.md)**: IMusicProvider 介面、MusicProviderFactory、MusicGenerationJob 實體
- **[006-gcp-terraform-deploy](../006-gcp-terraform-deploy/spec.md)**: GCP 基礎設施、Service Account 設定
- **[007-async-job-mgmt](../007-async-job-mgmt/spec.md)**: Background worker 任務處理
- **Google Vertex AI**: Lyria 2 API 外部服務依賴

---

## Risks & Mitigations

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Vertex AI API 變更 | 整合失效 | 封裝 API 呼叫於 LyriaVertexAIClient，便於適應變更 |
| GCP 認證問題 | 服務不可用 | 健康檢查端點驗證認證狀態、明確錯誤訊息 |
| WAV→MP3 轉換失敗 | 使用者無法下載 | WAV 直接下載作為降級方案 |
| 30 秒器樂長度限制 | 不符使用者需求 | 文件明確說明限制、引導使用 Mureka 生成長音樂 |
| Lyria 2 僅支援英文 | 中文使用者不便 | 前端提示語言限制、未來可加入翻譯層 |
| GCP 費用超支 | 營運成本 | 共用配額框架限制生成次數、GCP budget alerts |

---

## References

- [Gemini / Lyria 音樂生成研究](/docs/research/2026-music-ai/gemini-lyria-music.md)
- [012-music-generation 規格](../012-music-generation/spec.md)
- [Vertex AI — Lyria API Reference](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/lyria-music-generation)
- [Vertex AI — Lyria Prompt Guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/music/music-gen-prompt-guide)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

---

*Last updated: 2026-02-19*
