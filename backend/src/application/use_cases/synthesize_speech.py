"""Synthesize Speech Use Case.

T028: Update SynthesizeSpeechUseCase to support batch and streaming modes
"""

from collections.abc import AsyncGenerator
from typing import Protocol

from src.application.interfaces.storage_service import IStorageService
from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.errors import ProviderError, SynthesisError


class ISynthesisLogger(Protocol):
    """Protocol for synthesis logging."""

    async def log_synthesis(
        self,
        request: TTSRequest,
        result: TTSResult | None,
        error: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """Log a synthesis request and result."""
        ...


class SynthesizeSpeech:
    """Use case for synthesizing speech from text.

    Supports both batch mode (complete audio) and streaming mode (chunked audio).
    """

    def __init__(
        self,
        provider: ITTSProvider,
        storage: IStorageService | None = None,
        logger: ISynthesisLogger | None = None,
    ) -> None:
        self.provider = provider
        self.storage = storage
        self.logger = logger

    async def execute(
        self,
        request: TTSRequest,
        user_id: str | None = None,
    ) -> TTSResult:
        """Execute batch synthesis.

        Args:
            request: The TTS request parameters
            user_id: Optional user ID for logging

        Returns:
            TTSResult with complete audio data

        Raises:
            SynthesisError: If synthesis fails
            ProviderError: If provider is unavailable
        """
        try:
            # Synthesize audio
            result = await self.provider.synthesize(request)

            # Store audio if storage is configured
            if self.storage:
                storage_path = await self.storage.save(
                    result.audio, request.provider
                )
                result.storage_path = storage_path

            # Log synthesis if logger is configured
            if self.logger:
                await self.logger.log_synthesis(
                    request=request,
                    result=result,
                    user_id=user_id,
                )

            return result

        except Exception as e:
            # Log error if logger is configured
            if self.logger:
                await self.logger.log_synthesis(
                    request=request,
                    result=None,
                    error=str(e),
                    user_id=user_id,
                )

            # Re-raise as appropriate error type
            error_msg = str(e)
            if "unavailable" in error_msg.lower() or "timeout" in error_msg.lower():
                raise ProviderError(request.provider, error_msg) from e
            raise SynthesisError(request.provider, error_msg) from e

    async def execute_stream(
        self,
        request: TTSRequest,
        user_id: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Execute streaming synthesis.

        Args:
            request: The TTS request parameters
            user_id: Optional user ID for logging

        Yields:
            Audio data chunks as bytes

        Raises:
            SynthesisError: If synthesis fails
            ProviderError: If provider is unavailable
        """
        try:
            # Stream audio from provider
            async for chunk in self.provider.synthesize_stream(request):
                yield chunk

            # Log successful streaming synthesis
            if self.logger:
                # Create a minimal result for logging
                await self.logger.log_synthesis(
                    request=request,
                    result=None,  # No complete result for streaming
                    user_id=user_id,
                )

        except Exception as e:
            # Log error if logger is configured
            if self.logger:
                await self.logger.log_synthesis(
                    request=request,
                    result=None,
                    error=str(e),
                    user_id=user_id,
                )

            # Re-raise as appropriate error type
            error_msg = str(e)
            if "unavailable" in error_msg.lower() or "timeout" in error_msg.lower():
                raise ProviderError(request.provider, error_msg) from e
            raise SynthesisError(request.provider, error_msg) from e


class SynthesizeSpeechFactory:
    """Factory for creating SynthesizeSpeech use cases."""

    def __init__(
        self,
        providers: dict[str, ITTSProvider],
        storage: IStorageService | None = None,
        logger: ISynthesisLogger | None = None,
    ) -> None:
        self.providers = providers
        self.storage = storage
        self.logger = logger

    def create(self, provider_name: str) -> SynthesizeSpeech:
        """Create a SynthesizeSpeech use case for the specified provider.

        Args:
            provider_name: Name of the TTS provider

        Returns:
            SynthesizeSpeech instance configured for the provider

        Raises:
            ValueError: If provider is not found
        """
        provider = self.providers.get(provider_name)
        if not provider:
            valid_providers = list(self.providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not found. "
                f"Available: {valid_providers}"
            )

        return SynthesizeSpeech(
            provider=provider,
            storage=self.storage,
            logger=self.logger,
        )
