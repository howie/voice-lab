# Tasks: Long Text TTS Segmented Synthesis

**Input**: Design documents from `/docs/improvement/long-text-tts/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/tts-long-text.yaml, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

## User Stories (derived from plan phases)

- **US1**: TextSplitter core — user can split long text into provider-safe segments
- **US2**: Backend integration — system auto-segments and merges audio for long text
- **US3**: API integration — existing endpoint transparently handles long text + preview
- **US4**: Frontend UX — user sees progress feedback during long text synthesis

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Update shared domain limits so long text can flow through the system

- [ ] T001 Raise `MAX_TEXT_LENGTH` from 5000 to 50000 in `backend/src/domain/entities/tts.py` (line 10)
- [ ] T002 [P] Raise `max_length` from 5000 to 50000 in `SynthesizeRequest.text` field in `backend/src/presentation/api/schemas/tts.py` (line 15)
- [ ] T003 [P] Raise `max_length` from 5000 to 50000 in `StreamRequest.text` field in `backend/src/presentation/api/schemas/tts.py` (line 76)

**Checkpoint**: System accepts up to 50,000 characters at API and domain level. Existing short-text behavior unchanged.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain entities and ProviderLimits enhancements that all user stories depend on

- [ ] T004 Create `TextSegment`, `SplitConfig`, `LongTextTTSResult` dataclasses in `backend/src/domain/entities/long_text_tts.py` per data-model.md
- [ ] T005 Add `limit_type: str = "chars"` field to `ProviderLimits` dataclass in `backend/src/domain/config/provider_limits.py` (line 9-16)
- [ ] T006 Update Gemini entry in `PROVIDER_LIMITS` dict to use `limit_type="bytes"` and `max_text_length=4000` in `backend/src/domain/config/provider_limits.py` (lines 20-45)
- [ ] T007 Add `get_split_config(provider_id: str) -> SplitConfig` helper function in `backend/src/domain/config/provider_limits.py`
- [ ] T008 Update `validate_text_length()` in `backend/src/domain/config/provider_limits.py` (lines 66-95) to use byte-based comparison when `limit_type == "bytes"`

**Checkpoint**: Foundation ready — domain entities exist, ProviderLimits supports byte/char distinction, Gemini uses byte validation.

---

## Phase 3: User Story 1 — TextSplitter Core (Priority: P1) 🎯 MVP

**Goal**: Implement the text splitting algorithm that segments long text at semantic boundaries respecting provider-specific byte/char limits.

**Independent Test**: `pytest backend/tests -k "text_splitter" -v`

### Tests for US1

- [ ] T009 [P] [US1] Write unit tests for TextSplitter in `backend/tests/unit/test_text_splitter.py` covering: text shorter than limit returns single segment, Chinese sentence boundary split (。！？), English sentence boundary split (. ! ?), paragraph boundary split (\n\n), clause boundary fallback (，；), hard cut fallback for continuous text, byte-based splitting for Gemini (CJK 3 bytes/char), char-based splitting for Azure, empty text raises ValueError, mixed CJK+ASCII byte counting

### Implementation for US1

- [ ] T010 [US1] Implement `TextSplitter` class in `backend/src/domain/services/text_splitter.py` with methods: `split(text) -> list[TextSegment]`, `needs_splitting(text) -> bool`, `_find_best_boundary(text, max_pos) -> tuple[int, str]`, `_byte_limit_to_char_pos(text, max_bytes) -> int`. Boundary priority: paragraph > ZH sentence > EN sentence > ZH clause > EN clause > hard cut.
- [ ] T011 [US1] Verify all TextSplitter unit tests pass and run `ruff check backend/src/domain/services/text_splitter.py`

**Checkpoint**: TextSplitter can segment any text within provider limits. All unit tests green.

---

## Phase 4: User Story 2 — SynthesizeLongText Use Case (Priority: P2)

**Goal**: Orchestrate segmented synthesis using TextSplitter + existing SegmentedMergerService to produce merged audio.

**Independent Test**: `pytest backend/tests -k "long_text_synthesis" -v`

### Tests for US2

- [ ] T012 [P] [US2] Write integration tests with mock provider in `backend/tests/integration/test_long_text_synthesis.py` covering: 3 segments merge correctly with timings, style prompt applied to all segments, storage path set when storage available, provider error propagation (one segment fails → entire request fails), single segment (no split needed) returns result directly

### Implementation for US2

- [ ] T013 [US2] Implement `SynthesizeLongText` use case in `backend/src/application/use_cases/synthesize_long_text.py`. Constructor takes `provider: ITTSProvider`, optional `storage: IStorageService`, optional `logger: ISynthesisLogger`. The `execute()` method: calls `get_split_config()`, splits via `TextSplitter`, wraps segments as `DialogueTurn` (speaker="narrator"), builds `MergeConfig` (gap_ms=100, crossfade_ms=30), calls `SegmentedMergerService.synthesize_and_merge()`, maps `MultiRoleTTSResult` → `LongTextTTSResult`.
- [ ] T014 [US2] Verify all integration tests pass and run `ruff check backend/src/application/use_cases/synthesize_long_text.py`

**Checkpoint**: SynthesizeLongText use case produces merged audio from segmented text. Integration tests green with mock provider.

---

## Phase 5: User Story 3 — Route Integration & Preview API (Priority: P3)

**Goal**: Wire long text support into the existing `/synthesize` endpoint and add `/synthesize/preview` endpoint.

**Independent Test**: `curl -X POST localhost:8000/api/v1/tts/synthesize/preview -H 'Content-Type: application/json' -d '{"text":"<2000 char Chinese text>","provider":"gemini"}'`

### Implementation for US3

- [ ] T015 [US3] Add `SynthesisMetadata`, `SegmentTiming`, `SegmentPreviewRequest`, `SegmentPreviewResponse` Pydantic schemas in `backend/src/presentation/api/schemas/tts.py` per contracts/tts-long-text.yaml
- [ ] T016 [US3] Add optional `segment_gap_ms: int = 100` and `segment_crossfade_ms: int = 30` fields to `SynthesizeRequest` in `backend/src/presentation/api/schemas/tts.py`
- [ ] T017 [US3] Add optional `metadata: SynthesisMetadata | None = None` field to `SynthesizeResponse` in `backend/src/presentation/api/schemas/tts.py`
- [ ] T018 [US3] Modify `/synthesize` route handler in `backend/src/presentation/api/routes/tts.py` (lines 100-204): after provider creation, check `TextSplitter.needs_splitting()`. If true, use `SynthesizeLongText` use case; else existing `SynthesizeSpeech` path unchanged. Update `validate_text_length` calls (lines 114-118) to skip validation when text will be auto-segmented.
- [ ] T019 [US3] Add `POST /synthesize/preview` endpoint in `backend/src/presentation/api/routes/tts.py` that accepts `SegmentPreviewRequest`, runs `TextSplitter.split()` without calling TTS API, returns `SegmentPreviewResponse` with segment details and estimated duration.
- [ ] T020 [US3] Verify short text requests still return identical responses (no regression) and long text requests return merged audio with `metadata.segmented=true`

**Checkpoint**: Existing API transparently handles long text. Preview endpoint works without credentials.

---

## Phase 6: User Story 4 — Frontend Progress UI (Priority: P4)

**Goal**: Show synthesis progress feedback when processing long text.

**Independent Test**: Enter 2000+ character Chinese text in the UI, click synthesize, observe progress indicator.

### Implementation for US4

- [ ] T021 [US4] Add `segmentCount`, `isLongText`, `synthesisStartTime` state fields to `TTSState` interface and store initialization in `frontend/src/stores/ttsStore.ts` (around lines 12-55)
- [ ] T022 [US4] Update `synthesize()` action in `frontend/src/stores/ttsStore.ts` (lines 117-164): before synthesis call, call `/synthesize/preview` to get segment count; set `isLongText` if segments > 1; track elapsed time
- [ ] T023 [US4] Create `SynthesisProgress` component in `frontend/src/components/tts/SynthesisProgress.tsx` showing: "Synthesizing..." for short text, "Synthesizing N segments..." for long text, elapsed time after 5 seconds, cancel button using AbortController
- [ ] T024 [US4] Handle response `metadata` in ttsStore: if `metadata.segmented === true`, display segment count in synthesis result info

**Checkpoint**: Short text UX unchanged. Long text shows progress with segment count and cancel support.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and quality checks

- [ ] T025 Run `make check` (ruff check, ruff format, mypy, eslint, tsc) and fix any issues
- [ ] T026 Run full test suite `pytest backend/tests -v` and verify no regressions
- [ ] T027 Verify quickstart.md examples work end-to-end against running server

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 must complete before T004)
- **US1 (Phase 3)**: Depends on Phase 2 (needs entities from T004)
- **US2 (Phase 4)**: Depends on US1 (needs TextSplitter from T010)
- **US3 (Phase 5)**: Depends on US2 (needs SynthesizeLongText from T013) + Phase 1 (T002/T003 for schema limits)
- **US4 (Phase 6)**: Depends on US3 (needs preview API from T019)
- **Polish (Phase 7)**: Depends on all previous phases

### Within Each Phase

```
Phase 1:  T001 → T002 [P] + T003 [P]
Phase 2:  T004 → T005 → T006 → T007 → T008
Phase 3:  T009 [P] → T010 → T011
Phase 4:  T012 [P] → T013 → T014
Phase 5:  T015 [P] + T016 [P] + T017 [P] → T018 → T019 → T020
Phase 6:  T021 → T022 → T023 [P] → T024
Phase 7:  T025 → T026 → T027
```

### Parallel Opportunities

```bash
# Phase 1: Schema updates in parallel after T001
Task T002 + Task T003  # Different field locations in same file, but can batch

# Phase 3+4: Tests can be written in parallel with each other
Task T009 + Task T012  # Different test files

# Phase 5: Schema additions in parallel
Task T015 + Task T016 + Task T017  # Same file but additive schemas
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup (raise limits)
2. Complete Phase 2: Foundational (entities + provider limits)
3. Complete Phase 3: US1 — TextSplitter with tests
4. Complete Phase 4: US2 — SynthesizeLongText use case
5. **STOP and VALIDATE**: Test with mock provider, verify segments merge correctly

### Full Delivery

1. MVP above → Backend can segment and merge
2. Add US3 → API transparently handles long text + preview
3. Add US4 → Frontend shows progress
4. Polish → make check, full test suite, quickstart validation

---

## Notes

- Constitution requires TDD: tests written before implementation (T009 before T010, T012 before T013)
- Gemini uses byte limits (4000 bytes); all others use char limits
- Reuses existing `SegmentedMergerService` and `DialogueTurn` from multi-role TTS — no new audio merging code needed
- `validate_text_length()` in routes must be updated to not reject long text that will be auto-segmented
- Total tasks: 27
  - Setup: 3 | Foundational: 5 | US1: 3 | US2: 3 | US3: 6 | US4: 4 | Polish: 3
