"""Realtime API mode services.

T027-T028: OpenAI Realtime API and Gemini Live API implementations.
These will be fully implemented in Phase 3 (US1).
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from src.domain.services.interaction.base import (
    AudioChunk,
    InteractionModeService,
    ResponseEvent,
)


class OpenAIRealtimeService(InteractionModeService):
    """OpenAI Realtime API implementation.

    Provides voice-to-voice interaction using OpenAI's Realtime API
    for lowest latency voice conversations.
    """

    def __init__(self) -> None:
        self._connected = False
        self._session_id: UUID | None = None

    @property
    def mode_name(self) -> str:
        return "realtime"

    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],  # noqa: ARG002
        system_prompt: str = "",  # noqa: ARG002
    ) -> None:
        """Connect to OpenAI Realtime API."""
        self._session_id = session_id
        self._connected = True
        # TODO: Implement actual WebSocket connection to OpenAI Realtime API

    async def disconnect(self) -> None:
        """Disconnect from the API."""
        self._connected = False
        self._session_id = None

    async def send_audio(self, audio: AudioChunk) -> None:
        """Send audio to the API."""
        # TODO: Implement audio streaming

    async def end_turn(self) -> None:
        """Signal end of user turn."""
        # TODO: Implement turn end signal

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


class GeminiRealtimeService(InteractionModeService):
    """Google Gemini Live API implementation.

    Provides voice-to-voice interaction using Gemini's Live API.
    """

    def __init__(self) -> None:
        self._connected = False
        self._session_id: UUID | None = None

    @property
    def mode_name(self) -> str:
        return "realtime"

    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],  # noqa: ARG002
        system_prompt: str = "",  # noqa: ARG002
    ) -> None:
        """Connect to Gemini Live API."""
        self._session_id = session_id
        self._connected = True
        # TODO: Implement actual connection to Gemini Live API

    async def disconnect(self) -> None:
        """Disconnect from the API."""
        self._connected = False
        self._session_id = None

    async def send_audio(self, audio: AudioChunk) -> None:
        """Send audio to the API."""
        # TODO: Implement audio streaming

    async def end_turn(self) -> None:
        """Signal end of user turn."""
        # TODO: Implement turn end signal

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
