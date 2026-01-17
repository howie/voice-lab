"""Interaction domain entities for real-time voice conversation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.entities.audio import AudioData


@dataclass(frozen=True)
class InteractionConfig:
    """Configuration for interaction session."""

    stt_provider: str
    llm_provider: str
    tts_provider: str
    voice_id: str
    system_prompt: str = ""
    language: str = "zh-TW"
    max_response_tokens: int = 150


@dataclass(frozen=True)
class InteractionRequest:
    """Request for voice interaction - immutable value object."""

    config: InteractionConfig
    user_audio: AudioData
    conversation_history: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate request parameters."""
        if not self.user_audio.data:
            raise ValueError("User audio cannot be empty")


@dataclass
class InteractionResult:
    """Result of voice interaction."""

    request: InteractionRequest
    user_transcript: str
    ai_response_text: str
    ai_response_audio: AudioData
    stt_latency_ms: int
    llm_latency_ms: int
    tts_latency_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_latency_ms(self) -> int:
        """Get total end-to-end latency."""
        return self.stt_latency_ms + self.llm_latency_ms + self.tts_latency_ms

    @property
    def stt_provider(self) -> str:
        return self.request.config.stt_provider

    @property
    def llm_provider(self) -> str:
        return self.request.config.llm_provider

    @property
    def tts_provider(self) -> str:
        return self.request.config.tts_provider
