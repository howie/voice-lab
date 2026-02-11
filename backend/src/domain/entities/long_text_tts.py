"""Long Text TTS Domain Entities.

Defines entities for automatic text segmentation and merged audio synthesis
when input text exceeds provider-specific limits.
"""

from dataclasses import dataclass, field

from src.domain.entities.multi_role_tts import TurnTiming


@dataclass(frozen=True)
class TextSegment:
    """A single text segment produced by TextSplitter.

    Attributes:
        text: The segment text content.
        index: Position in the sequence (0-based).
        byte_length: UTF-8 byte length of text.
        char_length: Character count.
        boundary_type: How this segment was split.
    """

    text: str
    index: int
    byte_length: int
    char_length: int
    boundary_type: str

    _VALID_BOUNDARY_TYPES = frozenset({"paragraph", "sentence", "clause", "hard", "none"})

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.text:
            raise ValueError("Text must be non-empty")
        if self.index < 0:
            raise ValueError("Index must be non-negative")
        if self.byte_length != len(self.text.encode("utf-8")):
            raise ValueError(
                f"byte_length ({self.byte_length}) does not match "
                f"actual byte length ({len(self.text.encode('utf-8'))})"
            )
        if self.char_length != len(self.text):
            raise ValueError(
                f"char_length ({self.char_length}) does not match "
                f"actual char length ({len(self.text)})"
            )
        if self.boundary_type not in self._VALID_BOUNDARY_TYPES:
            raise ValueError(
                f"boundary_type must be one of {self._VALID_BOUNDARY_TYPES}, "
                f"got '{self.boundary_type}'"
            )


@dataclass(frozen=True)
class SplitConfig:
    """Configuration for text segmentation.

    Exactly one of max_bytes or max_chars must be set.

    Attributes:
        max_bytes: Max bytes per segment (e.g., 4000 for Gemini).
        max_chars: Max chars per segment (e.g., 5000 for Azure).
        preserve_paragraphs: Try to keep paragraphs intact.
    """

    max_bytes: int | None = None
    max_chars: int | None = None
    preserve_paragraphs: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        has_bytes = self.max_bytes is not None
        has_chars = self.max_chars is not None

        if has_bytes == has_chars:
            raise ValueError("Exactly one of max_bytes or max_chars must be set")
        if has_bytes and self.max_bytes is not None and self.max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if has_chars and self.max_chars is not None and self.max_chars <= 0:
            raise ValueError("max_chars must be positive")


@dataclass
class LongTextTTSResult:
    """Result of long text TTS synthesis.

    Attributes:
        audio_content: Merged audio bytes.
        content_type: MIME type (e.g., 'audio/mpeg').
        duration_ms: Total audio duration in milliseconds.
        latency_ms: Total processing latency in milliseconds.
        provider: Provider used for synthesis.
        segment_count: Number of segments synthesized.
        segment_timings: Timing info for each segment.
        storage_path: Path where audio was stored (if applicable).
        total_text_length: Original text length in characters.
        total_byte_length: Original text length in bytes.
    """

    audio_content: bytes
    content_type: str
    duration_ms: int
    latency_ms: int
    provider: str
    segment_count: int
    segment_timings: list[TurnTiming] | None = None
    storage_path: str | None = None
    total_text_length: int = 0
    total_byte_length: int = 0
    metadata: dict[str, object] = field(default_factory=dict)
