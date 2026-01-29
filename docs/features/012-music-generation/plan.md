# Implementation Plan: Music Generation (Mureka AI)

**Branch**: `012-music-generation` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/012-music-generation/spec.md`

## Summary

整合 Mureka AI 平台為 Voice Lab 提供音樂生成能力，包含純音樂（BGM）、歌曲（含人聲）和歌詞生成。採用直接 REST API 整合方式，透過 007-async-job-mgmt 機制處理非同步生成任務，並與 Magic DJ Controller 整合提供快速音軌生成入口。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+, httpx (Mureka API client)
**Storage**: PostgreSQL (任務元資料), Local filesystem / S3 (音檔儲存)
**Testing**: pytest, pytest-asyncio (Backend), Vitest (Frontend)
**Target Platform**: Linux server (Cloud Run), Web browser
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 任務提交響應 < 3 秒, 90% 生成任務 < 2 分鐘完成
**Constraints**: 每用戶最多 3 個並發任務, 每日/每月配額限制
**Scale/Scope**: 內部工具使用, 預估每日 < 100 個生成任務

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| **I. TDD** | ✅ Pass | 將為 Mureka API client 撰寫 contract tests，核心服務撰寫 unit tests |
| **II. Unified API Abstraction** | ✅ Pass | Mureka 作為新的 provider 實作 `MusicGenerationPort` 介面 |
| **III. Performance Benchmarking** | ✅ Pass | 記錄生成時間、成功率等指標 |
| **IV. Documentation First** | ✅ Pass | 本 plan 為文件先行，將產出 quickstart.md 和 API contracts |
| **V. Clean Architecture** | ✅ Pass | 遵循現有 domain/application/infrastructure 分層 |

## Project Structure

### Documentation (this feature)

```text
docs/features/012-music-generation/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (已完成，位於 011-music-generation/)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── music-api.yaml   # OpenAPI spec
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── models/
│   │   │   └── music.py           # MusicGenerationJob entity
│   │   ├── ports/
│   │   │   └── music_generation.py # MusicGenerationPort protocol
│   │   └── services/
│   │       └── music/
│   │           ├── __init__.py
│   │           ├── service.py     # MusicGenerationService
│   │           └── quota.py       # QuotaService
│   ├── infrastructure/
│   │   └── adapters/
│   │       └── mureka/
│   │           ├── __init__.py
│   │           ├── client.py      # MurekaAPIClient
│   │           └── adapter.py     # MurekaMusicAdapter
│   └── presentation/
│       └── api/
│           └── v1/
│               └── music/
│                   ├── __init__.py
│                   ├── router.py  # Music API routes
│                   └── schemas.py # Pydantic schemas
└── tests/
    ├── contract/
    │   └── music/
    │       └── test_mureka_contract.py
    ├── integration/
    │   └── music/
    │       └── test_music_generation.py
    └── unit/
        └── music/
            ├── test_service.py
            └── test_quota.py

frontend/
├── src/
│   ├── components/
│   │   └── music/
│   │       ├── MusicGenerationForm.tsx
│   │       ├── MusicJobStatus.tsx
│   │       ├── MusicPlayer.tsx
│   │       └── LyricsEditor.tsx
│   ├── routes/
│   │   └── music/
│   │       ├── index.tsx          # Music generation page
│   │       └── history.tsx        # Generation history
│   ├── services/
│   │   └── musicService.ts
│   ├── stores/
│   │   └── musicStore.ts
│   └── types/
│       └── music.ts
└── tests/
    └── music/
        └── MusicGenerationForm.test.tsx
```

**Structure Decision**: 採用現有的 Clean Architecture 分層結構，新增 `music` domain 相關模組。Mureka API client 實作於 `infrastructure/adapters/mureka/`。

## Complexity Tracking

> 無憲章違規需要說明

---

## Phase 0: Research Summary

研究已完成，詳見 [../011-music-generation/research.md](../011-music-generation/research.md)。

### 關鍵決策

| 決策 | 選擇 | 理由 | 替代方案 |
|------|------|------|----------|
| API 整合方式 | 直接 REST API | 與現有架構一致，可整合 async-job-mgmt | MCP Server (需額外運行環境) |
| 音樂服務提供者 | Mureka AI | 唯一提供官方 API 且商業授權明確 | Suno/Udio (無官方 API) |
| 任務管理 | 整合 007-async-job-mgmt | 統一任務管理體驗 | 獨立實作 (重複造輪) |
| 狀態通知 | 輪詢查詢 | 簡單可靠，與現有機制一致 | WebSocket/Push (額外複雜度) |

---

## Phase 1: Design Artifacts

### 1.1 Data Model

詳見 [data-model.md](./data-model.md)

### 1.2 API Contracts

詳見 [contracts/music-api.yaml](./contracts/music-api.yaml)

### 1.3 Quickstart Guide

詳見 [quickstart.md](./quickstart.md)

---

## Implementation Phases

### Phase 1: MVP (P1 Stories)

**目標**: 純音樂生成 + Magic DJ 整合

1. Backend: Mureka API client 實作
2. Backend: MusicGenerationService 核心邏輯
3. Backend: Music API endpoints
4. Backend: 整合 007-async-job-mgmt
5. Frontend: Music generation form
6. Frontend: Job status display
7. Frontend: Magic DJ 快速生成入口

### Phase 2: 完整功能 (P1 + P2 Stories)

**目標**: 歌曲生成 + 歌詞生成 + 歷史管理

1. Backend: 歌曲生成 API
2. Backend: 歌詞生成/延伸 API
3. Backend: 配額追蹤
4. Frontend: 歌曲生成 UI
5. Frontend: 歌詞編輯器
6. Frontend: 歷史記錄頁面

### Phase 3: 進階功能

**目標**: 模型選擇 + 風格模板

1. Frontend: 模型選擇 UI
2. Backend/Frontend: 風格模板
3. Magic DJ 深度整合

---

## Next Steps

1. 執行 `/speckit.tasks` 生成詳細任務清單
2. 開始 Phase 1 MVP 實作

---

*Last updated: 2026-01-29*
