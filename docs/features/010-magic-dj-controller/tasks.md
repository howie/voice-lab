# Tasks: Magic DJ Controller

**Input**: Design documents from `/docs/features/010-magic-dj-controller/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Constitution I (TDD) requires unit tests for core hooks and stores. Test tasks are included per Constitution compliance.

**Organization**: Tasks are grouped by user story (spec.md US1-US5) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for source, `frontend/tests/` for tests
- Based on existing Voice Lab frontend structure

---

## Phase 1: Setup

**Purpose**: Project initialization and basic structure for Magic DJ module

- [ ] T001 Create magic-dj component directory at `frontend/src/components/magic-dj/`
- [ ] T002 [P] Create magic-dj route directory at `frontend/src/routes/magic-dj/`
- [ ] T003 [P] Define TypeScript types and interfaces in `frontend/src/types/magic-dj.ts` including SoundItem, ChannelType, SoundPriority, PlaybackChannel, SoundItemLoadState, CueItem, CueItemStatus, CueList, OperationMode, MagicDJState, DJSettings per data-model.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create magicDJStore with Zustand in `frontend/src/stores/magicDJStore.ts` including soundLibrary, soundLoadStates, channels (voice/music/sfx), cueList, currentMode, isAIConnected, elapsedTime, settings state and actions per data-model.md MagicDJState/MagicDJActions
- [ ] T005 Create useMultiTrackPlayer hook in `frontend/src/hooks/useMultiTrackPlayer.ts` implementing Web Audio API multi-channel playback with AudioContext, 3 GainNodes (voice/music/sfx), preloading to AudioBuffer, play/stop/volume per channel, voice channel priority rules (rescue > normal)
- [ ] T006 [P] Create useDJHotkeys hook in `frontend/src/hooks/useDJHotkeys.ts` implementing keydown event listeners for Space (forceSubmit), Escape (interrupt/stopAll), M (toggleMode), N (playNextCue), plus dynamic hotkeys from SoundItem.hotkey field
- [ ] T007 Create MagicDJPage route component in `frontend/src/routes/magic-dj/MagicDJPage.tsx` as main page container
- [ ] T008 Add Magic DJ route to `frontend/src/App.tsx` at path `/magic-dj`
- [ ] T009 Add Magic DJ navigation item to `frontend/src/components/layout/Sidebar.tsx` with appropriate icon
- [ ] T010 Implement operation priority queue in magicDJStore with debounce logic (100ms window) and priority levels: interrupt > emergency > forceSubmit > playback (EC-002)
- [ ] T011 [P] Add visual feedback for ignored operations (grey flash on deprioritized buttons) per EC-002 SHOULD

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 即時語音互動控制 (Priority: P1) 🎯 MVP

**Goal**: RD 可透過控制台手動控制音訊送出時機、觸發思考音效、中斷 AI 回應 (FR-001, FR-002, FR-003)

**Independent Test**: 模擬「收到語音 → 強制送出 → 播放思考音效 → AI 回應 → 中斷」的完整流程

### Tests for User Story 1

- [ ] T012 [P] [US1] Unit test for ForceSubmitButton behavior in `frontend/tests/unit/magic-dj/ForceSubmitButton.test.ts` covering click trigger, Space hotkey, visual feedback, auto-filler option

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create ForceSubmitButton component in `frontend/src/components/magic-dj/ForceSubmitButton.tsx` that triggers end_turn via existing useWebSocket, shows visual feedback on click/Space key (FR-001)
- [ ] T014 [P] [US1] Create InterruptButton component in `frontend/src/components/magic-dj/InterruptButton.tsx` that sends interrupt message via WebSocket, stops AI audio playback (FR-003)
- [ ] T015 [P] [US1] Create FillerSoundTrigger component in `frontend/src/components/magic-dj/FillerSoundTrigger.tsx` that plays thinking sound effect via useMultiTrackPlayer on F key or click (FR-002)
- [ ] T016 [US1] Integrate ForceSubmitButton with magicDJStore to auto-trigger filler sound when autoPlayFillerOnSubmit is enabled
- [ ] T017 [US1] Connect US1 components to existing interactionStore for Gemini WebSocket connection management (FR-010)
- [ ] T018 [US1] Add US1 components to DJControlPanel layout in `frontend/src/components/magic-dj/DJControlPanel.tsx`

**Checkpoint**: User Story 1 fully functional - RD can force submit, play filler, and interrupt AI

---

## Phase 4: User Story 2 - 預錄音檔播放 (Priority: P1)

**Goal**: RD 可從聲音庫 (Sound Library) 快速播放預錄音檔，支援 3 頻道同時播放 (FR-004, FR-005, FR-006, FR-007, FR-024~FR-027)

**Independent Test**: 預先載入聲音庫，測試播放、即時中斷、切換、多頻道疊加

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for useMultiTrackPlayer in `frontend/tests/unit/magic-dj/useMultiTrackPlayer.test.ts` covering multi-channel playback, voice priority (rescue/normal), stop channel, stop all, volume control, preload, load error/retry
- [ ] T020 [P] [US2] Unit test for magicDJStore sound library actions in `frontend/tests/unit/magic-dj/magicDJStore.test.ts` covering addSound, updateSound, deleteSound, reorderSounds, playSound channel routing

### Implementation for User Story 2

- [ ] T021 [P] [US2] Create SoundLibrary component in `frontend/src/components/magic-dj/SoundLibrary.tsx` displaying all sound items grouped by channel (rescue voice / voice / sfx / music), with hotkey labels and play status indicators (FR-005, FR-006)
- [ ] T022 [P] [US2] Create SoundItemCard component in `frontend/src/components/magic-dj/SoundItemCard.tsx` with play/stop button, hotkey badge, channel indicator, drag handle (draggable for US3)
- [ ] T023 [P] [US2] Create ChannelStrip component in `frontend/src/components/magic-dj/ChannelStrip.tsx` showing per-channel playback status, volume slider, stop button per DD-001 four-column layout
- [ ] T024 [US2] Implement sound preloading on MagicDJPage mount using useMultiTrackPlayer.loadSound() for all DEFAULT_SOUND_LIBRARY items
- [ ] T025 [US2] Implement sound load error state in useMultiTrackPlayer with per-sound error flag, retry capability, red indicator (EC-001)
- [ ] T026 [US2] Add hotkey bindings for sound items in useDJHotkeys to trigger playback based on SoundItem.hotkey field
- [ ] T027 [US2] Add US2 components to DJControlPanel layout, ensure playback latency < 100ms (SC-003)

**Checkpoint**: User Story 2 fully functional - RD can play/stop sounds via click or hotkey, layer multiple channels

---

## Phase 5: User Story 3 - 播放清單 Cue List (Priority: P1)

**Goal**: RD 可從聲音庫拖曳項目到播放清單 (Cue List)，預先排好播放順序，測試時依序播放 (FR-028~FR-037)

**Independent Test**: RD 預先設定播放清單，依序點擊「播放下一個」驗證順序正確性

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for useCueList hook in `frontend/tests/unit/magic-dj/useCueList.test.ts` covering addToCueList, removeFromCueList, reorderCueList, playNextCue, resetCuePosition, clearCueList, auto-advance position, end-of-list reset, invalid item detection
- [ ] T029 [P] [US3] Unit test for useDragAndDrop hook in `frontend/tests/unit/magic-dj/useDragAndDrop.test.ts` covering cross-container drag (Sound Library → Cue List), intra-list reorder

### Implementation for User Story 3

- [ ] T030 [P] [US3] Create useCueList hook in `frontend/src/hooks/useCueList.ts` managing CueList state per data-model.md: addToCueList, removeFromCueList, reorderCueList, playNextCue, resetCuePosition, clearCueList, currentPosition tracking, auto-advance on playback end
- [ ] T031 [P] [US3] Create useDragAndDrop hook in `frontend/src/hooks/useDragAndDrop.ts` implementing HTML5 Drag and Drop API for cross-container drag (Sound Library → Cue List) and intra-list reorder per research.md decision
- [ ] T032 [P] [US3] Create CueList component in `frontend/src/components/magic-dj/CueList.tsx` displaying ordered items with sequence numbers (FR-031), current position highlight (FR-033), remove button per item (FR-032), drop zone for drag targets (FR-029)
- [ ] T033 [P] [US3] Create CueItem component in `frontend/src/components/magic-dj/CueItem.tsx` showing sound name, sequence number, play status (pending/playing/played/invalid), drag handle for reorder (FR-030), remove button
- [ ] T034 [US3] Create PlayNextButton component in `frontend/src/components/magic-dj/PlayNextButton.tsx` that calls useCueList.playNextCue() and displays remaining count (FR-034)
- [ ] T035 [US3] Implement auto-advance logic: when sound finishes playing, move cueList.currentPosition to next item without auto-playing (FR-035)
- [ ] T036 [US3] Implement end-of-list handling: when currentPosition reaches last item and playback ends, show "播放清單已結束" toast and reset position to first item (EC-007)
- [ ] T037 [US3] Implement invalid item detection: when SoundItem is deleted from sound library, mark referencing CueItems as 'invalid' status with visual warning (EC-006)
- [ ] T038 [US3] Implement same-sound-multiple-times support: allow CueList to contain multiple CueItems referencing the same SoundItem ID (FR-036)
- [ ] T039 [US3] Implement CueList localStorage persistence: save/load cueList on change using localStorage key 'magic-dj-cue-list' (FR-037)
- [ ] T040 [US3] Integrate Cue List into prerecorded mode layout: left panel = SoundLibrary, right panel = CueList per FR-028 dual-panel design
- [ ] T041 [US3] Add N hotkey for "play next cue" in useDJHotkeys

**Checkpoint**: User Story 3 fully functional - RD can build, reorder, and play through Cue List

---

## Phase 6: User Story 4 - 模式切換 (Priority: P2)

**Goal**: RD 可在「預錄模式」和「AI 對話模式」之間快速切換，保持 AI 連線 (FR-008, FR-009)

**Independent Test**: 從收玩具歌切換到「封印的魔法書」Q&A，驗證模式切換 < 500ms

### Implementation for User Story 4

- [ ] T042 [P] [US4] Create ModeSwitch component in `frontend/src/components/magic-dj/ModeSwitch.tsx` showing current mode (prerecorded/ai-conversation), toggle button/indicator with visual state
- [ ] T043 [US4] Implement mode switching logic in magicDJStore.setMode() that updates currentMode, toggles UI panels (prerecorded shows Cue List; AI shows conversation controls), manages WebSocket connection state
- [ ] T044 [US4] Ensure AI connection persists in standby when switching to prerecorded mode - no WebSocket disconnect/reconnect (FR-009)
- [ ] T045 [US4] Add M hotkey for mode toggle in useDJHotkeys (already defined in T006, verify integration)
- [ ] T046 [US4] Add ModeSwitch to DJControlPanel header, ensure mode switch completes in < 500ms (SC-004)

**Checkpoint**: User Story 4 fully functional - RD can switch modes instantly without losing AI connection

---

## Phase 7: User Story 5 - 救場語音 (Priority: P2)

**Goal**: RD 可快速觸發救場語音應對 AI 延遲或錯誤 (FR-013, FR-014)

**Independent Test**: 模擬 AI 無回應超過 4 秒，測試救場語音觸發

### Implementation for User Story 5

- [ ] T047 [P] [US5] Create RescuePanel component in `frontend/src/components/magic-dj/RescuePanel.tsx` with two prominent buttons: 「等待填補」(W key) and 「緊急結束」(E key) (FR-013)
- [ ] T048 [US5] Implement rescue sound playback in RescuePanel using useMultiTrackPlayer for voice_wait (priority: rescue) and voice_end (priority: rescue) - rescue sounds MUST interrupt current voice channel content
- [ ] T049 [US5] Add visual indicator in DJControlPanel when AI response exceeds 4 seconds (pulsing warning based on magicDJStore timing) (FR-014)
- [ ] T050 [US5] Add W and E hotkeys for rescue sounds in useDJHotkeys (already defined in T006, verify integration)
- [ ] T051 [US5] Add RescuePanel to DJControlPanel layout with prominent emergency styling

**Checkpoint**: User Story 5 fully functional - RD can quickly rescue from AI delays or errors

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Session management, data export, UI integration, performance validation

### Session & Timer

- [ ] T052 [P] Create SessionTimer component in `frontend/src/components/magic-dj/SessionTimer.tsx` showing elapsed time, warning at 25 min, alert at 30 min (FR-015, EC-004)
- [ ] T053 Implement session timing logic in magicDJStore with start/stop/reset actions
- [ ] T054 [P] Define Session and export data types in `frontend/src/types/magic-dj.ts` including SessionRecord, OperationLog
- [ ] T055 Create useSessionStorage hook in `frontend/src/hooks/useSessionStorage.ts` implementing localStorage read/write for session data with auto-save on operation (FR-016)

### Data Export

- [ ] T056 [P] Create ExportPanel component in `frontend/src/components/magic-dj/ExportPanel.tsx` with JSON and CSV export buttons
- [ ] T057 Implement JSON export function generating downloadable session file with all operation logs (FR-017)
- [ ] T058 Implement CSV export function generating spreadsheet-compatible observation data (FR-018)

### Sound Library Management Enhancement

- [ ] T059 [P] Add drag-and-drop sorting to SoundLibrary using HTML5 DnD (upgrade to @dnd-kit if needed per research.md) (FR-019)
- [ ] T060 Update SoundLibrary to allow editing sound items, enabling TTS regeneration (FR-020)
- [ ] T061 Update SoundLibrary to allow deleting sound items with confirmation dialog (FR-021)
- [ ] T062 [P] Implement sound library configuration persistence to localStorage including item order, custom items, TTS-generated audio as base64 (FR-022)
- [ ] T063 Create SoundLibraryConfigExport component for exporting configuration as JSON (FR-023)
- [ ] T064 Create SoundLibraryConfigImport component for importing configuration from JSON file (FR-023)

### UI Assembly & Styling

- [ ] T065 Create main DJControlPanel component in `frontend/src/components/magic-dj/DJControlPanel.tsx` assembling all US1-US5 components into cohesive DJ Mixer style layout per DD-001
- [ ] T066 Style DJControlPanel with Tailwind CSS: large buttons, clear visual hierarchy, four-column channel layout, emergency buttons in red
- [ ] T067 Add keyboard shortcut reference panel to MagicDJPage showing all hotkey mappings

### Testing & Validation

- [ ] T068 [P] Unit test for useSessionStorage in `frontend/tests/unit/magic-dj/useSessionStorage.test.ts` covering save/load/export operations
- [ ] T069 Verify all success criteria: audio latency < 100ms (SC-003), mode switch < 500ms (SC-004), system delay < 50ms (SC-001), drag feedback < 200ms (SC-007), play-next < 100ms (SC-008), cue list supports 50+ items (SC-009)
- [ ] T070 Validate quickstart.md test flow works end-to-end (SC-005)

**Note**: Sound library storage is **per-browser localStorage**, not global/server-side. Each browser maintains its own configuration independently.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1) and US2 (P1) can run in parallel
  - US3 (P1) depends on US2 (needs SoundLibrary drag source) but can start after Foundational
  - US4 (P2) and US5 (P2) can run in parallel after US1/US2
- **Polish (Phase 8)**: Can start incrementally after user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Needs useMultiTrackPlayer (filler sound), useWebSocket (AI control) → can start after Foundational
- **User Story 2 (P1)**: Needs useMultiTrackPlayer (sound playback) → can start after Foundational
- **User Story 3 (P1)**: Needs SoundLibrary component from US2 (drag source) + useMultiTrackPlayer → start after US2 or in parallel with shared components
- **User Story 4 (P2)**: Needs magicDJStore mode state → can start after Foundational
- **User Story 5 (P2)**: Needs useMultiTrackPlayer (rescue sounds) → can start after Foundational

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD per Constitution I)
- Components marked [P] can be created in parallel
- Integration tasks depend on component completion
- DJControlPanel integration is final step per story

### Parallel Opportunities

**Phase 1** (all parallel):
```
T001, T002, T003 → parallel
```

**Phase 2** (mostly sequential):
```
T004 (store) → T005 (hook, depends on types from T003)
T006 (hotkeys) → parallel with T005
T007-T009 (routing) → after T004
T010-T011 (priority queue) → after T004
```

**User Stories** (can run in parallel by different developers):
```
Developer A: US1 (T012-T018)
Developer B: US2 (T019-T027)
Then:
Developer A: US3 (T028-T041) - needs SoundLibrary from US2
Developer B: US4 (T042-T046) + US5 (T047-T051)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T011) - CRITICAL
3. Complete Phase 3: User Story 1 (T012-T018) - Core AI control
4. Complete Phase 4: User Story 2 (T019-T027) - Sound playback
5. **STOP and VALIDATE**: RD can do basic testing with force submit + sound library
6. Deploy/demo if ready for MVP testing

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test AI control → Basic MVP
3. Add US2 → Test sound playback → Full sound library
4. Add US3 → Test cue list → Prerecorded flow complete (Full P1 MVP!)
5. Add US4 → Test mode switching → Enhanced UX
6. Add US5 → Test rescue flows → Production ready
7. Add Polish → Timer, export, styling → Release

### Single Developer Strategy

Follow priority order:
1. Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → CHECKPOINT (P1 complete)
2. Phase 6 (US4) → Phase 7 (US5) → CHECKPOINT (P2 complete)
3. Phase 8 (Polish) → RELEASE

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability (US1-US5 match spec.md)
- Each user story should be independently completable and testable
- Tests are included per Constitution I (TDD) requirement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Leverage existing hooks: useAudioPlayback, useWebSocket, interactionStore
- No new backend APIs needed - pure frontend implementation
- Terminology: SoundItem (not Track), SoundLibrary (not TrackList) per spec.md/data-model.md
