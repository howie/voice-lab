"""Cascade mode service.

T029: STT → LLM → TTS pipeline implementation.
This will be fully implemented in Phase 3 (US1).
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from src.domain.services.interaction.base import (
    AudioChunk,
    InteractionModeService,
    ResponseEvent,
)


class CascadeModeService(InteractionModeService):
    """Cascade mode implementation.

    Provides voice interaction using a pipeline:
    STT (Speech-to-Text) → LLM → TTS (Text-to-Speech)

    This mode offers higher quality but more latency compared to
    direct V2V APIs.
    """

    def __init__(self) -> None:
        self._connected = False
        self._session_id: UUID | None = None

    @property
    def mode_name(self) -> str:
        return "cascade"

    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],  # noqa: ARG002
        system_prompt: str = "",  # noqa: ARG002
    ) -> None:
        """Initialize cascade pipeline."""
        self._session_id = session_id
        self._connected = True
        # TODO: Initialize STT, LLM, and TTS providers

    async def disconnect(self) -> None:
        """Cleanup resources."""
        self._connected = False
        self._session_id = None

    async def send_audio(self, audio: AudioChunk) -> None:
        """Send audio to STT."""
        # TODO: Implement STT processing

    async def end_turn(self) -> None:
        """Signal end of user turn and trigger LLM + TTS."""
        # TODO: Implement cascade processing

    async def interrupt(self) -> None:
        """Interrupt current response."""
        # TODO: Implement interrupt

    async def events(self) -> AsyncIterator[ResponseEvent]:
        """Async iterator for response events."""
        # TODO: Implement event streaming
        return
        yield  # Make this an async generator

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
