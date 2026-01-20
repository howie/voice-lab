# Implementation Plan: Real-time Voice Interaction Testing Module

**Branch**: `004-interaction-module` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/004-interaction-module/spec.md`

## Summary

本功能實現端對端的即時語音代理互動測試平台，支援兩種主要模式：
1. **Realtime API 模式**：透過 OpenAI Realtime API 實現語音到語音的即時互動
2. **Cascade 模式**：串聯現有的 STT (Phase 3) → LLM (Gemini/OpenAI) → TTS (Phase 1) 作為 fallback

核心技術方案：
- 前端使用 WebRTC 進行麥克風串流
- 後端使用 WebSocket 進行即時雙向通訊
- 整合現有的 BYOL 憑證管理系統
- 結構化日誌與基本指標監控

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, SQLAlchemy 2.0+, WebSockets, OpenAI SDK, Google GenAI SDK
- Frontend: React 18+, Vite 5+, Zustand, TanStack Query, WaveSurfer.js
**Storage**: PostgreSQL 16 (對話歷史), Local filesystem (音訊檔案), Redis 7 (快取)
**Testing**: pytest + pytest-asyncio (Backend), Vitest (Frontend)
**Target Platform**: Web browser (Chrome, Firefox, Safari - 支援 WebRTC)
**Project Type**: Web application (frontend + backend)
**Performance Goals**:
- Realtime API: 端對端延遲 < 1 秒
- Cascade 模式: 端對端延遲 < 3 秒
- 打斷偵測: < 500ms
**Constraints**:
- 支援 30 分鐘連續對話
- 歷史記錄載入 < 2 秒 (100 筆)
- 延遲測量誤差 < 50ms
**Scale/Scope**: 單一使用者測試工具，非多租戶生產系統

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (Phase 0)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-Driven Development | ✅ Pass | 將為 WebSocket handlers、串流處理、延遲測量撰寫 contract tests |
| II. Unified API Abstraction | ✅ Pass | 設計統一的 InteractionMode 介面，涵蓋 Realtime API 和 Cascade 模式 |
| III. Performance Benchmarking | ✅ Pass | FR-005/006 要求延遲測量，SC-002~004 定義效能目標 |
| IV. Documentation First | ✅ Pass | 將產出 quickstart.md、API 合約文件 |
| V. Clean Architecture | ✅ Pass | 遵循現有 domain/application/infrastructure/presentation 分層 |

**Gate Result**: ✅ PASS - 所有原則符合，可進入 Phase 0

### Post-Design Check (Phase 1 完成後)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-Driven Development | ✅ Pass | data-model.md 定義清晰的實體結構，可直接轉換為 contract tests；WebSocket 協議已定義完整訊息格式 |
| II. Unified API Abstraction | ✅ Pass | `domain/services/interaction/base.py` 定義統一 InteractionMode 介面；LLM 服務層 `domain/services/llm/base.py` 抽象化 OpenAI/Gemini |
| III. Performance Benchmarking | ✅ Pass | LatencyMetrics 實體設計完整，支援 STT/LLM/TTS 分段延遲追蹤；WebSocket 協議包含 `response_ended.latency` 數據 |
| IV. Documentation First | ✅ Pass | 已產出 quickstart.md、websocket-api.md、rest-api.yaml；research.md 記錄所有技術決策 |
| V. Clean Architecture | ✅ Pass | 遵循 domain/application/infrastructure/presentation 分層；entities、services、repositories 分離明確 |

**Post-Design Gate Result**: ✅ PASS - 所有原則持續符合，設計與憲章一致

## Project Structure

### Documentation (this feature)

```text
docs/features/004-interaction-module/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── websocket-api.md
│   └── rest-api.yaml
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── interaction_session.py      # 新增：對話會話實體
│   │   │   ├── conversation_turn.py        # 新增：對話回合實體
│   │   │   └── system_prompt_template.py   # 新增：提示詞模板實體
│   │   ├── repositories/
│   │   │   └── interaction_repository.py   # 新增：互動記錄儲存庫
│   │   └── services/
│   │       ├── interaction/                # 新增：互動服務模組
│   │       │   ├── __init__.py
│   │       │   ├── base.py                 # 統一介面定義
│   │       │   ├── realtime_mode.py        # OpenAI Realtime 實作
│   │       │   ├── cascade_mode.py         # STT→LLM→TTS 實作
│   │       │   └── latency_tracker.py      # 延遲追蹤器
│   │       └── llm/                        # 新增：LLM 服務模組
│   │           ├── __init__.py
│   │           ├── base.py                 # LLM 統一介面
│   │           ├── openai_provider.py      # OpenAI GPT-4o
│   │           └── gemini_provider.py      # Google Gemini
│   ├── application/
│   │   └── use_cases/
│   │       └── interaction/                # 新增：互動用例
│   │           ├── start_session.py
│   │           ├── process_audio.py
│   │           └── end_session.py
│   ├── infrastructure/
│   │   └── websocket/                      # 新增：WebSocket 處理
│   │       └── interaction_handler.py
│   └── presentation/
│       └── api/
│           ├── interaction_router.py       # 新增：互動 REST API
│           └── ws_router.py                # 新增：WebSocket 路由
└── tests/
    ├── contract/
    │   └── interaction/                    # 新增：互動合約測試
    ├── integration/
    │   └── test_interaction_flow.py        # 新增：整合測試
    └── unit/
        └── interaction/                    # 新增：單元測試

frontend/
├── src/
│   ├── components/
│   │   └── interaction/                    # 新增：互動元件
│   │       ├── InteractionPanel.tsx        # 主互動面板
│   │       ├── ModeSelector.tsx            # 模式選擇器
│   │       ├── AudioVisualizer.tsx         # 音訊視覺化
│   │       ├── LatencyDisplay.tsx          # 延遲顯示
│   │       ├── SystemPromptEditor.tsx      # 提示詞編輯器
│   │       └── ConversationHistory.tsx     # 對話歷史
│   ├── hooks/
│   │   ├── useWebSocket.ts                 # 新增：WebSocket hook
│   │   ├── useMicrophone.ts                # 新增：麥克風 hook
│   │   └── useAudioPlayback.ts             # 新增：音訊播放 hook
│   ├── services/
│   │   └── interactionService.ts           # 新增：互動 API 服務
│   ├── stores/
│   │   └── interactionStore.ts             # 新增：互動狀態管理
│   ├── routes/
│   │   └── interaction/                    # 新增：互動路由
│   │       └── InteractionPage.tsx
│   └── types/
│       └── interaction.ts                  # 新增：互動型別定義
└── tests/
    └── interaction/                        # 新增：互動元件測試
```

**Structure Decision**: 採用現有的 Web application 架構 (frontend + backend)，遵循 Clean Architecture 分層，新增功能模組整合於現有結構中。

## Complexity Tracking

> 無憲章違規需要辯護

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
