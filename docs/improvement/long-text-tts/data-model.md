# Data Model: Long Text TTS Segmented Synthesis

**Feature**: 超長文字 TTS 自動分段合成
**Date**: 2026-02-11

## 1. New Entities

### TextSegment

Represents a single chunk of text after splitting.

```python
@dataclass(frozen=True)
class TextSegment:
    """A single text segment produced by TextSplitter."""
    text: str           # The segment text content
    index: int          # Position in the sequence (0-based)
    byte_length: int    # UTF-8 byte length of text
    char_length: int    # Character count
    boundary_type: str  # How this segment was split: "paragraph", "sentence", "clause", "hard"
```

**Validation rules**:
- `text`: non-empty
- `index`: >= 0
- `byte_length`: must equal `len(text.encode("utf-8"))`
- `boundary_type`: one of `"paragraph"`, `"sentence"`, `"clause"`, `"hard"`

### SplitConfig

Configuration for the text splitting algorithm.

```python
@dataclass(frozen=True)
class SplitConfig:
    """Configuration for text segmentation."""
    max_bytes: int | None = None        # Max bytes per segment (e.g., 4000 for Gemini)
    max_chars: int | None = None        # Max chars per segment (e.g., 5000 for Azure)
    overlap_chars: int = 0              # Character overlap between segments (future use)
    preserve_paragraphs: bool = True    # Try to keep paragraphs intact
```

**Validation rules**:
- Exactly one of `max_bytes` or `max_chars` must be set (not both, not neither)
- `max_bytes`: > 0 if set
- `max_chars`: > 0 if set
- `overlap_chars`: >= 0

### LongTextTTSRequest

Extends the synthesis request concept for long text.

```python
@dataclass(frozen=True)
class LongTextTTSRequest:
    """Request for long text TTS synthesis with auto-segmentation."""
    text: str                                      # Full input text (no length limit)
    voice_id: str
    provider: str
    language: str = "zh-TW"
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    output_format: AudioFormat = AudioFormat.MP3
    style_prompt: str | None = None
    gap_ms: int = 100                              # Gap between segments (lower than multi-role default)
    crossfade_ms: int = 30                         # Crossfade between segments
```

### LongTextTTSResult

Result with segment-level metadata.

```python
@dataclass
class LongTextTTSResult:
    """Result of long text TTS synthesis."""
    audio_content: bytes
    content_type: str                              # MIME type
    duration_ms: int
    latency_ms: int
    provider: str
    segment_count: int                             # Number of segments synthesized
    segment_timings: list[TurnTiming] | None = None  # Reuse existing TurnTiming
    storage_path: str | None = None
    total_text_length: int = 0                     # Original text length (chars)
    total_byte_length: int = 0                     # Original text length (bytes)
```

## 2. Existing Entities Reused (No Modification)

### DialogueTurn (from multi_role_tts.py)

Each text segment is wrapped as a `DialogueTurn` with a fixed speaker name.

```python
# Usage: same speaker for all segments
turns = [
    DialogueTurn(speaker="narrator", text=segment.text, index=segment.index)
    for segment in segments
]
```

### MergeConfig (from segmented_merger.py)

Used with lower gap/crossfade defaults for same-speaker continuity.

```python
config = MergeConfig(
    gap_ms=100,         # Lower than default 300ms
    crossfade_ms=30,    # Slightly lower than default 50ms
    target_dbfs=-20.0,
    output_format=output_format,
    request_delay_ms=provider_delay,
)
```

### TurnTiming (from multi_role_tts.py)

Reused as-is for segment timing.

### ProviderLimits (from provider_limits.py)

Extended with `limit_type` field.

```python
@dataclass
class ProviderLimits:
    provider_id: str
    max_text_length: int
    recommended_max_length: int | None = None
    warning_message: str | None = None
    limit_type: str = "chars"           # NEW: "chars" or "bytes"
```

## 3. Entity Relationships

```
LongTextTTSRequest
    │
    ▼ (split by TextSplitter)
TextSegment[0..N]
    │
    ▼ (wrapped as)
DialogueTurn[0..N]  (speaker="narrator")
    │
    ▼ (synthesized by SegmentedMergerService)
MultiRoleTTSResult
    │
    ▼ (mapped to)
LongTextTTSResult
    ├── audio_content: merged audio bytes
    ├── segment_timings: TurnTiming[]
    └── segment_count: N
```

## 4. New Service: TextSplitter

```python
class TextSplitter:
    """Splits long text into provider-safe segments."""

    SENTENCE_BOUNDARIES_ZH = ["。", "！", "？"]
    SENTENCE_BOUNDARIES_EN = [". ", "! ", "? "]
    CLAUSE_BOUNDARIES_ZH = ["，", "；", "："]
    CLAUSE_BOUNDARIES_EN = [", ", "; ", ": "]

    def __init__(self, config: SplitConfig) -> None:
        self._config = config

    def split(self, text: str) -> list[TextSegment]:
        """Split text into segments respecting provider limits."""
        ...

    def needs_splitting(self, text: str) -> bool:
        """Check if text exceeds the configured limit."""
        ...

    def _find_best_boundary(self, text: str, max_pos: int) -> tuple[int, str]:
        """Find the best split point within max_pos characters.
        Returns (position, boundary_type).
        """
        ...

    def _byte_limit_to_char_pos(self, text: str, max_bytes: int) -> int:
        """Find the character position that fits within max_bytes."""
        ...
```

## 5. Database Changes

**None required.** This feature operates entirely in-memory. Audio results are stored via the existing `IStorageService` (local filesystem). No new tables or schema changes needed.

If future analytics are desired (e.g., tracking segment counts, split patterns), this can be added to the existing synthesis logging without schema changes (store in `metadata` JSON field of existing logs).
