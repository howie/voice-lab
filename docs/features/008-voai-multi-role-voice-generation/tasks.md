# Tasks: VoAI Multi-Role Voice Generation Enhancement

**Input**: Design documents from `/docs/features/008-voai-multi-role-voice-generation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT included unless explicitly requested. Each user story includes independent test criteria.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`, `backend/alembic/`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and project initialization

- [ ] T001 Create Alembic migration for VoiceCache enhancement and VoiceSyncJob table in `backend/alembic/versions/xxx_add_voice_cache_fields.py`
- [ ] T002 [P] Add AgeGroup enum to `backend/src/domain/entities/voice.py`
- [ ] T003 [P] Add VoiceSyncStatus enum to `backend/src/domain/entities/voice_sync_job.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Enhance VoiceCache model with age_group, styles, use_cases, is_deprecated, synced_at fields in `backend/src/infrastructure/persistence/models.py`
- [ ] T005 [P] Create VoiceSyncJobModel in `backend/src/infrastructure/persistence/models.py`
- [ ] T006 [P] Define VoiceCacheRepository protocol in `backend/src/application/interfaces/voice_repository.py`
- [ ] T007 [P] Define VoiceSyncJobRepository protocol in `backend/src/application/interfaces/voice_sync_job_repository.py`
- [ ] T008 Implement VoiceCacheRepositoryImpl (DB-backed) in `backend/src/infrastructure/persistence/voice_repository.py`
- [ ] T009 Implement VoiceSyncJobRepositoryImpl in `backend/src/infrastructure/persistence/voice_sync_job_repository.py`
- [ ] T010 Register repositories in dependency injection container

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Native 多角色語音合成 (Priority: P1) 🎯 MVP

**Goal**: 使用者選擇 Azure/ElevenLabs 時，系統使用 Native 模式一次性合成多角色對話

**Independent Test**: 選擇 Azure Provider，輸入多角色對話，驗證系統使用 SSML 多聲音標籤一次完成合成（非分段合併）

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement AzureSSMLBuilder.build_multi_voice_ssml() in `backend/src/infrastructure/providers/azure/ssml_builder.py`
- [ ] T012 [P] [US1] Implement ElevenLabsDialogueBuilder.build_dialogue_request() in `backend/src/infrastructure/providers/elevenlabs/dialogue_builder.py` (Note: Uses Text to Dialogue API, not [S1][S2] syntax)
- [ ] T013 [US1] Add Azure SSML character limit validation (50,000 chars) with auto-fallback logic in `backend/src/application/use_cases/synthesize_multi_role.py`
- [ ] T014 [US1] Add ElevenLabs character limit validation (5,000 chars) with auto-fallback logic in `backend/src/application/use_cases/synthesize_multi_role.py`
- [ ] T015 [US1] Modify _synthesize_native() to call AzureSSMLBuilder for Azure provider in `backend/src/application/use_cases/synthesize_multi_role.py`
- [ ] T016 [US1] Modify _synthesize_native() to call ElevenLabsDialogueBuilder for ElevenLabs provider in `backend/src/application/use_cases/synthesize_multi_role.py`
- [ ] T017 [US1] Ensure synthesis result includes synthesis_mode (native/segmented) in response

**Checkpoint**: Azure and ElevenLabs Native multi-role synthesis should work; exceeding limits auto-falls back to segmented mode

---

## Phase 4: User Story 2 - 依年齡層篩選聲音 (Priority: P1)

**Goal**: 使用者可以依年齡層（child/young/adult/senior）篩選適合的聲音

**Independent Test**: 在聲音選擇器中選擇「兒童」年齡層，驗證只顯示兒童聲音

### Implementation for User Story 2

- [ ] T018 [P] [US2] Add age_group query parameter to GET /api/v1/voices endpoint in `backend/src/presentation/api/routes/voices.py`
- [ ] T019 [US2] Implement age_group filtering in VoiceCacheRepositoryImpl.list_all() and .get_by_provider() in `backend/src/infrastructure/persistence/voice_repository.py`
- [ ] T020 [US2] Add age_group field to voice detail response schema in `backend/src/presentation/api/schemas/voice.py`
- [ ] T021 [US2] Update frontend VoiceSelector component with age_group filter dropdown in `frontend/src/components/VoiceSelector/`

**Checkpoint**: Users can filter voices by age_group; API returns filtered results correctly

---

## Phase 5: User Story 3 - 聲音資料庫同步 (Priority: P2)

**Goal**: 系統定期從各 Provider 同步聲音清單到資料庫，包含 age_group 推斷

**Independent Test**: 觸發手動同步後，驗證資料庫中聲音資料與 Provider 一致

### Implementation for User Story 3

- [ ] T022 [P] [US3] Implement Azure voice list fetching logic in `backend/src/infrastructure/providers/azure/voice_fetcher.py`
- [ ] T023 [P] [US3] Implement ElevenLabs voice list fetching logic in `backend/src/infrastructure/providers/elevenlabs/voice_fetcher.py`
- [ ] T024 [US3] Implement age_group inference logic per provider (Azure: VoiceStyleName, ElevenLabs: labels.age) in `backend/src/domain/services/voice_metadata_inferrer.py`
- [ ] T025 [US3] Create SyncVoicesUseCase in `backend/src/application/use_cases/sync_voices.py`
- [ ] T026 [US3] Implement exponential backoff retry logic (1s, 2s, 4s, max 3 retries) in SyncVoicesUseCase
- [ ] T027 [US3] Register sync_voices job type in JobWorker `backend/src/infrastructure/workers/job_worker.py`
- [ ] T028 [P] [US3] Add POST /api/v1/admin/voices/sync endpoint for manual trigger in `backend/src/presentation/api/routes/admin_voices.py`
- [ ] T029 [P] [US3] Add GET /api/v1/admin/voices/sync/status endpoint in `backend/src/presentation/api/routes/admin_voices.py`
- [ ] T030 [P] [US3] Add GET /api/v1/admin/voices/sync/jobs endpoint in `backend/src/presentation/api/routes/admin_voices.py`
- [ ] T031 [P] [US3] Add GET /api/v1/admin/voices/sync/jobs/{job_id} endpoint in `backend/src/presentation/api/routes/admin_voices.py`

**Checkpoint**: Voice sync works manually and via background job; age_group is correctly inferred and stored

---

## Phase 6: User Story 4 - 依風格篩選聲音 (Priority: P3)

**Goal**: 使用者可以依風格（news/conversation/cheerful 等）篩選聲音

**Independent Test**: 選擇「新聞播報」風格，驗證只顯示適合新聞播報的聲音

### Implementation for User Story 4

- [ ] T032 [P] [US4] Add style query parameter to GET /api/v1/voices endpoint in `backend/src/presentation/api/routes/voices.py`
- [ ] T033 [US4] Implement style filtering (JSON array contains) in VoiceCacheRepositoryImpl in `backend/src/infrastructure/persistence/voice_repository.py`
- [ ] T034 [US4] Update frontend VoiceSelector component with style filter dropdown in `frontend/src/components/VoiceSelector/`

**Checkpoint**: Users can filter voices by style; API returns filtered results correctly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T035 Run `make check` and fix any linting/type errors
- [ ] T036 Validate quickstart.md examples work correctly
- [ ] T037 Update CLAUDE.md with 008 feature information if needed
- [ ] T038 Code cleanup and ensure proper error handling across all new code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 are both P1, can proceed in parallel
  - US3 (P2) can start after Foundational, may integrate with US2 for filtered results
  - US4 (P3) depends on US3 completion (needs styles synced to DB)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Depends only on Foundational - No dependencies on other stories
- **User Story 3 (P2)**: Depends only on Foundational - Populates voice data for US2/US4
- **User Story 4 (P3)**: Depends on US3 (needs styles populated in DB via sync)

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Backend before frontend (for API-dependent UI)

### Parallel Opportunities

- T002, T003 can run in parallel (different enum files)
- T004, T005 can run in parallel (different models in same file, but logically separate)
- T006, T007 can run in parallel (different protocol files)
- T011, T012 can run in parallel (different provider builders)
- T022, T023 can run in parallel (different provider fetchers)
- T028, T029, T030, T031 can run in parallel (different admin endpoints)
- T032, T034 can run in parallel (backend and frontend)

---

## Parallel Example: User Story 1

```bash
# Launch all builder implementations together:
Task T011: "Implement AzureSSMLBuilder in backend/src/infrastructure/providers/azure/ssml_builder.py"
Task T012: "Implement ElevenLabsDialogueBuilder in backend/src/infrastructure/providers/elevenlabs/dialogue_builder.py"
```

## Parallel Example: User Story 3

```bash
# Launch all voice fetchers together:
Task T022: "Azure voice list fetching in backend/src/infrastructure/providers/azure/voice_fetcher.py"
Task T023: "ElevenLabs voice list fetching in backend/src/infrastructure/providers/elevenlabs/voice_fetcher.py"

# Launch all admin endpoints together:
Task T028: "POST /api/v1/admin/voices/sync endpoint"
Task T029: "GET /api/v1/admin/voices/sync/status endpoint"
Task T030: "GET /api/v1/admin/voices/sync/jobs endpoint"
Task T031: "GET /api/v1/admin/voices/sync/jobs/{job_id} endpoint"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T010)
3. Complete Phase 3: User Story 1 - Native Synthesis (T011-T017)
4. Complete Phase 4: User Story 2 - Age Group Filtering (T018-T021)
5. **STOP and VALIDATE**: Test US1 and US2 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Native Synthesis) → Test independently → Deploy (MVP Part 1)
3. Add US2 (Age Group Filter) → Test independently → Deploy (MVP Part 2)
4. Add US3 (Voice Sync) → Test independently → Deploy
5. Add US4 (Style Filter) → Test independently → Deploy
6. Polish phase → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Native Synthesis)
   - Developer B: User Story 2 (Age Group Filter)
3. After US1/US2:
   - Developer A: User Story 3 (Voice Sync)
   - Developer B: User Story 4 (Style Filter) - starts after US3 populates styles

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- ElevenLabs uses Text to Dialogue API (NOT `[S1][S2]` syntax per research.md)
- Azure SSML limit: 64 KB (50,000 Unicode chars conservative)
- ElevenLabs limit: 5,000 chars total
- Retry strategy: Exponential backoff 1s, 2s, 4s (max 3 times)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | T001-T003 (3) | Migration and enums |
| Phase 2: Foundational | T004-T010 (7) | Models, repositories, DI |
| Phase 3: US1 Native Synthesis | T011-T017 (7) | Azure SSML + ElevenLabs Dialogue |
| Phase 4: US2 Age Group Filter | T018-T021 (4) | API + UI filtering |
| Phase 5: US3 Voice Sync | T022-T031 (10) | Background sync + admin API |
| Phase 6: US4 Style Filter | T032-T034 (3) | Style filtering |
| Phase 7: Polish | T035-T038 (4) | Validation and cleanup |
| **Total** | **38 tasks** | |

### Tasks per User Story

- **US1**: 7 tasks (T011-T017)
- **US2**: 4 tasks (T018-T021)
- **US3**: 10 tasks (T022-T031)
- **US4**: 3 tasks (T032-T034)

### MVP Scope (Recommended)

Complete Phases 1-4 (US1 + US2) for MVP delivery: **21 tasks**
