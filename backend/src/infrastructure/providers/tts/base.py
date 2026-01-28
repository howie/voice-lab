"""Base TTS Provider implementation.

Provides common functionality for all TTS provider implementations.
"""

import time
from abc import abstractmethod
from collections.abc import AsyncGenerator

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.entities.voice import VoiceProfile


class BaseTTSProvider(ITTSProvider):
    """Base class for TTS provider implementations.

    Provides common functionality and default implementations
    for TTS providers. Subclasses must implement:
    - _do_synthesize: Actual synthesis logic
    - list_voices: Voice listing logic
    """

    def __init__(self, name: str):
        """Initialize base provider.

        Args:
            name: Provider identifier (e.g., 'gemini', 'azure')
        """
        self._name = name

    @property
    def name(self) -> str:
        """Get provider name identifier."""
        return self._name

    @property
    def display_name(self) -> str:
        """Get human-readable provider name."""
        display_names = {
            "gemini": "Gemini TTS",
            "azure": "Azure Cognitive Services",
            "elevenlabs": "ElevenLabs",
            "voai": "VoAI",
        }
        return display_names.get(self._name, self._name.upper())

    @property
    def supported_formats(self) -> list[AudioFormat]:
        """Get list of supported audio formats."""
        return [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OGG]

    def _get_output_format(self, request: TTSRequest) -> AudioFormat:
        """Determine output format from request.

        Args:
            request: TTS synthesis request

        Returns:
            Audio format to use for output
        """
        return request.output_format or AudioFormat.MP3

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech from text (batch mode).

        Wraps the provider-specific _do_synthesize method
        with timing and result packaging.

        Args:
            request: TTS synthesis request

        Returns:
            TTS result with audio data and metadata
        """
        start_time = time.time()

        audio = await self._do_synthesize(request)

        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate duration based on text length and speed
        # Rough estimate: ~150 words per minute at normal speed
        words = len(request.text.split())
        estimated_duration_ms = int((words / 150) * 60 * 1000 / request.speed)

        return TTSResult(
            request=request,
            audio=audio,
            duration_ms=estimated_duration_ms,
            latency_ms=latency_ms,
        )

    @abstractmethod
    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Provider-specific synthesis implementation.

        Subclasses must implement this method to perform
        the actual TTS synthesis.

        Args:
            request: TTS synthesis request

        Returns:
            Audio data from synthesis
        """
        ...

    async def synthesize_stream(self, request: TTSRequest) -> AsyncGenerator[bytes, None]:
        """Synthesize speech with streaming output.

        Default implementation: synthesize in batch and yield all at once.
        Providers with native streaming support should override this.

        Args:
            request: TTS synthesis request

        Yields:
            Audio data chunks
        """
        audio = await self._do_synthesize(request)
        yield audio.data

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available voices for this provider.

        Subclasses must implement this method.

        Args:
            language: Optional language filter

        Returns:
            List of available voice profiles
        """
        ...

    async def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Get a specific voice profile.

        Default implementation searches through all voices.
        Override for more efficient lookup if available.

        Args:
            voice_id: Provider-specific voice ID

        Returns:
            Voice profile if found, None otherwise
        """
        voices = await self.list_voices()
        for voice in voices:
            if voice.voice_id == voice_id:
                return voice
        return None

    def get_supported_params(self) -> dict:
        """Get supported parameters and their valid ranges.

        Returns:
            Dictionary with parameter names and their constraints
        """
        return {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
            "pitch": {"min": -20.0, "max": 20.0, "default": 0.0},
            "volume": {"min": 0.0, "max": 2.0, "default": 1.0},
        }

    async def health_check(self) -> bool:
        """Check if provider is available and configured.

        Default implementation returns True.
        Override for actual health checking.

        Returns:
            True if provider is healthy
        """
        return True
