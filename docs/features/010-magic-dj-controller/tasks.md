# Tasks: Magic DJ Controller

**Input**: Design documents from `/docs/features/010-magic-dj-controller/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Not explicitly requested - excluded per specification guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for source, `frontend/tests/` for tests
- Based on existing Voice Lab frontend structure

---

## Phase 1: Setup

**Purpose**: Project initialization and basic structure for Magic DJ module

- [x] T001 Create magic-dj component directory at `frontend/src/components/magic-dj/`
- [x] T002 [P] Create magic-dj route directory at `frontend/src/routes/magic-dj/`
- [x] T003 [P] Define TypeScript types and interfaces in `frontend/src/types/magic-dj.ts` including Track, TrackType, TrackPlaybackState, OperationMode, MagicDJState, DJSettings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create magicDJStore with Zustand in `frontend/src/stores/magicDJStore.ts` including tracks, trackStates, currentMode, isAIConnected, elapsedTime, settings state and actions
- [x] T005 Create useMultiTrackPlayer hook in `frontend/src/hooks/useMultiTrackPlayer.ts` implementing Web Audio API multi-track playback with AudioContext, GainNode per track, preloading, play/stop/volume control
- [x] T006 Create useDJHotkeys hook in `frontend/src/hooks/useDJHotkeys.ts` implementing keydown event listeners for Space (forceSubmit), Escape (interrupt), M (toggleMode), F (filler), W (wait), E (end), 1-5 (tracks)
- [x] T007 Create MagicDJPage route component in `frontend/src/routes/magic-dj/MagicDJPage.tsx` as main page container
- [x] T008 Add Magic DJ route to `frontend/src/App.tsx` at path `/magic-dj`
- [x] T009 Add Magic DJ navigation item to `frontend/src/components/layout/Sidebar.tsx` with appropriate icon
- [x] T048 Implement operation priority queue in magicDJStore with debounce logic (100ms window) and priority levels: interrupt > emergency > forceSubmit > playback

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 即時語音互動控制 (Priority: P1) 🎯 MVP

**Goal**: RD 可透過控制台手動控制音訊送出時機、觸發思考音效、中斷 AI 回應

**Independent Test**: 模擬「收到語音 → 強制送出 → 播放思考音效 → AI 回應」的完整流程

### Implementation for User Story 1

- [x] T010 [P] [US1] Create ForceSubmitButton component in `frontend/src/components/magic-dj/ForceSubmitButton.tsx` that triggers end_turn via existing useWebSocket, shows visual feedback on click/Space key
- [x] T011 [P] [US1] Create InterruptButton component in `frontend/src/components/magic-dj/InterruptButton.tsx` that sends interrupt message via WebSocket, stops AI audio playback
- [x] T012 [P] [US1] Create FillerSoundTrigger component in `frontend/src/components/magic-dj/FillerSoundTrigger.tsx` that plays thinking sound effect via useMultiTrackPlayer on F key or click
- [x] T013 [US1] Integrate ForceSubmitButton with magicDJStore to auto-trigger filler sound when autoPlayFillerOnSubmit is enabled
- [x] T014 [US1] Connect US1 components to existing interactionStore for Gemini WebSocket connection management
- [x] T015 [US1] Add US1 components to DJControlPanel layout in `frontend/src/components/magic-dj/DJControlPanel.tsx`

**Checkpoint**: User Story 1 should be fully functional - RD can force submit, play filler, and interrupt AI

---

## Phase 4: User Story 2 - 預錄音檔播放 (Priority: P1)

**Goal**: RD 可像 DJ 一樣快速播放預錄音檔，支援多音軌同時播放

**Independent Test**: 預先載入音檔列表，測試播放、暫停、切換、疊加音效

### Implementation for User Story 2

- [x] T016 [P] [US2] Create TrackList component in `frontend/src/components/magic-dj/TrackList.tsx` displaying all tracks with hotkey labels, play status indicators
- [x] T017 [P] [US2] Create TrackPlayer component in `frontend/src/components/magic-dj/TrackPlayer.tsx` with play/stop button, volume slider, progress indicator per track
- [x] T018 [US2] Implement track preloading on MagicDJPage mount using useMultiTrackPlayer.loadTrack() for all DEFAULT_TRACKS
- [x] T019 [US2] Add hotkey bindings for tracks 1-5 in useDJHotkeys to trigger track playback
- [x] T020 [US2] Implement multi-track mixing in useMultiTrackPlayer allowing simultaneous playback of background music + sound effects
- [x] T021 [US2] Add US2 components to DJControlPanel layout, ensure playback latency < 100ms
- [x] T046 [US2] Implement track loading error state in useMultiTrackPlayer with per-track error flag and retry capability
- [x] T047 [US2] Add error UI to TrackList showing failed tracks with red indicator and retry button

**Checkpoint**: User Story 2 should be fully functional - RD can play/stop tracks via click or hotkey, layer multiple tracks

---

## Phase 5: User Story 3 - 模式切換 (Priority: P2)

**Goal**: RD 可快速在「預錄模式」和「AI 對話模式」之間切換

**Independent Test**: 從收玩具歌切換到「封印的魔法書」Q&A，驗證切換無縫性

### Implementation for User Story 3

- [x] T022 [P] [US3] Create ModeSwitch component in `frontend/src/components/magic-dj/ModeSwitch.tsx` showing current mode (prerecorded/ai-conversation), toggle button/indicator
- [x] T023 [US3] Implement mode switching logic in magicDJStore.setMode() that updates currentMode and manages WebSocket connection state
- [x] T024 [US3] Ensure AI connection persists in standby when switching to prerecorded mode (no reconnection delay)
- [x] T025 [US3] Add hotkey M for mode toggle in useDJHotkeys
- [x] T026 [US3] Add ModeSwitch to DJControlPanel header, ensure mode switch completes in < 500ms

**Checkpoint**: User Story 3 should be fully functional - RD can switch modes instantly without losing AI connection

---

## Phase 6: User Story 4 - 救場語音 (Priority: P2)

**Goal**: RD 可快速觸發救場語音應對 AI 延遲或錯誤

**Independent Test**: 模擬 AI 無回應超過 4 秒，測試救場語音觸發

### Implementation for User Story 4

- [x] T027 [P] [US4] Create RescuePanel component in `frontend/src/components/magic-dj/RescuePanel.tsx` with two buttons: 「等待填補」(W key) and 「緊急結束」(E key)
- [x] T028 [US4] Implement rescue sound playback in RescuePanel using useMultiTrackPlayer for filler_wait and track_end
- [x] T029 [US4] Add visual indicator in DJControlPanel when AI response exceeds 4 seconds (based on magicDJStore timing)
- [x] T030 [US4] Ensure rescue sounds interrupt current AI playback and take priority
- [x] T031 [US4] Add RescuePanel to DJControlPanel layout with prominent styling for emergency access

**Checkpoint**: User Story 4 should be fully functional - RD can quickly rescue from AI delays or errors

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Session timer, integration, and final polish

- [x] T032 [P] Create SessionTimer component in `frontend/src/components/magic-dj/SessionTimer.tsx` showing elapsed time, warning at 25 min, alert at 30 min
- [x] T033 Implement session timing logic in magicDJStore with start/stop/reset actions
- [x] T034 [P] Integrate SessionTimer with DJControlPanel header
- [x] T035 Create main DJControlPanel component in `frontend/src/components/magic-dj/DJControlPanel.tsx` assembling all US1-US4 components into cohesive layout
- [x] T036 Style DJControlPanel with Tailwind CSS for intuitive DJ-style interface (large buttons, clear visual hierarchy)
- [x] T037 Add keyboard shortcut reference panel to MagicDJPage showing all hotkey mappings
- [x] T038 Verify all success criteria: audio latency < 100ms, mode switch < 500ms, system delay < 50ms
- [x] T039 Validate quickstart.md test flow works end-to-end
- [x] T040 [P] Define Session and Observation data types in `frontend/src/types/magic-dj.ts` including SessionRecord, OperationLog, ObservationEntry
- [x] T041 Create useSessionStorage hook in `frontend/src/hooks/useSessionStorage.ts` implementing localStorage read/write for session data with auto-save on operation
- [x] T042 [P] Create ExportPanel component in `frontend/src/components/magic-dj/ExportPanel.tsx` with JSON and CSV export buttons
- [x] T043 Implement JSON export function generating downloadable session file with all operation logs
- [x] T044 Implement CSV export function generating spreadsheet-compatible observation data
- [x] T045 Add ExportPanel to DJControlPanel footer area
- [x] T049 Add visual feedback for ignored operations (grey flash on deprioritized buttons)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 priority and can run in parallel
  - US3 and US4 are both P2 priority and can run in parallel after US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Needs useMultiTrackPlayer for filler sound, useWebSocket for AI control
- **User Story 2 (P1)**: Can start after Foundational - Needs useMultiTrackPlayer for track playback
- **User Story 3 (P2)**: Can start after Foundational - Needs magicDJStore mode state, optional to wait for US1/US2
- **User Story 4 (P2)**: Can start after Foundational - Needs useMultiTrackPlayer, optional to wait for US1/US2

### Within Each User Story

- Components can be created in parallel [P]
- Integration tasks depend on component completion
- DJControlPanel integration is final step per story

### Parallel Opportunities

**Phase 1** (all can run in parallel):
```
T001, T002, T003 → parallel
```

**Phase 2** (sequential due to dependencies):
```
T004 (store) → T005 (hook depends on types from T003)
T006 (hotkeys) → parallel with T005
T007-T009 (routing) → after T004
```

**User Stories** (can run in parallel by different developers):
```
Developer A: US1 (T010-T015)
Developer B: US2 (T016-T021)
Then:
Developer A: US3 (T022-T026)
Developer B: US4 (T027-T031)
```

---

## Parallel Example: User Story 1

```bash
# Launch all US1 components together:
Task: "Create ForceSubmitButton in frontend/src/components/magic-dj/ForceSubmitButton.tsx"
Task: "Create InterruptButton in frontend/src/components/magic-dj/InterruptButton.tsx"
Task: "Create FillerSoundTrigger in frontend/src/components/magic-dj/FillerSoundTrigger.tsx"

# Then integration (sequential):
Task: "Integrate ForceSubmitButton with magicDJStore..."
Task: "Connect US1 components to interactionStore..."
Task: "Add US1 components to DJControlPanel..."
```

---

## Parallel Example: User Story 2

```bash
# Launch all US2 components together:
Task: "Create TrackList in frontend/src/components/magic-dj/TrackList.tsx"
Task: "Create TrackPlayer in frontend/src/components/magic-dj/TrackPlayer.tsx"

# Then integration (sequential):
Task: "Implement track preloading..."
Task: "Add hotkey bindings..."
Task: "Implement multi-track mixing..."
Task: "Add US2 components to DJControlPanel..."
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009) - CRITICAL
3. Complete Phase 3: User Story 1 (T010-T015) - Core AI control
4. Complete Phase 4: User Story 2 (T016-T021) - Track playback
5. **STOP and VALIDATE**: RD can do basic testing with force submit + tracks
6. Deploy/demo if ready for MVP testing

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test AI control → Basic MVP
3. Add US2 → Test track playback → Full P1 MVP!
4. Add US3 → Test mode switching → Enhanced UX
5. Add US4 → Test rescue flows → Production ready
6. Add Polish → Timer, styling → Release

### Single Developer Strategy

Follow priority order:
1. Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → CHECKPOINT
2. Phase 5 (US3) → Phase 6 (US4) → CHECKPOINT
3. Phase 7 (Polish) → RELEASE

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Leverage existing hooks: useAudioPlayback, useWebSocket, interactionStore
- No new backend APIs needed - pure frontend implementation
