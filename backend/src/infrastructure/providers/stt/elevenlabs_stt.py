"""ElevenLabs STT Provider."""

import io

from elevenlabs.client import AsyncElevenLabs

from src.domain.entities.stt import STTRequest, WordTiming
from src.infrastructure.providers.stt.base import BaseSTTProvider


class ElevenLabsSTTProvider(BaseSTTProvider):
    """ElevenLabs STT provider implementation."""

    def __init__(self, api_key: str):
        """Initialize ElevenLabs provider.

        Args:
            api_key: ElevenLabs API key
        """
        super().__init__("elevenlabs")
        self._client = AsyncElevenLabs(api_key=api_key)

    @property
    def display_name(self) -> str:
        return "ElevenLabs Scribe"

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]

    @property
    def supports_streaming(self) -> bool:
        return False  # Scribe API is batch mostly (streaming exists but limited)

    @property
    def supports_child_mode(self) -> bool:
        return False

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using ElevenLabs Scribe."""
        if not request.audio:
            raise ValueError("Audio data required")

        try:
            # Wrap bytes in BytesIO with a filename (ElevenLabs might need it for format detection)
            audio_file = io.BytesIO(request.audio.data)
            audio_file.name = f"audio.{request.audio.format}"

            result = await self._client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v2",
                language_code=self._map_language(request.language),
                tag_audio_events=False,
                diarize=False,
                timestamps_granularity="word",
            )

            transcript = result.text

            # Note: ElevenLabs Python SDK return type for 'convert' with words
            # The structure might be dynamic.
            word_timings = []

            # Check if words are available (depends on SDK version/response)
            words_list = getattr(result, "words", [])
            if words_list:
                for w in words_list:
                    # Depending on object structure. Assuming attributes.
                    # If dictionary: w.get('text')
                    # If object: w.text
                    text = getattr(w, "text", "")
                    start = getattr(w, "start", 0.0)
                    end = getattr(w, "end", 0.0)
                    # confidence might not be exposed per word in Scribe v2?

                    word_timings.append(
                        WordTiming(
                            word=text,
                            start_ms=int(start * 1000),
                            end_ms=int(end * 1000),
                            confidence=1.0,  # Scribe might not return per-word confidence yet
                        )
                    )

            return transcript, word_timings, 1.0  # Overall confidence not always returned

        except Exception as e:
            raise RuntimeError(f"ElevenLabs STT failed: {str(e)}") from e

    def _map_language(self, language: str) -> str:
        """Map language code to ElevenLabs format."""
        mapping = {
            "zh-TW": "zh",
            "zh-CN": "zh",
            "en-US": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
        }
        return mapping.get(language, "en")
