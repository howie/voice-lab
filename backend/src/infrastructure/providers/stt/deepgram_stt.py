"""Deepgram STT Provider."""

import asyncio

from deepgram import DeepgramClient  # type: ignore[import-not-found]

from src.domain.entities.stt import STTRequest, WordTiming
from src.domain.errors import QuotaExceededError
from src.infrastructure.providers.stt.base import BaseSTTProvider


class DeepgramSTTProvider(BaseSTTProvider):
    """Deepgram STT provider implementation."""

    def __init__(self, api_key: str):
        """Initialize Deepgram provider.

        Args:
            api_key: Deepgram API key
        """
        super().__init__("deepgram")
        self._client = DeepgramClient(api_key=api_key)

    @property
    def display_name(self) -> str:
        return "Deepgram Nova-2"

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_child_mode(self) -> bool:
        return False  # Deepgram doesn't have explicit child mode

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using Deepgram."""
        if not request.audio:
            raise ValueError("Audio data required")

        try:
            # Execute in thread pool to avoid blocking event loop
            # SDK v5.x uses direct parameter passing instead of PrerecordedOptions
            response = await asyncio.to_thread(
                self._client.listen.v1.media.transcribe_file,
                request=request.audio.data,
                model="nova-2",
                smart_format=True,
                language=self._map_language(request.language),
                diarize=True,
                punctuate=True,
                utterances=True,
            )

            # Parse response
            if not response.results or not response.results.channels:
                return "", [], 0.0

            result = response.results.channels[0].alternatives[0]
            transcript = result.transcript
            confidence = result.confidence

            word_timings = []
            if result.words:
                for word in result.words:
                    word_timings.append(
                        WordTiming(
                            word=word.word,
                            start_ms=int(word.start * 1000),
                            end_ms=int(word.end * 1000),
                            confidence=word.confidence,
                        )
                    )

            return transcript, word_timings, confidence

        except Exception as e:
            # T014: Detect quota exceeded from Deepgram errors
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                raise QuotaExceededError(
                    provider="deepgram",
                    original_error=str(e),
                ) from e
            raise RuntimeError(f"Deepgram transcription failed: {str(e)}") from e

    def _map_language(self, language: str) -> str:
        """Map language code to Deepgram format."""
        mapping = {
            "zh-TW": "zh-TW",
            "zh-CN": "zh-CN",
            "en-US": "en-US",
            "ja-JP": "ja",
            "ko-KR": "ko",
        }
        return mapping.get(language, language)
