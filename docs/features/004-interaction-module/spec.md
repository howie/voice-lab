# Feature Specification: Real-time Voice Interaction Testing Module

**Feature Branch**: `004-interaction-module`
**Created**: 2026-01-19
**Status**: Draft
**Input**: User description: "Phase4 Interaction model 測試互動場景，如果有直接 realtime api 就直接使用，不然就是可以退一步 fallback 使用 STT->LLM->TTS model"

## Overview

本模組提供端對端的即時語音代理互動測試平台，支援兩種主要模式：
1. **Realtime API 模式**：直接使用語音到語音的 API（如 OpenAI Realtime API），提供最低延遲
2. **Cascade 模式**：串聯 STT → LLM → TTS 的傳統流程，作為 fallback 方案

使用者可以測試、比較不同方案的延遲表現、互動品質，並驗證打斷（Barge-in）功能。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 即時語音對話測試 (Priority: P1)

作為語音應用開發者，我想要在 Web 介面上直接與 AI 語音代理進行即時對話，以便測試端對端的互動體驗。

**Why this priority**: 這是模組的核心功能，沒有即時對話能力，其他所有功能都無法展示價值。

**Independent Test**: 可透過開啟麥克風、說一句話、收到 AI 語音回應來獨立測試。即使沒有延遲測量或場景模板，基本對話功能已能提供測試價值。

**Acceptance Scenarios**:

1. **Given** 使用者已登入並選擇一個語音互動模式, **When** 使用者點擊「開始對話」並說話, **Then** 系統顯示收音狀態、處理中狀態，並在合理時間內播放 AI 的語音回應
2. **Given** 使用者正在進行語音對話, **When** 使用者點擊「結束對話」, **Then** 系統停止收音並顯示對話摘要
3. **Given** 使用者麥克風權限被拒絕, **When** 使用者嘗試開始對話, **Then** 系統顯示友善的錯誤訊息，引導使用者開啟麥克風權限

---

### User Story 2 - 互動模式選擇與切換 (Priority: P1)

作為語音應用開發者，我想要在 Realtime API 模式與 Cascade 模式之間選擇和切換，以便比較不同技術方案的表現。

**Why this priority**: 模式選擇是本模組的核心差異化功能，讓使用者能評估最適合其場景的技術方案。

**Independent Test**: 可透過選擇不同模式並觀察系統行為差異來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者在模式選擇頁面, **When** 使用者選擇「Realtime API 模式」, **Then** 系統顯示可用的 Realtime API 提供者列表（如 OpenAI Realtime）
2. **Given** 使用者在模式選擇頁面, **When** 使用者選擇「Cascade 模式」, **Then** 系統顯示 STT、LLM、TTS 三個組件的提供者選擇器
3. **Given** 使用者已選擇 Realtime API 模式但該 API 不可用, **When** 系統偵測到連線失敗, **Then** 系統提示是否自動切換到 Cascade 模式作為 fallback

---

### User Story 3 - 端對端延遲測量 (Priority: P2)

作為 QA 測試人員，我想要看到每次對話回合的詳細延遲數據，以便評估不同提供者的效能表現。

**Why this priority**: 延遲是語音互動體驗的關鍵指標，但需要先有基本對話功能才能測量。

**Independent Test**: 可透過進行一次對話並查看延遲報告來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者完成一輪語音互動, **When** 系統處理完成, **Then** 介面顯示該回合的總延遲時間以及各階段延遲（STT、LLM、TTS 或 Realtime API）
2. **Given** 使用者進行多輪對話, **When** 對話結束, **Then** 系統顯示整體延遲統計（平均、最小、最大、P95）
3. **Given** 使用者正在使用 Cascade 模式, **When** 查看延遲數據, **Then** 可以看到 STT 時間、LLM 首 Token 時間、TTS 首音訊時間的分段數據

---

### User Story 4 - 系統提示詞配置 (Priority: P2)

作為產品經理，我想要配置 AI 代理的系統提示詞和角色設定，以便測試不同的對話場景。

**Why this priority**: 系統提示詞決定 AI 的行為模式，是場景測試的基礎，但核心對話功能優先。

**Independent Test**: 可透過設定不同的系統提示詞並觀察 AI 回應風格變化來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者在設定頁面, **When** 使用者輸入自訂系統提示詞並儲存, **Then** 後續對話中 AI 依照該提示詞行為
2. **Given** 系統提供預設場景模板, **When** 使用者選擇「客服機器人」模板, **Then** 系統自動填入對應的系統提示詞
3. **Given** 使用者已設定系統提示詞, **When** 使用者切換到不同的語音模式, **Then** 系統提示詞設定保持不變

---

### User Story 5 - 打斷（Barge-in）功能測試 (Priority: P3)

作為語音應用開發者，我想要測試當使用者在 AI 說話時打斷的情境，以便確保系統能正確處理打斷行為。

**Why this priority**: 打斷是進階互動功能，需要基本對話和延遲測量穩定後才能有效測試。

**Independent Test**: 可透過在 AI 回應播放中說話並觀察系統反應來獨立測試。

**Acceptance Scenarios**:

1. **Given** AI 正在播放語音回應, **When** 使用者開始說話, **Then** 系統偵測到打斷並立即停止 AI 語音播放
2. **Given** 打斷功能已啟用, **When** 發生打斷事件, **Then** 系統記錄打斷發生的時間點和後續處理延遲
3. **Given** 使用者在設定中關閉打斷功能, **When** AI 正在說話時使用者說話, **Then** AI 繼續播放直到完成

---

### User Story 6 - 對話歷史與回放 (Priority: P3)

作為 QA 測試人員，我想要查看過去的測試對話記錄並回放音訊，以便進行問題分析和報告。

**Why this priority**: 歷史記錄對於分析和報告很有價值，但不影響核心測試功能。

**Independent Test**: 可透過進行對話後在歷史頁面查看記錄並播放音訊來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者完成一次測試對話, **When** 使用者進入歷史記錄頁面, **Then** 可以看到該次對話的時間、使用的模式、提供者、延遲數據
2. **Given** 使用者查看一筆歷史記錄, **When** 點擊「播放」, **Then** 系統依序播放使用者和 AI 的音訊
3. **Given** 使用者查看歷史記錄列表, **When** 使用篩選器選擇特定日期或模式, **Then** 列表僅顯示符合條件的記錄

---

### Edge Cases

- 當網路連線不穩定時，系統如何處理？顯示連線狀態指示器，並在斷線時嘗試重連或提示使用者
- 當使用者說話時間過長時，系統如何處理？設定合理的單次發言時間上限，並在接近上限時提示使用者
- 當 LLM 回應過長時，系統如何處理？支援串流式 TTS 播放，避免等待完整回應
- 當麥克風收音品質不佳時，系統如何處理？顯示音量指示器，並在音量過低時提示使用者
- 當選擇的提供者 API 配額用盡時，系統如何處理？顯示錯誤訊息並建議切換提供者或模式

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 支援透過瀏覽器麥克風進行即時語音輸入
- **FR-002**: 系統 MUST 支援 Realtime API 模式，直接串接支援語音到語音的 API
- **FR-003**: 系統 MUST 支援 Cascade 模式，串聯 STT → LLM → TTS 流程
- **FR-004**: 系統 MUST 在 Realtime API 不可用時，提供自動或手動切換到 Cascade 模式的機制
- **FR-005**: 系統 MUST 測量並顯示每次互動的端對端延遲
- **FR-006**: 系統 MUST 在 Cascade 模式下顯示各階段（STT、LLM、TTS）的分段延遲
- **FR-007**: 系統 MUST 支援打斷（Barge-in）功能，在使用者說話時停止 AI 語音播放
- **FR-008**: 系統 MUST 允許使用者配置 AI 的系統提示詞
- **FR-009**: 系統 MUST 提供預設的場景模板供快速配置
- **FR-010**: 系統 MUST 記錄對話歷史，包含音訊檔案和延遲數據
- **FR-011**: 系統 MUST 支援回放歷史對話的音訊
- **FR-012**: 系統 MUST 顯示即時的收音狀態和處理狀態指示
- **FR-013**: 系統 MUST 整合現有的 BYOL（Bring Your Own License）憑證管理功能

### Realtime API 模式提供者

- **FR-014**: 系統 MUST 支援 OpenAI Realtime API 和 Gemini Live API 作為 Realtime API 模式的提供者

### Cascade 模式提供者

- **FR-015**: 系統 MUST 整合 Phase 3 已實作的 STT 提供者（Deepgram、AssemblyAI 等）用於 Cascade 模式
- **FR-016**: 系統 MUST 支援 Google Gemini 和 OpenAI (GPT-4o) 作為 Cascade 模式的 LLM 提供者
- **FR-017**: 系統 MUST 整合 Phase 1 已實作的 TTS 提供者（Azure、Google、ElevenLabs 等）用於 Cascade 模式

### Observability Requirements

- **FR-018**: 系統 MUST 產生結構化日誌，包含對話 ID、時間戳記、事件類型、提供者名稱
- **FR-019**: 系統 MUST 記錄基本指標：API 呼叫計數、錯誤率、各提供者使用次數
- **FR-020**: 系統 MUST 在發生錯誤時記錄足夠的上下文資訊以支援除錯

### Key Entities

- **Conversation Session**: 代表一次完整的語音互動會話，包含開始時間、結束時間、使用的模式和提供者設定
- **Conversation Turn**: 代表一個對話回合（使用者說話 + AI 回應），包含時間戳記、延遲數據、音訊檔案參照
- **Latency Metrics**: 記錄延遲測量數據，包含總延遲、各階段延遲、時間戳記
- **System Prompt Template**: 預設的場景模板，包含名稱、描述、提示詞內容
- **Provider Configuration**: 使用者選擇的提供者組合設定，包含模式類型和各組件的提供者選擇

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 使用者可以在 5 秒內完成模式選擇並開始第一次語音對話
- **SC-002**: Realtime API 模式的端對端延遲在正常網路條件下低於 1 秒
- **SC-003**: Cascade 模式的端對端延遲在正常網路條件下低於 3 秒
- **SC-004**: 延遲測量數據的準確度誤差在 50 毫秒以內
- **SC-005**: 打斷功能在使用者開始說話後 500 毫秒內停止 AI 語音播放
- **SC-006**: 系統支援連續 30 分鐘的語音對話測試而不中斷
- **SC-007**: 歷史記錄頁面可在 2 秒內載入最近 100 筆對話記錄
- **SC-008**: 90% 的測試使用者可以在無教學的情況下成功完成一次完整的語音對話測試

## Clarifications

### Session 2026-01-19

- Q: Cascade 模式應支援哪些 LLM 提供者？ → A: Google Gemini + OpenAI (GPT-4o)
- Q: 系統的可觀測性需求層級？ → A: 結構化日誌 + 基本指標（API 呼叫計數、錯誤率）

## Assumptions

- 使用者的瀏覽器支援 WebRTC 和麥克風存取 API
- 使用者已透過 BYOL 功能設定所需的 API 憑證，或使用系統預設憑證
- 網路延遲在合理範圍內（RTT < 200ms）
- 使用者具備基本的語音測試相關知識
- Phase 1 的 TTS 模組和 Phase 3 的 STT 模組已完成且可供整合
