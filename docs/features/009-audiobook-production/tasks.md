# Tasks: Audiobook Production System

**Input**: Design documents from `/docs/features/009-audiobook-production/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Tests**: Tests are NOT included unless explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`, `backend/alembic/`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and project initialization

- [ ] T001 Create Alembic migration for audiobook tables (audiobook_projects, audiobook_characters, audiobook_script_turns, audiobook_generation_jobs, audiobook_background_music) in `backend/alembic/versions/xxx_add_audiobook_tables.py`
- [ ] T002 [P] Add ProjectStatus enum to `backend/src/domain/entities/audiobook_project.py`
- [ ] T003 [P] Add TurnStatus enum to `backend/src/domain/entities/script_turn.py`
- [ ] T004 [P] Add JobStatus enum to `backend/src/domain/entities/audiobook_job.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create AudiobookProject entity in `backend/src/domain/entities/audiobook_project.py`
- [ ] T006 [P] Create Character entity in `backend/src/domain/entities/character.py`
- [ ] T007 [P] Create ScriptTurn entity in `backend/src/domain/entities/script_turn.py`
- [ ] T008 [P] Create AudiobookGenerationJob entity in `backend/src/domain/entities/audiobook_job.py`
- [ ] T009 [P] Create BackgroundMusic entity in `backend/src/domain/entities/background_music.py`
- [ ] T010 Create AudiobookProjectModel in `backend/src/infrastructure/persistence/models.py`
- [ ] T011 [P] Create CharacterModel in `backend/src/infrastructure/persistence/models.py`
- [ ] T012 [P] Create ScriptTurnModel in `backend/src/infrastructure/persistence/models.py`
- [ ] T013 [P] Create AudiobookGenerationJobModel in `backend/src/infrastructure/persistence/models.py`
- [ ] T014 [P] Create BackgroundMusicModel in `backend/src/infrastructure/persistence/models.py`
- [ ] T015 Define AudiobookProjectRepository protocol in `backend/src/application/interfaces/audiobook_repository.py`
- [ ] T016 [P] Define CharacterRepository protocol in `backend/src/application/interfaces/audiobook_repository.py`
- [ ] T017 [P] Define ScriptTurnRepository protocol in `backend/src/application/interfaces/audiobook_repository.py`
- [ ] T018 Implement AudiobookProjectRepositoryImpl in `backend/src/infrastructure/persistence/audiobook_repository.py`
- [ ] T019 [P] Implement CharacterRepositoryImpl in `backend/src/infrastructure/persistence/audiobook_repository.py`
- [ ] T020 [P] Implement ScriptTurnRepositoryImpl in `backend/src/infrastructure/persistence/audiobook_repository.py`
- [ ] T021 Register repositories in dependency injection container

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 建立故事專案與劇本編輯 (Priority: P1) 🎯 MVP

**Goal**: 使用者可建立專案、輸入劇本、系統自動識別角色

**Independent Test**: 建立專案、貼上劇本、驗證角色自動識別並可編輯

### Implementation for User Story 1

- [ ] T022 [P] [US1] Implement ScriptParser.parse() for extracting characters and turns in `backend/src/infrastructure/audio/script_parser.py`
- [ ] T023 [US1] Create CreateAudiobookProjectUseCase in `backend/src/application/use_cases/create_audiobook_project.py`
- [ ] T024 [US1] Create UpdateScriptUseCase (parse script, upsert characters, create turns) in `backend/src/application/use_cases/update_script.py`
- [ ] T025 [P] [US1] Add POST /api/v1/audiobook/projects endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T026 [P] [US1] Add GET /api/v1/audiobook/projects endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T027 [P] [US1] Add GET /api/v1/audiobook/projects/{id} endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T028 [P] [US1] Add PATCH /api/v1/audiobook/projects/{id} endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T029 [P] [US1] Add DELETE /api/v1/audiobook/projects/{id} endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T030 [US1] Add PUT /api/v1/audiobook/projects/{id}/script endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T031 [US1] Create Pydantic schemas for project requests/responses in `backend/src/presentation/api/schemas/audiobook.py`
- [ ] T032 [US1] Create AudiobookList page component in `frontend/src/pages/AudiobookList.tsx`
- [ ] T033 [US1] Create AudiobookEditor page component in `frontend/src/pages/AudiobookEditor.tsx`
- [ ] T034 [US1] Create ScriptEditor component in `frontend/src/components/ScriptEditor/index.tsx`
- [ ] T035 [US1] Create audiobookStore (Zustand) in `frontend/src/stores/audiobookStore.ts`
- [ ] T036 [US1] Add routing for audiobook pages in `frontend/src/App.tsx`

**Checkpoint**: Users can create projects, paste scripts, and see auto-detected characters

---

## Phase 4: User Story 2 - 角色聲音設定與預覽 (Priority: P1)

**Goal**: 使用者可為每個角色選擇聲音並預覽效果

**Independent Test**: 選擇角色聲音、預覽單句台詞、確認聲音符合預期

### Implementation for User Story 2

- [ ] T037 [US2] Create PreviewCharacterVoiceUseCase in `backend/src/application/use_cases/preview_character_voice.py`
- [ ] T038 [P] [US2] Add GET /api/v1/audiobook/projects/{id}/characters endpoint in `backend/src/presentation/api/routes/audiobook_characters.py`
- [ ] T039 [P] [US2] Add PATCH /api/v1/audiobook/projects/{id}/characters/{char_id} endpoint in `backend/src/presentation/api/routes/audiobook_characters.py`
- [ ] T040 [US2] Add POST /api/v1/audiobook/projects/{id}/characters/{char_id}/preview endpoint in `backend/src/presentation/api/routes/audiobook_characters.py`
- [ ] T041 [US2] Create CharacterPanel component in `frontend/src/components/CharacterPanel/index.tsx`
- [ ] T042 [US2] Integrate VoiceSelector (from 008) into CharacterPanel in `frontend/src/components/CharacterPanel/VoiceSelection.tsx`
- [ ] T043 [US2] Create AudioPreview component in `frontend/src/components/AudioPreview/index.tsx`
- [ ] T044 [US2] Add character state management to audiobookStore in `frontend/src/stores/audiobookStore.ts`

**Checkpoint**: Users can select voices for characters and preview their sound

---

## Phase 5: User Story 3 - 非同步故事生成 (Priority: P1)

**Goal**: 使用者可啟動生成、查看進度、下載完成的音訊

**Independent Test**: 啟動生成、查看進度、等待完成、下載結果

### Implementation for User Story 3

- [ ] T045 [US3] Create GenerateAudiobookUseCase in `backend/src/application/use_cases/generate_audiobook.py`
- [ ] T046 [US3] Implement AudiobookWorker (process turns, retry logic) in `backend/src/infrastructure/workers/audiobook_worker.py`
- [ ] T047 [US3] Implement audio merging logic using pydub in `backend/src/infrastructure/audio/audio_merger.py`
- [ ] T048 [US3] Register audiobook_generation job type in JobWorker `backend/src/infrastructure/workers/job_worker.py`
- [ ] T049 [P] [US3] Add POST /api/v1/audiobook/projects/{id}/generate endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T050 [P] [US3] Add GET /api/v1/audiobook/projects/{id}/jobs endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T051 [P] [US3] Add GET /api/v1/audiobook/projects/{id}/jobs/{job_id} endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T052 [P] [US3] Add POST /api/v1/audiobook/projects/{id}/jobs/{job_id}/cancel endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T053 [US3] Add GET /api/v1/audiobook/projects/{id}/turns endpoint in `backend/src/presentation/api/routes/audiobook_characters.py`
- [ ] T054 [US3] Create GenerationProgress component in `frontend/src/components/GenerationProgress/index.tsx`
- [ ] T055 [US3] Implement polling for job status in audiobookStore in `frontend/src/stores/audiobookStore.ts`
- [ ] T056 [US3] Add download button and audio player for completed audiobook in `frontend/src/pages/AudiobookEditor.tsx`

**Checkpoint**: Users can generate full audiobooks asynchronously with progress tracking

---

## Phase 6: User Story 4 - 背景音樂融合 (Priority: P2)

**Goal**: 使用者可上傳背景音樂、調整音量、混音

**Independent Test**: 上傳背景音樂、調整音量、預覽混音效果、匯出最終版本

### Implementation for User Story 4

- [ ] T057 [US4] Create UploadBackgroundMusicUseCase in `backend/src/application/use_cases/upload_background_music.py`
- [ ] T058 [US4] Create MixAudioUseCase in `backend/src/application/use_cases/mix_audio.py`
- [ ] T059 [US4] Implement AudioMixer (overlay, loop, fade) using pydub in `backend/src/infrastructure/audio/audio_mixer.py`
- [ ] T060 [P] [US4] Add POST /api/v1/audiobook/projects/{id}/background-music endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T061 [P] [US4] Add DELETE /api/v1/audiobook/projects/{id}/background-music endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T062 [US4] Add POST /api/v1/audiobook/projects/{id}/mix endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T063 [US4] Create BackgroundMusicUploader component in `frontend/src/components/BackgroundMusicUploader/index.tsx`
- [ ] T064 [US4] Add volume slider and mix button to AudiobookEditor in `frontend/src/pages/AudiobookEditor.tsx`

**Checkpoint**: Users can add background music and create mixed audiobooks

---

## Phase 7: User Story 5 - 專案管理與匯出 (Priority: P2)

**Goal**: 使用者可管理多個專案、複製專案、匯出成品

**Independent Test**: 列出專案、複製專案、匯出為 MP3/WAV

### Implementation for User Story 5

- [ ] T065 [US5] Create DuplicateProjectUseCase in `backend/src/application/use_cases/duplicate_project.py`
- [ ] T066 [US5] Create ExportAudiobookUseCase in `backend/src/application/use_cases/export_audiobook.py`
- [ ] T067 [US5] Implement MP3 export with ID3 metadata in `backend/src/infrastructure/audio/audio_exporter.py`
- [ ] T068 [P] [US5] Add POST /api/v1/audiobook/projects/{id}/duplicate endpoint in `backend/src/presentation/api/routes/audiobook_projects.py`
- [ ] T069 [P] [US5] Add POST /api/v1/audiobook/projects/{id}/export endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T070 [P] [US5] Add GET /api/v1/audiobook/projects/{id}/export endpoint in `backend/src/presentation/api/routes/audiobook_generation.py`
- [ ] T071 [US5] Add duplicate button to project list in `frontend/src/pages/AudiobookList.tsx`
- [ ] T072 [US5] Create ExportDialog component in `frontend/src/components/ExportDialog/index.tsx`

**Checkpoint**: Users can manage multiple projects and export final audiobooks

---

## Phase 8: User Story 6 - 章節與書籤功能 (Priority: P3)

**Goal**: 使用者可將長篇故事分成多個章節

**Independent Test**: 建立章節、設定章節標題、在輸出中包含章節標記

### Implementation for User Story 6

- [ ] T073 [US6] Enhance ScriptParser to detect chapter markers in `backend/src/infrastructure/audio/script_parser.py`
- [ ] T074 [US6] Add chapter field handling in ScriptTurnRepository in `backend/src/infrastructure/persistence/audiobook_repository.py`
- [ ] T075 [US6] Add ID3 chapter markers to MP3 export in `backend/src/infrastructure/audio/audio_exporter.py`
- [ ] T076 [US6] Add chapter navigation UI to ScriptEditor in `frontend/src/components/ScriptEditor/ChapterNav.tsx`

**Checkpoint**: Users can organize scripts into chapters with markers in exported files

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T077 Run `make check` and fix any linting/type errors
- [ ] T078 Validate quickstart.md examples work correctly
- [ ] T079 Update CLAUDE.md with 009 feature information
- [ ] T080 Add error handling for edge cases (empty script, missing voices, etc.)
- [ ] T081 Add loading states and error messages to frontend components

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T004) completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 and US2 are both P1, can proceed in parallel after US1 T022-T030 (need characters)
  - US3 (P1) depends on US2 (needs voice settings)
  - US4 (P2) depends on US3 (needs generated audio to mix)
  - US5 (P2) can start after US3 (needs generation complete for export)
  - US6 (P3) can start after US1 (extends script parser)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

```
US1 (Project & Script) ──┬──► US2 (Voice Settings) ──► US3 (Generation)
                         │                                    │
                         │                                    ▼
                         │                              US4 (Background Music)
                         │                                    │
                         │                                    ▼
                         │                              US5 (Export)
                         │
                         └──► US6 (Chapters) ─────────────────┘
```

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different enum files)
- T006-T009 can run in parallel (different entity files)
- T011-T014 can run in parallel (different models)
- T025-T029 can run in parallel (different CRUD endpoints)
- T049-T052 can run in parallel (different generation endpoints)
- T060, T061 can run in parallel (upload/delete endpoints)

---

## Parallel Example: User Story 1 Backend

```bash
# Launch all CRUD endpoints together:
Task T025: "POST /api/v1/audiobook/projects endpoint"
Task T026: "GET /api/v1/audiobook/projects endpoint"
Task T027: "GET /api/v1/audiobook/projects/{id} endpoint"
Task T028: "PATCH /api/v1/audiobook/projects/{id} endpoint"
Task T029: "DELETE /api/v1/audiobook/projects/{id} endpoint"
```

## Parallel Example: User Story 3 Backend

```bash
# Launch all generation endpoints together:
Task T049: "POST /api/v1/audiobook/projects/{id}/generate endpoint"
Task T050: "GET /api/v1/audiobook/projects/{id}/jobs endpoint"
Task T051: "GET /api/v1/audiobook/projects/{id}/jobs/{job_id} endpoint"
Task T052: "POST /api/v1/audiobook/projects/{id}/jobs/{job_id}/cancel endpoint"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T021)
3. Complete Phase 3: User Story 1 - Project & Script (T022-T036)
4. Complete Phase 4: User Story 2 - Voice Settings (T037-T044)
5. Complete Phase 5: User Story 3 - Generation (T045-T056)
6. **STOP and VALIDATE**: Test full generation workflow
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Project & Script) → Test independently → Deploy (Users can create projects)
3. Add US2 (Voice Settings) → Test independently → Deploy (Users can configure voices)
4. Add US3 (Generation) → Test independently → Deploy (MVP Complete!)
5. Add US4 (Background Music) → Test independently → Deploy
6. Add US5 (Export) → Test independently → Deploy
7. Add US6 (Chapters) → Test independently → Deploy
8. Polish phase → Final release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Depends on 008 for voice selection API (VoiceSelector component)
- Depends on 007 for JobWorker architecture
- pydub is used for all audio processing (merge, mix, export)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | T001-T004 (4) | Migration and enums |
| Phase 2: Foundational | T005-T021 (17) | Entities, models, repositories |
| Phase 3: US1 Project & Script | T022-T036 (15) | Project CRUD, script parsing |
| Phase 4: US2 Voice Settings | T037-T044 (8) | Character config, preview |
| Phase 5: US3 Generation | T045-T056 (12) | Async generation, progress |
| Phase 6: US4 Background Music | T057-T064 (8) | Upload, mix |
| Phase 7: US5 Export | T065-T072 (8) | Duplicate, export |
| Phase 8: US6 Chapters | T073-T076 (4) | Chapter markers |
| Phase 9: Polish | T077-T081 (5) | Validation and cleanup |
| **Total** | **81 tasks** | |

### Tasks per User Story

- **US1 (P1)**: 15 tasks (T022-T036)
- **US2 (P1)**: 8 tasks (T037-T044)
- **US3 (P1)**: 12 tasks (T045-T056)
- **US4 (P2)**: 8 tasks (T057-T064)
- **US5 (P2)**: 8 tasks (T065-T072)
- **US6 (P3)**: 4 tasks (T073-T076)

### MVP Scope (Recommended)

Complete Phases 1-5 (US1 + US2 + US3) for MVP delivery: **56 tasks**

This delivers:
- Project creation and management
- Script parsing with character detection
- Voice selection and preview
- Full async audiobook generation
- Progress tracking and download
