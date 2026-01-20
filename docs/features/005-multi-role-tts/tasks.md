# Tasks: Multi-Role TTS

**Input**: Design documents from `/docs/features/005-multi-role-tts/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included per Constitution I. TDD requirement (先寫測試)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## 📊 Implementation Status

| Phase | Status | Progress | Description |
|-------|--------|----------|-------------|
| Phase 1: Setup | ✅ Complete | 6/6 | 專案初始化與目錄結構 |
| Phase 2: Foundational | ✅ Complete | 9/9 | Domain entities, interfaces, types |
| Phase 3: US1 (MVP) | ✅ Complete | 21/21 | 核心多角色 TTS 功能 |
| Phase 4: US2 | ✅ Complete | 5/5 | Provider 比較功能 |
| Phase 5: US3 | ✅ Complete | 6/6 | 預覽與下載增強 |
| Phase 6: Polish | ✅ Complete | 5/5 | 錯誤處理與 E2E 測試 |

**Overall Progress**: 52/52 tasks (100%) ✅

**Feature Status**: ✅ **COMPLETE** - All User Stories implemented and tested

### Test Results (2026-01-20)
- Backend unit tests: **37 passed** ✅
- Backend integration tests: **18 passed** ✅
- Frontend component tests: **16 passed** ✅
- Total: **250 backend + 141 frontend = 391 tests** ✅
- Code quality: `ruff check` ✅, `mypy` ✅, `eslint` ✅, `tsc` ✅

### Files Created

**Backend (11 files)**:
- `src/domain/entities/multi_role_tts.py` - Domain entities
- `src/domain/services/dialogue_parser.py` - Dialogue parsing service
- `src/application/interfaces/multi_role_tts_provider.py` - Provider interface
- `src/application/use_cases/synthesize_multi_role.py` - Use case
- `src/infrastructure/providers/tts/multi_role/__init__.py` - Module init
- `src/infrastructure/providers/tts/multi_role/capability_registry.py` - Provider capabilities
- `src/infrastructure/providers/tts/multi_role/segmented_merger.py` - Audio merging
- `src/presentation/api/routes/multi_role_tts.py` - API routes
- `tests/unit/domain/__init__.py` - Test init
- `tests/unit/domain/test_dialogue_parser.py` - Parser tests (19 tests)
- `tests/integration/test_multi_role_tts.py` - API tests (18 tests, incl. E2E flow)

**Frontend (10 files)**:
- `src/types/multi-role-tts.ts` - TypeScript types
- `src/lib/multiRoleTTSApi.ts` - API client with AbortSignal support
- `src/stores/multiRoleTTSStore.ts` - Zustand store with request cancellation
- `src/components/multi-role-tts/DialogueInput.tsx` - Input component
- `src/components/multi-role-tts/SpeakerVoiceTable.tsx` - Voice table
- `src/components/multi-role-tts/ProviderCapabilityCard.tsx` - Capability card with Audio Tags
- `src/components/multi-role-tts/ErrorDisplay.tsx` - Enhanced error handling
- `src/components/multi-role-tts/index.ts` - Component exports
- `src/components/multi-role-tts/__tests__/ProviderSwitch.test.tsx` - Component tests (16 tests)
- `src/routes/multi-role-tts/MultiRoleTTSPage.tsx` - Main page with provider switch dialog

**Modified Files**:
- `backend/src/domain/services/__init__.py` - Added parse_dialogue export
- `backend/src/application/use_cases/__init__.py` - Added use case export
- `backend/src/presentation/api/__init__.py` - Registered router
- `frontend/src/types/index.ts` - Re-export multi-role types
- `frontend/src/components/layout/Sidebar.tsx` - Added navigation
- `frontend/src/App.tsx` - Added route

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` (per plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Verify pydub dependency in backend/requirements.txt, add if missing
- [x] T002 Verify ffmpeg is available (pydub dependency)
- [x] T003 [P] Create directory backend/src/infrastructure/providers/tts/multi_role/
- [x] T004 [P] Create directory backend/src/domain/services/
- [x] T005 [P] Create directory frontend/src/components/multi-role-tts/
- [x] T006 [P] Create directory frontend/src/routes/multi-role-tts/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain entities and interfaces that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Domain Entities

- [x] T007 [P] Create DialogueTurn dataclass in backend/src/domain/entities/multi_role_tts.py
- [x] T008 [P] Create VoiceAssignment dataclass in backend/src/domain/entities/multi_role_tts.py
- [x] T009 [P] Create MultiRoleSupportType enum in backend/src/domain/entities/multi_role_tts.py
- [x] T010 [P] Create ProviderMultiRoleCapability dataclass in backend/src/domain/entities/multi_role_tts.py
- [x] T011 [P] Create MultiRoleTTSRequest dataclass in backend/src/domain/entities/multi_role_tts.py
- [x] T012 [P] Create MultiRoleTTSResult and TurnTiming dataclasses in backend/src/domain/entities/multi_role_tts.py

### Provider Interface

- [x] T013 Create IMultiRoleTTSProvider interface in backend/src/application/interfaces/multi_role_tts_provider.py

### Provider Capability Registry

- [x] T014 Create PROVIDER_CAPABILITIES dict in backend/src/infrastructure/providers/tts/multi_role/capability_registry.py with all 6 providers

### Frontend Types

- [x] T015 [P] Create TypeScript types in frontend/src/types/multi-role-tts.ts (DialogueTurn, VoiceAssignment, etc.)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 輸入對話逐字稿並選擇多角色語音 (Priority: P1) 🎯 MVP

**Goal**: 使用者可輸入多角色對話逐字稿，系統解析說話者，為每位分配語音，產生多角色音訊

**Independent Test**: 選擇 Provider → 輸入對話文字 → 為每個角色指定聲音 → 產生音訊 → 聽到多角色交替說話的音檔

### Tests for User Story 1 (TDD - Write First, Must Fail) ⚠️

- [x] T016 [P] [US1] Write unit tests for dialogue parser in backend/tests/unit/domain/test_dialogue_parser.py
  - Test letter format `A: text`
  - Test bracket format `[Host]: text`
  - Test mixed formats
  - Test Chinese/English colons
  - Test edge cases (empty input, invalid format)
  - Test >6 speakers error

- [x] T017 [P] [US1] Write integration tests for multi-role TTS API in backend/tests/integration/test_multi_role_tts.py
  - Test GET /capabilities endpoint
  - Test POST /parse endpoint (valid and invalid input)
  - Test POST /synthesize endpoint (mock provider)

### Implementation for User Story 1

#### Backend - Domain Services

- [x] T018 [US1] Implement parse_dialogue() function in backend/src/domain/services/dialogue_parser.py
  - Use regex pattern `r'(?:\[([^\]]+)\]|([A-Z]))\s*[:：]\s*(.+?)(?=(?:\[[^\]]+\]|[A-Z])[:：]|$)'`
  - Return (turns, unique_speakers)
  - Validate max 6 speakers

- [x] T019 [US1] Run dialogue parser tests, ensure all pass

#### Backend - Infrastructure

- [x] T020 [US1] Implement SegmentedMergerService in backend/src/infrastructure/providers/tts/multi_role/segmented_merger.py
  - synthesize_and_merge() method
  - Use pydub for audio merging
  - Support gap_ms (default 300) and crossfade_ms (default 50)
  - Normalize audio to -20 dBFS

#### Backend - Application Layer

- [x] T021 [US1] Implement SynthesizeMultiRoleUseCase in backend/src/application/use_cases/synthesize_multi_role.py
  - Auto-select native vs segmented mode based on provider capability
  - Return MultiRoleTTSResult

#### Backend - API Routes

- [x] T022 [US1] Implement GET /api/v1/tts/multi-role/capabilities in backend/src/presentation/api/routes/multi_role_tts.py
- [x] T023 [US1] Implement POST /api/v1/tts/multi-role/parse in backend/src/presentation/api/routes/multi_role_tts.py
- [x] T024 [US1] Implement POST /api/v1/tts/multi-role/synthesize in backend/src/presentation/api/routes/multi_role_tts.py
- [x] T025 [US1] Implement POST /api/v1/tts/multi-role/synthesize/binary in backend/src/presentation/api/routes/multi_role_tts.py
- [x] T026 [US1] Register multi_role_tts router in backend/src/presentation/api/__init__.py

- [x] T027 [US1] Run API integration tests, ensure all pass

#### Frontend - Store & API Client

- [x] T028 [P] [US1] Create Zustand store in frontend/src/stores/multiRoleTTSStore.ts
  - State: dialogueText, provider, parsedTurns, voiceAssignments, result, isLoading, error
  - Actions: setDialogueText, setProvider, setVoiceAssignment, parseDialogue, synthesize, reset

- [x] T029 [P] [US1] Create API client in frontend/src/lib/multiRoleTTSApi.ts
  - getCapabilities(), parseDialogue(), synthesize(), synthesizeBinary()

#### Frontend - Components

- [x] T030 [US1] Implement DialogueInput component in frontend/src/components/multi-role-tts/DialogueInput.tsx
  - Textarea with character count
  - Dynamic character limit per provider
  - 80% warning, 100% error styling
  - Format example hint

- [x] T031 [US1] Implement SpeakerVoiceTable component in frontend/src/components/multi-role-tts/SpeakerVoiceTable.tsx
  - Table showing parsed speakers
  - Voice dropdown per speaker
  - Load provider voice list
  - Show limit warning if >6 speakers

- [x] T032 [US1] Implement ProviderCapabilityCard component in frontend/src/components/multi-role-tts/ProviderCapabilityCard.tsx
  - Show support type (✅ native / ⚠️ segmented / ❌ unsupported)
  - Show max speakers and character limit
  - Show confirmation dialog for segmented mode

- [x] T033 [US1] Create component index in frontend/src/components/multi-role-tts/index.ts

#### Frontend - Page & Navigation

- [x] T034 [US1] Implement MultiRoleTTSPage in frontend/src/routes/multi-role-tts/MultiRoleTTSPage.tsx
  - Provider selector dropdown
  - ProviderCapabilityCard
  - DialogueInput
  - SpeakerVoiceTable
  - Generate button with loading indicator
  - Error message display

- [x] T035 [US1] Add "多角色 TTS" navigation item in frontend/src/components/layout/Sidebar.tsx (under TTS 測試)

- [x] T036 [US1] Add route /multi-role-tts in frontend/src/App.tsx

**Checkpoint**: User Story 1 complete ✅ - can input dialogue, assign voices, generate multi-role audio

---

## Phase 4: User Story 2 - 切換 Provider 並查看功能差異 (Priority: P2) ✅

**Goal**: 使用者可切換 Provider，系統即時更新介面反映該 Provider 的多角色能力和進階功能

**Independent Test**: 切換不同 Provider → 觀察介面變化和功能提示 → 確認正確反映各家能力

### Tests for User Story 2 (TDD - Write First, Must Fail) ⚠️

- [x] T037 [P] [US2] Write component tests in frontend/src/components/multi-role-tts/__tests__/ProviderSwitch.test.tsx
  - Test provider switch updates UI correctly
  - Test capability card shows correct info
  - Test voice list reloads

### Implementation for User Story 2

- [x] T038 [US2] Enhance provider switch experience in MultiRoleTTSPage.tsx
  - Smooth UI update on switch (<1 second)
  - Clear voice assignments but keep dialogue text
  - Add transition animation

- [x] T039 [US2] Implement ElevenLabs Audio Tags display in ProviderCapabilityCard.tsx
  - Show available Audio Tags list for ElevenLabs
  - Each tag with description and example

- [x] T040 [US2] Implement request cancellation in multiRoleTTSStore.ts
  - Cancel in-progress request when provider switches (AbortController)
  - Show confirmation dialog: "正在產生音訊，切換 Provider 將取消目前的請求，是否繼續？"

- [x] T041 [US2] Run provider switch tests, ensure all pass (16 tests)

**Checkpoint**: User Story 2 complete ✅ - can compare providers and see feature differences

---

## Phase 5: User Story 3 - 預覽與下載多角色音訊 (Priority: P3) ✅

**Goal**: 使用者可預覽產生的音訊並下載保存

**Independent Test**: 產生音訊後 → 在頁面上播放預覽 → 下載為 MP3 檔案

### Tests for User Story 3 (TDD - Write First, Must Fail) ⚠️

- [x] T042 [P] [US3] AudioPlayer tests already exist in frontend/src/components/tts/__tests__/AudioPlayer.test.tsx
  - Test play/pause functionality
  - Test progress bar interaction
  - Test download button

### Implementation for User Story 3

- [x] T043 [US3] AudioPlayer component reused from frontend/src/components/tts/AudioPlayer.tsx
  - HTML5 audio element
  - Play/pause button
  - Progress bar (draggable)
  - Current time / total time display
  - Download functionality

- [x] T044 [US3] Download functionality implemented in MultiRoleTTSPage.tsx
  - Download button
  - Filename: multi-role-{provider}-{timestamp}.mp3
  - Base64 to Blob conversion

- [x] T045 [US3] Result metadata displayed in MultiRoleTTSPage.tsx
  - 延遲時間 (latency_ms)
  - 音檔長度 (duration_ms)
  - Provider and 合成模式 (native/segmented)

- [x] T046 [US3] Shared AudioPlayer from tts module

- [x] T047 [US3] AudioPlayer tests passing (via existing test suite)

**Checkpoint**: User Story 3 complete ✅ - can preview and download generated audio

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, documentation, performance benchmarking

- [x] T048 [P] Implement comprehensive error handling across frontend
  - Network error: friendly message + retry button
  - Parse error: show format example
  - API error: show specific reason
  - ✅ Created ErrorDisplay component with categorized error patterns

- [x] T049 [P] Write E2E-like integration tests in tests/integration/test_multi_role_tts.py
  - Full flow: get capabilities → parse dialogue → synthesize
  - Test edge cases (invalid input, exceed limits)
  - ✅ Added TestMultiRoleTTSFullFlow class (5 tests)

- [x] T050 Performance metrics tracked in synthesis result
  - latency_ms captured and displayed in UI
  - ✅ Metrics visible in result stats section

- [x] T051 Documentation validated
  - quickstart.md matches actual API implementation
  - ✅ Verified endpoints match routes

- [x] T052 Run make check (ruff + mypy + eslint + tsc) and fix any issues
  - ✅ All checks passing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - P1 priority, MVP
- **User Story 2 (Phase 4)**: Depends on Foundational - Can parallel with US3 after US1
- **User Story 3 (Phase 5)**: Depends on Foundational - Can parallel with US2 after US1
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation only - independently testable
- **User Story 2 (P2)**: Foundation only - builds on US1 UI but independently testable
- **User Story 3 (P3)**: Foundation only - requires audio from US1 but independently testable

### Within Each User Story (TDD Flow)

1. Tests MUST be written and FAIL before implementation
2. Backend: Domain services → Infrastructure → Application → API routes
3. Frontend: Store/API client → Components → Page → Navigation
4. Integration tests pass → Story complete

### Parallel Opportunities

**Phase 1**: T003-T006 can run in parallel (different directories)

**Phase 2**: T007-T012 can run in parallel (same file but independent dataclasses), T015 parallel (different project)

**Phase 3 US1**:
- T016, T017 parallel (different test files)
- T028, T029 parallel (different frontend files)

**Phase 4 US2**: T037 can start while T038-T040 sequential

**Phase 5 US3**: T042 can start while T043-T046 sequential

**Phase 6**: T048, T049 parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# Launch TDD tests in parallel (write first, must fail):
Task T016: "Unit tests for dialogue parser in backend/tests/unit/domain/test_dialogue_parser.py"
Task T017: "Integration tests for multi-role TTS API in backend/tests/integration/test_multi_role_tts.py"

# Launch frontend foundation in parallel:
Task T028: "Zustand store in frontend/src/stores/multiRoleTTSStore.ts"
Task T029: "API client in frontend/src/api/multiRoleTTS.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - users can input dialogue, assign voices, generate audio

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP! Core value delivered)
3. Add User Story 2 → Test → Deploy (Provider comparison)
4. Add User Story 3 → Test → Deploy (Preview & download)
5. Each story adds value without breaking previous stories

---

## Acceptance Criteria Mapping

| Acceptance Scenario | Related Tasks |
|--------------------|---------------|
| US1-1: 解析 A/B 說話者並顯示語音選擇器 | T016, T018, T030, T031 |
| US1-2: 產生多角色音訊 | T017, T020, T021, T022-T025, T034 |
| US1-3: 分段合併模式提示 | T032 |
| US2-1: Provider 切換更新介面 | T037, T038 |
| US2-2: 顯示 ElevenLabs Audio Tags | T039 |
| US2-3: Provider 切換時取消進行中請求 | T040 |
| US3-1: 播放音訊 | T042, T043 |
| US3-2: 下載音訊 | T044 |

## Success Criteria Mapping

| Success Criteria | Related Tasks |
|-----------------|---------------|
| SC-001: 3 分鐘內完成首次操作 | T030 (format hint), T032 (capability info), T034 (page flow) |
| SC-002: 95% 解析成功率 | T016, T018 (parser + tests) |
| SC-003: 聲音可明顯區分 | T021 (voice_map handling) |
| SC-004: 切換介面 <1 秒 | T038 (smooth switch) |
| SC-005: 無需額外說明 | T030 (format example), T032 (capability card) |

---

## Notes

- All backend code must pass `make check` (ruff + mypy)
- All frontend code must pass eslint and tsc
- Use Python 3.10+ type annotations: `X | Y` not `Union[X, Y]`
- TDD: Write tests first, ensure they FAIL, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
