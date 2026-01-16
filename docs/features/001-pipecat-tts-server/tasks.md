# Tasks: Pipecat TTS Server

**Input**: Design documents from `/docs/features/001-pipecat-tts-server/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not explicitly requested in spec - test tasks are OPTIONAL and not included by default.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- **Backend**: `backend/src/`
- **Frontend**: `frontend/src/`
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Pipecat framework setup

- [ ] T001 Create project structure per plan.md (`backend/src/core/`, `backend/src/api/`, `backend/src/transport/`, `backend/src/config/`)
- [ ] T002 Initialize Python project with pyproject.toml and dependencies (`pipecat-ai[azure,elevenlabs,google]`, `fastapi`, `uvicorn`, `websockets`, `httpx`)
- [ ] T003 [P] Configure linting and formatting tools (ruff, mypy) in `pyproject.toml`
- [ ] T004 [P] Create `.env.example` with required environment variables (API keys for Azure, ElevenLabs, Google)
- [ ] T005 [P] Initialize frontend project structure (`frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/services/`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create settings configuration with pydantic-settings in `backend/src/config/settings.py`
- [ ] T007 [P] Create domain entities (AudioFormat enum, TTSRequest, TTSResult) in `backend/src/core/entities/tts.py`
- [ ] T008 [P] Create streaming entities (StreamingChunk, StreamingSession, StreamingStatus) in `backend/src/core/entities/streaming.py`
- [ ] T009 [P] Create API DTOs (SynthesizeRequest, SynthesizeResponse, StreamingEvent) in `backend/src/api/schemas/tts.py`
- [ ] T010 Create base Pipecat TTS service wrapper in `backend/src/core/services/base_tts.py`
- [ ] T011 [P] Implement Azure TTS service wrapper in `backend/src/core/services/azure_tts.py`
- [ ] T012 [P] Implement ElevenLabs TTS service wrapper in `backend/src/core/services/elevenlabs_tts.py`
- [ ] T013 [P] Implement Google TTS service wrapper in `backend/src/core/services/google_tts.py`
- [ ] T014 Create TTS service factory (provider selection) in `backend/src/core/services/factory.py`
- [ ] T015 Create Pipecat TTS Pipeline builder in `backend/src/core/pipeline/tts_pipeline.py`
- [ ] T016 Setup FastAPI application with CORS and middleware in `backend/src/api/main.py`
- [ ] T017 [P] Create health check endpoint in `backend/src/api/routes/health.py`
- [ ] T018 Configure structured logging with structlog in `backend/src/config/logging.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 文字轉語音基本功能 (Priority: P1) 🎯 MVP

**Goal**: 透過 API 將文字轉換為語音，支援批次與串流兩種模式

**Independent Test**: 發送文字到 API 端點，驗證返回的音訊檔案可播放

### Implementation for User Story 1

- [ ] T019 [US1] Implement batch synthesize endpoint `POST /api/v1/tts/synthesize` in `backend/src/api/routes/tts.py`
- [ ] T020 [US1] Implement HTTP streaming endpoint `POST /api/v1/tts/synthesize/stream` in `backend/src/api/routes/tts.py`
- [ ] T021 [US1] Implement list voices endpoint `GET /api/v1/tts/voices` in `backend/src/api/routes/voices.py`
- [ ] T022 [US1] Implement list providers endpoint `GET /api/v1/tts/providers` in `backend/src/api/routes/voices.py`
- [ ] T023 [US1] Add input validation (text length 1-5000, speed 0.5-2.0) in `backend/src/api/schemas/tts.py`
- [ ] T024 [US1] Implement error handling with meaningful error messages in `backend/src/api/middleware/error_handler.py`
- [ ] T025 [US1] Add request logging for all API calls in `backend/src/api/middleware/logging.py`
- [ ] T026 [US1] Register all routes in FastAPI app in `backend/src/api/main.py`

**Checkpoint**: User Story 1 完成 - API 可透過 curl 測試批次與串流合成

---

## Phase 4: User Story 2 - Web 介面試聽 (Priority: P2)

**Goal**: 透過 Web 介面輸入文字並即時試聽語音合成結果

**Independent Test**: 瀏覽器訪問 Web 頁面，輸入文字並點擊播放按鈕

### Implementation for User Story 2

- [ ] T027 [US2] Implement WebSocket transport server in `backend/src/transport/websocket_server.py`
- [ ] T028 [US2] Implement WebSocket TTS endpoint `/ws/tts` in `backend/src/api/routes/websocket.py`
- [ ] T029 [US2] Integrate WebSocket routes in FastAPI app in `backend/src/api/main.py`
- [ ] T030 [P] [US2] Create TTS API service client in `frontend/src/services/ttsApi.ts`
- [ ] T031 [P] [US2] Create useWebSocket hook in `frontend/src/hooks/useWebSocket.ts`
- [ ] T032 [P] [US2] Create useStreamingAudio hook in `frontend/src/hooks/useStreamingAudio.ts`
- [ ] T033 [US2] Create TTSForm component (text input, provider/voice selection) in `frontend/src/components/TTSForm/TTSForm.tsx`
- [ ] T034 [US2] Create StreamingPlayer component (audio playback) in `frontend/src/components/AudioPlayer/StreamingPlayer.tsx`
- [ ] T035 [US2] Create WaveformVisualizer component (波形顯示) in `frontend/src/components/AudioPlayer/WaveformVisualizer.tsx`
- [ ] T036 [US2] Implement download functionality in StreamingPlayer in `frontend/src/components/AudioPlayer/StreamingPlayer.tsx`
- [ ] T037 [US2] Add loading state indicator during synthesis in `frontend/src/components/TTSForm/TTSForm.tsx`
- [ ] T038 [US2] Create main TTS page integrating all components in `frontend/src/pages/TTSPage.tsx`

**Checkpoint**: User Story 2 完成 - Web 介面可試聽與下載音訊

---

## Phase 5: User Story 3 - 語音參數調整 (Priority: P3)

**Goal**: 調整語音合成參數（語速、音調、音色）獲得符合需求的輸出

**Independent Test**: 透過 API 或 Web 介面發送不同參數請求，比較輸出差異

### Implementation for User Story 3

- [ ] T039 [US3] Add voice parameter support (speed, pitch, volume) to Pipecat TTS services in `backend/src/core/services/base_tts.py`
- [ ] T040 [P] [US3] Update Azure TTS service with parameter support in `backend/src/core/services/azure_tts.py`
- [ ] T041 [P] [US3] Update ElevenLabs TTS service with parameter support in `backend/src/core/services/elevenlabs_tts.py`
- [ ] T042 [P] [US3] Update Google TTS service with parameter support in `backend/src/core/services/google_tts.py`
- [ ] T043 [US3] Add parameter controls to TTSForm (語速滑桿、音調滑桿) in `frontend/src/components/TTSForm/TTSForm.tsx`
- [ ] T044 [US3] Add voice selector dropdown (依提供者顯示可用音色) in `frontend/src/components/TTSForm/VoiceSelector.tsx`
- [ ] T045 [US3] Implement parameter persistence in local storage in `frontend/src/hooks/useParameterStorage.ts`

**Checkpoint**: User Story 3 完成 - 可調整語音參數並聽到差異

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Implement VoAI custom TTS service (台灣本土供應商) in `backend/src/core/services/voai_tts.py`
- [ ] T047 [P] Add rate limiting middleware in `backend/src/api/middleware/rate_limit.py`
- [ ] T048 [P] Add concurrent request handling (target: 10 concurrent) in `backend/src/api/middleware/concurrency.py`
- [ ] T049 [P] Add edge case handling (empty text, special characters, emoji) in `backend/src/api/schemas/tts.py`
- [ ] T050 [P] Add network error handling and retry logic in frontend in `frontend/src/services/ttsApi.ts`
- [ ] T051 [P] Add browser compatibility checks (Chrome, Firefox, Safari, Edge) in `frontend/src/utils/browserCompat.ts`
- [ ] T052 Run quickstart.md validation and update if needed
- [ ] T053 Performance optimization: TTFB < 500ms, total < 5s for 100 chars

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Phase 2
  - User Story 2 (P2): Can start after Phase 2 (parallel with US1)
  - User Story 3 (P3): Can start after Phase 2 (parallel with US1/US2)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: 核心 API - 無依賴其他 story
- **User Story 2 (P2)**: Web 介面 - 使用 US1 的 API，但可獨立測試
- **User Story 3 (P3)**: 參數調整 - 擴展 US1/US2 功能，可獨立測試

### Within Each User Story

- Models before services
- Services before endpoints
- Backend endpoints before frontend integration
- Core implementation before integration

### Parallel Opportunities

Within Phase 2 (Foundational):
- T007, T008, T009 (entities/schemas) can run in parallel
- T011, T012, T013 (TTS services) can run in parallel
- T017 (health check) can run in parallel with other routes

Within User Stories:
- Tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all entity tasks together:
Task: "T007 Create domain entities in backend/src/core/entities/tts.py"
Task: "T008 Create streaming entities in backend/src/core/entities/streaming.py"
Task: "T009 Create API DTOs in backend/src/api/schemas/tts.py"

# Then launch all TTS services together:
Task: "T011 Implement Azure TTS service in backend/src/core/services/azure_tts.py"
Task: "T012 Implement ElevenLabs TTS service in backend/src/core/services/elevenlabs_tts.py"
Task: "T013 Implement Google TTS service in backend/src/core/services/google_tts.py"
```

## Parallel Example: User Story 2

```bash
# Launch all frontend hooks together:
Task: "T031 Create useWebSocket hook in frontend/src/hooks/useWebSocket.ts"
Task: "T032 Create useStreamingAudio hook in frontend/src/hooks/useStreamingAudio.ts"
Task: "T030 Create TTS API service in frontend/src/services/ttsApi.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (API endpoints)
4. **STOP and VALIDATE**: Test with curl/Postman
5. Deploy API if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test API → Deploy (API MVP!)
3. Add User Story 2 → Test Web UI → Deploy (Full MVP!)
4. Add User Story 3 → Test parameters → Deploy (Enhanced!)
5. Polish → Performance & edge cases → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Backend API)
   - Developer B: User Story 2 (Frontend + WebSocket)
   - Developer C: User Story 3 (Parameter support)
3. Stories complete and integrate independently

---

## Task Summary

| Phase | Task Count | Parallel Tasks |
|-------|------------|----------------|
| Phase 1: Setup | 5 | 3 |
| Phase 2: Foundational | 13 | 7 |
| Phase 3: US1 (P1) MVP | 8 | 0 |
| Phase 4: US2 (P2) | 12 | 3 |
| Phase 5: US3 (P3) | 7 | 3 |
| Phase 6: Polish | 8 | 6 |
| **Total** | **53** | **22** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Pipecat services wrap underlying SDKs for unified interface
- VoAI service in Polish phase (not Pipecat built-in, requires custom implementation)
