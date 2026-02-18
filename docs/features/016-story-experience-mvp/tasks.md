# Tasks: MVP Story Experience Interface (父母的故事體驗介面)

**Input**: Design documents from `/docs/features/016-story-experience-mvp/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, merge StoryPal base code, and configure routing

- [x] T001 Merge StoryPal base code from `hackthon-storypal` branch into current branch (story entities, engine, prompts)
- [x] T002 [P] Create frontend route structure: `frontend/src/routes/story-experience/StoryExperiencePage.tsx`
- [x] T003 [P] Create frontend types: `frontend/src/types/story-experience.ts`
- [x] T004 [P] Create frontend API service: `frontend/src/services/storyExperienceApi.ts`
- [x] T005 [P] Create frontend Zustand store: `frontend/src/stores/storyExperienceStore.ts`
- [x] T006 Register `/story-experience` route in `frontend/src/App.tsx` and add to navigation menu

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure - MVP prompt templates and API scaffolding

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create MVP prompt templates in `backend/src/domain/services/story/mvp_prompts.py`:
  - `MVP_STORY_SYSTEM_PROMPT`: 系統角色定義（年齡適配、安全內容、繁體中文）
  - `MVP_STORY_GENERATE_PROMPT`: 故事生成 prompt（接受 age, educational_content, values, emotions, favorite_character）
  - `MVP_SONG_GENERATE_PROMPT`: 兒歌生成 prompt（歌詞結構、重複句）
  - `MVP_STORY_BRANCH_PROMPT`: 故事走向選項生成 prompt
  - `MVP_STORY_QA_PROMPT`: Q&A 問題生成和回答 prompt
- [x] T008 Create API schemas in `backend/src/presentation/api/schemas/story_experience_schemas.py`:
  - `GenerateContentRequest`: age, educational_content, values, emotions, favorite_character, content_type
  - `GenerateContentResponse`: content_id, content_type, text_content, parameters_summary
  - `BranchRequest/Response`: story_context, branches list
  - `QARequest/Response`: story_context, questions, answers
  - `TTSRequest/Response`: text_content, voice_id, audio_url, duration_ms
- [x] T009 Create use case in `backend/src/application/use_cases/story_experience.py`:
  - `StoryExperienceUseCase` class with methods: `generate_content()`, `generate_branches()`, `generate_qa()`, `generate_tts()`
  - Inject `ILLMProvider` and existing TTS service
- [x] T010 Create API route file `backend/src/presentation/api/routes/story_experience.py`:
  - Register router with prefix `/story-experience`
  - Scaffold endpoints (empty bodies to be filled in user story phases)
- [x] T011 Register story-experience router in main FastAPI app

**Checkpoint**: Foundation ready - backend has prompt templates, schemas, use case skeleton, and route scaffolding

---

## Phase 3: User Story 1 - 父母輸入參數並生成故事內容 (Priority: P1) 🎯 MVP

**Goal**: 父母填寫參數後 AI 生成故事/兒歌內容，可預覽和重新生成

**Independent Test**: 在介面上選擇參數後點擊生成，系統產出符合要求的故事內容

### Implementation for User Story 1

- [x] T012 [US1] Implement `POST /api/v1/story-experience/generate` endpoint in `backend/src/presentation/api/routes/story_experience.py`:
  - Accept `GenerateContentRequest`
  - Call `StoryExperienceUseCase.generate_content()`
  - Return `GenerateContentResponse`
- [x] T013 [US1] Implement `StoryExperienceUseCase.generate_content()` in `backend/src/application/use_cases/story_experience.py`:
  - Build prompt from MVP templates based on content_type (story/song)
  - Call LLM provider
  - Parse response into structured content
  - Generate content_id (UUID)
  - Return text content with parameters summary
- [x] T014 [US1] Implement `ParentInputForm` component in `frontend/src/components/story-experience/ParentInputForm.tsx`:
  - AgeSelector: dropdown 2-12 歲
  - EducationalContentInput: text input
  - ValuesSelector: multi-select chips (勇氣、善良、分享、誠實、尊重、感恩、合作、耐心)
  - EmotionsSelector: multi-select chips (快樂、悲傷、憤怒、恐懼、驚訝、同理心)
  - FavoriteCharacterInput: text input
  - ContentTypeSelector: radio buttons (故事/兒歌)
  - Form validation (required fields)
  - Generate button
- [x] T015 [US1] Implement `ContentPreview` component in `frontend/src/components/story-experience/ContentPreview.tsx`:
  - Display generated text content in readable format
  - `ParameterSummary` sub-section showing used parameters
  - 「重新生成」and「確認並生成音頻」buttons
  - Loading state during generation
- [x] T016 [US1] Implement `storyExperienceStore.ts` core actions:
  - `setFormData()`: update input parameters
  - `generateContent()`: call API and store result
  - `regenerateContent()`: call API with same params
  - `confirmContent()`: mark content as confirmed, transition to TTS step
  - `setStep()`: manage wizard steps (input → preview → tts)
  - `reset()`: clear all state
- [x] T017 [US1] Implement `storyExperienceApi.ts` for content generation:
  - `generateContent(request)` → POST /api/v1/story-experience/generate
- [x] T018 [US1] Wire up `StoryExperiencePage.tsx` with step-based flow:
  - Step 1: `ParentInputForm`
  - Step 2: `ContentPreview`
  - Step navigation and state management

**Checkpoint**: User Story 1 complete - 父母可輸入參數、生成故事/兒歌內容、預覽和重新生成

---

## Phase 4: User Story 2 - 確認後生成 TTS 音頻並播放 (Priority: P1) 🎯 MVP

**Goal**: 確認內容後 TTS 生成音頻並在現場播放

**Independent Test**: 確認已生成的文字內容後，系統產出可播放的音頻

### Implementation for User Story 2

- [x] T019 [US2] Implement `POST /api/v1/story-experience/tts` endpoint in `backend/src/presentation/api/routes/story_experience.py`:
  - Accept text_content, voice_id, provider
  - Call existing TTS synthesize service
  - Return audio_url and duration_ms
- [x] T020 [US2] Implement `StoryExperienceUseCase.generate_tts()`:
  - Call existing `SynthesizeSpeech` use case or TTS service
  - Handle long text splitting if needed (EC-004)
  - Return audio file path/URL
- [x] T021 [US2] Implement `GET /api/v1/story-experience/voices` endpoint:
  - Return available Chinese TTS voices from existing voice listing logic
  - Filter to zh-TW / zh-CN voices only
- [x] T022 [US2] Implement `TTSPlayer` component in `frontend/src/components/story-experience/TTSPlayer.tsx`:
  - VoiceSelector: dropdown of available Chinese voices
  - GenerateAudioButton with loading state
  - Audio playback controls (play, pause, replay)
  - Change voice and regenerate option
- [x] T023 [US2] Add TTS actions to `storyExperienceStore.ts`:
  - `fetchVoices()`: load available voices
  - `generateTTS()`: call TTS API
  - `setSelectedVoice()`: voice selection
  - Audio state management (playing, paused, etc.)
- [x] T024 [US2] Add TTS API functions to `storyExperienceApi.ts`:
  - `generateTTS(request)` → POST /api/v1/story-experience/tts
  - `listVoices()` → GET /api/v1/story-experience/voices
- [x] T025 [US2] Wire up Step 3 (TTSPlayer) in `StoryExperiencePage.tsx`

**Checkpoint**: User Stories 1+2 complete - 完整的「輸入 → 生成 → 預覽 → 確認 → TTS → 播放」核心流程

---

## Phase 5: User Story 3 - 生成兒歌內容並播放 (Priority: P2)

**Goal**: 兒歌形式的內容生成使用不同的 prompt 結構和 TTS 配置

**Independent Test**: 選擇「兒歌」形式後生成包含歌詞結構的內容

### Implementation for User Story 3

- [x] T026 [US3] Fine-tune `MVP_SONG_GENERATE_PROMPT` in `backend/src/domain/services/story/mvp_prompts.py`:
  - 確保 prompt 產出具有歌詞結構（段落、副歌、重複句）
  - 適合 TTS 朗讀的格式（標點、停頓標記）
- [x] T027 [US3] Add content_type routing in `StoryExperienceUseCase.generate_content()`:
  - 根據 content_type 選擇對應的 prompt template (story vs song)
  - 兒歌生成可能需要不同的 TTS 參數（語速、語調）
- [x] T028 [US3] Update `ContentPreview` component to handle song format:
  - 歌詞格式化顯示（段落分隔、副歌標記）

**Checkpoint**: User Stories 1-3 complete - 故事和兒歌兩種內容形式都可生成和播放

---

## Phase 6: User Story 4 - 故事走向選擇 (Priority: P2)

**Goal**: 父母可選擇故事走向讓 AI 延伸故事

**Independent Test**: 故事生成後顯示走向選項，選擇後產出延續內容

### Implementation for User Story 4

- [x] T029 [US4] Implement `POST /api/v1/story-experience/branch` endpoint:
  - 無 selected_branch 時：生成 2-3 個走向選項
  - 有 selected_branch 時：基於選定走向生成後續內容
- [x] T030 [US4] Implement `StoryExperienceUseCase.generate_branches()`:
  - 使用 MVP_STORY_BRANCH_PROMPT
  - 保留對話歷史/故事脈絡供後續生成使用
- [x] T031 [US4] Implement `StoryBranchSelector` component in `frontend/src/components/story-experience/StoryBranchSelector.tsx`:
  - 顯示 2-3 個走向選項卡片
  - 點擊選項後觸發後續內容生成
  - Loading state during generation
- [x] T032 [US4] Add branch actions to store and API service:
  - `generateBranches()`, `selectBranch()`
  - `branchContent()` API call
- [x] T033 [US4] Update `ContentPreview` to show「延伸故事」button and append extended content:
  - 在已生成內容下方顯示延伸按鈕
  - 延伸內容追加到原始內容下方
  - 支援多次延伸

**Checkpoint**: User Stories 1-4 complete - 父母可生成、延伸故事並播放

---

## Phase 7: User Story 5 - 故事 Q&A 互動 (Priority: P3)

**Goal**: 基於故事內容的 Q&A 問答環節

**Independent Test**: 故事生成後可啟動 Q&A，產出相關問答並播放

### Implementation for User Story 5

- [x] T034 [US5] Implement `POST /api/v1/story-experience/qa` endpoint:
  - 無 question 時：基於故事內容生成 2-3 個問題
  - 有 question 時：根據故事脈絡生成回答
- [x] T035 [US5] Implement `StoryExperienceUseCase.generate_qa()`:
  - 使用 MVP_STORY_QA_PROMPT
  - 接受故事上下文生成問題或回答
- [x] T036 [US5] Implement `QAInteraction` component in `frontend/src/components/story-experience/QAInteraction.tsx`:
  - AI 生成問題列表顯示
  - 自訂問題輸入框
  - 回答內容顯示
  - 生成 Q&A 音頻按鈕
- [x] T037 [US5] Add QA actions to store and API service:
  - `generateQuestions()`, `askQuestion()`, `generateQAAudio()`
  - QA API calls
- [x] T038 [US5] Update `ContentPreview` to show「Q&A 互動」button:
  - 在已生成內容下方顯示 Q&A 入口
  - Q&A 區域可展開/收合

**Checkpoint**: All user stories complete - 完整的 MVP 故事體驗介面

---

## Phase 8: Polish & Integration

**Purpose**: Error handling, UX improvements, and final validation

- [x] T039 [P] Add error handling for all API calls (EC-001, EC-002):
  - Frontend toast notifications for failures
  - Retry buttons that preserve input state
- [x] T040 [P] Add form validation feedback (EC-005):
  - Required field indicators
  - Inline error messages
- [x] T041 [P] Handle long text TTS splitting (EC-004):
  - Backend: split text at sentence boundaries when exceeding TTS limit
  - Concatenate audio segments
- [x] T042 Add loading states and transitions between steps:
  - Skeleton loading for content generation
  - Progress indicator for TTS conversion
  - Smooth step transitions
- [x] T043 Run `make check` and fix any linting/type errors
- [x] T044 Manual end-to-end testing of complete flow:
  - 故事生成 → 預覽 → 延伸 → Q&A → TTS → 播放
  - 兒歌生成 → 預覽 → TTS → 播放
  - Error scenarios (empty inputs, API failures)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - merge base code first
- **Phase 2 (Foundational)**: Depends on Phase 1 - creates backend scaffolding
- **Phase 3 (US1)**: Depends on Phase 2 - content generation
- **Phase 4 (US2)**: Depends on Phase 2 - TTS can be built in parallel with US1, but integration depends on US1
- **Phase 5 (US3)**: Depends on Phase 3 - extends content generation for song format
- **Phase 6 (US4)**: Depends on Phase 3 - extends content with branching
- **Phase 7 (US5)**: Depends on Phase 3 - extends content with Q&A
- **Phase 8 (Polish)**: Depends on all desired phases being complete

### Parallel Opportunities

- Phase 3 (US1) and Phase 4 (US2) backend work can proceed in parallel
- Phase 5, 6, 7 can proceed in parallel once Phase 3 is complete
- All [P] tasks within a phase can run in parallel

### Recommended Execution Order (Single Developer)

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 (Core MVP complete)
2. Phase 5 (兒歌 fine-tuning)
3. Phase 6 (故事走向) and Phase 7 (Q&A)
4. Phase 8 (Polish)

---

## Implementation Strategy

### MVP First (User Stories 1+2 Only)

1. Complete Phase 1-2: Setup + Foundation
2. Complete Phase 3: Content Generation (US1)
3. Complete Phase 4: TTS Playback (US2)
4. **STOP and VALIDATE**: 驗證核心流程「輸入 → 生成 → 確認 → TTS → 播放」
5. Deploy for initial testing

### Full Experience

6. Phase 5: 兒歌支援 (US3)
7. Phase 6: 故事走向選擇 (US4)
8. Phase 7: Q&A 互動 (US5)
9. Phase 8: Polish
