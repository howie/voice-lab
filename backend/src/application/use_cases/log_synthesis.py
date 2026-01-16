"""Log Synthesis Use Case.

T029: Create LogSynthesisUseCase for request logging (FR-010)
"""

import hashlib
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities.tts import TTSRequest, TTSResult


class ISynthesisLogRepository(Protocol):
    """Protocol for synthesis log repository."""

    async def create(
        self,
        text_hash: str,
        text_length: int,
        provider: str,
        voice_id: str,
        language: str,
        output_format: str,
        output_mode: str,
        speed: float,
        pitch: float,
        volume: float,
        duration_ms: int | None,
        latency_ms: int | None,
        audio_size_bytes: int | None,
        storage_path: str | None,
        success: bool,
        error_message: str | None,
        user_id: UUID | None,
    ) -> UUID:
        """Create a synthesis log entry."""
        ...


class LogSynthesisUseCase:
    """Use case for logging TTS synthesis requests.

    Logs all synthesis attempts for monitoring, analytics, and debugging.
    """

    def __init__(self, repository: ISynthesisLogRepository) -> None:
        self.repository = repository

    @staticmethod
    def _hash_text(text: str) -> str:
        """Create a hash of the input text for privacy-preserving logging."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    async def log_synthesis(
        self,
        request: TTSRequest,
        result: TTSResult | None,
        error: str | None = None,
        user_id: str | None = None,
    ) -> UUID:
        """Log a synthesis request.

        Args:
            request: The TTS request parameters
            result: The synthesis result (None if failed or streaming)
            error: Error message if synthesis failed
            user_id: Optional user ID for attribution

        Returns:
            UUID of the created log entry
        """
        # Hash text for privacy
        text_hash = self._hash_text(request.text)

        # Extract result data if available
        duration_ms = result.duration_ms if result else None
        latency_ms = result.latency_ms if result else None
        audio_size = len(result.audio.data) if result and result.audio else None
        storage_path = result.storage_path if result else None
        success = error is None

        # Parse user_id to UUID if provided
        user_uuid = UUID(user_id) if user_id else None

        return await self.repository.create(
            text_hash=text_hash,
            text_length=len(request.text),
            provider=request.provider,
            voice_id=request.voice_id,
            language=request.language,
            output_format=request.output_format.value,
            output_mode=request.output_mode.value,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            duration_ms=duration_ms,
            latency_ms=latency_ms,
            audio_size_bytes=audio_size,
            storage_path=storage_path,
            success=success,
            error_message=error,
            user_id=user_uuid,
        )

    async def log_success(
        self,
        request: TTSRequest,
        result: TTSResult,
        user_id: str | None = None,
    ) -> UUID:
        """Log a successful synthesis.

        Convenience method for logging successful synthesis.
        """
        return await self.log_synthesis(
            request=request,
            result=result,
            error=None,
            user_id=user_id,
        )

    async def log_failure(
        self,
        request: TTSRequest,
        error: str,
        user_id: str | None = None,
    ) -> UUID:
        """Log a failed synthesis.

        Convenience method for logging failed synthesis.
        """
        return await self.log_synthesis(
            request=request,
            result=None,
            error=error,
            user_id=user_id,
        )

    async def log_streaming_start(
        self,
        request: TTSRequest,
        user_id: str | None = None,
    ) -> UUID:
        """Log the start of a streaming synthesis.

        For streaming synthesis, we log when streaming starts.
        """
        return await self.log_synthesis(
            request=request,
            result=None,  # No result yet for streaming
            error=None,
            user_id=user_id,
        )
