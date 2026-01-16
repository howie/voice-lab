"""OpenAI Whisper Speech-to-Text Provider."""

import httpx

from src.domain.entities.stt import STTRequest, WordTiming
from src.infrastructure.providers.stt.base import BaseSTTProvider


class WhisperSTTProvider(BaseSTTProvider):
    """OpenAI Whisper STT provider implementation."""

    BASE_URL = "https://api.openai.com/v1/audio/transcriptions"

    def __init__(self, api_key: str, model: str = "whisper-1"):
        """Initialize Whisper STT provider.

        Args:
            api_key: OpenAI API key
            model: Whisper model to use (default: whisper-1)
        """
        super().__init__("whisper")
        self._api_key = api_key
        self._model = model

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using OpenAI Whisper API."""
        if request.audio is None:
            raise ValueError("Audio data is required for Whisper")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }

        # Prepare form data
        files = {
            "file": (
                f"audio.{request.audio.format.value}",
                request.audio.data,
                request.audio.format.mime_type,
            ),
        }

        data = {
            "model": self._model,
            "language": self._map_language(request.language),
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"Whisper STT failed with status {response.status_code}: {error_detail}"
                )

            result = response.json()

        transcript = result.get("text", "")

        # Extract word timings
        word_timings = None
        if "words" in result:
            word_timings = [
                WordTiming(
                    word=w.get("word", ""),
                    start_time=w.get("start", 0.0),
                    end_time=w.get("end", 0.0),
                    confidence=None,
                )
                for w in result["words"]
            ]

        return transcript, word_timings, None

    def _map_language(self, language: str) -> str:
        """Map language code to Whisper format."""
        mapping = {
            "zh-TW": "zh",
            "zh-CN": "zh",
            "en-US": "en",
            "ja-JP": "ja",
        }
        return mapping.get(language, language.split("-")[0])
