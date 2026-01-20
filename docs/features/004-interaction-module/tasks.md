# Tasks: Real-time Voice Interaction Testing Module

**Input**: Design documents from `/docs/features/004-interaction-module/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/` (Python FastAPI)
- **Frontend**: `frontend/src/` (React TypeScript)
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create interaction module directory structure per plan.md
- [x] T002 [P] Create database migration for interaction_sessions table in backend/src/infrastructure/database/migrations/
- [x] T003 [P] Create database migration for conversation_turns table in backend/src/infrastructure/database/migrations/
- [x] T004 [P] Create database migration for latency_metrics table in backend/src/infrastructure/database/migrations/
- [x] T005 [P] Create database migration for system_prompt_templates table in backend/src/infrastructure/database/migrations/
- [x] T006 Create audio storage directory structure (storage/interactions/) and add to .gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Domain Layer

- [x] T007 [P] Create InteractionMode and SessionStatus enums in backend/src/domain/entities/interaction_enums.py
- [x] T008 [P] Create InteractionSession entity in backend/src/domain/entities/interaction_session.py
- [x] T009 [P] Create ConversationTurn entity in backend/src/domain/entities/conversation_turn.py
- [x] T010 [P] Create LatencyMetrics entity in backend/src/domain/entities/latency_metrics.py
- [x] T011 [P] Create SystemPromptTemplate entity in backend/src/domain/entities/system_prompt_template.py
- [x] T012 Create InteractionRepository interface in backend/src/domain/repositories/interaction_repository.py
- [x] T013 Create base InteractionMode service interface in backend/src/domain/services/interaction/base.py
- [x] T014 Create LatencyTracker service in backend/src/domain/services/interaction/latency_tracker.py

### Backend Infrastructure Layer

- [x] T015 [P] Implement InteractionRepository with SQLAlchemy in backend/src/infrastructure/persistence/interaction_repository_impl.py
- [x] T016 [P] Create AudioStorageService for file management in backend/src/infrastructure/storage/audio_storage.py
- [x] T017 Create WebSocket handler base class in backend/src/infrastructure/websocket/base_handler.py
- [x] T018 Implement InteractionWebSocketHandler in backend/src/infrastructure/websocket/interaction_handler.py

### Backend Presentation Layer

- [x] T019 [P] Create WebSocket router in backend/src/presentation/api/routes/interaction_ws.py
- [x] T020 [P] Create interaction REST router (extended) in backend/src/presentation/api/routes/interaction.py

### Frontend Foundation

- [x] T021 [P] Create interaction TypeScript types in frontend/src/types/interaction.ts
- [x] T022 [P] Create useWebSocket hook in frontend/src/hooks/useWebSocket.ts
- [x] T023 [P] Create useMicrophone hook in frontend/src/hooks/useMicrophone.ts
- [x] T024 [P] Create useAudioPlayback hook in frontend/src/hooks/useAudioPlayback.ts
- [x] T025 Create interactionStore with Zustand in frontend/src/stores/interactionStore.ts
- [x] T026 Create interactionService API client in frontend/src/services/interactionApi.ts

### Contract Tests (TDD - Write First, Must Fail)

- [x] T026a [P] Write WebSocket protocol contract tests in backend/tests/contract/test_websocket_protocol.py
- [x] T026b [P] Write interaction REST API contract tests in backend/tests/contract/test_interaction_api.py
- [x] T026c [P] Write InteractionRepository contract tests in backend/tests/contract/test_interaction_repository.py

**✅ Checkpoint Complete**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 即時語音對話測試 (Priority: P1) 🎯 MVP

**Goal**: Users can have real-time voice conversations with AI through the web interface

**Independent Test**: Open microphone, speak a sentence, receive AI voice response

### Tests for User Story 1 (TDD - Write First, Must Fail)

- [x] T027a [P] [US1] Write integration test for basic conversation flow in backend/tests/integration/test_realtime_conversation.py
- [x] T027b [P] [US1] Write unit tests for Realtime API clients in backend/tests/unit/test_realtime_mode.py

### Backend Implementation for US1

- [x] T027 [US1] Implement OpenAI Realtime API client in backend/src/domain/services/interaction/openai_realtime.py
- [x] T027c [P] [US1] Implement Gemini Live API client in backend/src/domain/services/interaction/gemini_realtime.py
- [x] T027d [US1] Create RealtimeMode factory with provider selection in backend/src/domain/services/interaction/realtime_mode.py
- [x] T028 [US1] Create StartSession use case in backend/src/application/use_cases/interaction/start_session.py
- [x] T029 [US1] Create ProcessAudio use case in backend/src/application/use_cases/interaction/process_audio.py
- [x] T030 [US1] Create EndSession use case in backend/src/application/use_cases/interaction/end_session.py
- [x] T031 [US1] Implement WebSocket message handlers for start_session, audio_chunk, end_session in backend/src/infrastructure/websocket/interaction_handler.py
- [x] T032 [US1] Add connection_ready and session_started WebSocket responses
- [x] T033 [US1] Add audio_chunk streaming from Realtime API to client
- [x] T034 [US1] Implement speech_started and speech_ended VAD event forwarding

### Frontend Implementation for US1

- [x] T035 [P] [US1] Create AudioVisualizer component in frontend/src/components/interaction/AudioVisualizer.tsx
- [x] T036 [P] [US1] Create basic ModeSelector component with realtime provider selection (OpenAI/Gemini) in frontend/src/components/interaction/ModeSelector.tsx
- [x] T037 [US1] Create InteractionPanel main component in frontend/src/components/interaction/InteractionPanel.tsx
- [x] T038 [US1] Implement microphone permission request and error handling in InteractionPanel
- [x] T039 [US1] Implement audio playback for AI responses in InteractionPanel
- [x] T040 [US1] Create InteractionPage route in frontend/src/routes/interaction/InteractionPage.tsx
- [x] T041 [US1] Add interaction route to main router configuration
- [x] T042 [US1] Add status indicators (listening, processing, speaking) to InteractionPanel

**Checkpoint**: User Story 1 complete - basic voice conversation functional with Realtime API

---

## Phase 4: User Story 2 - 互動模式選擇與切換 (Priority: P1)

**Goal**: Users can choose between Realtime API mode and Cascade mode (STT→LLM→TTS)

**Independent Test**: Select Cascade mode, configure providers, verify conversation works

### Tests for User Story 2 (TDD - Write First, Must Fail)

- [ ] T043a [P] [US2] Write integration test for cascade mode flow in backend/tests/integration/test_cascade_conversation.py
- [ ] T043b [P] [US2] Write unit tests for LLM providers in backend/tests/unit/test_llm_providers.py
- [ ] T043c [P] [US2] Write unit tests for mode switching logic in backend/tests/unit/test_mode_selection.py

### Backend Implementation for US2

- [ ] T043 [P] [US2] Create LLM service base interface in backend/src/domain/services/llm/base.py
- [ ] T044 [P] [US2] Implement OpenAI GPT-4o provider in backend/src/domain/services/llm/openai_provider.py
- [ ] T045 [P] [US2] Implement Google Gemini provider in backend/src/domain/services/llm/gemini_provider.py
- [ ] T046 [US2] Implement Cascade mode service (STT→LLM→TTS) in backend/src/domain/services/interaction/cascade_mode.py
- [ ] T047 [US2] Integrate existing Phase 3 STT providers in cascade_mode.py
- [ ] T048 [US2] Integrate existing Phase 1 TTS providers in cascade_mode.py
- [ ] T049 [US2] Add mode selection logic to StartSession use case
- [ ] T050 [US2] Implement fallback from Realtime to Cascade mode on connection failure
- [ ] T051 [US2] Add providers endpoint GET /api/v1/interaction/providers in backend/src/presentation/api/interaction_router.py

### Frontend Implementation for US2

- [ ] T052 [US2] Extend ModeSelector with Cascade mode UI in frontend/src/components/interaction/ModeSelector.tsx
- [ ] T053 [US2] Add STT provider dropdown to ModeSelector
- [ ] T054 [US2] Add LLM provider dropdown to ModeSelector
- [ ] T055 [US2] Add TTS provider dropdown to ModeSelector
- [ ] T056 [US2] Fetch available providers from API and display availability status
- [ ] T057 [US2] Update interactionStore to handle mode and provider configuration
- [ ] T058 [US2] Implement fallback prompt UI when Realtime API fails

**Checkpoint**: User Story 2 complete - both modes functional and switchable

---

## Phase 5: User Story 3 - 端對端延遲測量 (Priority: P2)

**Goal**: Display detailed latency metrics for each conversation turn

**Independent Test**: Complete a conversation turn, verify latency breakdown appears

### Tests for User Story 3 (TDD - Write First, Must Fail)

- [ ] T059a [P] [US3] Write unit tests for LatencyTracker in backend/tests/unit/test_latency_tracker.py

### Backend Implementation for US3

- [ ] T059 [US3] Implement latency measurement in LatencyTracker for Realtime mode
- [ ] T060 [US3] Implement segment latency measurement (STT, LLM TTFT, TTS TTFB) for Cascade mode
- [ ] T061 [US3] Add latency data to response_ended WebSocket message
- [ ] T062 [US3] Create latency statistics aggregation in InteractionRepository
- [ ] T063 [US3] Add latency-stats endpoint GET /api/v1/interaction/sessions/{id}/latency-stats in interaction_router.py

### Frontend Implementation for US3

- [ ] T064 [P] [US3] Create LatencyDisplay component in frontend/src/components/interaction/LatencyDisplay.tsx
- [ ] T065 [US3] Show real-time latency per turn in InteractionPanel
- [ ] T066 [US3] Show segment breakdown for Cascade mode (STT/LLM/TTS bars)
- [ ] T067 [US3] Display session summary statistics (avg, min, max, P95) on session end

**Checkpoint**: User Story 3 complete - latency metrics visible for all turns

---

## Phase 6: User Story 4 - 系統提示詞配置 (Priority: P2)

**Goal**: Users can configure AI system prompts and select from templates

**Independent Test**: Select a template, start conversation, verify AI behaves according to template

### Backend Implementation for US4

- [ ] T068 [US4] Create template repository in backend/src/domain/repositories/template_repository.py
- [ ] T069 [US4] Implement template repository with SQLAlchemy in backend/src/infrastructure/repositories/template_repository_impl.py
- [ ] T070 [US4] Create seed data migration for default templates (客服機器人, 語言教師, 技術支援, 一般助理)
- [ ] T071 [US4] Add templates endpoints GET /api/v1/interaction/templates in interaction_router.py
- [ ] T072 [US4] Add template detail endpoint GET /api/v1/interaction/templates/{id} in interaction_router.py
- [ ] T073 [US4] Pass system_prompt to Realtime API and LLM in interaction modes

### Frontend Implementation for US4

- [ ] T074 [P] [US4] Create SystemPromptEditor component in frontend/src/components/interaction/SystemPromptEditor.tsx
- [ ] T075 [US4] Add template selection dropdown to SystemPromptEditor
- [ ] T076 [US4] Add custom prompt textarea input
- [ ] T077 [US4] Persist prompt selection in interactionStore
- [ ] T078 [US4] Include system_prompt in start_session WebSocket message

**Checkpoint**: User Story 4 complete - system prompts configurable

---

## Phase 7: User Story 5 - 打斷（Barge-in）功能測試 (Priority: P3)

**Goal**: AI stops speaking when user starts talking (barge-in/interruption)

**Independent Test**: While AI is responding, start speaking, verify playback stops immediately

### Tests for User Story 5 (TDD - Write First, Must Fail)

- [ ] T079a [P] [US5] Write integration test for barge-in handling in backend/tests/integration/test_barge_in.py

### Backend Implementation for US5

- [ ] T079 [US5] Handle interrupted event from OpenAI Realtime API in realtime_mode.py
- [ ] T080 [US5] Implement barge-in detection in Cascade mode (new speech during TTS playback)
- [ ] T081 [US5] Add interrupt client message handler in interaction_handler.py
- [ ] T082 [US5] Send interrupted server message when barge-in detected
- [ ] T083 [US5] Record interrupted flag and timing in ConversationTurn
- [ ] T084 [US5] Add barge_in_enabled configuration to start_session

### Frontend Implementation for US5

- [ ] T085 [US5] Handle interrupted WebSocket message - stop audio playback immediately
- [ ] T086 [US5] Add barge-in toggle switch to InteractionPanel settings
- [ ] T087 [US5] Display barge-in indicator when interruption occurs
- [ ] T088 [US5] Show interrupt latency in LatencyDisplay

**Checkpoint**: User Story 5 complete - barge-in functional

---

## Phase 8: User Story 6 - 對話歷史與回放 (Priority: P3)

**Goal**: Users can view past conversations and replay audio

**Independent Test**: Complete a conversation, navigate to history, play back audio

### Tests for User Story 6 (TDD - Write First, Must Fail)

- [ ] T089a [P] [US6] Write integration test for history retrieval and playback in backend/tests/integration/test_conversation_history.py

### Backend Implementation for US6

- [ ] T089 [US6] Add sessions list endpoint GET /api/v1/interaction/sessions with pagination and filters
- [ ] T090 [US6] Add session detail endpoint GET /api/v1/interaction/sessions/{id}
- [ ] T091 [US6] Add session delete endpoint DELETE /api/v1/interaction/sessions/{id}
- [ ] T092 [US6] Add turns list endpoint GET /api/v1/interaction/sessions/{id}/turns
- [ ] T093 [US6] Add audio streaming endpoint GET /api/v1/interaction/sessions/{id}/turns/{turn_id}/audio
- [ ] T094 [US6] Implement audio file cleanup on session delete

### Frontend Implementation for US6

- [ ] T095 [P] [US6] Create ConversationHistory component in frontend/src/components/interaction/ConversationHistory.tsx
- [ ] T096 [US6] Create HistoryPage with session list in frontend/src/routes/interaction/HistoryPage.tsx
- [ ] T097 [US6] Add date range filter to HistoryPage
- [ ] T098 [US6] Add mode filter (realtime/cascade) to HistoryPage
- [ ] T099 [US6] Implement session detail view with turn list
- [ ] T100 [US6] Implement audio playback for user and AI audio per turn
- [ ] T101 [US6] Add session delete confirmation dialog
- [ ] T102 [US6] Add history route to main router

**Checkpoint**: User Story 6 complete - history browsing and playback functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Observability (FR-018, FR-019, FR-020)

- [ ] T103 [P] Implement structured logging with session_id, event_type, provider_name in backend/src/infrastructure/logging/
- [ ] T104 [P] Add API call counter metrics per provider
- [ ] T105 [P] Add error rate tracking and detailed error context logging

### Documentation & Validation

- [ ] T106 [P] Update CLAUDE.md with new interaction module commands
- [ ] T107 Run quickstart.md validation - verify all setup steps work
- [ ] T108 Add API documentation comments to interaction_router.py

### Code Quality

- [ ] T109 [P] Run ruff check and fix any linting issues
- [ ] T110 [P] Run mypy and fix any type errors
- [ ] T111 [P] Run frontend eslint and tsc checks
- [ ] T112 Run pytest with coverage and verify >=80% on backend/src/domain/services/
- [ ] T113 Generate coverage report and add coverage configuration to pyproject.toml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational completion
  - US1 & US2 (both P1): Can proceed sequentially (US1 first for MVP) or in parallel
  - US3 & US4 (both P2): Can proceed after US1/US2 or in parallel
  - US5 & US6 (both P3): Can proceed after US1/US2 or in parallel
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|------------|---------------------|
| US1 (P1) | Foundational | - |
| US2 (P1) | Foundational | US1 (but US1 first for MVP) |
| US3 (P2) | Foundational | US4 |
| US4 (P2) | Foundational | US3 |
| US5 (P3) | Foundational | US6 |
| US6 (P3) | Foundational | US5 |

### Within Each User Story

- Models before services
- Services before use cases
- Use cases before handlers/routers
- Backend before frontend (for API contracts)
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004, T005 can run in parallel (different migration files)

**Phase 2 (Foundational)**:
- T007-T011 can run in parallel (different entity files)
- T015, T016 can run in parallel (different infrastructure files)
- T019, T020 can run in parallel (different router files)
- T021-T024 can run in parallel (different frontend files)

**User Stories**:
- Within US2: T043, T044, T045 can run in parallel (different provider files)
- Within US4: T074 can run in parallel with backend tasks

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all entity tasks together:
Task: "Create InteractionMode and SessionStatus enums in backend/src/domain/entities/interaction_enums.py"
Task: "Create InteractionSession entity in backend/src/domain/entities/interaction_session.py"
Task: "Create ConversationTurn entity in backend/src/domain/entities/conversation_turn.py"
Task: "Create LatencyMetrics entity in backend/src/domain/entities/latency_metrics.py"
Task: "Create SystemPromptTemplate entity in backend/src/domain/entities/system_prompt_template.py"

# Launch all frontend hooks together:
Task: "Create useWebSocket hook in frontend/src/hooks/useWebSocket.ts"
Task: "Create useMicrophone hook in frontend/src/hooks/useMicrophone.ts"
Task: "Create useAudioPlayback hook in frontend/src/hooks/useAudioPlayback.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (6 tasks)
2. Complete Phase 2: Foundational (20 tasks)
3. Complete Phase 3: User Story 1 (16 tasks)
4. **STOP and VALIDATE**: Test basic voice conversation with Realtime API
5. Deploy/demo if ready - users can have voice conversations!

**MVP Scope**: 42 tasks for working voice conversation

### Incremental Delivery

1. **MVP**: Setup + Foundational + US1 → Voice conversation works
2. **+US2**: Add Cascade mode → Multiple provider options
3. **+US3**: Add latency metrics → Performance visibility
4. **+US4**: Add prompts → Scenario customization
5. **+US5**: Add barge-in → Natural interruption
6. **+US6**: Add history → Test record keeping
7. **Polish**: Observability + documentation

### Recommended Execution Order

For single developer:
```
Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → US5 → US6 → Phase 9
```

---

## Summary

| Phase | Tasks | Cumulative | Description |
|-------|-------|------------|-------------|
| Phase 1: Setup | 6 | 6 | Database migrations, directory structure |
| Phase 2: Foundational | 23 | 29 | Entities, repositories, base services, hooks, contract tests |
| Phase 3: US1 (P1) | 20 | 49 | Basic voice conversation (MVP) + TDD tests + Gemini support |
| Phase 4: US2 (P1) | 19 | 68 | Mode selection, Cascade mode + TDD tests |
| Phase 5: US3 (P2) | 10 | 78 | Latency measurement + TDD tests |
| Phase 6: US4 (P2) | 11 | 89 | System prompts |
| Phase 7: US5 (P3) | 11 | 100 | Barge-in + TDD tests |
| Phase 8: US6 (P3) | 15 | 115 | History & playback + TDD tests |
| Phase 9: Polish | 11 | 126 | Observability, docs, quality, coverage verification |

**Total Tasks**: 126
**MVP Tasks**: 49 (Phase 1-3)
**Test Tasks**: 14 (TDD contract + integration + unit tests)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Integrate with existing BYOL credential management from Phase 1-3
