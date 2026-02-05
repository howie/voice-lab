# Tasks: Magic DJ AI Prompt Templates

**Input**: Design documents from `/docs/features/015-magic-dj-ai-prompts/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test tasks included alongside implementation phases per Constitution Principle I (TDD).

**Organization**: Tasks grouped by user story (US1-US4) per spec.md priority order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for all tasks (pure frontend feature)

---

## Phase 1: Setup (Types & Store Foundation)

**Purpose**: Define new TypeScript types and extend magicDJStore with prompt template state

- [ ] T001 [P] Add PromptTemplate, StoryPrompt, and PromptTemplateColor types in `frontend/src/types/magic-dj.ts`
- [ ] T002 [P] Add DEFAULT_PROMPT_TEMPLATES constant (8 templates: 裝傻, 轉移話題, 鼓勵, 等一下, 結束故事, 回到主題, 簡短回答, 多問問題) in `frontend/src/types/magic-dj.ts`
- [ ] T003 [P] Add DEFAULT_STORY_PROMPTS constant (4 templates: 魔法森林, 海底冒險, 太空旅行, 動物運動會) in `frontend/src/types/magic-dj.ts`
- [ ] T004 Extend MagicDJState interface with promptTemplates, storyPrompts, lastSentPromptId, lastSentPromptTime fields in `frontend/src/types/magic-dj.ts`
- [ ] T005 Add OperationLog.action union values: 'send_prompt_template' and 'send_story_prompt' in `frontend/src/types/magic-dj.ts`
- [ ] T006 Extend magicDJStore with promptTemplates/storyPrompts initial state and CRUD actions (addPromptTemplate, updatePromptTemplate, removePromptTemplate, reorderPromptTemplates, addStoryPrompt, updateStoryPrompt, removeStoryPrompt, setLastSentPrompt, clearLastSentPrompt) in `frontend/src/stores/magicDJStore.ts`
- [ ] T007 Update magicDJStore persist partialize to include promptTemplates and storyPrompts in `frontend/src/stores/magicDJStore.ts`
- [ ] T008 Add store version migration: load DEFAULT_PROMPT_TEMPLATES and DEFAULT_STORY_PROMPTS for pre-015 state in `frontend/src/stores/magicDJStore.ts`

### Tests for Phase 1

- [ ] T036 [P] Create promptTemplateStore unit tests: CRUD operations (add, update, remove, reorder), default template protection (isDefault cannot be deleted), persist/rehydrate verification, store version migration from pre-015 state in `frontend/tests/unit/magic-dj/promptTemplateStore.test.ts`

**Checkpoint**: Types compile, store can read/write promptTemplates and storyPrompts, persist/rehydrate works, store tests pass

---

## Phase 2: Foundational (AI Control Bar Extraction)

**Purpose**: Extract AI control functions from AIVoiceChannelStrip into a reusable top-bar component. This MUST be complete before US1-US3 layout integration.

**⚠️ CRITICAL**: The new AI mode layout depends on this component

- [ ] T009 Create AIControlBar component with mic toggle, connection status dot, interrupt button, force submit button, and filler sound trigger — horizontal layout for header embedding in `frontend/src/components/magic-dj/AIControlBar.tsx`
- [ ] T010 Refactor AIVoiceChannelStrip: keep existing component functional for backward compatibility but mark as legacy; new AI mode will use AIControlBar + PromptTemplatePanel instead — update comments in `frontend/src/components/magic-dj/AIVoiceChannelStrip.tsx`

**Checkpoint**: AIControlBar renders correctly with all controls, props match existing AIVoiceChannelStrip functionality

---

## Phase 3: User Story 1 — RD 使用 Prompt Template 即時介入 AI 對話 (Priority: P1) 🎯 MVP

**Goal**: RD 可透過預建的 prompt template 按鈕，一鍵送出文字指令給 Gemini AI 控制其回應行為

**Independent Test**: 在 AI 對話模式中點擊「裝傻」按鈕 → WebSocket 發送 text_input → AI 調整回應

### Implementation for User Story 1

- [ ] T011 [P] [US1] Create PromptTemplateButton component: display name with color badge, click triggers onSend callback, 200ms pulse animation on click, disabled state when AI not connected in `frontend/src/components/magic-dj/PromptTemplateButton.tsx`
- [ ] T012 [P] [US1] Create PromptTemplatePanel component: grid layout of PromptTemplateButton items, scrollable container, "+" add button at bottom, receives promptTemplates from store and onSendPrompt callback in `frontend/src/components/magic-dj/PromptTemplatePanel.tsx`
- [ ] T013 [US1] Add handleSendPromptTemplate handler in MagicDJPage: call sendMessage('text_input', { text: template.prompt }), update lastSentPromptId, logOperation('send_prompt_template') in `frontend/src/routes/magic-dj/MagicDJPage.tsx`
- [ ] T014 [US1] Integrate PromptTemplatePanel into DJControlPanel AI mode: replace rescue channel in AI conversation mode branch (lines 158-186) with PromptTemplatePanel as first column, add AIControlBar to header in `frontend/src/components/magic-dj/DJControlPanel.tsx`
- [ ] T015 [US1] Update DJControlPanelProps interface: add onSendPromptTemplate and onSendStoryPrompt callbacks in `frontend/src/components/magic-dj/DJControlPanel.tsx`
- [ ] T016 [US1] Wire prompt template props through DJControlPanel → PromptTemplatePanel → PromptTemplateButton in `frontend/src/components/magic-dj/DJControlPanel.tsx`

### Tests for Phase 3

- [ ] T037 [P] [US1] Create PromptTemplatePanel tests: render all templates, click triggers onSendPrompt callback with correct template, disabled state when AI not connected, "+" button renders in `frontend/tests/unit/magic-dj/PromptTemplatePanel.test.tsx`
- [ ] T038 [US1] Add EC-002 rapid successive trigger test: verify that multiple rapid clicks (<500ms interval) on different prompt template buttons all invoke sendMessage in order without loss — no debounce should drop messages (spec EC-002) in `frontend/tests/unit/magic-dj/PromptTemplatePanel.test.tsx`

**Checkpoint**: Click prompt template button → WebSocket sends text_input → Gemini receives prompt. Prerecorded mode unaffected. All US1 tests pass.

---

## Phase 4: User Story 2 — RD 透過 Story Prompt 欄位發送故事指令 (Priority: P1)

**Goal**: RD 可選擇預設故事模板或輸入自訂文字，引導 AI 進入特定故事場景

**Independent Test**: 選擇「魔法森林」模板或輸入自訂文字 → text_input 送出 → AI 切換場景

### Implementation for User Story 2

- [ ] T017 [P] [US2] Create StoryPromptPanel component: upper section with story template cards (click to send), lower section with textarea input + submit button, receives storyPrompts from store and onSendStoryPrompt callback in `frontend/src/components/magic-dj/StoryPromptPanel.tsx`
- [ ] T018 [US2] Add handleSendStoryPrompt handler in MagicDJPage: call sendMessage('text_input', { text }), logOperation('send_story_prompt', { text: text.slice(0, 100) }) in `frontend/src/routes/magic-dj/MagicDJPage.tsx`
- [ ] T019 [US2] Integrate StoryPromptPanel into DJControlPanel AI mode: add as second column in the four-column AI mode layout in `frontend/src/components/magic-dj/DJControlPanel.tsx`
- [ ] T020 [US2] Wire story prompt props through DJControlPanel → StoryPromptPanel in `frontend/src/components/magic-dj/DJControlPanel.tsx`

### Tests for Phase 4

- [ ] T039 [P] [US2] Create StoryPromptPanel tests: render preset story templates, click preset triggers onSendStoryPrompt callback, textarea submit sends custom text, empty textarea submit is prevented, disabled state when AI not connected in `frontend/tests/unit/magic-dj/StoryPromptPanel.test.tsx`

**Checkpoint**: Select story template or type custom text → text_input sent → AI transitions to story scenario. All US2 tests pass.

---

## Phase 5: User Story 3 — RD 在 AI 講話時播放音效與背景音樂 (Priority: P1)

**Goal**: AI 語音回應時可同時播放音效和背景音樂，各使用獨立頻道互不干擾

**Independent Test**: AI 正在回應 → 點擊音效按鈕 → 音效播放但 AI 語音不中斷 → 啟動背景音樂 → 三者同時播放

### Implementation for User Story 3

- [ ] T021 [US3] Modify ChannelBoard to support AI mode four-column layout: when AI mode, show only SFX and Music ChannelStrips (exclude rescue and voice channels), accept promptPanel and storyPanel as leading JSX content in `frontend/src/components/magic-dj/ChannelBoard.tsx`
- [ ] T022 [US3] Update DJControlPanel AI mode branch to use new ChannelBoard four-column layout: pass PromptTemplatePanel and StoryPromptPanel as leading content, followed by SFX and Music ChannelStrips in `frontend/src/components/magic-dj/DJControlPanel.tsx`
- [ ] T023 [US3] Ensure AI audio playback (WebSocket response) and local track playback (useMultiTrackPlayer) operate on independent audio channels — verify no stopAll() call interrupts AI audio when playing SFX/Music in `frontend/src/routes/magic-dj/MagicDJPage.tsx`
- [ ] T024 [US3] Update handlePlayTrack and handleInterrupt to preserve AI audio stream when playing SFX/Music tracks: only stopAll + interrupt AI when explicitly calling interrupt, not when playing regular tracks in `frontend/src/routes/magic-dj/MagicDJPage.tsx`

**Checkpoint**: AI speaking + SFX playing + Music playing all simultaneously without interference

---

## Phase 6: User Story 4 — RD 管理 Prompt Template 清單 (Priority: P2)

**Goal**: RD 可新增、編輯、刪除自訂 prompt template

**Independent Test**: 點擊 "+" 新增 template → 填寫名稱/prompt/顏色 → 儲存 → 新按鈕出現 → 編輯 → 刪除

### Implementation for User Story 4

- [ ] T025 [P] [US4] Create PromptTemplateEditor modal component: form with name input (max 20 chars), prompt textarea (max 500 chars), color picker (8 color options), icon selector (optional), validation logic, save/cancel buttons in `frontend/src/components/magic-dj/PromptTemplateEditor.tsx`
- [ ] T026 [US4] Add context menu (long press / right click) to PromptTemplateButton: show Edit and Delete options, prevent deletion of isDefault templates in `frontend/src/components/magic-dj/PromptTemplateButton.tsx`
- [ ] T027 [US4] Wire editor modal open/close state and CRUD handlers in MagicDJPage: handleAddPromptTemplate, handleEditPromptTemplate, handleDeletePromptTemplate calling store actions in `frontend/src/routes/magic-dj/MagicDJPage.tsx`
- [ ] T028 [US4] Pass CRUD callbacks from MagicDJPage → DJControlPanel → PromptTemplatePanel → PromptTemplateButton in `frontend/src/components/magic-dj/DJControlPanel.tsx`

**Checkpoint**: Full CRUD lifecycle works, changes persist after page reload

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Persistence, preset export, hotkeys, operation logging, and visual polish

- [ ] T029 Extend TrackConfigPanel export format to include promptTemplates and storyPrompts arrays; import with merge logic (custom templates import, default templates don't overwrite) in `frontend/src/components/magic-dj/TrackConfigPanel.tsx`
- [ ] T030 Extend ExportPanel session JSON/CSV export to include send_prompt_template and send_story_prompt operation log entries in `frontend/src/components/magic-dj/ExportPanel.tsx`
- [ ] T031 [P] Add hotkey support for AI mode: number keys 1-8 trigger first 8 prompt templates, Shift+Enter submits story prompt text in `frontend/src/hooks/useDJHotkeys.ts`
- [ ] T032 [P] Add visual feedback: toast notification on prompt send ("已送出: {template.name}"), brief color pulse on PromptTemplateButton after click in `frontend/src/components/magic-dj/PromptTemplateButton.tsx`
- [ ] T033 [P] Add StoryPromptPanel UX polish: clear textarea after submit, show "已送出" toast, disable submit when empty or AI disconnected in `frontend/src/components/magic-dj/StoryPromptPanel.tsx`
- [ ] T034 Update ChannelBoard SoundLibrary filter: in AI mode, only show SFX and Music type tracks in the library (hide rescue and voice tracks) in `frontend/src/components/magic-dj/ChannelBoard.tsx`
- [ ] T035 Verify prerecorded mode is fully unaffected: test mode switch between prerecorded and AI modes, confirm CueList and 4-channel layout still work in `frontend/src/components/magic-dj/DJControlPanel.tsx`
- [ ] T040 [SC-001] Add performance verification for prompt template send latency: instrument handleSendPromptTemplate with timestamp measurement, verify text_input WebSocket message is dispatched within 100ms of button click in `frontend/tests/unit/magic-dj/PromptTemplatePanel.test.tsx`
- [ ] T041 [SC-004] Add performance verification for 20+ templates rendering: test that PromptTemplatePanel renders 25 PromptTemplateButton items without frame drops, verify scrollable container maintains smooth interaction in `frontend/tests/unit/magic-dj/PromptTemplatePanel.test.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately. T036 (store tests) runs after T006-T008.
- **Phase 2 (Foundational)**: Depends on T001 (types must exist) — BLOCKS all user stories. Note: AIControlBar depends on existing AIVoiceChannelStrip props, not full Phase 1 completion.
- **Phase 3 (US1)**: Depends on Phase 2 completion. T037-T038 (tests) run after T011-T016 implementation.
- **Phase 4 (US2)**: Depends on Phase 2 completion; can run in parallel with US1 (different components). T039 (tests) runs after T017-T020.
- **Phase 5 (US3)**: Depends on Phase 3 and Phase 4 (needs four-column layout assembled)
- **Phase 6 (US4)**: Depends on Phase 3 (needs PromptTemplateButton to exist)
- **Phase 7 (Polish)**: Depends on all user stories being complete. T040-T041 (performance tests) verify SC-001 and SC-004.

### User Story Dependencies

```
Phase 1 (Setup) ─────┐
  └─ T036 (store tests)
                      ▼
Phase 2 (Foundation) ─┬──────────────────┐
                      ▼                  ▼
Phase 3 (US1)                     Phase 4 (US2)
  └─ T037, T038 (tests)            └─ T039 (tests)
      │                                  │
      └──────────┬───────────────────────┘
                 ▼
Phase 5 (US3: Concurrent Audio + Layout Assembly)
                 │
                 ▼
Phase 6 (US4: Template CRUD)
                 │
                 ▼
Phase 7 (Polish + Performance Tests)
  └─ T040 (SC-001), T041 (SC-004)
```

### Within Each User Story

- Types/store extensions before component creation
- Component creation before page-level integration
- Integration before visual polish

### Parallel Opportunities

**Phase 1 (all parallel)**:
- T001, T002, T003 can all run in parallel (different sections of same file, but independent content)
- T036 (store tests) runs after T006-T008

**Phase 2 (parallel)**:
- T009, T010 can run in parallel (different files)

**Phase 3 + Phase 4 (cross-story parallel)**:
- T011, T012 (US1 components) can run in parallel with T017 (US2 component)
- All three are different files with no dependencies
- T037, T038 (US1 tests) can run in parallel with T039 (US2 tests)

**Phase 6 (partial parallel)**:
- T025 (editor modal) can run in parallel with other stories

**Phase 7 (mostly parallel)**:
- T029, T030, T031, T032, T033 can all run in parallel (different files)
- T040, T041 (performance tests) can run in parallel with other Phase 7 tasks

---

## Parallel Example: US1 + US2 Concurrent Start

```bash
# After Phase 2 completes, launch US1 and US2 components in parallel:
Task: T011 "[US1] Create PromptTemplateButton in frontend/src/components/magic-dj/PromptTemplateButton.tsx"
Task: T012 "[US1] Create PromptTemplatePanel in frontend/src/components/magic-dj/PromptTemplatePanel.tsx"
Task: T017 "[US2] Create StoryPromptPanel in frontend/src/components/magic-dj/StoryPromptPanel.tsx"

# Then integrate sequentially:
Task: T013 "[US1] Add handleSendPromptTemplate in MagicDJPage.tsx"
Task: T018 "[US2] Add handleSendStoryPrompt in MagicDJPage.tsx"

# Then assemble layout:
Task: T014 "[US1] Integrate PromptTemplatePanel into DJControlPanel"
Task: T019 "[US2] Integrate StoryPromptPanel into DJControlPanel"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Types & Store (T001-T008) + Store Tests (T036)
2. Complete Phase 2: AIControlBar extraction (T009-T010)
3. Complete Phase 3: US1 — Prompt Template buttons working (T011-T016) + Tests (T037-T038)
4. **STOP and VALIDATE**: Click prompt template → text_input sent → AI behavior changes. All tests pass.
5. This alone delivers the core value: RD can instantly control AI behavior

### Incremental Delivery

1. Setup + Foundation → Types and AIControlBar ready
2. US1 (Prompt Templates) → Test: click buttons → AI responds → **MVP! 🎯**
3. US2 (Story Prompts) → Test: select/type stories → AI transitions
4. US3 (Concurrent Audio) → Test: AI + SFX + Music simultaneously
5. US4 (Template CRUD) → Test: add/edit/delete custom templates
6. Polish → Hotkeys, export, visual feedback

### Single Developer Strategy

1. Phase 1 + T036 → Phase 2 → Phase 3 + T037-T038 → Phase 4 + T039 → Phase 5 → Phase 6 → Phase 7 + T040-T041
2. Validate at each checkpoint before proceeding (tests must pass)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 41 |
| **Phase 1 (Setup + Tests)** | 9 tasks (8 impl + 1 test) |
| **Phase 2 (Foundation)** | 2 tasks |
| **Phase 3 (US1 + Tests)** | 8 tasks (6 impl + 2 tests) |
| **Phase 4 (US2 + Tests)** | 5 tasks (4 impl + 1 test) |
| **Phase 5 (US3 - Concurrent Audio)** | 4 tasks |
| **Phase 6 (US4 - Template CRUD)** | 4 tasks |
| **Phase 7 (Polish + Perf Tests)** | 9 tasks (7 polish + 2 perf tests) |
| **Parallel opportunities** | 18 tasks marked [P] |
| **MVP scope** | Phase 1-3 (19 tasks) |
| **Test tasks** | 6 (T036-T041) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All WebSocket text_input sending uses existing backend infrastructure (no backend changes needed)
- Prerecorded mode must remain fully functional throughout implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
