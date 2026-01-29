# Tasks: TTS 角色管理介面

**Input**: Design documents from `/docs/features/013-tts-role-mgmt/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDD 流程已在 constitution.md 中定義，本任務清單包含測試任務。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and base type definitions

- [ ] T001 Create Alembic migration for voice_customization table in backend/alembic/versions/013_create_voice_customization.py
- [ ] T002 [P] Create VoiceCustomization domain entity in backend/src/domain/entities/voice_customization.py
- [ ] T003 [P] Create IVoiceCustomizationRepository interface in backend/src/domain/repositories/voice_customization.py
- [ ] T004 [P] Create VoiceCustomization TypeScript types in frontend/src/types/voice-customization.ts
- [ ] T005 [P] Create Pydantic schemas for API in backend/src/presentation/api/schemas/voice_customization.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create VoiceCustomizationModel SQLAlchemy model in backend/src/infrastructure/persistence/models.py
- [ ] T007 Create VoiceCustomizationRepositoryImpl in backend/src/infrastructure/persistence/voice_customization_repository_impl.py
- [ ] T008 Register VoiceCustomizationRepository in dependency container in backend/src/infrastructure/container.py
- [ ] T009 [P] Create voiceCustomizationApi service in frontend/src/services/voiceCustomizationApi.ts
- [ ] T010 [P] Create voiceManagementStore Zustand store in frontend/src/stores/voiceManagementStore.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 自訂角色顯示名稱 (Priority: P1) 🎯 MVP

**Goal**: 讓使用者能夠為 TTS 角色設定自訂顯示名稱

**Independent Test**: 編輯一個角色的顯示名稱，然後確認該名稱在 TTS 設定選單中正確顯示

### Tests for User Story 1

- [ ] T011 [P] [US1] Unit test for UpdateVoiceCustomizationUseCase in backend/tests/unit/use_cases/test_update_voice_customization.py
- [ ] T012 [P] [US1] Integration test for PUT /voice-customizations/{id} in backend/tests/integration/api/test_voice_customization_api.py

### Implementation for User Story 1

- [ ] T013 [US1] Create UpdateVoiceCustomizationUseCase in backend/src/application/use_cases/update_voice_customization.py
- [ ] T014 [US1] Create GetVoiceCustomizationUseCase in backend/src/application/use_cases/get_voice_customization.py
- [ ] T015 [US1] Create voice_customizations API routes (GET, PUT, DELETE) in backend/src/presentation/api/routes/voice_customizations.py
- [ ] T016 [US1] Register voice_customizations routes in backend/src/presentation/api/routes/__init__.py
- [ ] T017 [P] [US1] Create VoiceNameEditor component in frontend/src/components/voice-management/VoiceNameEditor.tsx
- [ ] T018 [P] [US1] Create VoiceCustomizationRow component in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
- [ ] T019 [US1] Create VoiceManagementTable component in frontend/src/components/voice-management/VoiceManagementTable.tsx
- [ ] T020 [US1] Create VoiceManagementPage route in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [ ] T021 [US1] Add route for /voice-management in frontend/src/App.tsx
- [ ] T022 [US1] Add sidebar navigation link for 角色管理 in frontend/src/components/layout/Sidebar.tsx
- [ ] T023 [US1] Modify ListVoicesUseCase to include display_name in backend/src/application/use_cases/list_voices.py
- [ ] T024 [US1] Modify GET /voices endpoint to return display_name, is_favorite, is_hidden in backend/src/presentation/api/routes/voices.py
- [ ] T025 [US1] Modify VoiceSelector to display display_name instead of name in frontend/src/components/tts/VoiceSelector.tsx

**Checkpoint**: User Story 1 完成 - 使用者可以自訂角色名稱並在 TTS 選單中看到

---

## Phase 4: User Story 2 - 收藏常用角色 (Priority: P2)

**Goal**: 讓使用者能夠收藏常用角色，並在選單中優先顯示

**Independent Test**: 收藏一個角色，然後確認該角色在 TTS 選擇介面中排在最上方

### Tests for User Story 2

- [ ] T026 [P] [US2] Unit test for favorite toggle logic in backend/tests/unit/use_cases/test_update_voice_customization.py (extend)
- [ ] T027 [P] [US2] Integration test for favorite sorting in backend/tests/integration/api/test_voice_customization_api.py (extend)

### Implementation for User Story 2

- [ ] T028 [P] [US2] Create FavoriteToggle component in frontend/src/components/voice-management/FavoriteToggle.tsx
- [ ] T029 [US2] Add toggleFavorite action to voiceManagementStore in frontend/src/stores/voiceManagementStore.ts
- [ ] T030 [US2] Integrate FavoriteToggle into VoiceCustomizationRow in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
- [ ] T031 [US2] Modify ListVoicesUseCase to sort favorites first in backend/src/application/use_cases/list_voices.py
- [ ] T032 [US2] Modify VoiceSelector to sort favorites to top in frontend/src/components/tts/VoiceSelector.tsx

**Checkpoint**: User Story 2 完成 - 收藏角色會在選單最上方顯示

---

## Phase 5: User Story 4 - 瀏覽和篩選角色 (Priority: P2)

**Goal**: 讓使用者能夠按提供者、語言、性別等條件篩選角色

**Independent Test**: 選擇特定提供者（如 VoAI），確認只顯示該提供者的角色

### Tests for User Story 4

- [ ] T033 [P] [US4] Unit test for filter logic in backend/tests/unit/use_cases/test_list_voices.py
- [ ] T034 [P] [US4] Integration test for filter parameters in backend/tests/integration/api/test_voice_customization_api.py (extend)

### Implementation for User Story 4

- [ ] T035 [P] [US4] Create VoiceFilters component in frontend/src/components/voice-management/VoiceFilters.tsx
- [ ] T036 [US4] Add filter state to voiceManagementStore in frontend/src/stores/voiceManagementStore.ts
- [ ] T037 [US4] Integrate VoiceFilters into VoiceManagementPage in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [ ] T038 [US4] Add URL query params sync for filters in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [ ] T039 [US4] Add search parameter to ListVoicesUseCase in backend/src/application/use_cases/list_voices.py
- [ ] T040 [US4] Add favorites_only parameter to GET /voices in backend/src/presentation/api/routes/voices.py

**Checkpoint**: User Story 4 完成 - 可以篩選和搜尋角色

---

## Phase 6: User Story 3 - 隱藏不需要的角色 (Priority: P3)

**Goal**: 讓使用者能夠隱藏不常用的角色，簡化 TTS 選單

**Independent Test**: 隱藏一個角色，確認該角色不再出現在 TTS 設定選單中

### Tests for User Story 3

- [ ] T041 [P] [US3] Unit test for hidden toggle logic (auto-unfavorite) in backend/tests/unit/use_cases/test_update_voice_customization.py (extend)
- [ ] T042 [P] [US3] Integration test for exclude_hidden parameter in backend/tests/integration/api/test_voice_customization_api.py (extend)

### Implementation for User Story 3

- [ ] T043 [P] [US3] Create HiddenToggle component in frontend/src/components/voice-management/HiddenToggle.tsx
- [ ] T044 [US3] Add toggleHidden action to voiceManagementStore (with auto-unfavorite) in frontend/src/stores/voiceManagementStore.ts
- [ ] T045 [US3] Integrate HiddenToggle into VoiceCustomizationRow in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
- [ ] T046 [US3] Add showHidden toggle to VoiceFilters in frontend/src/components/voice-management/VoiceFilters.tsx
- [ ] T047 [US3] Modify UpdateVoiceCustomizationUseCase to auto-unfavorite when hiding in backend/src/application/use_cases/update_voice_customization.py
- [ ] T048 [US3] Add exclude_hidden parameter to ListVoicesUseCase in backend/src/application/use_cases/list_voices.py
- [ ] T049 [US3] Modify VoiceSelector to pass exclude_hidden=true by default in frontend/src/components/tts/VoiceSelector.tsx

**Checkpoint**: User Story 3 完成 - 隱藏的角色不會出現在 TTS 選單中

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 批量操作、效能優化、文件更新

- [ ] T050 Create BulkUpdateVoiceCustomizationUseCase in backend/src/application/use_cases/bulk_update_voice_customization.py
- [ ] T051 Add PATCH /voice-customizations/bulk endpoint in backend/src/presentation/api/routes/voice_customizations.py
- [ ] T052 Add bulk update UI or keyboard shortcuts in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [ ] T053 [P] Run make check and fix any linting/type errors
- [ ] T054 [P] Update frontend/src/components/tts/VoiceSelector.tsx for SpeakerVoiceTable integration
- [ ] T055 [P] Update frontend/src/components/multi-role-tts/SpeakerVoiceTable.tsx to use display_name
- [ ] T056 Validate quickstart.md scenarios work end-to-end
- [ ] T057 [P] Add loading states and error handling to VoiceManagementPage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on T001 (migration) completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1) → US2 (P2) → US4 (P2) → US3 (P3) in priority order
  - Or can proceed in parallel if staffed
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - May reuse US1 components but independently testable
- **User Story 4 (P2)**: Can start after Foundational - May reuse US1 components but independently testable
- **User Story 3 (P3)**: Can start after Foundational - Depends on US2 components (FavoriteToggle) for auto-unfavorite logic

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Domain/Use Cases before API routes
- Backend before Frontend (API must exist)
- Core implementation before integration with existing components

### Parallel Opportunities

**Phase 1 Parallel Tasks**:
```
T002, T003, T004, T005 can run in parallel
```

**Phase 2 Parallel Tasks**:
```
T009, T010 can run in parallel (after T006-T008)
```

**User Story 1 Parallel Tasks**:
```
T011, T012 (tests) can run in parallel
T017, T018 (components) can run in parallel
```

**User Story 2 Parallel Tasks**:
```
T026, T027 (tests) can run in parallel
```

**User Story 4 Parallel Tasks**:
```
T033, T034 (tests) can run in parallel
```

**User Story 3 Parallel Tasks**:
```
T041, T042 (tests) can run in parallel
```

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for UpdateVoiceCustomizationUseCase in backend/tests/unit/use_cases/test_update_voice_customization.py"
Task: "Integration test for PUT /voice-customizations/{id} in backend/tests/integration/api/test_voice_customization_api.py"

# Launch frontend components in parallel:
Task: "Create VoiceNameEditor component in frontend/src/components/voice-management/VoiceNameEditor.tsx"
Task: "Create VoiceCustomizationRow component in frontend/src/components/voice-management/VoiceCustomizationRow.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T010)
3. Complete Phase 3: User Story 1 (T011-T025)
4. **STOP and VALIDATE**: Test 自訂名稱功能獨立運作
5. Deploy/demo if ready - 使用者已經可以自訂角色名稱

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (收藏功能)
4. Add User Story 4 → Test independently → Deploy/Demo (篩選功能)
5. Add User Story 3 → Test independently → Deploy/Demo (隱藏功能)
6. Add Polish → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Backend)
   - Developer B: User Story 1 (Frontend)
3. After US1 complete:
   - Developer A: User Story 2 + 3 (Backend)
   - Developer B: User Story 4 (Frontend filters)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per constitution)
- Commit after each task or logical group
- Run `make check` before each commit
- Stop at any checkpoint to validate story independently
