# Tasks: TTS 角色管理介面

**Input**: Design documents from `/docs/features/013-tts-role-mgmt/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD 流程已在 constitution.md 中定義，本任務清單包含測試任務。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and base type definitions

- [X] T001 Create Alembic migration for voice_customization table in backend/alembic/versions/013_create_voice_customization.py
- [X] T002 [P] Create VoiceCustomization domain entity in backend/src/domain/entities/voice_customization.py
- [X] T003 [P] Create IVoiceCustomizationRepository interface in backend/src/domain/repositories/voice_customization.py
- [X] T004 [P] Create VoiceCustomization TypeScript types in frontend/src/types/voice-customization.ts
- [X] T005 [P] Create Pydantic schemas for API in backend/src/presentation/api/schemas/voice_customization.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create VoiceCustomizationModel SQLAlchemy model in backend/src/infrastructure/persistence/models.py
- [X] T007 Create VoiceCustomizationRepositoryImpl in backend/src/infrastructure/persistence/voice_customization_repository_impl.py
- [X] T008 Register VoiceCustomizationRepository in dependency container in backend/src/infrastructure/container.py
- [X] T009 [P] Create voiceCustomizationApi service in frontend/src/services/voiceCustomizationApi.ts
- [X] T010 [P] Create voiceManagementStore Zustand store in frontend/src/stores/voiceManagementStore.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 自訂角色顯示名稱 (Priority: P1) 🎯 MVP

**Goal**: 讓使用者能夠為 TTS 角色設定自訂顯示名稱

**Independent Test**: 編輯一個角色的顯示名稱，然後確認該名稱在 TTS 設定選單中正確顯示

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for UpdateVoiceCustomizationUseCase in backend/tests/unit/use_cases/test_update_voice_customization.py
- [X] T012 [P] [US1] Integration test for PUT /voice-customizations/{id} in backend/tests/integration/api/test_voice_customization_api.py

### Implementation for User Story 1

- [X] T013 [US1] Create UpdateVoiceCustomizationUseCase in backend/src/application/use_cases/update_voice_customization.py
- [X] T014 [US1] Create GetVoiceCustomizationUseCase in backend/src/application/use_cases/get_voice_customization.py
- [X] T015 [US1] Create voice_customizations API routes (GET, PUT, DELETE) in backend/src/presentation/api/routes/voice_customizations.py
- [X] T016 [US1] Register voice_customizations routes in backend/src/presentation/api/routes/__init__.py
- [X] T017 [P] [US1] Create VoiceNameEditor component in frontend/src/components/voice-management/VoiceNameEditor.tsx
- [X] T018 [P] [US1] Create VoiceCustomizationRow component in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
- [X] T019 [US1] Create VoiceManagementTable component in frontend/src/components/voice-management/VoiceManagementTable.tsx
- [X] T020 [US1] Create VoiceManagementPage route in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [X] T021 [US1] Add route for /voice-management in frontend/src/App.tsx
- [X] T022 [US1] Add sidebar navigation link for 角色管理 in frontend/src/components/layout/Sidebar.tsx
- [X] T023 [US1] Modify ListVoicesUseCase to include display_name in backend/src/application/use_cases/list_voices.py
- [X] T024 [US1] Modify GET /voices endpoint to return display_name, is_favorite, is_hidden in backend/src/presentation/api/routes/voices.py
- [X] T025 [US1] Modify VoiceSelector to display display_name instead of name in frontend/src/components/tts/VoiceSelector.tsx

**Checkpoint**: User Story 1 完成 - 使用者可以自訂角色名稱並在 TTS 選單中看到

---

## Phase 4: User Story 2 - 收藏常用角色 (Priority: P2)

**Goal**: 讓使用者能夠收藏常用角色，並在選單中優先顯示

**Independent Test**: 收藏一個角色，然後確認該角色在 TTS 選擇介面中排在最上方

### Tests for User Story 2

- [X] T026 [P] [US2] Unit test for favorite toggle logic in backend/tests/unit/use_cases/test_update_voice_customization.py (extend)
- [X] T027 [P] [US2] Integration test for favorite sorting in backend/tests/integration/api/test_voice_customization_api.py (extend)

### Implementation for User Story 2

- [X] T028 [P] [US2] Create FavoriteToggle component in frontend/src/components/voice-management/FavoriteToggle.tsx
- [X] T029 [US2] Add toggleFavorite action to voiceManagementStore in frontend/src/stores/voiceManagementStore.ts
- [X] T030 [US2] Integrate FavoriteToggle into VoiceCustomizationRow in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
- [X] T031 [US2] Modify ListVoicesUseCase to sort favorites first in backend/src/application/use_cases/list_voices.py
- [X] T032 [US2] Modify VoiceSelector to sort favorites to top in frontend/src/components/tts/VoiceSelector.tsx

**Checkpoint**: User Story 2 完成 - 收藏角色會在選單最上方顯示

---

## Phase 5: User Story 4 - 瀏覽和篩選角色 (Priority: P2)

**Goal**: 讓使用者能夠按提供者、語言、性別等條件篩選角色

**Independent Test**: 選擇特定提供者（如 VoAI），確認只顯示該提供者的角色

### Tests for User Story 4

- [X] T033 [P] [US4] Unit test for filter logic in backend/tests/unit/use_cases/test_list_voices.py
- [X] T034 [P] [US4] Integration test for filter parameters in backend/tests/integration/api/test_voice_customization_api.py (extend)

### Implementation for User Story 4

- [X] T035 [P] [US4] Create VoiceFilters component in frontend/src/components/voice-management/VoiceFilters.tsx
- [X] T036 [US4] Add filter state to voiceManagementStore in frontend/src/stores/voiceManagementStore.ts
- [X] T037 [US4] Integrate VoiceFilters into VoiceManagementPage in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [X] T038 [US4] Add URL query params sync for filters in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [X] T039 [US4] Add search parameter to ListVoicesUseCase in backend/src/application/use_cases/list_voices.py
- [X] T040 [US4] Add favorites_only parameter to GET /voices in backend/src/presentation/api/routes/voices.py

**Checkpoint**: User Story 4 完成 - 可以篩選和搜尋角色

---

## Phase 6: User Story 3 - 隱藏不需要的角色 (Priority: P3)

**Goal**: 讓使用者能夠隱藏不常用的角色，簡化 TTS 選單

**Independent Test**: 隱藏一個角色，確認該角色不再出現在 TTS 設定選單中

### Tests for User Story 3

- [X] T041 [P] [US3] Unit test for hidden toggle logic (auto-unfavorite) in backend/tests/unit/use_cases/test_update_voice_customization.py (extend)
- [X] T042 [P] [US3] Integration test for exclude_hidden parameter in backend/tests/integration/api/test_voice_customization_api.py (extend)

### Implementation for User Story 3

- [X] T043 [P] [US3] Create HiddenToggle component in frontend/src/components/voice-management/HiddenToggle.tsx
- [X] T044 [US3] Add toggleHidden action to voiceManagementStore (with auto-unfavorite) in frontend/src/stores/voiceManagementStore.ts
- [X] T045 [US3] Integrate HiddenToggle into VoiceCustomizationRow in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
- [X] T046 [US3] Add showHidden toggle to VoiceFilters in frontend/src/components/voice-management/VoiceFilters.tsx
- [X] T047 [US3] Modify UpdateVoiceCustomizationUseCase to auto-unfavorite when hiding in backend/src/application/use_cases/update_voice_customization.py
- [X] T048 [US3] Add exclude_hidden parameter to ListVoicesUseCase in backend/src/application/use_cases/list_voices.py
- [X] T049 [US3] Modify VoiceSelector to pass exclude_hidden=true by default in frontend/src/components/tts/VoiceSelector.tsx

**Checkpoint**: User Story 3 完成 - 隱藏的角色不會出現在 TTS 選單中

---

## Phase 7: User Story 5 - 播放聲音預覽 (Priority: P1)

**Goal**: 讓使用者能在角色管理頁面直接播放每個角色的聲音預覽，辨識角色聲音特色

**Independent Test**: 在角色管理頁面點擊播放按鈕，確認能聽到對應角色的聲音預覽

**Technical Context**:
- ElevenLabs：API 回傳 `preview_url`（CDN），直接使用
- Azure / Gemini / VoAI：不提供原生預覽，需自行合成並快取
- 合成使用固定短語（如「大家好，歡迎收聽，我是你的語音助理」）
- 預覽存於 `storage/previews/{provider}/{voice_id}.mp3`，更新 `voice_cache.sample_audio_url`
- 前端已有可複用的 `AudioPlayer.tsx` 和 `useAudioPlayback.ts`
- 後端已有可複用的 `SynthesizeSpeech` use case 和 `ITTSProvider` 介面

### Tests for User Story 5

- [ ] T058 [P] [US5] Unit test for GenerateVoicePreviewUseCase in backend/tests/unit/use_cases/test_generate_voice_preview.py
- [ ] T059 [P] [US5] Unit test for VoicePreviewButton component behavior (play/stop/loading states) in frontend/tests/components/voice-management/VoicePreviewButton.test.tsx

### Implementation for User Story 5

#### Backend: Preview Generation

- [ ] T060 [US5] Create GenerateVoicePreviewUseCase in backend/src/application/use_cases/generate_voice_preview.py
  - Accept voice_cache_id, check if sample_audio_url already exists (cached)
  - If cached: return existing URL
  - If ElevenLabs: use preview_url from voice_cache metadata
  - If no preview: call ITTSProvider.synthesize() with fixed preview phrase
  - Save result to `storage/previews/{provider}/{voice_id}.mp3`
  - Update voice_cache.sample_audio_url with the file path
  - Return preview URL or audio content

- [ ] T061 [US5] Create POST /voices/{voice_cache_id}/preview endpoint in backend/src/presentation/api/routes/voices.py
  - On-demand preview generation (FR-016)
  - Returns JSON `{ "audio_url": "...", "content_type": "audio/mpeg", "cached": true/false }`
  - If synthesis needed: may take up to 10 seconds (SC-007)
  - If already cached: return immediately (SC-006)

- [ ] T062 [US5] Create GET /voices/{voice_cache_id}/preview/audio endpoint for streaming preview audio in backend/src/presentation/api/routes/voices.py
  - Returns audio file directly (Content-Type: audio/mpeg)
  - Serves from storage/previews/ directory
  - Returns 404 if preview not yet generated

- [ ] T063 [P] [US5] Add preview Pydantic schemas (VoicePreviewResponse) in backend/src/presentation/api/schemas/voice_customization.py

#### Frontend: Preview Playback

- [ ] T064 [P] [US5] Create VoicePreviewButton component in frontend/src/components/voice-management/VoicePreviewButton.tsx
  - Play/stop toggle button with loading spinner
  - Three states: idle (play icon), loading (spinner), playing (stop icon)
  - Calls POST /voices/{id}/preview to trigger generation
  - Uses HTML5 Audio element to play audio_url
  - FR-017: Only one preview plays at a time

- [ ] T065 [US5] Create useVoicePreview hook for global playback state in frontend/src/hooks/useVoicePreview.ts
  - Track currently playing voice_cache_id
  - Provide play(voiceCacheId) and stop() functions
  - Auto-stop current playback when a different voice starts (FR-017)
  - Manage Audio element lifecycle and cleanup

- [ ] T066 [US5] Add preview API methods to voiceCustomizationApi in frontend/src/lib/voiceCustomizationApi.ts
  - generatePreview(voiceCacheId): POST /voices/{id}/preview → VoicePreviewResponse
  - getPreviewAudioUrl(voiceCacheId): returns GET /voices/{id}/preview/audio URL

- [ ] T067 [US5] Integrate VoicePreviewButton into VoiceCustomizationRow in frontend/src/components/voice-management/VoiceCustomizationRow.tsx
  - Add play button column between checkbox and name columns
  - Pass voice.id and voice.sample_audio_url to VoicePreviewButton

- [ ] T068 [US5] Add preview playback state to voiceManagementStore in frontend/src/stores/voiceManagementStore.ts
  - currentlyPlayingId: string | null
  - previewLoading: Set<string> (tracks which voices are generating previews)
  - playPreview(voiceCacheId) and stopPreview() actions

#### Edge Cases & Error Handling

- [ ] T069 [US5] Handle preview errors in VoicePreviewButton (provider API key not set, synthesis failure, URL expired)
  - Show tooltip or inline error message on failure (spec edge case)
  - If ElevenLabs CDN URL expired: trigger re-generation
  - If provider API key not configured: show "該 provider 未設定 API key，無法產生預覽"

**Checkpoint**: User Story 5 完成 - 使用者可以在角色管理頁面試聽每個角色的聲音預覽

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 批量操作、效能優化、文件更新

- [X] T050 Create BulkUpdateVoiceCustomizationUseCase in backend/src/application/use_cases/bulk_update_voice_customization.py
- [X] T051 Add PATCH /voice-customizations/bulk endpoint in backend/src/presentation/api/routes/voice_customizations.py
- [ ] T052 Add bulk update UI or keyboard shortcuts in frontend/src/routes/voice-management/VoiceManagementPage.tsx
- [X] T053 [P] Run make check and fix any linting/type errors
- [X] T054 [P] Update frontend/src/components/tts/VoiceSelector.tsx for SpeakerVoiceTable integration
- [X] T055 [P] Update frontend/src/components/multi-role-tts/SpeakerVoiceTable.tsx to use display_name
- [ ] T056 Validate quickstart.md scenarios work end-to-end
- [X] T057 [P] Add loading states and error handling to VoiceManagementPage
- [ ] T070 [P] Run make check after US5 implementation and fix any linting/type errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately ✅ DONE
- **Foundational (Phase 2)**: Depends on T001 (migration) completion - BLOCKS all user stories ✅ DONE
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1) ✅ DONE
  - US2 (P2) ✅ DONE
  - US4 (P2) ✅ DONE
  - US3 (P3) ✅ DONE
  - **US5 (P1) → 待實作**
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: ✅ DONE - 自訂角色名稱
- **User Story 2 (P2)**: ✅ DONE - 收藏常用角色
- **User Story 4 (P2)**: ✅ DONE - 瀏覽和篩選
- **User Story 3 (P3)**: ✅ DONE - 隱藏不需要的角色
- **User Story 5 (P1)**: Can start immediately - Depends on existing VoiceCustomizationRow and TTS synthesis infrastructure

### Within User Story 5

- Tests (T058-T059) can run in parallel
- Backend (T060-T063) before Frontend (T064-T068)
- T060 (use case) → T061/T062 (endpoints) → T063 (schemas, parallel with endpoints)
- T064 (button component) + T065 (hook) can be developed in parallel
- T066 (API methods) before T067 (integration)
- T068 (store state) before T069 (error handling)

### Parallel Opportunities

**User Story 5 Parallel Tasks**:
```
T058, T059 (tests) can run in parallel
T063 (schemas) can run in parallel with T061/T062
T064 (button), T065 (hook) can run in parallel
```

---

## Parallel Example: User Story 5

```bash
# Launch tests in parallel:
Task: "Unit test for GenerateVoicePreviewUseCase in backend/tests/unit/use_cases/test_generate_voice_preview.py"
Task: "Unit test for VoicePreviewButton component in frontend/tests/components/voice-management/VoicePreviewButton.test.tsx"

# Launch frontend components in parallel:
Task: "Create VoicePreviewButton component in frontend/src/components/voice-management/VoicePreviewButton.tsx"
Task: "Create useVoicePreview hook in frontend/src/hooks/useVoicePreview.ts"
```

---

## Implementation Strategy

### Current Progress

Phase 1-6 (Setup + US1-US4) are **complete** (55/57 tasks done). Remaining:
- **US5 (Phase 7)**: 12 new tasks (T058-T069) - 聲音預覽播放
- **Polish (Phase 8)**: T052, T056, T070 未完成

### Recommended Execution Order for US5

1. **Backend first**: T060 (use case) → T061/T062 (endpoints) + T063 (schemas)
2. **Frontend next**: T065 (hook) + T064 (button) in parallel → T066 (API) → T067 (integrate) → T068 (store)
3. **Edge cases**: T069 (error handling)
4. **Verify**: T070 (make check)

### MVP for US5

最小可行版本只需：
1. T060 + T061 (backend: 產生預覽 + API 端點)
2. T064 + T065 + T066 + T067 (frontend: 按鈕 + hook + API + 整合)

進階項目（可後續迭代）：
- T062 (streaming audio endpoint)
- T069 (完整錯誤處理)
- T058/T059 (測試)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per constitution)
- Commit after each task or logical group
- Run `make check` before each commit
- Stop at any checkpoint to validate story independently
