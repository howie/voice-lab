# Tasks: Music Generation (Mureka AI)

**Input**: Design documents from `/docs/features/012-music-generation/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/music-api.yaml

**Tests**: Constitution Check 要求 TDD，因此包含測試任務。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Add httpx dependency in backend/pyproject.toml for Mureka API client
- [ ] T002 [P] Create music domain directory structure: backend/src/domain/models/music.py, backend/src/domain/ports/music_generation.py, backend/src/domain/services/music/
- [ ] T003 [P] Create Mureka adapter directory structure: backend/src/infrastructure/adapters/mureka/
- [ ] T004 [P] Create music API directory structure: backend/src/presentation/api/v1/music/
- [ ] T005 [P] Add MUREKA_API_KEY and MUREKA_API_BASE_URL to backend/src/config.py
- [ ] T006 [P] Create frontend music module directories: frontend/src/components/music/, frontend/src/routes/music/, frontend/src/services/, frontend/src/stores/, frontend/src/types/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**Critical**: No user story work can begin until this phase is complete

- [ ] T007 Create MusicGenerationType and MusicGenerationStatus enums in backend/src/domain/models/music.py
- [ ] T008 Create MusicGenerationJob SQLAlchemy model in backend/src/domain/models/music.py (per data-model.md)
- [ ] T009 Create database migration for music_generation_jobs table in backend/alembic/versions/
- [ ] T010 [P] Create MusicGenerationPort protocol in backend/src/domain/ports/music_generation.py
- [ ] T011 [P] Create Pydantic schemas (InstrumentalRequest, SongRequest, LyricsRequest, etc.) in backend/src/presentation/api/v1/music/schemas.py (per contracts/music-api.yaml)
- [ ] T012 [P] Create TypeScript types (MusicGenerationType, MusicGenerationStatus, MusicGenerationJob, etc.) in frontend/src/types/music.ts
- [ ] T013 Implement MurekaAPIClient base class with authentication in backend/src/infrastructure/adapters/mureka/client.py
- [ ] T014 Implement MurekaMusicAdapter (implements MusicGenerationPort) in backend/src/infrastructure/adapters/mureka/adapter.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 生成背景音樂用於 Magic DJ (Priority: P1)

**Goal**: 使用者可以根據情境描述生成 BGM，用於 Magic DJ Controller 的預錄音軌

**Independent Test**: 透過描述情境生成 BGM，下載並驗證 MP3 檔案

### Tests for User Story 1

- [ ] T015 [P] [US1] Contract test for Mureka instrumental API in backend/tests/contract/music/test_mureka_contract.py
- [ ] T016 [P] [US1] Unit test for MusicGenerationService.submit_instrumental in backend/tests/unit/music/test_service.py

### Implementation for User Story 1

- [ ] T017 [US1] Implement submit_instrumental method in MurekaAPIClient in backend/src/infrastructure/adapters/mureka/client.py
- [ ] T018 [US1] Implement query_task method in MurekaAPIClient for status polling in backend/src/infrastructure/adapters/mureka/client.py
- [ ] T019 [US1] Implement MusicGenerationService with submit_instrumental, get_job, list_jobs in backend/src/domain/services/music/service.py
- [ ] T020 [US1] Implement background worker for Mureka task polling in backend/src/domain/services/music/worker.py
- [ ] T021 [US1] Implement POST /music/instrumental endpoint in backend/src/presentation/api/v1/music/router.py
- [ ] T022 [US1] Implement GET /music/jobs and GET /music/jobs/{job_id} endpoints in backend/src/presentation/api/v1/music/router.py
- [ ] T023 [US1] Implement GET /music/jobs/{job_id}/download endpoint in backend/src/presentation/api/v1/music/router.py
- [ ] T024 [US1] Register music router in backend/src/main.py
- [ ] T025 [P] [US1] Create musicService.ts with submitInstrumental, getJob, listJobs, downloadJob in frontend/src/services/musicService.ts
- [ ] T026 [P] [US1] Create musicStore.ts with Zustand for job state management in frontend/src/stores/musicStore.ts
- [ ] T027 [US1] Create MusicGenerationForm component for instrumental in frontend/src/components/music/MusicGenerationForm.tsx
- [ ] T028 [US1] Create MusicJobStatus component for status display in frontend/src/components/music/MusicJobStatus.tsx
- [ ] T029 [US1] Create MusicPlayer component for preview and download in frontend/src/components/music/MusicPlayer.tsx
- [ ] T030 [US1] Create music generation page in frontend/src/routes/music/index.tsx
- [ ] T031 [US1] Add music route to frontend router configuration

**Checkpoint**: User Story 1 is complete - BGM generation works end-to-end

---

## Phase 4: User Story 5 - Magic DJ 快速音軌生成 (Priority: P1)

**Goal**: RD 可以直接從 Magic DJ 控制台生成新的音軌

**Independent Test**: 在 Magic DJ 控制台點擊「生成新音軌」按鈕，填入描述後等待生成完成並加入音軌列表

**Depends on**: User Story 1 (reuses instrumental generation)

### Implementation for User Story 5

- [ ] T032 [US5] Create MusicGenerationDialog component in frontend/src/components/music/MusicGenerationDialog.tsx
- [ ] T033 [US5] Add "生成新音軌" button to Magic DJ controller in frontend/src/routes/magic-dj/ (existing files)
- [ ] T034 [US5] Implement callback to add generated track to Magic DJ track list

**Checkpoint**: User Story 5 is complete - Magic DJ integration works

---

## Phase 5: User Story 2 - 生成主題歌曲 (Priority: P1)

**Goal**: 使用者可以根據歌詞和風格描述生成完整歌曲（含人聲）

**Independent Test**: 透過提供歌詞和風格描述，驗證生成的歌曲是否包含人聲

### Tests for User Story 2

- [ ] T035 [P] [US2] Contract test for Mureka song API in backend/tests/contract/music/test_mureka_contract.py
- [ ] T036 [P] [US2] Unit test for MusicGenerationService.submit_song in backend/tests/unit/music/test_service.py

### Implementation for User Story 2

- [ ] T037 [US2] Implement submit_song method in MurekaAPIClient in backend/src/infrastructure/adapters/mureka/client.py
- [ ] T038 [US2] Implement submit_song in MusicGenerationService in backend/src/domain/services/music/service.py
- [ ] T039 [US2] Implement POST /music/song endpoint in backend/src/presentation/api/v1/music/router.py
- [ ] T040 [US2] Update musicService.ts with submitSong in frontend/src/services/musicService.ts
- [ ] T041 [US2] Update MusicGenerationForm to support song mode with lyrics input in frontend/src/components/music/MusicGenerationForm.tsx
- [ ] T042 [US2] Update music generation page to show song results (cover, lyrics) in frontend/src/routes/music/index.tsx

**Checkpoint**: User Story 2 is complete - Song generation works end-to-end

---

## Phase 6: User Story 3 - AI 輔助歌詞創作 (Priority: P2)

**Goal**: 使用者可以透過 AI 根據主題生成歌詞，再用於歌曲生成

**Independent Test**: 輸入主題（如「太空探險」）驗證生成的歌詞結構和內容

### Tests for User Story 3

- [ ] T043 [P] [US3] Contract test for Mureka lyrics API in backend/tests/contract/music/test_mureka_contract.py
- [ ] T044 [P] [US3] Unit test for MusicGenerationService lyrics methods in backend/tests/unit/music/test_service.py

### Implementation for User Story 3

- [ ] T045 [US3] Implement submit_lyrics and extend_lyrics methods in MurekaAPIClient in backend/src/infrastructure/adapters/mureka/client.py
- [ ] T046 [US3] Implement submit_lyrics and extend_lyrics in MusicGenerationService in backend/src/domain/services/music/service.py
- [ ] T047 [US3] Implement POST /music/lyrics and POST /music/lyrics/extend endpoints in backend/src/presentation/api/v1/music/router.py
- [ ] T048 [US3] Update musicService.ts with submitLyrics, extendLyrics in frontend/src/services/musicService.ts
- [ ] T049 [US3] Create LyricsEditor component with extend functionality in frontend/src/components/music/LyricsEditor.tsx
- [ ] T050 [US3] Add lyrics generation tab/mode to music generation page in frontend/src/routes/music/index.tsx
- [ ] T051 [US3] Implement "一鍵送入歌曲生成" button in LyricsEditor

**Checkpoint**: User Story 3 is complete - Lyrics generation and extension work

---

## Phase 7: User Story 4 - 音樂生成歷史管理 (Priority: P2)

**Goal**: 使用者可以查看和管理過去生成的音樂

**Independent Test**: 查看歷史記錄，找到並重新下載之前生成的音樂

### Tests for User Story 4

- [ ] T052 [P] [US4] Unit test for list_jobs with pagination and retry_job in backend/tests/unit/music/test_service.py

### Implementation for User Story 4

- [ ] T053 [US4] Implement retry_job in MusicGenerationService in backend/src/domain/services/music/service.py
- [ ] T054 [US4] Implement POST /music/jobs/{job_id}/retry endpoint in backend/src/presentation/api/v1/music/router.py
- [ ] T055 [US4] Create MusicHistoryList component in frontend/src/components/music/MusicHistoryList.tsx
- [ ] T056 [US4] Create music history page in frontend/src/routes/music/history.tsx
- [ ] T057 [US4] Add history route and navigation link

**Checkpoint**: User Story 4 is complete - History management works

---

## Phase 8: Quota Management (Cross-cutting)

**Purpose**: 配額追蹤和限制（支援所有 User Stories）

### Tests for Quota

- [ ] T058 [P] Unit test for QuotaService in backend/tests/unit/music/test_quota.py

### Implementation for Quota

- [ ] T059 Implement QuotaService with check_quota, can_submit, get_usage_stats in backend/src/domain/services/music/quota.py
- [ ] T060 Integrate QuotaService into MusicGenerationService submission methods in backend/src/domain/services/music/service.py
- [ ] T061 Implement GET /music/quota endpoint in backend/src/presentation/api/v1/music/router.py
- [ ] T062 Update musicService.ts with getQuota in frontend/src/services/musicService.ts
- [ ] T063 Add quota status display to music generation page in frontend/src/routes/music/index.tsx
- [ ] T064 Add quota warning when approaching limit in MusicGenerationForm

**Checkpoint**: Quota management complete

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T065 [P] Integration test for full music generation flow in backend/tests/integration/music/test_music_generation.py
- [ ] T066 [P] Frontend component test for MusicGenerationForm in frontend/tests/music/MusicGenerationForm.test.tsx
- [ ] T067 Add error handling for all edge cases (EC-001 to EC-006) across backend endpoints
- [ ] T068 Add loading states and error displays across frontend components
- [ ] T069 [P] Update quickstart.md with actual API examples and screenshots
- [ ] T070 Run quickstart.md validation with curl commands
- [ ] T071 Performance optimization: add caching for quota checks
- [ ] T072 Add logging for music generation operations in backend

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core BGM generation
- **User Story 5 (Phase 4)**: Depends on User Story 1 - Magic DJ integration
- **User Story 2 (Phase 5)**: Depends on Foundational - Song generation
- **User Story 3 (Phase 6)**: Depends on User Story 2 - Lyrics + Song flow
- **User Story 4 (Phase 7)**: Depends on Foundational - History management
- **Quota (Phase 8)**: Depends on Foundational - Cross-cutting
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Foundational (Phase 2)
       │
       ├──────────────────────────────────────────────┐
       │                    │                         │
       ▼                    ▼                         ▼
   US1 (BGM)            US2 (Song)              US4 (History)
       │                    │
       ▼                    ▼
   US5 (Magic DJ)       US3 (Lyrics)
```

- **US1 (Phase 3)**: Independent - Core BGM generation
- **US5 (Phase 4)**: Depends on US1 - Reuses instrumental generation
- **US2 (Phase 5)**: Independent - Song generation
- **US3 (Phase 6)**: Best after US2 - Lyrics flow into song
- **US4 (Phase 7)**: Independent - History management
- **Quota (Phase 8)**: Independent - Can be added at any point

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend before Frontend
- Models/Services before Endpoints
- Core implementation before integration

### Parallel Opportunities

Within Phase 2 (Foundational):
- T010, T011, T012 can run in parallel (different files)

Within Phase 3 (US1):
- T015, T016 can run in parallel (different test files)
- T025, T026 can run in parallel (different frontend files)

Within each story:
- Test tasks marked [P] can run in parallel
- Frontend tasks can start once backend endpoints are ready

---

## Parallel Example: User Story 1

```bash
# Phase 3: Launch tests in parallel
Task: T015 [P] [US1] Contract test for Mureka instrumental API
Task: T016 [P] [US1] Unit test for MusicGenerationService.submit_instrumental

# After tests fail, launch frontend setup in parallel with backend
Task: T025 [P] [US1] Create musicService.ts
Task: T026 [P] [US1] Create musicStore.ts
# (while backend T017-T024 proceeds sequentially)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (BGM generation)
4. **STOP and VALIDATE**: Test BGM generation end-to-end
5. Deploy/demo if ready - this is the minimum viable product

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (BGM) → Test independently → **MVP Done!**
3. Add User Story 5 (Magic DJ) → Test independently → Deploy (RD can use)
4. Add User Story 2 (Song) → Test independently → Deploy
5. Add User Story 3 (Lyrics) → Test independently → Deploy
6. Add User Story 4 (History) → Test independently → Deploy
7. Add Quota Management → Deploy
8. Polish phase → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 5
   - Developer B: User Story 2 → User Story 3
   - Developer C: User Story 4 + Quota Management
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution Check requires TDD - tests are included

---

*Generated: 2026-01-29*
