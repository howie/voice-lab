"""AssemblyAI STT Provider."""

import asyncio

import httpx

from src.domain.entities.stt import STTRequest, WordTiming
from src.infrastructure.providers.stt.base import BaseSTTProvider


class AssemblyAISTTProvider(BaseSTTProvider):
    """AssemblyAI STT provider implementation."""

    def __init__(self, api_key: str):
        """Initialize AssemblyAI provider.

        Args:
            api_key: AssemblyAI API key
        """
        super().__init__("assemblyai")
        self._api_key = api_key
        self._base_url = "https://api.assemblyai.com/v2"

    @property
    def display_name(self) -> str:
        return "AssemblyAI"

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-TW", "en-US", "ja-JP", "ko-KR"]  # zh-CN? AssemblyAI supports zh

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_child_mode(self) -> bool:
        return False

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using AssemblyAI."""
        if not request.audio:
            raise ValueError("Audio data required")

        headers = {"authorization": self._api_key}

        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            # 1. Upload
            # Use chunks for upload? Or oneshot.
            # AssemblyAI recommends chunked for large files, but for testing small files oneshot is ok.
            upload_resp = await client.post(
                f"{self._base_url}/upload",
                content=request.audio.data,
            )
            upload_resp.raise_for_status()
            upload_url = upload_resp.json()["upload_url"]

            # 2. Transcribe
            json_data = {
                "audio_url": upload_url,
                "language_code": self._map_language(request.language),
                "speaker_labels": True,
                "punctuate": True,
            }

            transcript_resp = await client.post(
                f"{self._base_url}/transcript",
                json=json_data,
            )
            transcript_resp.raise_for_status()
            transcript_id = transcript_resp.json()["id"]

            # 3. Poll
            # Polling interval strategy
            for _ in range(300):  # Timeout 300s
                polling_resp = await client.get(f"{self._base_url}/transcript/{transcript_id}")
                polling_resp.raise_for_status()
                result = polling_resp.json()

                status = result["status"]

                if status == "completed":
                    transcript = result.get("text", "")

                    word_timings = []
                    words = result.get("words", [])
                    total_conf = 0.0

                    for w in words:
                        conf = w.get("confidence", 0.0)
                        total_conf += conf
                        word_timings.append(
                            WordTiming(
                                word=w["text"],
                                start_ms=w["start"],  # AssemblyAI uses ms
                                end_ms=w["end"],
                                confidence=conf,
                            )
                        )

                    avg_confidence = total_conf / len(words) if words else 1.0
                    if not words and not transcript:
                        avg_confidence = 0.0

                    return transcript, word_timings, avg_confidence

                elif status == "error":
                    raise RuntimeError(f"AssemblyAI failed: {result['error']}")

                await asyncio.sleep(1.0)

            raise TimeoutError("AssemblyAI transcription timed out")

    def _map_language(self, language: str) -> str:
        """Map language code to AssemblyAI format."""
        # AssemblyAI: "zh" for both? Or "zh-TW"?
        # Docs: "zh" is generic. "zh-TW" is supported in Universal-2?
        # Assuming ISO codes
        mapping = {
            "zh-TW": "zh",  # Universal-1 supports zh
            "zh-CN": "zh",
            "en-US": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
        }
        return mapping.get(language, "en")
