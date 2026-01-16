"""Base TTS Provider with common functionality."""

import time
from abc import abstractmethod

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.entities.voice import VoiceProfile


class BaseTTSProvider(ITTSProvider):
    """Base class for TTS providers with common functionality."""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech with timing measurement."""
        start_time = time.perf_counter()

        audio_data = await self._do_synthesize(request)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return TTSResult(
            audio=audio_data,
            provider=self.name,
            voice_id=request.voice_id,
            latency_ms=latency_ms,
            text_length=len(request.text),
        )

    @abstractmethod
    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Provider-specific synthesis implementation."""
        pass

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available voices."""
        pass

    def _get_output_format(self, request: TTSRequest) -> AudioFormat:
        """Get output format from request or use default."""
        return request.output_format or AudioFormat.MP3
