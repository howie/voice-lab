# Tasks: STT Speech-to-Text Testing Module

**Input**: Design documents from `/docs/features/003-stt-testing-module/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/stt-api.yaml

**Tests**: Test tasks included - following existing project TDD patterns from 001/002 features.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend follows Clean Architecture: domain → application → infrastructure → presentation
- Frontend uses React with routes, components, services, stores, types

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and STT module structure

- [ ] T001 Create STT provider directory structure in backend/src/infrastructure/providers/stt/
- [ ] T002 [P] Create STT domain entities directory structure in backend/src/domain/entities/
- [ ] T003 [P] Create STT frontend directory structure in frontend/src/components/stt/
- [ ] T004 [P] Add STT TypeScript types in frontend/src/types/stt.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Domain Layer

- [ ] T005 Extend existing STTRequest entity with persistence fields in backend/src/domain/entities/stt.py
- [ ] T006 [P] Create AudioFile entity in backend/src/domain/entities/audio_file.py
- [ ] T007 [P] Create WERAnalysis entity in backend/src/domain/entities/wer_analysis.py
- [ ] T008 [P] Create GroundTruth entity in backend/src/domain/entities/ground_truth.py
- [ ] T009 Create Alembic migration for STT tables (audio_files, transcription_requests, transcription_results, wer_analyses, ground_truths)

### STT Provider Abstraction Layer

- [ ] T010 Define ISTTProvider interface in backend/src/application/interfaces/stt_provider.py
- [ ] T011 Create BaseSTTProvider abstract class in backend/src/infrastructure/providers/stt/base.py
- [ ] T012 [P] Implement AzureSTTProvider in backend/src/infrastructure/providers/stt/azure_stt.py
- [ ] T013 [P] Implement GCPSTTProvider in backend/src/infrastructure/providers/stt/gcp_stt.py
- [ ] T014 [P] Implement WhisperSTTProvider in backend/src/infrastructure/providers/stt/whisper_stt.py
- [ ] T015 Create STTProviderFactory in backend/src/infrastructure/providers/stt/factory.py

### Repository Layer

- [ ] T016 Create TranscriptionRepository interface in backend/src/domain/repositories/transcription_repository.py
- [ ] T017 Implement TranscriptionRepositoryImpl in backend/src/infrastructure/persistence/transcription_repository_impl.py

### Service Layer

- [ ] T018 Create STTService in backend/src/application/services/stt_service.py (orchestrates providers + repository)

### API Routes Setup

- [ ] T019 Create STT routes blueprint in backend/src/presentation/api/stt_routes.py (skeleton only)
- [ ] T020 Register STT routes in backend/src/presentation/api/__init__.py

### Frontend Foundation

- [ ] T021 Create STT API client in frontend/src/services/sttApi.ts
- [ ] T022 Create STT store in frontend/src/stores/sttStore.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Upload Audio File for Transcription (Priority: P1) 🎯 MVP

**Goal**: Users can upload audio files and transcribe them using selected STT provider

**Independent Test**: Upload a test MP3 file, select Azure STT, verify transcribed text is returned with confidence score and latency

### Tests for User Story 1

- [ ] T023 [P] [US1] Contract test for POST /stt/transcribe endpoint in backend/tests/contract/test_stt_transcribe_contract.py
- [ ] T024 [P] [US1] Contract test for GET /stt/providers endpoint in backend/tests/contract/test_stt_providers_contract.py
- [ ] T025 [P] [US1] Unit test for STTService.transcribe() in backend/tests/unit/test_stt_service.py
- [ ] T026 [P] [US1] Integration test for file upload flow in backend/tests/integration/test_stt_upload_integration.py

### Implementation for User Story 1

- [ ] T027 [US1] Implement GET /stt/providers endpoint in backend/src/presentation/api/stt_routes.py
- [ ] T028 [US1] Implement POST /stt/transcribe endpoint in backend/src/presentation/api/stt_routes.py
- [ ] T029 [US1] Add audio file validation (format, size limits) in backend/src/application/services/stt_service.py
- [ ] T030 [US1] Implement audio file storage logic in backend/src/infrastructure/storage/audio_storage.py
- [ ] T031 [P] [US1] Create AudioUploader component in frontend/src/components/stt/AudioUploader.tsx
- [ ] T032 [P] [US1] Create ProviderSelector component in frontend/src/components/stt/ProviderSelector.tsx
- [ ] T033 [P] [US1] Create TranscriptDisplay component in frontend/src/components/stt/TranscriptDisplay.tsx
- [ ] T034 [US1] Create STTTest page in frontend/src/routes/STTTest.tsx
- [ ] T035 [US1] Add STT route to frontend router in frontend/src/App.tsx
- [ ] T036 [US1] Implement file upload flow in STT store (sttStore.ts)

**Checkpoint**: User Story 1 complete - users can upload audio and get transcriptions

---

## Phase 4: User Story 2 - Real-time Microphone Recording (Priority: P2)

**Goal**: Users can record audio via microphone and submit for batch transcription

**Independent Test**: Click record, speak for 5 seconds, stop recording, verify audio is sent to STT provider and transcript is displayed

### Tests for User Story 2

- [ ] T037 [P] [US2] Unit test for AudioRecorder component in frontend/tests/stt/AudioRecorder.test.tsx
- [ ] T038 [P] [US2] Integration test for recording → transcribe flow in backend/tests/integration/test_stt_recording_integration.py

### Implementation for User Story 2

- [ ] T039 [US2] Create AudioRecorder component with MediaRecorder API in frontend/src/components/stt/AudioRecorder.tsx
- [ ] T040 [US2] Create WaveformDisplay component (reuse TTS pattern) in frontend/src/components/shared/WaveformDisplay.tsx
- [ ] T041 [US2] Implement Safari fallback (WebM → MP4) in AudioRecorder component
- [ ] T042 [US2] Add microphone permission handling in frontend/src/components/stt/AudioRecorder.tsx
- [ ] T043 [US2] Integrate AudioRecorder into STTTest page in frontend/src/routes/STTTest.tsx
- [ ] T044 [US2] Add recording state management to STT store (sttStore.ts)

**Checkpoint**: User Story 2 complete - users can record and transcribe via microphone

---

## Phase 5: User Story 3 - WER/CER Calculation (Priority: P3)

**Goal**: Users can input ground truth text and see WER/CER accuracy metrics

**Independent Test**: Complete a transcription, enter correct text, verify WER/CER is calculated with insertion/deletion/substitution breakdown

### Tests for User Story 3

- [ ] T045 [P] [US3] Unit test for WER calculation in backend/tests/unit/test_wer_calculator.py
- [ ] T046 [P] [US3] Unit test for CER calculation in backend/tests/unit/test_wer_calculator.py
- [ ] T047 [P] [US3] Contract test for POST /stt/analysis/wer endpoint in backend/tests/contract/test_stt_wer_contract.py

### Implementation for User Story 3

- [ ] T048 [US3] Extend WERCalculator with CER support in backend/src/domain/services/wer_calculator.py
- [ ] T049 [US3] Add language-based WER/CER auto-selection in backend/src/domain/services/wer_calculator.py
- [ ] T050 [US3] Implement alignment visualization logic in backend/src/domain/services/wer_calculator.py
- [ ] T051 [US3] Implement POST /stt/analysis/wer endpoint in backend/src/presentation/api/stt_routes.py
- [ ] T052 [US3] Create WERDisplay component in frontend/src/components/stt/WERDisplay.tsx
- [ ] T053 [US3] Create GroundTruthInput component in frontend/src/components/stt/GroundTruthInput.tsx
- [ ] T054 [US3] Integrate WER display into STTTest page in frontend/src/routes/STTTest.tsx

**Checkpoint**: User Story 3 complete - users can calculate and view accuracy metrics

---

## Phase 6: User Story 4 - Child Voice Mode Testing (Priority: P4)

**Goal**: Users can enable child voice optimization when available on selected provider

**Independent Test**: Upload child voice audio, enable child mode, compare results with child mode on/off

### Tests for User Story 4

- [ ] T055 [P] [US4] Unit test for child mode parameter handling in backend/tests/unit/test_stt_provider_child_mode.py

### Implementation for User Story 4

- [ ] T056 [US4] Add child_mode parameter to Azure provider (phrase hints) in backend/src/infrastructure/providers/stt/azure_stt.py
- [ ] T057 [US4] Add child_mode parameter to GCP provider (model selection) in backend/src/infrastructure/providers/stt/gcp_stt.py
- [ ] T058 [US4] Add ChildModeToggle component in frontend/src/components/stt/ChildModeToggle.tsx
- [ ] T059 [US4] Show child mode availability per provider in ProviderSelector component
- [ ] T060 [US4] Integrate child mode toggle into STTTest page

**Checkpoint**: User Story 4 complete - users can test child voice optimization

---

## Phase 7: Multi-Provider Comparison & History

**Goal**: Users can compare results across providers and view transcription history

**Independent Test**: Upload audio, select 3 providers for comparison, verify side-by-side results; view history list, delete an entry

### Tests for Phase 7

- [ ] T061 [P] Contract test for POST /stt/compare endpoint in backend/tests/contract/test_stt_compare_contract.py
- [ ] T062 [P] Contract test for GET /stt/history endpoint in backend/tests/contract/test_stt_history_contract.py
- [ ] T063 [P] Contract test for DELETE /stt/history/{id} endpoint in backend/tests/contract/test_stt_history_contract.py

### Implementation for Phase 7

- [ ] T064 Implement POST /stt/compare endpoint in backend/src/presentation/api/stt_routes.py
- [ ] T065 Implement GET /stt/history endpoint with pagination in backend/src/presentation/api/stt_routes.py
- [ ] T066 Implement GET /stt/history/{id} endpoint in backend/src/presentation/api/stt_routes.py
- [ ] T067 Implement DELETE /stt/history/{id} endpoint in backend/src/presentation/api/stt_routes.py
- [ ] T068 [P] Create ProviderComparison component in frontend/src/components/stt/ProviderComparison.tsx
- [ ] T069 [P] Create TranscriptionHistory component in frontend/src/components/stt/TranscriptionHistory.tsx
- [ ] T070 Create STTHistory page in frontend/src/routes/STTHistory.tsx
- [ ] T071 Add history route to frontend router

**Checkpoint**: Comparison and history features complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T072 [P] Add error handling and user-friendly error messages across all STT endpoints
- [ ] T073 [P] Add logging for STT operations in backend services
- [ ] T074 [P] Implement provider-specific file size/duration limit display in frontend
- [ ] T075 [P] Add auto-segmentation for long audio files exceeding provider limits
- [ ] T076 Run quickstart.md validation - verify all documented API calls work
- [ ] T077 Performance optimization - ensure batch transcription < 30s for 1-min audio
- [ ] T078 Security review - validate BYOL key handling follows 002 feature patterns

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 can proceed independently
  - US2 can proceed independently (may reuse US1 components)
  - US3 can proceed independently (needs transcription result from US1 or US2)
  - US4 can proceed independently (extends US1 provider logic)
- **Comparison & History (Phase 7)**: Benefits from US1 completion but can start in parallel
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses components from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires a transcription result (can mock)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Extends provider implementations

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before services
- Services before API endpoints
- Backend before frontend (for API-dependent components)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational provider implementations (T012, T013, T014) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel
- All tests for a user story marked [P] can run in parallel
- Frontend components marked [P] within a story can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: T023 "Contract test for POST /stt/transcribe"
Task: T024 "Contract test for GET /stt/providers"
Task: T025 "Unit test for STTService.transcribe()"
Task: T026 "Integration test for file upload flow"

# Launch all frontend components for User Story 1 together:
Task: T031 "Create AudioUploader component"
Task: T032 "Create ProviderSelector component"
Task: T033 "Create TranscriptDisplay component"
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all provider implementations in parallel:
Task: T012 "Implement AzureSTTProvider"
Task: T013 "Implement GCPSTTProvider"
Task: T014 "Implement WhisperSTTProvider"

# Launch all entity definitions in parallel:
Task: T006 "Create AudioFile entity"
Task: T007 "Create WERAnalysis entity"
Task: T008 "Create GroundTruth entity"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Upload & Transcribe)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - **this is a functional STT testing platform**

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (adds recording)
4. Add User Story 3 → Test independently → Deploy/Demo (adds WER metrics)
5. Add User Story 4 → Test independently → Deploy/Demo (adds child voice)
6. Add Phase 7 → Test independently → Deploy/Demo (adds comparison & history)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + Phase 7 (core flow + comparison)
   - Developer B: User Story 2 + User Story 4 (recording + child mode)
   - Developer C: User Story 3 (WER/CER calculation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Batch mode only** - Streaming deferred to Phase 4 Interaction Module
- Provider-specific limits: Azure 200MB, GCP 480MB, Whisper 25MB
- WER for English, CER for CJK languages (zh-TW, zh-CN, ja-JP, ko-KR)
