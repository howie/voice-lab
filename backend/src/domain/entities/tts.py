"""TTS (Text-to-Speech) domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.entities.audio import AudioData, AudioFormat, OutputMode

# Maximum text length in characters
MAX_TEXT_LENGTH = 5000


@dataclass(frozen=True)
class TTSRequest:
    """Request for TTS synthesis - immutable value object."""

    text: str
    voice_id: str
    provider: str
    language: str = "zh-TW"
    speed: float = 1.0  # 0.5 - 2.0
    pitch: float = 0.0  # -20 to +20 semitones
    volume: float = 1.0  # 0.0 - 2.0
    output_format: AudioFormat = AudioFormat.MP3
    output_mode: OutputMode = OutputMode.BATCH
    style_prompt: str | None = None  # Gemini TTS style prompt for voice control

    def __post_init__(self) -> None:
        """Validate request parameters."""
        if not self.text:
            raise ValueError("Text cannot be empty")
        if len(self.text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text exceeds {MAX_TEXT_LENGTH} characters limit")
        if not self.voice_id:
            raise ValueError("Voice ID cannot be empty")
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        if not -20 <= self.pitch <= 20:
            raise ValueError("Pitch must be between -20 and 20")
        if not 0.0 <= self.volume <= 2.0:
            raise ValueError("Volume must be between 0.0 and 2.0")


@dataclass
class TTSResult:
    """Result of TTS synthesis."""

    request: TTSRequest
    audio: AudioData
    duration_ms: int
    latency_ms: int
    ttfb_ms: int | None = None  # T065: Time to First Byte measurement
    storage_path: str | None = None
    cost_estimate: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def provider(self) -> str:
        """Get provider name from request."""
        return self.request.provider

    @property
    def voice_id(self) -> str:
        """Get voice ID from request."""
        return self.request.voice_id

    @property
    def characters_count(self) -> int:
        """Get character count of synthesized text."""
        return len(self.request.text)


@dataclass
class VoiceProfile:
    """Represents an available voice from a provider."""

    id: str
    name: str
    provider: str
    language: str
    gender: str | None = None  # 'male', 'female', 'neutral'
    styles: list[str] = field(default_factory=list)

    @property
    def unique_id(self) -> str:
        """Get a globally unique ID for this voice."""
        return f"{self.provider}:{self.id}"
