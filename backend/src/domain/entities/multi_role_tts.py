"""Multi-Role TTS Domain Entities.

This module defines the core domain entities for multi-role dialogue
text-to-speech synthesis.
"""

from dataclasses import dataclass, field
from enum import Enum


class MultiRoleSupportType(str, Enum):
    """Type of multi-role support a provider offers."""

    NATIVE = "native"
    """Provider supports multi-role natively in a single request."""

    SEGMENTED = "segmented"
    """Provider requires separate requests per speaker, merged afterward."""

    UNSUPPORTED = "unsupported"
    """Provider does not support multi-role TTS."""


@dataclass
class DialogueTurn:
    """Represents a single turn in a dialogue.

    Attributes:
        speaker: Speaker identifier (e.g., 'A', 'B', 'Host').
        text: The text content of this turn.
        index: Position in the dialogue sequence (0-based).
    """

    speaker: str
    text: str
    index: int

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.speaker or len(self.speaker) > 50:
            raise ValueError("Speaker must be non-empty and max 50 characters")
        if not self.text:
            raise ValueError("Text must be non-empty")
        if self.index < 0:
            raise ValueError("Index must be non-negative")


@dataclass
class VoiceAssignment:
    """Maps a speaker to a voice.

    Attributes:
        speaker: Speaker identifier matching DialogueTurn.speaker.
        voice_id: Provider-specific voice ID.
        voice_name: Human-readable voice name (optional, for display).
    """

    speaker: str
    voice_id: str
    voice_name: str | None = None

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.speaker:
            raise ValueError("Speaker must be non-empty")
        if not self.voice_id:
            raise ValueError("Voice ID must be non-empty")


@dataclass
class ProviderMultiRoleCapability:
    """Describes a provider's multi-role capabilities.

    Attributes:
        provider_name: Provider identifier (e.g., 'elevenlabs', 'azure').
        support_type: Type of multi-role support.
        max_speakers: Maximum number of speakers supported.
        character_limit: Maximum total characters for the dialogue.
        advanced_features: List of advanced features (e.g., 'interrupting', 'overlapping').
        notes: Additional notes about this provider's capabilities.
    """

    provider_name: str
    support_type: MultiRoleSupportType
    max_speakers: int
    character_limit: int
    advanced_features: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass
class TurnTiming:
    """Timing information for a single turn.

    Attributes:
        turn_index: Index of the turn.
        start_ms: Start time in milliseconds.
        end_ms: End time in milliseconds.
    """

    turn_index: int
    start_ms: int
    end_ms: int


@dataclass
class MultiRoleTTSRequest:
    """Request for multi-role TTS synthesis.

    Attributes:
        provider: TTS provider to use.
        turns: List of dialogue turns to synthesize.
        voice_assignments: Voice assignment for each speaker.
        language: Language code for synthesis.
        output_format: Output audio format.
        gap_ms: Gap between turns in milliseconds (for segmented mode).
        crossfade_ms: Crossfade duration in milliseconds (for segmented mode).
    """

    provider: str
    turns: list[DialogueTurn]
    voice_assignments: list[VoiceAssignment]
    language: str = "zh-TW"
    output_format: str = "mp3"
    gap_ms: int = 300
    crossfade_ms: int = 50

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.turns:
            raise ValueError("Turns must be non-empty")
        if not self.voice_assignments:
            raise ValueError("Voice assignments must be non-empty")
        if not 0 <= self.gap_ms <= 2000:
            raise ValueError("gap_ms must be between 0 and 2000")
        if not 0 <= self.crossfade_ms <= 500:
            raise ValueError("crossfade_ms must be between 0 and 500")

        # Validate all speakers have voice assignments
        speakers = {turn.speaker for turn in self.turns}
        assigned_speakers = {va.speaker for va in self.voice_assignments}
        missing = speakers - assigned_speakers
        if missing:
            raise ValueError(f"Missing voice assignments for speakers: {missing}")


@dataclass
class MultiRoleTTSResult:
    """Result of multi-role TTS synthesis.

    Attributes:
        audio_content: Raw audio content.
        content_type: MIME type (e.g., 'audio/mpeg').
        duration_ms: Total audio duration in milliseconds.
        latency_ms: Total processing latency in milliseconds.
        provider: Provider used for synthesis.
        synthesis_mode: Whether native or segmented mode was used.
        turn_timings: Optional timing information for each turn.
        storage_path: Path where audio was stored (if applicable).
    """

    audio_content: bytes
    content_type: str
    duration_ms: int
    latency_ms: int
    provider: str
    synthesis_mode: MultiRoleSupportType
    turn_timings: list[TurnTiming] | None = None
    storage_path: str | None = None
