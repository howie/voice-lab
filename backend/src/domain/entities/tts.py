"""TTS (Text-to-Speech) domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.entities.audio import AudioFormat, AudioData


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

    def __post_init__(self) -> None:
        """Validate request parameters."""
        if not self.text:
            raise ValueError("Text cannot be empty")
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
