# Implementation Plan: Magic DJ AI Prompt Templates

**Branch**: `015-magic-dj-ai-prompts` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/015-magic-dj-ai-prompts/spec.md`
**Parent Feature**: `010-magic-dj-controller`

## Summary

改良 Magic DJ 的 AI 對話模式，從原有的「預錄救場語音 + AI 控制」重新設計為「Prompt Template 驅動的 AI 對話控制台」。核心變更：

1. **第一欄改為 Prompt Templates** — 預建的 AI 行為控制按鈕（裝傻、轉移話題、鼓勵等），按下即透過 WebSocket `text_input` 發送隱藏 prompt 給 Gemini
2. **第二欄新增 Story Prompts** — 故事模板按鈕 + 自由文字輸入，引導 AI 進入特定故事場景
3. **第三欄音效 + 第四欄音樂保持** — 維持現有架構，支援 AI 講話時同時播放音效/背景音樂
4. **AI 控制列移至頂部** — 麥克風、連線狀態、中斷等功能移至 Header 常駐區域

本功能為純前端實作，利用現有 Gemini V2V WebSocket 連線和 `text_input` message type，無需新增後端 API。

## Technical Context

**Language/Version**: TypeScript 5.3+, React 18.2+
**Primary Dependencies**:
- Zustand 4.5+ (狀態管理，擴展現有 magicDJStore)
- Tailwind CSS 3.4+ (樣式)
- Lucide React (圖示)
- 現有 useWebSocket hook (Gemini 通訊)
- 現有 useMultiTrackPlayer hook (音訊播放)

**Storage**: localStorage（Zustand persist，擴展現有 magic-dj-store）
**Testing**: Vitest 1.2+, Testing Library
**Target Platform**: Web (Chrome/Edge)
**Project Type**: Web application (前端功能增強)
**Performance Goals**:
- Prompt template 按鈕反應 < 100ms（text_input 發送）
- 音效/音樂播放不影響 AI 語音輸出
- UI 支援 20+ prompt template 無卡頓

**Constraints**:
- 純前端實作，利用現有後端 WebSocket infrastructure
- 不改變 Gemini 連線邏輯，僅增加 `text_input` 發送
- 向後相容：prerecorded 模式佈局不受影響

**Scale/Scope**: 單一 RD 操作，支援 20-25 分鐘測試流程

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ✅ PASS | 為 PromptTemplatePanel、StoryPromptPanel 元件和 store 擴展撰寫單元測試 |
| II. Unified API Abstraction | ✅ PASS | 複用現有 WebSocket text_input handler，無新增服務 |
| III. Performance Benchmarking | ✅ PASS | SC-001 定義按鈕反應 < 100ms，SC-003 定義頻道獨立性 |
| IV. Documentation First | ✅ PASS | quickstart.md 已建立 |
| V. Clean Architecture | ✅ PASS | 遵循現有前端分層結構，新增元件於 components/magic-dj/ |

## Project Structure

### Documentation (this feature)

```text
docs/features/015-magic-dj-ai-prompts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # N/A (純前端，無新 API)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── magic-dj/
│   │       ├── DJControlPanel.tsx          # 修改：AI 模式佈局重新設計
│   │       ├── AIVoiceChannelStrip.tsx     # 修改：精簡為頂部 AI 控制列
│   │       ├── PromptTemplatePanel.tsx     # 新增：Prompt Template 面板（第一欄）
│   │       ├── PromptTemplateButton.tsx    # 新增：單一 Prompt Template 按鈕
│   │       ├── PromptTemplateEditor.tsx    # 新增：Prompt Template 編輯對話框
│   │       ├── StoryPromptPanel.tsx        # 新增：Story Prompt 面板（第二欄）
│   │       ├── AIControlBar.tsx            # 新增：頂部 AI 控制列 (mic, status, interrupt)
│   │       ├── ChannelBoard.tsx            # 修改：支援新的 AI 模式四欄佈局
│   │       └── ChannelStrip.tsx            # 不變
│   ├── stores/
│   │   └── magicDJStore.ts                # 修改：新增 promptTemplates, storyPrompts state
│   └── types/
│       └── magic-dj.ts                    # 修改：新增 PromptTemplate, StoryPrompt types
├── src/routes/
│   └── magic-dj/
│       └── MagicDJPage.tsx                # 修改：新增 prompt 發送 handlers
└── tests/
    └── unit/
        └── magic-dj/
            ├── PromptTemplatePanel.test.tsx  # 新增
            ├── StoryPromptPanel.test.tsx     # 新增
            └── promptTemplateStore.test.ts   # 新增
```

**Structure Decision**: 在現有 `components/magic-dj/` 目錄下新增元件，擴展 `magicDJStore` 和 `magic-dj.ts` types。不建立新目錄。

## Complexity Tracking

> 無 Constitution 違規項目。以下為中等複雜度功能備註：

| 功能 | 複雜度 | 風險 | 緩解措施 |
|------|--------|------|----------|
| DJControlPanel AI 模式佈局重構 | 中 | 可能影響現有 prerecorded 模式 | 確保 prerecorded 分支不受影響，測試兩種模式 |
| Prompt Template CRUD + Persist | 低 | localStorage 遷移 | 使用 Zustand version 升級，fallback 載入預設 |
| WebSocket text_input 發送 | 低 | 已有後端支援 | 直接使用現有 sendMessage('text_input', ...) |

## Implementation Phases

### Phase 1: Types & Store Extension (Foundation)

**目標**: 定義新 types，擴展 magicDJStore

**修改檔案**:
- `frontend/src/types/magic-dj.ts` — 新增 PromptTemplate, StoryPrompt, PromptTemplateColor types
- `frontend/src/stores/magicDJStore.ts` — 新增 state fields, actions, default data, persist partialize

**新增內容**:
```typescript
// types/magic-dj.ts 新增
type PromptTemplateColor = 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'orange' | 'pink' | 'cyan'

interface PromptTemplate {
  id: string
  name: string
  prompt: string
  color: PromptTemplateColor
  icon?: string
  order: number
  isDefault: boolean
  createdAt: string
}

interface StoryPrompt {
  id: string
  name: string
  prompt: string
  category: string
  icon?: string
  order: number
  isDefault: boolean
}
```

**驗證**: types 編譯通過，store 可正確讀寫 promptTemplates/storyPrompts

---

### Phase 2: Core Components (UI)

**目標**: 建立 Prompt Template 和 Story Prompt UI 元件

**新增檔案**:

#### 2a. PromptTemplatePanel.tsx
- 顯示所有 prompt template 按鈕（grid 排列）
- 每個按鈕顯示名稱、顏色標記
- 點擊觸發 `onSendPrompt(template)` callback
- 底部「+ 新增」按鈕

#### 2b. PromptTemplateButton.tsx
- 單一按鈕元件，接收 PromptTemplate props
- 顏色對應 tailwind classes
- 點擊 feedback：按鈕短暫 pulse 動畫
- 長按或右鍵：顯示編輯/刪除選項
- disabled 狀態（AI 未連線時）

#### 2c. PromptTemplateEditor.tsx
- Modal 對話框，用於新增/編輯 template
- 表單欄位：名稱、prompt 內容 (textarea)、顏色選擇
- 驗證邏輯

#### 2d. StoryPromptPanel.tsx
- 上方：預設故事模板按鈕（card 風格）
- 下方：自由文字輸入框 + 送出按鈕
- 點擊預設模板或送出自訂文字，觸發 `onSendStoryPrompt(text)` callback

#### 2e. AIControlBar.tsx
- 從 AIVoiceChannelStrip 提取的精簡版 AI 控制功能
- 包含：麥克風 toggle、連線狀態 dot、中斷按鈕、強制送出按鈕
- 水平排列，作為 header 的一部分

**驗證**: 元件可獨立 render，props 正確傳遞

---

### Phase 3: Layout Integration (Assembly)

**目標**: 將新元件整合到 DJControlPanel 的 AI 對話模式

**修改檔案**:

#### 3a. DJControlPanel.tsx
- AI 對話模式分支（line 158-186）重構
- Header 區域新增 `AIControlBar`（mic, status, interrupt, force submit）
- Main 區域改為四欄佈局：
  ```
  <PromptTemplatePanel> | <StoryPromptPanel> | <ChannelStrip sfx> | <ChannelStrip music>
  ```
- 移除 `AIVoiceChannelStrip` 作為 leadingChannel

#### 3b. MagicDJPage.tsx
- 新增 `handleSendPromptTemplate(template: PromptTemplate)` handler
  - 呼叫 `sendMessage('text_input', { text: template.prompt })`
  - 更新 `lastSentPromptId` for visual feedback
  - 呼叫 `logOperation('send_prompt_template', { templateId, name })`
- 新增 `handleSendStoryPrompt(text: string)` handler
  - 呼叫 `sendMessage('text_input', { text })`
  - 呼叫 `logOperation('send_story_prompt', { text: text.slice(0, 100) })`
- 傳遞新 handlers 到 DJControlPanel

#### 3c. ChannelBoard.tsx
- 修改以支援新的 AI 模式佈局
- 當 AI 模式時，只顯示 SFX 和 Music 兩個 ChannelStrip（不再顯示 rescue 和 voice）
- 接收 `promptPanel` 和 `storyPanel` 作為 leading content

**驗證**: AI 模式切換後顯示新四欄佈局，prerecorded 模式不受影響

---

### Phase 4: WebSocket Integration & Feedback

**目標**: 實現 prompt 發送和視覺回饋

**實作內容**:

#### 4a. WebSocket text_input 發送
- 在 MagicDJPage 中透過現有 `sendMessage('text_input', { text })` 發送
- 後端已有 `_handle_text_input` handler（`interaction_handler.py:348`）
- Gemini 已有 `send_text()` method（`gemini_realtime.py:269`）

#### 4b. 視覺回饋
- Prompt template 按鈕點擊後：200ms pulse 動畫 + 短暫顏色加深
- Story prompt 送出後：輸入框清空 + toast 提示「已送出」
- Operation log：所有 prompt 發送記錄到 session log

#### 4c. AI 控制列狀態同步
- 從 AIVoiceChannelStrip 提取的功能需保持與 WebSocket 狀態同步
- mic toggle、interrupt、force submit 功能不變

**驗證**: 按下 prompt template → WebSocket 收到 text_input → AI 回應變化

---

### Phase 5: Persistence & Polish

**目標**: 持久化、preset 匯出支援、UI 打磨

**實作內容**:

#### 5a. Store Persist 擴展
- `magicDJStore` persist partialize 加入 `promptTemplates` 和 `storyPrompts`
- Store version bump（用於 migration）
- Migration function：舊版 store 自動載入 DEFAULT_PROMPT_TEMPLATES

#### 5b. Preset Import/Export 支援
- `TrackConfigPanel` 匯出格式擴展，包含 promptTemplates 和 storyPrompts
- 匯入時 merge 邏輯：自訂 template 匯入，預設 template 不覆蓋

#### 5c. Operation Log 擴展
- `OperationLog.action` 新增：`send_prompt_template` | `send_story_prompt`
- Session 匯出 JSON/CSV 包含 prompt 操作紀錄

#### 5d. Hotkey 支援（可選）
- 數字鍵 1-8 對應前 8 個 prompt template（AI 模式時）
- Shift + Enter 送出 story prompt 文字

**驗證**: 重新載入頁面後 prompt template 保持、preset 匯出/匯入正確

---

### Phase 6: Tests

**目標**: 撰寫單元測試確保功能正確性

**新增測試檔案**:

#### 6a. promptTemplateStore.test.ts
- CRUD 操作測試（add, update, remove, reorder）
- Default template 不可刪除
- Persist/rehydrate 測試

#### 6b. PromptTemplatePanel.test.tsx
- Render 測試：顯示所有 template
- Click 測試：觸發 onSendPrompt callback
- Disabled 狀態測試

#### 6c. StoryPromptPanel.test.tsx
- Render 測試：預設模板 + 輸入框
- Submit 測試：自訂文字送出
- 預設模板點擊測試

**目標覆蓋率**: 核心 store 邏輯 80%+

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MagicDJPage                                  │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐ │
│  │ magicDJStore  │   │ useWebSocket │   │ useMultiTrackPlayer     │ │
│  │ (Zustand)     │   │              │   │                         │ │
│  │ promptTemplates│  │ sendMessage  │   │ playTrack / stopTrack   │ │
│  │ storyPrompts  │   │ ('text_input')│  │                         │ │
│  └──────┬───────┘   └──────┬───────┘   └────────────┬────────────┘ │
│         │                  │                         │              │
│  ┌──────┴──────────────────┴─────────────────────────┴──────────┐  │
│  │                     DJControlPanel                            │  │
│  │                                                               │  │
│  │  ┌─ AI Mode ─────────────────────────────────────────────┐   │  │
│  │  │                                                        │   │  │
│  │  │  ┌──────────────────────────────────────────────────┐  │   │  │
│  │  │  │ AIControlBar (mic, status, interrupt, submit)    │  │   │  │
│  │  │  └──────────────────────────────────────────────────┘  │   │  │
│  │  │                                                        │   │  │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │   │  │
│  │  │  │Prompt  │ │Story   │ │ SFX    │ │ Music  │         │   │  │
│  │  │  │Template│ │Prompt  │ │Channel │ │Channel │         │   │  │
│  │  │  │Panel   │ │Panel   │ │Strip   │ │Strip   │         │   │  │
│  │  │  │        │ │        │ │        │ │        │         │   │  │
│  │  │  │[click] │ │[submit]│ │[play]  │ │[play]  │         │   │  │
│  │  │  │   ↓    │ │   ↓    │ │   ↓    │ │   ↓    │         │   │  │
│  │  │  │text_   │ │text_   │ │Web     │ │Web     │         │   │  │
│  │  │  │input   │ │input   │ │Audio   │ │Audio   │         │   │  │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘         │   │  │
│  │  └────────────────────────────────────────────────────────┘   │  │
│  │                                                               │  │
│  │  ┌─ Prerecorded Mode (unchanged) ─────────────────────────┐  │  │
│  │  │  SoundLibrary + ChannelBoard (4ch) + CueList           │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│         ↓ WebSocket text_input                                      │
│  ┌──────────────────────────────┐                                   │
│  │ Backend WebSocket Handler    │                                   │
│  │ _handle_text_input           │                                   │
│  │         ↓                    │                                   │
│  │ GeminiRealtimeService        │                                   │
│  │ .send_text(prompt)           │                                   │
│  │         ↓                    │                                   │
│  │ Gemini V2V WebSocket         │                                   │
│  │ client_content.turns[text]   │                                   │
│  └──────────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Prompt Template Flow

```
1. RD clicks "裝傻" button
2. PromptTemplateButton → onSendPrompt(template)
3. MagicDJPage.handleSendPromptTemplate(template)
   a. sendMessage('text_input', { text: template.prompt })
   b. store.setLastSentPrompt(template.id)
   c. store.logOperation('send_prompt_template', { templateId, name })
4. Backend: interaction_handler._handle_text_input
5. Backend: gemini_realtime.send_text(prompt)
6. Gemini processes text as user input
7. Gemini adjusts response behavior accordingly
8. AI audio response streams back through existing pipeline
```

### Story Prompt Flow

```
1. RD selects "魔法森林" or types custom text
2. StoryPromptPanel → onSendStoryPrompt(text)
3. MagicDJPage.handleSendStoryPrompt(text)
   a. sendMessage('text_input', { text })
   b. store.logOperation('send_story_prompt', { text })
4. Same backend pipeline as Prompt Template
5. AI transitions to new story scenario
```

### Concurrent Audio Flow (AI + SFX + Music)

```
AI Voice: WebSocket audio → AudioContext (AI channel)
SFX:      useMultiTrackPlayer → AudioContext (SFX channel)
Music:    useMultiTrackPlayer → AudioContext (Music channel)

All three can play simultaneously — independent audio channels
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Gemini 忽略 text_input prompt 指令 | AI 不改變行為 | 調整 prompt 措辭，加入更強指令語氣；提供 prompt 編輯功能讓 RD 微調 |
| AI 模式佈局重構破壞 prerecorded 模式 | 預錄模式無法使用 | 兩種模式獨立分支 render，CI 測試覆蓋兩種模式 |
| localStorage persist migration 失敗 | 舊資料遺失 | 使用 version 升級 + fallback 載入 DEFAULT_PROMPT_TEMPLATES |
| 太多 prompt template 按鈕影響 UX | 按鈕找不到 | 限制顯示區域可滾動，提供搜尋/分類（Phase 2 可擴展） |

## Generated Artifacts

- [research.md](./research.md) — Phase 0 研究成果
- [data-model.md](./data-model.md) — Phase 1 資料模型
- [quickstart.md](./quickstart.md) — Phase 1 快速開始指南
- contracts/ — N/A（純前端功能）
