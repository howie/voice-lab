"""STT Provider Interface (Port)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from src.domain.entities.stt import STTRequest, STTResult


class ISTTProvider(ABC):
    """Abstract interface for STT providers.

    This interface defines the contract that all STT provider
    implementations must follow. Infrastructure layer provides
    concrete implementations (GCP, Azure, VoAI, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name identifier (e.g., 'gcp', 'azure')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get human-readable provider name."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Get list of supported language codes."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether the provider supports streaming transcription."""
        pass

    @property
    @abstractmethod
    def supports_child_mode(self) -> bool:
        """Whether the provider has child speech optimization."""
        pass

    @property
    def supports_diarization(self) -> bool:
        """Whether the provider supports speaker diarization."""
        return False

    @abstractmethod
    async def transcribe(self, request: STTRequest) -> STTResult:
        """Transcribe audio to text.

        Args:
            request: STT transcription request

        Returns:
            STT result with transcript and metadata

        Raises:
            STTProviderError: If transcription fails
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "zh-TW",
        child_mode: bool = False,
    ) -> AsyncIterator[STTResult]:
        """Stream transcription for real-time audio.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code for transcription
            child_mode: Whether to optimize for children's speech

        Yields:
            Partial STT results as they become available

        Raises:
            STTProviderError: If transcription fails
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is available and configured correctly.

        Returns:
            True if provider is healthy, False otherwise
        """
        return True
