# Implementation Plan: MVP Story Experience Interface (父母的故事體驗介面)

**Branch**: `016-story-experience-mvp` | **Date**: 2026-02-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/016-story-experience-mvp/spec.md`

## Summary

建立一個簡易的父母端故事體驗介面，讓父母在 MVP 測試現場透過輸入參數（年齡、教導內容、價值觀、情緒認知、喜愛角色、內容形式）產出客製化的故事或兒歌內容，確認後生成 TTS 音頻播放給孩子聆聽。本功能大幅複用現有 `hackthon-storypal` 分支的故事引擎和 prompt 模板，搭配既有 TTS 基礎設施，以 REST API（非 WebSocket）實現「輸入 → 生成 → 預覽 → 確認 → TTS → 播放」的線性流程。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+, Zustand, Shadcn/ui, TailwindCSS
**Storage**: 無新增持久化需求（MVP 為一次性體驗流程，前端狀態管理即可）；TTS 音頻使用現有 storage 機制
**Testing**: pytest (Backend), vitest/playwright (Frontend)
**Target Platform**: Web browser (Chrome 推薦，用於 MVP 現場測試)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 內容生成 < 30 秒（LLM），TTS 轉換 < 30 秒（300-500 字）
**Constraints**: 繁體中文限定、需穩定網路連線存取 LLM/TTS API
**Scale/Scope**: 單一使用者（現場測試用途），不需並發支援

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | PASS | 新增 API 端點需有對應測試 |
| II. Unified API Abstraction | PASS | 複用現有 LLM 和 TTS 統一抽象層 |
| III. Performance Benchmarking | PASS | MVP 不需正式基準測試，但需確保生成時間在可接受範圍 |
| IV. Documentation First | PASS | 本計劃文件即為文件先行產出 |
| V. Clean Architecture | PASS | 遵循現有 domain → infrastructure → presentation 分層 |

## Project Structure

### Documentation (this feature)

```text
docs/features/016-story-experience-mvp/
├── spec.md              # Feature specification
├── plan.md              # This file
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Implementation tasks (to be generated)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── story.py                    # 複用 + 擴充 StoryRequest 相關實體
│   │   └── services/
│   │       └── story/
│   │           ├── engine.py                # 複用 StoryEngine，新增 MVP 生成方法
│   │           ├── prompts.py               # 新增 MVP 專用 prompt 模板
│   │           └── __init__.py
│   ├── presentation/
│   │   └── api/
│   │       ├── routes/
│   │       │   └── story_experience.py      # 新增 MVP 故事體驗 API 路由
│   │       └── schemas/
│   │           └── story_experience_schemas.py  # 新增 MVP API schemas
│   └── application/
│       └── use_cases/
│           └── story_experience.py          # 新增 MVP use case（協調 LLM + TTS）
└── tests/
    ├── unit/
    │   └── test_story_experience.py
    └── integration/
        └── test_story_experience_api.py

frontend/
├── src/
│   ├── routes/
│   │   └── story-experience/
│   │       └── StoryExperiencePage.tsx       # MVP 主頁面
│   ├── components/
│   │   └── story-experience/
│   │       ├── ParentInputForm.tsx           # 父母輸入表單
│   │       ├── ContentPreview.tsx            # 內容預覽與確認
│   │       ├── StoryBranchSelector.tsx       # 故事走向選擇
│   │       ├── QAInteraction.tsx             # Q&A 互動
│   │       ├── TTSPlayer.tsx                 # TTS 音頻生成與播放
│   │       └── ParameterSummary.tsx          # 參數摘要顯示
│   ├── stores/
│   │   └── storyExperienceStore.ts          # Zustand 狀態管理
│   ├── services/
│   │   └── storyExperienceApi.ts            # API client
│   └── types/
│       └── story-experience.ts              # TypeScript 型別定義
└── tests/
    └── story-experience/
```

**Structure Decision**: 遵循現有 Voice Lab 的 web application 結構。Backend 在 domain/services/story/ 目錄下擴充，避免重複建立新的 story domain。Frontend 建立獨立的 story-experience 目錄，與現有 storypal 分開但可共享型別。

## Design Decisions

### DD-001: REST API 而非 WebSocket

**選擇**: 使用 REST API 進行內容生成和 TTS 轉換
**理由**: MVP 故事體驗是線性流程（輸入 → 生成 → 確認 → TTS），不需要即時雙向通訊。REST API 更簡單、更容易除錯，且能充分滿足需求。既有 StoryPal 的 WebSocket 用於即時互動故事，兩者使用場景不同。

### DD-002: 前端狀態管理，無 DB 持久化

**選擇**: 使用 Zustand 管理 MVP 會話狀態，不新增資料庫表
**理由**: MVP 為一次性體驗流程，不需要跨 session 持久化。父母填完參數、生成內容、播放音頻即完成。簡化架構，降低開發複雜度。TTS 音頻利用現有 storage 機制暫存即可。

### DD-003: 複用現有 StoryEngine 並擴充

**選擇**: 在現有 StoryEngine 基礎上新增 MVP 專用方法，而非建立全新引擎
**理由**: 現有引擎的 LLM 呼叫、JSON 解析、對話歷史管理等核心邏輯可直接複用。只需新增根據「父母輸入參數」（而非「故事模板」）生成內容的方法和對應 prompt。

### DD-004: MVP Prompt 模板設計

**選擇**: 新增專用的 prompt 模板，接受父母輸入參數作為變數
**理由**: 現有 prompt 基於 StoryTemplate（預設角色、場景），MVP 需要根據自由輸入（年齡、教導內容、喜愛角色等）動態生成。需要新的 prompt 結構但可複用安全性和格式規範。

### DD-005: TTS 整合方式

**選擇**: 透過現有 TTS synthesize API 進行音頻生成
**理由**: 系統已有完整的 TTS 基礎設施（多 provider 支援、語音選擇、音頻儲存）。MVP 只需在 use case 層呼叫現有 TTS 服務，將確認的文字內容轉為音頻即可。

## API Design

### Endpoints

```
POST /api/v1/story-experience/generate
  Body: { age, educational_content, values[], emotions[], favorite_character, content_type }
  Response: { content_id, content_type, text_content, parameters_summary }

POST /api/v1/story-experience/regenerate
  Body: { age, educational_content, values[], emotions[], favorite_character, content_type }
  Response: { content_id, content_type, text_content, parameters_summary }

POST /api/v1/story-experience/branch
  Body: { content_id, story_context, selected_branch? }
  Response: { branches: [{ id, description }] } | { content_id, text_content }

POST /api/v1/story-experience/qa
  Body: { content_id, story_context, question? }
  Response: { questions: [{ id, text }] } | { question, answer }

POST /api/v1/story-experience/tts
  Body: { text_content, voice_id, provider? }
  Response: { audio_url, duration_ms }
```

### Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Parent Input   │───▶│  /generate API   │───▶│  Content Preview  │
│   Form (FE)      │    │  (LLM Engine)    │    │  (FE)            │
└─────────────────┘    └──────────────────┘    └────────┬─────────┘
                                                         │
                                    ┌────────────────────┼────────────────────┐
                                    │                    │                    │
                                    ▼                    ▼                    ▼
                            ┌──────────────┐   ┌──────────────┐    ┌──────────────┐
                            │  /branch API │   │  /qa API     │    │  Confirm     │
                            │  (延伸故事)   │   │  (Q&A 互動)  │    │  Content     │
                            └──────────────┘   └──────────────┘    └──────┬───────┘
                                                                          │
                                                                          ▼
                                                                   ┌──────────────┐
                                                                   │  /tts API    │
                                                                   │  (音頻生成)   │
                                                                   └──────┬───────┘
                                                                          │
                                                                          ▼
                                                                   ┌──────────────┐
                                                                   │  Audio Player │
                                                                   │  (FE)        │
                                                                   └──────────────┘
```

## Frontend Component Architecture

```
StoryExperiencePage
├── Step 1: ParentInputForm
│   ├── AgeSelector (dropdown: 2-12 歲)
│   ├── EducationalContentInput (text input)
│   ├── ValuesSelector (multi-select chips)
│   ├── EmotionsSelector (multi-select chips)
│   ├── FavoriteCharacterInput (text input)
│   ├── ContentTypeSelector (radio: 故事/兒歌)
│   └── GenerateButton
│
├── Step 2: ContentPreview
│   ├── ParameterSummary (顯示使用的參數)
│   ├── ContentDisplay (故事文字/兒歌歌詞)
│   ├── RegenerateButton
│   ├── ConfirmButton → 進入 Step 3
│   ├── BranchButton → 進入 StoryBranchSelector
│   └── QAButton → 進入 QAInteraction
│
├── Step 2a: StoryBranchSelector (optional)
│   ├── BranchOptions (2-3 個走向選項卡片)
│   └── 選擇後回到 ContentPreview (附加延伸內容)
│
├── Step 2b: QAInteraction (optional)
│   ├── QuestionList (AI 生成的問題)
│   ├── CustomQuestionInput
│   ├── AnswerDisplay
│   └── GenerateQAAudioButton
│
└── Step 3: TTSPlayer
    ├── VoiceSelector (TTS 語音選擇)
    ├── GenerateAudioButton
    ├── AudioPlayer (播放/暫停/重播)
    └── ChangeVoiceButton (更換語音重新生成)
```

## Complexity Tracking

No constitution violations. The implementation follows established patterns.
