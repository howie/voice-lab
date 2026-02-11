# Research: Long Text TTS Segmented Synthesis

**Feature**: 超長文字 TTS 自動分段合成
**Date**: 2026-02-11

## 1. Text Splitting Strategy

### Decision: Sentence-boundary splitting with byte-aware limits

**Rationale**: TTS providers have diverse limits (byte-based for Gemini, char-based for others). Splitting at sentence boundaries preserves prosody and natural speech flow. Unicode-aware splitting is essential for CJK text where a single character = 3 UTF-8 bytes.

**Alternatives considered**:
- **NLTK sentence tokenizer**: Too heavy a dependency; overkill for segmentation needs. Would add ~40MB to Docker image.
- **Fixed character count**: Loses sentence context; causes unnatural pauses mid-sentence.
- **Paragraph-only splitting**: Too coarse; paragraphs can still exceed provider limits.

### Splitting Priority (descending)

| Priority | Boundary | Pattern | Rationale |
|----------|----------|---------|-----------|
| 1 | Paragraph | `\n\n` | Natural topic break |
| 2 | Chinese sentence-end | `。！？` | Complete thought boundary |
| 3 | English sentence-end | `. ! ? ` (with trailing space) | Complete thought boundary |
| 4 | Chinese clause-end | `，；：` | Clause boundary |
| 5 | English clause-end | `, ; : ` (with trailing space) | Clause boundary |
| 6 | Hard cut | Character position | Last resort, respects UTF-8 boundary |

### Byte vs Character Limit Handling

| Provider | Limit Type | Max Value | Effective CJK Chars |
|----------|-----------|-----------|---------------------|
| gemini | bytes | 4000 | ~1333 |
| azure | chars | 5000 | 5000 |
| elevenlabs | chars | 5000 | 5000 |
| gcp | chars | 5000 | 5000 |
| openai | chars | 4096 | 4096 |
| voai | chars | 500 | 500 |

**Decision**: `TextSplitter` accepts a `max_unit` parameter (`bytes` or `chars`) with a `max_value`. For Gemini, use `bytes`/`4000`; for others, use `chars`/`max_text_length`.

## 2. Audio Merging Strategy

### Decision: Reuse existing `SegmentedMergerService`

**Rationale**: The multi-role TTS module already implements segment-by-segment synthesis, pydub-based audio merging with configurable gap/crossfade, volume normalization, and turn timing tracking. Reusing it avoids code duplication and maintains consistency.

**Key reuse points**:
- `SegmentedMergerService.synthesize_and_merge()` — per-segment synthesis + merge
- `MergeConfig` — gap, crossfade, normalization config
- `DialogueTurn` — wraps each text segment as a "turn" with same speaker
- `TurnTiming` — segment timing metadata

**Adaptation needed**:
- Default `gap_ms` should be lower for same-speaker segments (100ms vs 300ms for multi-role)
- `crossfade_ms` of 30-50ms for smoother same-speaker transitions
- Single speaker → single voice_id in voice_map

## 3. Concurrency and Rate Limiting

### Decision: Sequential synthesis with optional parallelism

**Rationale**: Most providers have strict rate limits. Gemini limits concurrent requests to 2 via semaphore. Sequential synthesis with request delays (already in `SegmentedMergerService`) is the safe default.

**Future optimization**: For providers with higher rate limits (Azure, ElevenLabs), parallel synthesis of segments could reduce total latency. This is out of scope for the initial implementation.

## 4. Where to Integrate in the Architecture

### Decision: New `SynthesizeLongText` use case + route-level detection

**Rationale**: Clean Architecture requires business logic in use cases, not routes. A dedicated use case keeps the single-responsibility principle and is independently testable.

**Alternatives considered**:
- **Modify existing `SynthesizeSpeech`**: Adds complexity to an already working use case; violates SRP.
- **Route-level splitting only**: Moves business logic into the presentation layer; violates Clean Architecture.
- **Middleware approach**: Too implicit; hard to test and debug.

**Integration flow**:
```
Route: POST /tts/synthesize
  ├── text.encode("utf-8") <= provider_limit → existing SynthesizeSpeech
  └── text.encode("utf-8") > provider_limit  → SynthesizeLongText
         ├── TextSplitter.split() → segments
         ├── Wrap segments as DialogueTurn[]
         └── SegmentedMergerService.synthesize_and_merge()
```

## 5. Frontend UX for Long Text

### Decision: Progressive feedback with elapsed timer

**Rationale**: Long text synthesis may take 30-60+ seconds. Users need feedback to know the system is working.

**Approach**:
- Show segment progress: "Synthesizing segment 3/7..."
- Show elapsed time after 5 seconds
- Show warning after 30 seconds: "Long text synthesis in progress"
- Support cancellation via AbortController

**Alternative considered**:
- Real-time streaming per segment: More complex; requires WebSocket or SSE changes. Deferred to future enhancement.

## 6. Provider-Specific Considerations

### Gemini
- **Byte limit**: 4000 bytes (not characters)
- **Semaphore**: Max 2 concurrent requests
- **Request delay**: 200ms between segments (already configured)
- **Style prompt**: Prepended to each segment (consistent voice across segments)

### Azure
- **SSML support**: Could use single SSML with `<break>` tags instead of segmentation for texts within SSML limit (50,000 chars). Out of scope initially.
- **Character limit**: 5000 per request

### ElevenLabs
- **Character limit**: 5000 per request
- **Streaming**: Supports native streaming; future enhancement could stream per-segment

### VoAI
- **Character limit**: 500 per request (most aggressive segmentation needed)
- **Request delay**: May need delay to avoid rate limiting
