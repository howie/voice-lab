"""Base interface for interaction mode services.

T013: Unified abstraction for Realtime API and Cascade modes.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class AudioChunk:
    """Audio data chunk for streaming."""

    data: bytes
    format: str  # "pcm16" or "mp3"
    sample_rate: int  # 16000 or 24000
    is_final: bool = False


@dataclass
class TranscriptResult:
    """Speech-to-text result."""

    text: str
    is_final: bool
    confidence: float | None = None


@dataclass
class ResponseEvent:
    """Event from the interaction mode service."""

    type: str  # "speech_started", "speech_ended", "transcript", "audio", "text_delta", "response_ended", "interrupted", "error"
    data: dict[str, Any]


class InteractionModeService(ABC):
    """Abstract base class for voice interaction modes.

    Implements Unified API Abstraction principle - both Realtime API
    and Cascade mode implement this same interface.
    """

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the mode identifier ('realtime' or 'cascade')."""
        ...

    @abstractmethod
    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],
        system_prompt: str = "",
    ) -> None:
        """Establish connection to the voice service.

        Args:
            session_id: Unique session identifier
            config: Provider-specific configuration
            system_prompt: Optional system prompt for the AI
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection and cleanup resources."""
        ...

    @abstractmethod
    async def send_audio(self, audio: AudioChunk) -> None:
        """Send audio data to the service.

        Args:
            audio: Audio chunk to process
        """
        ...

    @abstractmethod
    async def end_turn(self) -> None:
        """Signal end of user speech (when VAD doesn't detect it)."""
        ...

    @abstractmethod
    async def interrupt(self) -> None:
        """Interrupt the current AI response (barge-in)."""
        ...

    @abstractmethod
    def events(self) -> AsyncIterator[ResponseEvent]:
        """Async iterator for response events.

        Yields ResponseEvent objects of various types:
        - speech_started: VAD detected user speech start
        - speech_ended: VAD detected user speech end
        - transcript: Speech-to-text result (cascade mode)
        - audio: Audio chunk from AI response
        - text_delta: Incremental text from AI response
        - response_ended: AI finished responding
        - interrupted: Response was interrupted
        - error: An error occurred
        """
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the service is connected."""
        ...

    async def trigger_greeting(self, greeting_prompt: str | None = None) -> None:
        """Trigger AI to start the conversation with a greeting.

        Optional method - default implementation does nothing.
        Subclasses can override to support AI-initiated greetings.

        Args:
            greeting_prompt: Optional custom prompt to trigger greeting.
        """
        # Default: do nothing (not all modes support this)
        _ = greeting_prompt  # Suppress unused variable warning
