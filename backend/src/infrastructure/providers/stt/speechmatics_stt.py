"""Speechmatics STT Provider."""

import asyncio
import io

from speechmatics.batch_client import BatchClient  # type: ignore[import-not-found]
from speechmatics.models import ConnectionSettings  # type: ignore[import-not-found]

from src.domain.entities.stt import STTRequest, WordTiming
from src.infrastructure.providers.stt.base import BaseSTTProvider


class SpeechmaticsSTTProvider(BaseSTTProvider):
    """Speechmatics STT provider implementation."""

    def __init__(self, api_key: str):
        """Initialize Speechmatics provider.

        Args:
            api_key: Speechmatics API key
        """
        super().__init__("speechmatics")
        self._api_key = api_key
        self._url = "https://asr.api.speechmatics.com/v2"

    @property
    def display_name(self) -> str:
        return "Speechmatics"

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_child_mode(self) -> bool:
        return False

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using Speechmatics."""
        if not request.audio:
            raise ValueError("Audio data required")

        settings = ConnectionSettings(url=self._url, auth_token=self._api_key)

        # Audio must be file-like object
        audio_file = io.BytesIO(request.audio.data)
        audio_file.name = f"audio.{request.audio.format}"

        # Config
        config = {
            "type": "transcription",
            "transcription_config": {
                "language": self._map_language(request.language),
                "diarization": "none",
                "operating_point": "enhanced",  # Best accuracy
            },
        }

        try:

            def run_batch():
                with BatchClient(settings) as client:
                    job_id = client.submit_job(
                        audio=audio_file, transcription_config=config["transcription_config"]
                    )
                    # wait_for_completion blocks until done
                    return client.wait_for_completion(job_id, transcription_format="json-v2")

            # Run blocking code in thread
            result = await asyncio.to_thread(run_batch)

            # Parse result
            word_timings = []
            full_text = ""

            # Speechmatics json-v2
            results_list = result.get("results", [])
            for item in results_list:
                alternatives = item.get("alternatives", [])
                if not alternatives:
                    continue

                best = alternatives[0]
                content = best.get("content", "")
                confidence = best.get("confidence", 1.0)

                item_type = item.get("type")

                if item_type == "punctuation":
                    full_text += content
                elif item_type == "word":
                    if full_text and not full_text.endswith(" ") and not _is_cjk(content):
                        full_text += " "
                    full_text += content

                    word_timings.append(
                        WordTiming(
                            word=content,
                            start_ms=int(item.get("start_time", 0) * 1000),
                            end_ms=int(item.get("end_time", 0) * 1000),
                            confidence=confidence,
                        )
                    )

            return full_text, word_timings, 1.0

        except Exception as e:
            raise RuntimeError(f"Speechmatics failed: {str(e)}") from e

    def _map_language(self, language: str) -> str:
        """Map language code to Speechmatics format."""
        mapping = {
            "zh-TW": "cmn",  # Mandarin
            "zh-CN": "cmn",
            "en-US": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
        }
        return mapping.get(language, "en")


def _is_cjk(char: str) -> bool:
    """Simple check if char is CJK to avoid spaces."""
    if not char:
        return False
    code = ord(char[0])
    return 0x4E00 <= code <= 0x9FFF
