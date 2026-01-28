"""TTS Provider Interface (Port)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from src.domain.entities.audio import AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult, VoiceProfile


class ITTSProvider(ABC):
    """Abstract interface for TTS providers.

    This interface defines the contract that all TTS provider
    implementations must follow. Infrastructure layer provides
    concrete implementations (GCP, Azure, ElevenLabs, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name identifier (e.g., 'gemini', 'azure')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get human-readable provider name."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list[AudioFormat]:
        """Get list of supported audio formats."""
        pass

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech from text (batch mode).

        Args:
            request: TTS synthesis request

        Returns:
            TTS result with audio data and metadata

        Raises:
            TTSProviderError: If synthesis fails
        """
        pass

    @abstractmethod
    async def synthesize_stream(self, request: TTSRequest) -> AsyncGenerator[bytes, None]:
        """Synthesize speech from text with streaming output.

        Args:
            request: TTS synthesis request

        Yields:
            Audio data chunks as they become available

        Raises:
            TTSProviderError: If synthesis fails
        """
        pass

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available voices for this provider.

        Args:
            language: Optional language filter (e.g., 'zh-TW')

        Returns:
            List of available voice profiles
        """
        pass

    @abstractmethod
    async def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Get a specific voice profile.

        Args:
            voice_id: Provider-specific voice ID

        Returns:
            Voice profile if found, None otherwise
        """
        pass

    @abstractmethod
    def get_supported_params(self) -> dict:
        """Get supported parameters and their valid ranges.

        Returns:
            Dictionary with parameter names and their constraints
            Example: {'speed': {'min': 0.5, 'max': 2.0, 'default': 1.0}}
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is available and configured correctly.

        Returns:
            True if provider is healthy, False otherwise
        """
        return True
