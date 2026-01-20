# Tasks: Async Job Management

**Input**: Design documents from `/docs/features/007-async-job-mgmt/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/jobs-api.yaml ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**TDD Compliance**: Each user story includes test tasks that MUST be completed BEFORE implementation tasks (Constitution Principle I).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and core entity setup

- [ ] T001 Create Alembic migration for `jobs` table in `backend/alembic/versions/xxx_add_jobs_table.py`
- [ ] T002 [P] Create JobStatus enum (PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED) in `backend/src/domain/entities/job.py`
- [ ] T003 [P] Create JobType enum in `backend/src/domain/entities/job.py`
- [ ] T004 Create Job entity with all attributes in `backend/src/domain/entities/job.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repository interface, test infrastructure, and schemas that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Test Infrastructure

- [ ] T005 [P] Setup pytest and pytest-asyncio configuration in `backend/pyproject.toml`
- [ ] T006 [P] Create test fixtures for database session in `backend/tests/conftest.py`
- [ ] T007 [P] Create test fixtures for Job factory in `backend/tests/conftest.py`

### Core Infrastructure

- [ ] T008 Define JobRepository interface (abstract) in `backend/src/domain/repositories/job_repository.py`
- [ ] T009 Implement JobRepositoryImpl (PostgreSQL) in `backend/src/infrastructure/persistence/job_repository_impl.py`
- [ ] T010 [P] Create Pydantic schemas (CreateJobRequest, JobResponse, JobDetailResponse) in `backend/src/presentation/api/schemas/job_schemas.py`
- [ ] T011 [P] Create error response schemas (ErrorResponse, error codes) in `backend/src/presentation/api/schemas/error_schemas.py`
- [ ] T012 Register repository in dependency injection container
- [ ] T013 [P] Create frontend API client skeleton in `frontend/src/services/jobApi.ts`
- [ ] T014 [P] Create Zustand store skeleton in `frontend/src/stores/jobStore.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 背景合成工作提交 (Priority: P1) 🎯 MVP

**Goal**: 使用者可以提交 TTS 合成工作，系統在背景執行，不依賴瀏覽器連線

**Independent Test**: 提交工作後關閉瀏覽器，稍後返回確認工作已完成

**Functional Requirements**: FR-001, FR-002, FR-003, FR-004, FR-015

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Contract test for POST /jobs endpoint (201 response) in `backend/tests/contract/test_jobs_api.py`
- [ ] T016 [P] [US1] Contract test for job concurrent limit (429 response) in `backend/tests/contract/test_jobs_api.py`
- [ ] T017 [US1] Integration test for job submission → background execution → completion flow in `backend/tests/integration/test_job_workflow.py`

### Backend Implementation

- [ ] T018 [US1] Implement `create_job()` in JobService `backend/src/application/services/job_service.py`
- [ ] T019 [US1] Implement concurrent job limit check (max 3) in JobService
- [ ] T020 [US1] Create POST /jobs endpoint in `backend/src/presentation/api/jobs_router.py`
- [ ] T021 [US1] Implement job worker polling loop in `backend/src/infrastructure/workers/job_worker.py`
- [ ] T022 [US1] Implement `SELECT ... FOR UPDATE SKIP LOCKED` for job pickup in worker
- [ ] T023 [US1] Integrate with existing `multi_role_tts_service` for TTS execution
- [ ] T024 [US1] Implement retry logic (max 3, exponential backoff: 5s, 10s, 20s) in worker
- [ ] T025 [US1] Implement result storage (audio_file_id, result_metadata) on completion
- [ ] T026 [US1] Register worker as FastAPI lifespan background task

### Frontend Implementation

- [ ] T027 [P] [US1] Implement `createJob()` API call in `frontend/src/services/jobApi.ts`
- [ ] T028 [US1] Add `submitJob` action to Zustand store in `frontend/src/stores/jobStore.ts`
- [ ] T029 [US1] Create job submission UI integration (connect to existing Multi-Role TTS form)

**Checkpoint**: User Story 1 should be fully functional - jobs submitted run in background

---

## Phase 4: User Story 2 - 工作狀態追蹤 (Priority: P1) 🎯 MVP

**Goal**: 使用者可以查看所有工作及其狀態（pending, processing, completed, failed）

**Independent Test**: 查看工作列表，確認狀態顯示正確

**Functional Requirements**: FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-016, FR-017, FR-018, FR-019

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T030 [P] [US2] Contract test for GET /jobs (list with pagination) in `backend/tests/contract/test_jobs_api.py`
- [ ] T031 [P] [US2] Contract test for GET /jobs/{id} (detail) in `backend/tests/contract/test_jobs_api.py`
- [ ] T032 [US2] Integration test for timeout monitoring (10 min → failed) in `backend/tests/integration/test_job_timeout.py`
- [ ] T033 [US2] Integration test for system restart recovery (processing → failed) in `backend/tests/integration/test_job_recovery.py`

### Backend Implementation

- [ ] T034 [US2] Implement `get_job()` in JobService `backend/src/application/services/job_service.py`
- [ ] T035 [US2] Implement `list_jobs()` with status filter in JobService
- [ ] T036 [US2] Create GET /jobs endpoint (list with pagination) in `backend/src/presentation/api/jobs_router.py`
- [ ] T037 [US2] Create GET /jobs/{id} endpoint (detail) in `backend/src/presentation/api/jobs_router.py`
- [ ] T038 [US2] Implement timeout monitoring (10 min) background task in worker
- [ ] T039 [US2] Implement system startup recovery (mark processing→failed) in FastAPI lifespan

### Frontend Implementation

- [ ] T040 [P] [US2] Implement `getJob()` and `listJobs()` API calls in `frontend/src/services/jobApi.ts`
- [ ] T041 [P] [US2] Create JobStatus badge component in `frontend/src/components/jobs/JobStatus.tsx`
- [ ] T042 [US2] Create JobList component with status filter in `frontend/src/components/jobs/JobList.tsx`
- [ ] T043 [US2] Create JobDetail component in `frontend/src/components/jobs/JobDetail.tsx`
- [ ] T044 [US2] Implement polling (5s interval) with TanStack Query in JobList
- [ ] T045 [US2] Create JobsPage integrating JobList and JobDetail in `frontend/src/pages/JobsPage.tsx`
- [ ] T046 [US2] Add jobs state and actions to Zustand store `frontend/src/stores/jobStore.ts`

**Checkpoint**: User Stories 1 AND 2 should both work - jobs can be submitted and tracked

---

## Phase 5: User Story 3 - 歷史記錄與結果下載 (Priority: P2)

**Goal**: 使用者可以查看 30 天內完成的工作，並下載/播放音檔

**Independent Test**: 找到歷史完成工作並下載音檔

**Functional Requirements**: FR-011, FR-012, FR-013, FR-020, FR-021

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T047 [P] [US3] Contract test for GET /jobs/{id}/download (200 audio stream) in `backend/tests/contract/test_jobs_api.py`
- [ ] T048 [US3] Contract test for download non-completed job (404 response) in `backend/tests/contract/test_jobs_api.py`

### Backend Implementation

- [ ] T049 [US3] Create GET /jobs/{id}/download endpoint in `backend/src/presentation/api/jobs_router.py`
- [ ] T050 [US3] Implement audio file streaming from storage in download endpoint
- [ ] T051 [US3] Implement data retention cleanup task (30 days) in worker

### Frontend Implementation

- [ ] T052 [P] [US3] Implement `getDownloadUrl()` in `frontend/src/services/jobApi.ts`
- [ ] T053 [US3] Add download button to JobDetail component
- [ ] T054 [US3] Add audio player to JobDetail component for completed jobs
- [ ] T055 [US3] Display original input parameters in JobDetail (provider, turns, voices)

**Checkpoint**: All P1 and P2 stories complete - full job lifecycle with download

---

## Phase 6: User Story 4 - 工作取消 (Priority: P3)

**Goal**: 使用者可以取消「等待中」狀態的工作

**Independent Test**: 提交工作後立即取消

**Functional Requirements**: FR-014

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T056 [P] [US4] Contract test for DELETE /jobs/{id} (200 cancelled) in `backend/tests/contract/test_jobs_api.py`
- [ ] T057 [US4] Contract test for cancel non-pending job (409 conflict) in `backend/tests/contract/test_jobs_api.py`

### Backend Implementation

- [ ] T058 [US4] Implement `cancel_job()` in JobService `backend/src/application/services/job_service.py`
- [ ] T059 [US4] Create DELETE /jobs/{id} endpoint in `backend/src/presentation/api/jobs_router.py`
- [ ] T060 [US4] Return 409 Conflict if job is not in pending status

### Frontend Implementation

- [ ] T061 [P] [US4] Implement `cancelJob()` API call in `frontend/src/services/jobApi.ts`
- [ ] T062 [US4] Add cancel button to JobList (only for pending jobs)
- [ ] T063 [US4] Show confirmation dialog before cancellation

**Checkpoint**: All user stories complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, documentation, and cleanup

- [ ] T064 [P] Add comprehensive error handling to all API endpoints
- [ ] T065 [P] Add logging for job lifecycle events (submit, start, complete, fail, cancel)
- [ ] T066 [P] Update quickstart.md with actual usage examples after testing
- [ ] T067 Run end-to-end validation using quickstart.md flow
- [ ] T068 Code cleanup and ensure `make check` passes

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational + Test Infrastructure) ← BLOCKS all user stories
    ↓
┌───────────────────────────────────────────────┐
│  Phase 3 (US1-P1) ←→ Phase 4 (US2-P1)        │ (can run in parallel)
└───────────────────────────────────────────────┘
    ↓
Phase 5 (US3-P2)
    ↓
Phase 6 (US4-P3)
    ↓
Phase 7 (Polish)
```

### User Story Dependencies

- **User Story 1 (P1)**: After Phase 2 - No dependencies on other stories
- **User Story 2 (P1)**: After Phase 2 - Reads jobs from US1 but independently testable
- **User Story 3 (P2)**: After US1 complete (needs completed jobs with audio)
- **User Story 4 (P3)**: After US1 complete (needs pending jobs to cancel)

### TDD Workflow Within Each User Story

1. **Write tests FIRST** (T0XX tests) - ensure they FAIL
2. **Implement backend** - make tests PASS
3. **Implement frontend** - integrate with working backend
4. **Verify checkpoint** - all tests green, feature works end-to-end

### Parallel Opportunities

```bash
# Phase 1 parallel tasks:
T002: Create JobStatus enum
T003: Create JobType enum

# Phase 2 parallel tasks:
T005: Setup pytest configuration
T006: Create test fixtures (db session)
T007: Create test fixtures (job factory)
T010: Create Pydantic schemas
T011: Create error schemas
T013: Create frontend API client skeleton
T014: Create Zustand store skeleton

# Phase 3 (US1) parallel test tasks:
T015: Contract test POST /jobs (201)
T016: Contract test POST /jobs (429)

# Phase 4 (US2) parallel test tasks:
T030: Contract test GET /jobs
T031: Contract test GET /jobs/{id}

# Phase 5 (US3) parallel test task:
T047: Contract test GET /jobs/{id}/download

# Phase 6 (US4) parallel test task:
T056: Contract test DELETE /jobs/{id}
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup (database, entities)
2. Complete Phase 2: Foundational + Test Infrastructure
3. Complete Phase 3: User Story 1 (tests → implementation)
4. Complete Phase 4: User Story 2 (tests → implementation)
5. **STOP and VALIDATE**: All tests green, job submission → tracking → completion flow works
6. Deploy/demo if ready

### TDD Cycle Per User Story

```
Write Tests (Red) → Implement (Green) → Refactor → Checkpoint
```

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 → Jobs can be submitted (MVP start)
3. US2 → Jobs can be tracked (MVP complete!)
4. US3 → Results downloadable (enhanced experience)
5. US4 → Jobs cancelable (full control)

---

## Test Coverage Summary

| User Story | Contract Tests | Integration Tests | Total |
|------------|----------------|-------------------|-------|
| US1 | 2 (T015, T016) | 1 (T017) | 3 |
| US2 | 2 (T030, T031) | 2 (T032, T033) | 4 |
| US3 | 2 (T047, T048) | 0 | 2 |
| US4 | 2 (T056, T057) | 0 | 2 |
| **Total** | **8** | **3** | **11** |

---

## Notes

- [P] tasks = different files, no dependencies
- Backend uses Clean Architecture: domain → application → infrastructure → presentation
- Frontend uses Zustand for state, TanStack Query for server state
- All timestamps in UTC
- Polling interval: 5s for UI, 30s for timeout monitoring
- Retry backoff: 5s, 10s, 20s (exponential)
- Job timeout: 10 minutes
- Data retention: 30 days
- **TDD**: Tests MUST fail before implementation begins (Constitution Principle I)
