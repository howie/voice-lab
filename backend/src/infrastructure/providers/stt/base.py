"""Base STT Provider with common functionality."""

import time
from abc import abstractmethod
from collections.abc import AsyncIterator

from src.application.interfaces.stt_provider import ISTTProvider
from src.domain.entities.audio import AudioData
from src.domain.entities.stt import SpeakerSegment, STTRequest, STTResult, WordTiming


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

        metadata = {}
        if audio_duration_ms:
            metadata["audio_duration_ms"] = audio_duration_ms

        words = word_timings or []
        speaker_segments = self._build_speaker_segments(words)

        return STTResult(
            request=request,
            transcript=transcript,
            confidence=confidence,
            latency_ms=latency_ms,
            words=words,
            speaker_segments=speaker_segments,
            metadata=metadata,
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

    @staticmethod
    def _build_speaker_segments(words: list[WordTiming]) -> list[SpeakerSegment]:
        """Aggregate consecutive words from the same speaker into segments."""
        segments: list[SpeakerSegment] = []
        if not words:
            return segments

        current_speaker: str | None = None
        current_words: list[WordTiming] = []

        for word in words:
            if word.speaker_id is None:
                continue
            if word.speaker_id != current_speaker:
                if current_speaker is not None and current_words:
                    segments.append(
                        SpeakerSegment(
                            speaker_id=current_speaker,
                            text=" ".join(w.word for w in current_words),
                            start_ms=current_words[0].start_ms,
                            end_ms=current_words[-1].end_ms,
                        )
                    )
                current_speaker = word.speaker_id
                current_words = [word]
            else:
                current_words.append(word)

        # Flush last segment
        if current_speaker is not None and current_words:
            segments.append(
                SpeakerSegment(
                    speaker_id=current_speaker,
                    text=" ".join(w.word for w in current_words),
                    start_ms=current_words[0].start_ms,
                    end_ms=current_words[-1].end_ms,
                )
            )

        return segments

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
