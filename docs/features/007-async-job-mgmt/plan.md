# Implementation Plan: Async Job Management

**Branch**: `007-async-job-mgmt` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/007-async-job-mgmt/spec.md`

## Summary

將 Multi-Role TTS 合成從同步請求-回應模式改為背景工作處理，支援：
- 背景執行長時間合成任務（不依賴瀏覽器連線）
- 工作狀態追蹤 (pending/processing/completed/failed)
- 歷史記錄查詢與下載（30 天保留）
- TTS Provider 呼叫失敗自動重試（最多 3 次）

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, SQLAlchemy 2.0+, Redis 5.0+, Pydantic 2.0+
- Frontend: React 18+, Zustand, TanStack Query
**Storage**: PostgreSQL (工作元資料), Local filesystem / S3 (音檔儲存)
**Testing**: pytest, pytest-asyncio (Backend), vitest (Frontend)
**Target Platform**: Linux server (Docker), Web browser
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- 工作提交回應 < 500ms
- 狀態查詢回應 < 200ms
- 支援每用戶 3 個並發工作
**Constraints**:
- 工作逾時上限 10 分鐘
- 狀態更新延遲 ≤ 30 秒
- 30 天資料保留
**Scale/Scope**: 單一用戶環境，預期工作量適中

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate (2026-01-20)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ✅ Pass | 將先撰寫 contract/integration tests，再實作 |
| II. Unified API Abstraction | ✅ Pass | 使用現有 TTS 抽象層，Job 不影響 Provider 介面 |
| III. Performance Benchmarking | ✅ Pass | 將包含 Job 處理延遲基準測試 |
| IV. Documentation First | ✅ Pass | 先完成 quickstart.md 和 API contracts |
| V. Clean Architecture | ✅ Pass | Job entity 放 domain/，Job worker 放 infrastructure/ |

**Gate Status**: ✅ PASSED

### Post-Phase 1 Re-check (2026-01-20)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ✅ Pass | 測試結構已規劃於 project structure |
| II. Unified API Abstraction | ✅ Pass | Job 透過 JobService 呼叫現有 multi_role_tts_service |
| III. Performance Benchmarking | ✅ Pass | 效能指標已定義（提交 <500ms, 查詢 <200ms） |
| IV. Documentation First | ✅ Pass | quickstart.md, contracts/jobs-api.yaml 已完成 |
| V. Clean Architecture | ✅ Pass | 分層設計符合規範：domain → application → infrastructure → presentation |

**Gate Status**: ✅ PASSED - 可進入 Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
docs/features/007-async-job-mgmt/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── jobs-api.yaml    # OpenAPI spec for Jobs API
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── job.py           # Job, JobStatus entities
│   │   └── repositories/
│   │       └── job_repository.py # JobRepository interface
│   ├── application/
│   │   └── services/
│   │       └── job_service.py    # Job orchestration service
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   └── job_repository_impl.py  # PostgreSQL implementation
│   │   └── workers/
│   │       └── job_worker.py     # Background job processor
│   └── presentation/
│       └── api/
│           └── jobs_router.py    # REST API endpoints
├── alembic/
│   └── versions/
│       └── xxx_add_jobs_table.py # Database migration
└── tests/
    ├── contract/
    │   └── test_job_repository.py
    ├── integration/
    │   └── test_job_workflow.py
    └── unit/
        └── test_job_service.py

frontend/
├── src/
│   ├── services/
│   │   └── jobApi.ts             # Job API client
│   ├── stores/
│   │   └── jobStore.ts           # Zustand store for jobs
│   ├── components/
│   │   └── jobs/
│   │       ├── JobList.tsx       # Job list component
│   │       ├── JobDetail.tsx     # Job detail component
│   │       └── JobStatus.tsx     # Status badge component
│   └── pages/
│       └── JobsPage.tsx          # Jobs management page
└── tests/
    └── components/
        └── jobs/
            └── JobList.test.tsx
```

**Structure Decision**: 採用現有的 Web application 結構（backend/ + frontend/），遵循 Clean Architecture 分層設計。

**Constitution Alignment Note**: 憲章 V (Clean Architecture) 定義的 `core/adapters/cli` 結構適用於 CLI 工具型專案。本功能為 Web application，採用等效的 `domain/application/infrastructure/presentation` 分層：
- `domain/` ≈ `core/`：領域模型與介面定義
- `infrastructure/` ≈ `adapters/`：外部服務實作
- `presentation/` ≈ `cli/`：使用者介面（此處為 REST API）
- `application/`：應用服務層（協調領域與基礎設施）

此變體符合憲章「依賴方向由外向內」的核心原則。

## Complexity Tracking

> 無違規項目需要追蹤

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Phase 0: Research ✅ COMPLETED

**Output**: [research.md](./research.md)

### 關鍵決策摘要

| 決策項目 | 選擇 | 理由 |
|----------|------|------|
| 背景工作方案 | PostgreSQL Queue (pg-boss) | 無額外基礎設施，ACID 持久化 |
| 狀態儲存 | 標準化欄位 + JSONB | 查詢效能 + 彈性 |
| 逾時監控 | 背景輪詢（30 秒） | 簡單可靠，符合延遲要求 |
| 重試機制 | Exponential Backoff (5s, 10s, 20s) | 業界標準實踐 |
| 系統重啟 | 啟動時標記失敗 | 符合 FR-018/FR-019 規格 |

---

## Phase 1: Design & Contracts ✅ COMPLETED

**Outputs**:
- [data-model.md](./data-model.md) - 資料模型設計
- [contracts/jobs-api.yaml](./contracts/jobs-api.yaml) - OpenAPI 規格
- [quickstart.md](./quickstart.md) - 快速開始指南

### 設計摘要

- **Job Entity**: 21 個欄位，支援完整生命週期追蹤
- **API Endpoints**: 5 個 REST 端點（CRUD + download）
- **狀態機**: 5 個狀態，4 種轉換路徑

---

## Phase 2: Tasks ✅ COMPLETED

**Output**: [tasks.md](./tasks.md)

### 任務摘要

- **總任務數**: 68 個任務 (T001-T068)
- **測試任務**: 11 個 (Contract: 8, Integration: 3)
- **階段分布**:
  - Phase 1 Setup: 4 tasks
  - Phase 2 Foundational: 10 tasks (含 3 個測試基礎設施)
  - Phase 3 US1 (P1): 15 tasks (含 3 個測試)
  - Phase 4 US2 (P1): 17 tasks (含 4 個測試)
  - Phase 5 US3 (P2): 9 tasks (含 2 個測試)
  - Phase 6 US4 (P3): 8 tasks (含 2 個測試)
  - Phase 7 Polish: 5 tasks

**TDD Compliance**: ✅ 符合憲章原則 I（測試先行）

---

## Next: Implementation

執行 `/speckit.implement` 開始實作
