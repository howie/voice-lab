# Implementation Plan: Long Text TTS Segmented Synthesis

**Branch**: `claude/fix-tts-timeout-PQ8cR` | **Date**: 2026-02-11
**Input**: `docs/improvement/long-text-tts-timeout/README.md` (Phase 3b)
**Related**: 001-pipecat-tts-server, 005-multi-role-tts

## Summary

讓 TTS 合成支援超出 provider 單次上限的長文字輸入。系統在語意邊界（句號、逗號等）自動分段，逐段呼叫 TTS provider 後合併音訊。核心策略是**複用現有的 `SegmentedMergerService`**，僅新增一個 `TextSplitter` 工具類和 `SynthesizeLongText` use case。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, pydub, httpx, SQLAlchemy 2.0+
**Storage**: Local filesystem (merged audio), PostgreSQL (synthesis logs)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (Cloud Run)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 50,000 字元以內的文字皆可合成；延遲 = N × 單段延遲 + merge overhead
**Constraints**: Gemini 4000 bytes/request, Semaphore max 2 concurrent; VoAI 500 chars/request
**Scale/Scope**: 單一使用者請求，無需考慮多使用者排隊

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | PASS | TextSplitter 是純函式，適合 unit test 先行；use case 適合 integration test |
| II. Unified API Abstraction | PASS | 透過 ITTSProvider 統一介面呼叫，不直接呼叫 provider |
| III. Performance Benchmarking | PASS | 記錄 segment_count、latency_ms、duration_ms |
| IV. Documentation First | PASS | quickstart.md + contracts/ 先於實作 |
| V. Clean Architecture | PASS | TextSplitter → domain/services; Use case → application/use_cases; Route → presentation |

## Project Structure

### Documentation (this improvement)

```text
docs/improvement/long-text-tts/
├── plan.md              # This file
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: usage guide
└── contracts/
    └── tts-long-text.yaml  # Phase 1: OpenAPI contract
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── long_text_tts.py              # NEW: TextSegment, SplitConfig, LongTextTTSResult
│   │   ├── services/
│   │   │   └── text_splitter.py              # NEW: TextSplitter service
│   │   └── config/
│   │       └── provider_limits.py            # MODIFY: add limit_type field
│   ├── application/
│   │   └── use_cases/
│   │       └── synthesize_long_text.py       # NEW: SynthesizeLongText use case
│   └── presentation/
│       └── api/
│           ├── routes/
│           │   └── tts.py                    # MODIFY: route detection + preview endpoint
│           └── schemas/
│               └── tts.py                    # MODIFY: raise max_length, add metadata fields
└── tests/
    ├── unit/
    │   └── test_text_splitter.py             # NEW: TextSplitter unit tests
    └── integration/
        └── test_long_text_synthesis.py       # NEW: end-to-end integration tests

frontend/
└── src/
    ├── stores/
    │   └── ttsStore.ts                       # MODIFY: progress feedback for long text
    └── components/
        └── tts/
            └── SynthesisProgress.tsx         # NEW: segment progress indicator
```

**Structure Decision**: Web application (backend + frontend). All new backend code follows the existing Clean Architecture layers. Frontend changes are minimal (progress UI only).

## Complexity Tracking

No constitution violations. All changes follow existing patterns.

---

## Implementation Phases

### Phase 1: TextSplitter Core (Backend Domain Layer)

**Goal**: Implement the text splitting algorithm with comprehensive tests.

**Files**:
- `backend/src/domain/services/text_splitter.py` (NEW)
- `backend/src/domain/entities/long_text_tts.py` (NEW)
- `backend/tests/unit/test_text_splitter.py` (NEW)

**Tasks**:

1. **Define entities** (`long_text_tts.py`):
   - `TextSegment` dataclass with validation
   - `SplitConfig` dataclass with mutual exclusion validation (bytes XOR chars)
   - `LongTextTTSResult` dataclass

2. **Implement TextSplitter** (`text_splitter.py`):
   - `split(text: str) -> list[TextSegment]` — main entry point
   - `needs_splitting(text: str) -> bool` — quick check
   - `_find_best_boundary(text: str, max_pos: int) -> tuple[int, str]` — boundary search
   - `_byte_limit_to_char_pos(text: str, max_bytes: int) -> int` — byte-to-char mapping
   - Boundary priority: paragraph > sentence (ZH/EN) > clause (ZH/EN) > hard cut

3. **Write unit tests** (`test_text_splitter.py`):
   - Test: text shorter than limit → single segment, no split
   - Test: text splits at Chinese sentence boundary (。！？)
   - Test: text splits at English sentence boundary (. ! ?)
   - Test: text splits at paragraph boundary (\n\n)
   - Test: text falls back to clause boundary when no sentence boundary exists
   - Test: hard cut when no boundary found (e.g., continuous text without punctuation)
   - Test: byte-based splitting (Gemini scenario: CJK 3 bytes/char)
   - Test: char-based splitting (Azure/ElevenLabs scenario)
   - Test: empty text → raises ValueError
   - Test: style prompt prepended to each segment correctly
   - Test: mixed CJK + ASCII text handles byte counting correctly

**Acceptance criteria**:
- All tests pass
- `ruff check` + `ruff format --check` + `mypy` pass

---

### Phase 2: ProviderLimits Enhancement

**Goal**: Add `limit_type` to ProviderLimits for byte vs char distinction.

**Files**:
- `backend/src/domain/config/provider_limits.py` (MODIFY)
- Existing tests for provider_limits (UPDATE)

**Tasks**:

1. **Add `limit_type` field** to `ProviderLimits`:
   ```python
   limit_type: str = "chars"  # "chars" or "bytes"
   ```

2. **Update Gemini entry**:
   ```python
   "gemini": ProviderLimits(
       provider_id="gemini",
       max_text_length=4000,    # Now represents bytes
       limit_type="bytes",
       recommended_max_length=2400,  # ~800 CJK chars in bytes
       warning_message="...",
   ),
   ```

3. **Add helper** `get_split_config(provider_id: str) -> SplitConfig`:
   - Reads `ProviderLimits` and returns a `SplitConfig` with correct max_bytes/max_chars

4. **Update `validate_text_length`** to handle byte-based validation:
   - When `limit_type == "bytes"`: compare `len(text.encode("utf-8"))` vs `max_text_length`
   - When `limit_type == "chars"`: compare `len(text)` vs `max_text_length` (existing behavior)

**Acceptance criteria**:
- Existing tests still pass (backward compatible)
- New `limit_type` field defaults to `"chars"` (no breaking change)
- Gemini validation uses byte counting

---

### Phase 3: SynthesizeLongText Use Case

**Goal**: Orchestrate segmented synthesis using TextSplitter + SegmentedMergerService.

**Files**:
- `backend/src/application/use_cases/synthesize_long_text.py` (NEW)
- `backend/tests/integration/test_long_text_synthesis.py` (NEW)

**Tasks**:

1. **Implement `SynthesizeLongText`** use case:
   ```python
   class SynthesizeLongText:
       def __init__(
           self,
           provider: ITTSProvider,
           storage: IStorageService | None = None,
           logger: ISynthesisLogger | None = None,
       ) -> None: ...

       async def execute(
           self,
           text: str,
           voice_id: str,
           provider_name: str,
           language: str = "zh-TW",
           output_format: AudioFormat = AudioFormat.MP3,
           style_prompt: str | None = None,
           gap_ms: int = 100,
           crossfade_ms: int = 30,
           speed: float = 1.0,
           pitch: float = 0.0,
           volume: float = 1.0,
       ) -> LongTextTTSResult: ...
   ```

2. **Execute flow**:
   - Get `SplitConfig` from `get_split_config(provider_name)`
   - Split text via `TextSplitter(config).split(text)`
   - If style_prompt provided, prepend to each segment's text
   - Wrap segments as `DialogueTurn` (speaker=`"narrator"`)
   - Build `MergeConfig` with gap_ms, crossfade_ms, provider request delay
   - Call `SegmentedMergerService.synthesize_and_merge()`
   - Map `MultiRoleTTSResult` → `LongTextTTSResult`
   - Store via `IStorageService` if available
   - Log via `ISynthesisLogger` if available

3. **Write integration tests** (mock provider):
   - Test: 3 segments merge correctly with expected timings
   - Test: style prompt applied to all segments
   - Test: storage path set when storage available
   - Test: provider error propagation (one segment fails → entire request fails)
   - Test: empty segment list → raises error

**Acceptance criteria**:
- Integration tests pass with mock provider
- Use case follows existing patterns (cf. `SynthesizeSpeech`, `SynthesizeMultiRoleUseCase`)

---

### Phase 4: Route Integration

**Goal**: Wire long text support into the existing TTS endpoint.

**Files**:
- `backend/src/presentation/api/routes/tts.py` (MODIFY)
- `backend/src/presentation/api/schemas/tts.py` (MODIFY)

**Tasks**:

1. **Update `SynthesizeRequest` schema**:
   - Raise `max_length` from 5000 to 50000
   - Add optional `segment_gap_ms: int = 100`
   - Add optional `segment_crossfade_ms: int = 30`

2. **Update `SynthesizeResponse` schema**:
   - Add optional `metadata: SynthesisMetadata | None`
   - Define `SynthesisMetadata` with segmented, segment_count, segment_timings fields

3. **Modify `/synthesize` route handler**:
   ```python
   # After provider creation, before use case execution:
   split_config = get_split_config(request_data.provider)
   splitter = TextSplitter(split_config)

   if splitter.needs_splitting(request_data.text):
       # Long text path
       use_case = SynthesizeLongText(provider=provider, storage=storage, logger=logger)
       result = await use_case.execute(
           text=request_data.text,
           voice_id=request_data.voice_id,
           provider_name=request_data.provider,
           ...
       )
       return SynthesizeResponse(
           audio_content=base64.b64encode(result.audio_content).decode(),
           content_type=result.content_type,
           duration_ms=result.duration_ms,
           latency_ms=result.latency_ms,
           storage_path=result.storage_path,
           metadata=SynthesisMetadata(
               segmented=True,
               segment_count=result.segment_count,
               ...
           ),
       )
   else:
       # Existing short text path (unchanged)
       ...
   ```

4. **Add `/synthesize/preview` endpoint**:
   - Accept `SegmentPreviewRequest` (text + provider)
   - Return `SegmentPreviewResponse` with segment details
   - No TTS API calls — pure text analysis

5. **Update text validation**:
   - Remove the 5000-char validation from route level (replaced by 50000 absolute max)
   - Keep per-segment validation inside TextSplitter

**Acceptance criteria**:
- Short text requests (<= provider limit) behave identically to before
- Long text requests return valid merged audio with metadata
- Preview endpoint works without provider credentials
- `make check` passes

---

### Phase 5: Frontend Progress UI

**Goal**: Show synthesis progress when processing long text.

**Files**:
- `frontend/src/stores/ttsStore.ts` (MODIFY)
- `frontend/src/components/tts/SynthesisProgress.tsx` (NEW)

**Tasks**:

1. **Update ttsStore**:
   - Call preview endpoint before synthesis to get segment count
   - Add state: `segmentCount`, `isLongText`, `synthesisStartTime`
   - Track elapsed time during synthesis

2. **Create SynthesisProgress component**:
   - Show "Synthesizing..." for short text (existing behavior)
   - For long text (segmentCount > 1):
     - Show "Synthesizing N segments..."
     - Show elapsed time after 5 seconds
     - Show estimated remaining time based on preview
   - Support cancel button (AbortController)

3. **Handle response metadata**:
   - If `metadata.segmented === true`, show segment count in result info
   - Display segment timings in audio player (optional, future enhancement)

**Acceptance criteria**:
- Short text UX unchanged
- Long text shows progress indicator
- Cancel button aborts the request

---

### Phase 6: TTSRequest Max Length Update

**Goal**: Update the domain entity validation to support long text.

**Files**:
- `backend/src/domain/entities/tts.py` (MODIFY)

**Tasks**:

1. **Raise `MAX_TEXT_LENGTH`** from 5000 to 50000:
   ```python
   MAX_TEXT_LENGTH = 50000  # Was 5000; per-provider limits enforced by TextSplitter
   ```

2. **Ensure no other hardcoded 5000 limits** exist in the codebase.

**Acceptance criteria**:
- `TTSRequest` accepts text up to 50,000 characters
- All existing tests pass

---

## Dependency Graph

```
Phase 1 (TextSplitter)
    │
    ├── Phase 2 (ProviderLimits) ── depends on Phase 1 entities
    │       │
    │       ▼
    ├── Phase 3 (Use Case) ──────── depends on Phase 1 + Phase 2
    │       │
    │       ▼
    └── Phase 4 (Route) ─────────── depends on Phase 3 + Phase 6
            │
            ▼
        Phase 5 (Frontend) ──────── depends on Phase 4 API contract
        Phase 6 (TTSRequest) ────── independent, can run in parallel with Phase 2-3
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Segment boundaries cause unnatural speech | Medium | Medium | Prioritize sentence boundaries; allow user to adjust gap_ms |
| Total synthesis time too long for large text | Medium | High | Show progress; support cancellation; document expected times |
| Provider rate limiting during multi-segment | Low | Medium | Sequential synthesis + request delay (already in SegmentedMergerService) |
| Audio quality degradation at merge points | Low | Medium | Use crossfade + volume normalization (already in merger) |
| Memory pressure from merging many segments | Low | Low | pydub handles incrementally; Cloud Run has 512Mi |

## Out of Scope (Future Enhancements)

- **Per-segment streaming**: SSE/WebSocket streaming of individual segments as they complete
- **Parallel segment synthesis**: Synthesize N segments concurrently for providers with high rate limits
- **Intelligent caching**: Cache segments for repeated text
- **Azure SSML mega-request**: Use single SSML with `<break>` tags instead of segmentation (up to 50K chars)
- **Segment-level voice switching**: Different voices for different segments (already supported by multi-role)
