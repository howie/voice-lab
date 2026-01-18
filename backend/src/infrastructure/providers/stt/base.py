"""Base STT Provider with common functionality."""

import time
from abc import abstractmethod
from collections.abc import AsyncIterator

from src.application.interfaces.stt_provider import ISTTProvider
from src.domain.entities.audio import AudioData
from src.domain.entities.stt import STTRequest, STTResult, WordTiming


class BaseSTTProvider(ISTTProvider):
    """Base class for STT providers with common functionality."""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def transcribe(self, request: STTRequest) -> STTResult:
        """Transcribe audio with timing measurement."""
        start_time = time.perf_counter()

        transcript, word_timings, confidence = await self._do_transcribe(request)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Calculate audio duration if possible
        audio_duration_ms = None
        if request.audio:
            audio_duration_ms = self._estimate_audio_duration(request.audio)

        return STTResult(
            transcript=transcript,
            provider=self.name,
            language=request.language,
            latency_ms=latency_ms,
            confidence=confidence,
            word_timings=word_timings,
            audio_duration_ms=audio_duration_ms,
        )

    @abstractmethod
    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Provider-specific transcription implementation.

        Returns:
            Tuple of (transcript, word_timings, confidence)
        """
        pass

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes], language: str = "zh-TW"
    ) -> AsyncIterator[STTResult]:
        """Default streaming implementation - not all providers support this."""
        raise NotImplementedError(f"{self.name} does not support streaming STT")

    @property
    def supports_streaming(self) -> bool:
        """Override in subclasses that support streaming."""
        return False

    def _estimate_audio_duration(self, audio: AudioData) -> int | None:
        """Estimate audio duration in milliseconds."""
        try:
            # For raw PCM: duration = bytes / (sample_rate * channels * bytes_per_sample)
            # Assuming mono 16-bit audio
            bytes_per_sample = 2
            channels = 1
            duration_seconds = len(audio.data) / (audio.sample_rate * channels * bytes_per_sample)
            return int(duration_seconds * 1000)
        except Exception:
            return None
