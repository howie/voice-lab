# Tasks: API Quota Error Handling

**Input**: Design documents from `/docs/features/014-quota-error-handling/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included based on constitution TDD principle (I. Test-Driven Development)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Domain layer foundational classes that all user stories depend on

- [x] T001 Add `QuotaExceededError` class in `backend/src/domain/errors.py`
- [x] T002 Add `ProviderQuotaInfo` class in `backend/src/domain/errors.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Error middleware and handler that MUST be complete before user stories can be tested end-to-end

**⚠️ CRITICAL**: No user story integration testing can occur until this phase is complete

- [x] T003 Add `QuotaExceededError` handler in `backend/src/presentation/api/middleware/error_handler.py`
- [x] T004 Add `Retry-After` header support in quota error handler

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 看到友善的錯誤訊息 (Priority: P1) 🎯 MVP

**Goal**: 使用者在 API 配額用盡時看到清楚的中文說明，知道是哪個服務出了問題

**Independent Test**: 呼叫任一已達配額的 provider API，確認回應包含 `provider_display_name` 和中文訊息

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T005 [P] [US1] Unit test for `QuotaExceededError` in `backend/tests/unit/domain/test_quota_errors.py`
- [x] T006 [P] [US1] Unit test for `ProviderQuotaInfo.get()` in `backend/tests/unit/domain/test_quota_errors.py`
- [x] T007 [P] [US1] Unit test for error handler quota response in `backend/tests/unit/presentation/test_error_handler.py`

### Implementation for User Story 1 - TTS Providers

- [x] T008 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/tts/gemini_tts.py`
- [x] T009 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/tts/elevenlabs_tts.py`
- [x] T010 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/tts/azure_tts.py`
- [x] T011 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/tts/gcp_tts.py`
- [x] T012 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/tts/voai_tts.py`

### Implementation for User Story 1 - STT Providers

- [x] T013 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/stt/whisper_stt.py`
- [x] T014 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/stt/deepgram_stt.py`
- [x] T015 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/stt/azure_stt.py`
- [x] T016 [P] [US1] Add 429 quota detection in `backend/src/infrastructure/providers/stt/gcp_stt.py`

**Checkpoint**: At this point, backend returns friendly Chinese quota error messages for all providers

---

## Phase 4: User Story 2 - 獲得解決建議 (Priority: P2)

**Goal**: 使用者在配額超限時得到具體的解決步驟，例如去哪裡查看用量或升級方案

**Independent Test**: 呼叫任一已達配額的 API，確認回應包含 `suggestions` 陣列和 `help_url`

### Tests for User Story 2

- [x] T017 [P] [US2] Unit test for suggestion content per provider in `backend/tests/unit/domain/test_quota_errors.py`

### Implementation for User Story 2 - Frontend

- [x] T018 [P] [US2] Add TypeScript types in `frontend/src/lib/error-types.ts`
- [x] T019 [US2] Add quota error pattern to `ERROR_PATTERNS` in `frontend/src/components/multi-role-tts/ErrorDisplay.tsx`
- [x] T020 [US2] Add suggestions display with clickable help links in `frontend/src/components/multi-role-tts/ErrorDisplay.tsx`
- [x] T021 [US2] Add quota error card styling in `frontend/src/components/multi-role-tts/ErrorDisplay.tsx`

**Checkpoint**: Users see actionable suggestions and clickable links in quota errors

---

## Phase 5: User Story 3 - 知道何時可以重試 (Priority: P3)

**Goal**: 使用者知道大概要等多久才能再次使用，或是可以切換到其他供應商

**Independent Test**: 呼叫已達配額的 API，確認回應包含 `retry_after` 秒數，且前端顯示人性化的等待時間

### Tests for User Story 3

- [x] T022 [P] [US3] Unit test for retry_after parsing in `backend/tests/unit/domain/test_quota_errors.py`
- [x] T023 [P] [US3] Frontend test for retry display in `frontend/src/lib/__tests__/errorMessages.test.ts`

### Implementation for User Story 3

- [x] T024 [US3] Add retry countdown display in `frontend/src/components/multi-role-tts/ErrorDisplay.tsx`
- [x] T025 [US3] Add "switch provider" button/link in `frontend/src/components/multi-role-tts/ErrorDisplay.tsx`
- [x] T026 [US3] Format retry_after to human-readable Chinese (e.g., "約 1 小時後可重試") in `frontend/src/lib/error-messages.ts`

**Checkpoint**: Users see retry timing and can easily switch providers

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements across all user stories

- [x] T027 [P] Run `make check` and fix any linting/type issues
- [x] T028 [P] Run all tests with `pytest backend/tests -v`
- [x] T029 Validate against `contracts/error-response.yaml` schema
- [x] T030 Update `quickstart.md` with actual test commands and examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS user story testing
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
  - US1 backend work can proceed while US2/US3 frontend work is parallel
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Backend-only, can start after Phase 2
- **User Story 2 (P2)**: Frontend, depends on US1 backend for integration testing
- **User Story 3 (P3)**: Frontend, depends on US1 backend for integration testing

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core detection before display
- Backend before frontend (for integration testing)

### Parallel Opportunities

**Phase 1** (2 tasks): Both can run in parallel after reading errors.py

**Phase 2** (2 tasks): Sequential - T003 before T004

**US1 Provider Tasks** (9 tasks):
- All TTS providers (T008-T012) can run in parallel
- All STT providers (T013-T016) can run in parallel
- TTS and STT groups can run in parallel

**US2 Frontend** (4 tasks): T018 parallel, then T019→T020→T021 sequential

**US3** (5 tasks): Tests parallel, then frontend implementation

---

## Parallel Example: User Story 1 TTS/STT Detection

```bash
# Launch all TTS provider 429 detection tasks together:
Task: "Add 429 quota detection in backend/src/infrastructure/providers/tts/gemini_tts.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/tts/elevenlabs_tts.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/tts/azure_tts.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/tts/gcp_tts.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/tts/voai_tts.py"

# Launch all STT provider 429 detection tasks together:
Task: "Add 429 quota detection in backend/src/infrastructure/providers/stt/whisper_stt.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/stt/deepgram_stt.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/stt/azure_stt.py"
Task: "Add 429 quota detection in backend/src/infrastructure/providers/stt/gcp_stt.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T004)
3. Complete Phase 3: User Story 1 tests (T005-T007)
4. Complete Phase 3: User Story 1 TTS providers (T008-T012)
5. Complete Phase 3: User Story 1 STT providers (T013-T016)
6. **STOP and VALIDATE**: Test with a quota-exceeded API key
7. Deploy/demo if ready - users can now see friendly error messages!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Backend returns friendly Chinese errors (MVP!)
3. Add User Story 2 → Frontend shows suggestions and help links
4. Add User Story 3 → Frontend shows retry timing
5. Each story adds value without breaking previous stories

---

## Summary

| Category | Count |
|----------|-------|
| **Total Tasks** | 30 |
| **Setup Tasks** | 2 |
| **Foundational Tasks** | 2 |
| **US1 Tasks (P1 - MVP)** | 12 |
| **US2 Tasks (P2)** | 5 |
| **US3 Tasks (P3)** | 5 |
| **Polish Tasks** | 4 |
| **Parallelizable Tasks** | 20 |

### MVP Scope

- **Recommended MVP**: Complete through Phase 3 (User Story 1)
- **MVP Deliverable**: Backend returns friendly Chinese quota error messages for all 9 providers
- **MVP Task Count**: 16 tasks (T001-T016)

---

## Notes

- [P] tasks = different files, no dependencies
- [US*] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Run `make check` frequently to catch lint/type issues early
