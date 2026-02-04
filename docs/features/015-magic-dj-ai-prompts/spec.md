# Feature Specification: Magic DJ AI Prompt Templates

**Feature Branch**: `015-magic-dj-ai-prompts`
**Created**: 2026-02-04
**Status**: Draft
**Input**: User description: "Magic DJ AI interaction mode 改良 - 以 AI 對話為主的 prompt template 介入系統，讓語音互動模式更順暢"
**Parent Feature**: `010-magic-dj-controller`

## Clarifications

### Session 2026-02-04

- Q: Prompt template 的用途？ → A: 預建的 prompt 按鈕，按下去直接送文字指令給 AI，例如小孩問奇怪問題時按「裝傻」按鈕，AI 就會裝傻不回答
- Q: AI interaction mode 的欄位佈局？ → A: 第一欄 Prompt Templates、第二欄 Story Prompts、第三欄音效、第四欄音樂
- Q: AI 講話時能否同時播放音效/音樂？ → A: 可以，AI 在講話時我們可以放音效或背景音樂
- Q: Gemini 直連參考哪些功能？ → A: 參考 004-interaction-module 的 Gemini V2V realtime 實作，讓語音互動更順暢

## User Scenarios & Testing *(mandatory)*

### User Story 1 - RD 使用 Prompt Template 即時介入 AI 對話 (Priority: P1)

RD (研發人員/巫師) 在 AI 對話模式中，需要透過預建的 prompt template 按鈕，一鍵送出文字指令給 Gemini AI，以控制 AI 的回應行為。例如當小孩問奇怪的問題時，RD 可以按下「裝傻」按鈕，AI 就會裝傻不回答小孩的問題。

**Why this priority**: 這是 AI 互動模式最核心的改良。現有的「救場語音」是播放預錄音檔，但實際使用中 RD 需要的是能即時「指揮」AI 的行為，而非播放固定內容。Prompt template 讓 RD 能像導演一樣指導 AI 的即時演出。

**Independent Test**: RD 可在 AI 對話中測試各種 prompt template 按鈕，驗證 AI 是否按照指令調整回應行為。

**Acceptance Scenarios**:

1. **Given** 控制台處於 AI 對話模式且 Gemini 已連線，**When** RD 按下「裝傻」prompt template 按鈕，**Then** 系統透過 WebSocket 發送 `text_input` 訊息，內容為「裝傻」按鈕內建的 prompt 文字
2. **Given** AI 收到 prompt template 指令，**When** AI 處理該指令，**Then** AI 的後續回應行為應符合 prompt 指令（如裝傻、轉移話題等）
3. **Given** RD 在 prompt template 面板上，**When** 查看可用的 template，**Then** 應顯示 template 名稱、圖示，並可一鍵觸發

---

### User Story 2 - RD 透過 Story Prompt 欄位發送故事指令 (Priority: P1)

RD 需要在第二欄輸入或選擇故事指令 (Story Prompt)，引導 AI 進入特定的故事情節或場景。這些 story prompt 可以是預設的故事模板，也可以是 RD 即時輸入的自訂內容。

**Why this priority**: Story prompt 是驅動 AI 互動內容的核心。RD 透過 story prompt 來設定場景、切換故事章節、引導情節發展。

**Independent Test**: RD 可測試預設 story prompt 和自訂輸入，驗證 AI 是否正確進入對應的故事情節。

**Acceptance Scenarios**:

1. **Given** 控制台處於 AI 對話模式，**When** RD 從 Story Prompt 欄位選擇預設故事模板，**Then** 系統發送完整的故事 prompt 給 AI
2. **Given** RD 在 Story Prompt 欄位，**When** RD 在文字輸入框輸入自訂 story prompt 並送出，**Then** 系統發送該文字給 AI
3. **Given** AI 正在對話中，**When** RD 送出新的 story prompt，**Then** AI 應自然地轉換到新的故事場景

---

### User Story 3 - RD 在 AI 講話時播放音效與背景音樂 (Priority: P1)

RD 需要在 AI 正在語音回應時，同時播放音效（如魔法聲、掌聲）或啟動背景音樂，以增強互動體驗的沉浸感。音效和音樂不應中斷 AI 的語音輸出。

**Why this priority**: 音效和背景音樂是營造氛圍的關鍵。4-6 歲兒童對聲音環境非常敏感，在 AI 講故事時搭配音效可以大幅提升沉浸感。

**Independent Test**: 在 AI 回應語音播放中，測試音效和音樂是否能同時疊加播放，且不影響 AI 語音品質。

**Acceptance Scenarios**:

1. **Given** AI 正在語音回應中，**When** RD 從音效欄點擊音效按鈕，**Then** 音效在 SFX 頻道播放，AI 語音持續不受影響
2. **Given** AI 正在語音回應中，**When** RD 從音樂欄啟動背景音樂，**Then** 音樂在 Music 頻道播放，AI 語音持續不受影響
3. **Given** 背景音樂已在播放，**When** AI 開始語音回應，**Then** 三者（AI 語音 + 音效 + 音樂）可同時播放

---

### User Story 4 - RD 管理 Prompt Template 清單 (Priority: P2)

RD 需要能新增、編輯、刪除 prompt template，以適應不同測試場景和兒童的反應。每個 template 包含顯示名稱、圖示/顏色、以及隱藏的 prompt 內容。

**Why this priority**: 不同測試場景需要不同的 prompt template 組合。RD 需要能根據經驗調整 template 內容。

**Independent Test**: RD 可測試新增自訂 template、編輯現有 template 的 prompt 內容、以及刪除不需要的 template。

**Acceptance Scenarios**:

1. **Given** 控制台 prompt template 面板，**When** RD 點擊新增按鈕，**Then** 顯示編輯對話框，可輸入名稱、選擇顏色/圖示、輸入 prompt 內容
2. **Given** 已有 prompt template，**When** RD 長按或右鍵某個 template，**Then** 顯示編輯/刪除選項
3. **Given** RD 修改 template 內容，**When** 儲存變更，**Then** template 設定持久化至 localStorage

---

### Edge Cases

- **EC-001 AI 未連線時的 Prompt Template**: 當 Gemini 未連線時，prompt template 按鈕應顯示為禁用狀態，並在 RD 嘗試點擊時顯示 toast「AI 未連線」
- **EC-002 快速連續觸發 Prompt**: 當 RD 在極短時間內（< 500ms）連續按下不同 prompt template，系統 SHOULD 將所有 prompt 依序送出，不丟棄任何指令
- **EC-003 AI 回應中送出 Prompt**: 當 AI 正在語音回應時送出 prompt template，系統 SHOULD 直接送出，由 Gemini 自行處理中斷和新回應
- **EC-004 音效/音樂與 AI 語音衝突**: 系統 MUST 確保音效/音樂播放不影響 AI 語音輸出（各自獨立頻道）

## Requirements *(mandatory)*

### Functional Requirements

**Prompt Template 系統**

- **FR-001**: 系統 MUST 在 AI 對話模式第一欄提供 Prompt Template 面板，顯示可點擊的 template 按鈕
- **FR-002**: 每個 Prompt Template MUST 包含：顯示名稱（短名）、prompt 內容（隱藏文字）、顏色標記
- **FR-003**: 系統 MUST 在 RD 點擊 template 按鈕時，透過 WebSocket `text_input` 訊息將 prompt 內容發送給 Gemini
- **FR-004**: 系統 MUST 提供至少 8 個預設 Prompt Template（裝傻、轉移話題、鼓勵、等一下、結束故事、回到主題、簡短回答、多問問題）
- **FR-005**: 系統 MUST 支援新增、編輯、刪除自訂 Prompt Template
- **FR-006**: 系統 MUST 將 Prompt Template 設定持久化至 localStorage

**Story Prompt 欄位**

- **FR-007**: 系統 MUST 在 AI 對話模式第二欄提供 Story Prompt 面板
- **FR-008**: Story Prompt 面板 MUST 包含預設的故事模板按鈕和一個自由文字輸入框
- **FR-009**: 系統 MUST 在 RD 選擇或輸入 story prompt 後，透過 WebSocket `text_input` 訊息發送給 Gemini
- **FR-010**: 系統 SHOULD 提供至少 4 個預設 Story Prompt 模板

**AI 對話模式佈局**

- **FR-011**: AI 對話模式 MUST 以四欄佈局顯示：Prompt Templates | Story Prompts | 音效 | 音樂
- **FR-012**: 系統 MUST 保留現有的 AI 即時語音控制功能（麥克風、WebSocket 連線、音量指示）
- **FR-013**: AI 語音、音效、音樂 MUST 可同時播放，各使用獨立頻道

**Gemini 直連增強**

- **FR-014**: 系統 MUST 利用現有 Gemini V2V (realtime) WebSocket 連線發送 text_input 訊息
- **FR-015**: 系統 SHOULD 在 prompt 送出後顯示送出視覺回饋（按鈕閃爍或 toast）

### Key Entities

- **PromptTemplate**: 代表一個可點擊的 prompt 按鈕，包含 id、name（顯示名稱）、prompt（隱藏 prompt 內容）、color（顏色標記）、icon（可選圖示）、order（排序）
- **StoryPrompt**: 代表一個故事模板，包含 id、name、prompt（完整故事指令）、category（分類）
- **AIInteractionLayout**: AI 對話模式的四欄佈局配置

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: RD 點擊 prompt template 按鈕後，text_input 訊息應在 100ms 內發送至 WebSocket
- **SC-002**: AI 應在收到 prompt template 指令後 2 秒內調整回應行為
- **SC-003**: 音效/音樂播放不應影響 AI 語音輸出（各自獨立頻道，無互相干擾）
- **SC-004**: Prompt template 面板應支援至少 20 個 template 而不影響 UI 滾動流暢度
- **SC-005**: 在 20-25 分鐘的測試流程中，RD 應能順暢使用 prompt template 介入 AI 對話

## Assumptions

- 現有 Gemini V2V WebSocket 連線已穩定運作（已在 010-magic-dj-controller 和 004-interaction-module 驗證）
- Gemini `send_text()` 方法已實作（`gemini_realtime.py:269-293`），可在 V2V 中送出 text_input
- 後端 `_handle_text_input` handler 已存在（`interaction_handler.py:348`）
- RD 已熟悉 Magic DJ 控制台基本操作
- Prompt template 的效果取決於 Gemini 模型對指令的理解能力，可能需要調整 prompt 措辭

## Scope Boundaries

**In Scope**:
- AI 對話模式四欄佈局重新設計
- Prompt Template 按鈕系統（預設 + 自訂）
- Story Prompt 面板（預設模板 + 自由輸入）
- 透過 WebSocket text_input 發送 prompt
- 音效/音樂與 AI 語音同時播放

**Out of Scope**:
- 後端 prompt template 資料庫儲存（使用 localStorage）
- Prompt template 跨裝置同步
- AI 回應品質自動監控
- 新的 Gemini 連線模式（繼續使用現有 V2V）
- 語音辨識/轉錄 UI 顯示

## Design Decisions

### DD-001: AI 對話模式四欄佈局

**決策日期**: 2026-02-04
**選擇**: 將原有佈局（AI控制 + 4頻道）改為以 AI 對話為中心的四欄佈局

**新佈局**:
1. **Prompt Templates** - 預建的 AI 行為控制按鈕（替代原救場語音欄）
2. **Story Prompts** - 故事指令模板和自由輸入
3. **音效 (SFX)** - 串場音效（維持）
4. **音樂 (Music)** - 背景音樂（維持）

**AI 控制列**: 麥克風、連線狀態、中斷等控制功能移至頂部或側邊常駐區域

```
┌──────────────────────────────────────────────────────────────────┐
│ Header: Timer | Preset | Mode | [Mic] [Status] [Interrupt]     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Prompt        Story          音效          音樂                │
│  Templates     Prompts        (SFX)         (Music)             │
│  ──────────    ──────────     ──────────    ──────────           │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│ │ 裝傻     │  │ 魔法森林 │  │ 魔法聲   │  │ BGM_1    │         │
│ │ 轉移話題 │  │ 海底冒險 │  │ 掌聲     │  │ (loop)   │         │
│ │ 鼓勵     │  │ 太空旅行 │  │ 轉場     │  ├──────────┤         │
│ │ 等一下   │  ├──────────┤  │ 驚喜     │  │ BGM_2    │         │
│ │ 結束故事 │  │ [自由輸入]│  │          │  │          │         │
│ │ 回到主題 │  │ _________ │  │          │  │          │         │
│ │ 簡短回答 │  │ [送出]    │  │          │  │          │         │
│ │ 多問問題 │  └──────────┘  └──────────┘  └──────────┘         │
│ │ + 自訂   │                                                    │
│ └──────────┘                                                    │
│                                                                  │
│    🔊          🔊             🔊            🔊                  │
│   ━━●━━       ━━━●━          ━━━━●         ━━━●━                │
│  (音量)      (音量)         (音量)        (音量)                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**選擇理由**: AI 對話是主要使用模式，prompt template 比預錄救場語音更靈活。RD 可以即時控制 AI 行為，同時搭配音效和音樂營造沉浸氛圍。
