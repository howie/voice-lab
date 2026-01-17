"""VoAI TTS Provider implementation.

VoAI is a custom TTS provider for Taiwan Chinese voices.
This implementation uses httpx for API calls since Pipecat doesn't have
a built-in VoAI service.
"""

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult, VoiceProfile

# VoAI voice mappings
VOAI_VOICES: dict[str, list[dict[str, Any]]] = {
    "zh-TW": [
        {"id": "voai-tw-female-1", "name": "小美", "gender": "female"},
        {"id": "voai-tw-male-1", "name": "小明", "gender": "male"},
        {"id": "voai-tw-female-2", "name": "小玲", "gender": "female"},
    ],
    "zh-CN": [
        {"id": "voai-cn-female-1", "name": "小红", "gender": "female"},
        {"id": "voai-cn-male-1", "name": "小强", "gender": "male"},
    ],
    "en-US": [
        {"id": "voai-en-female-1", "name": "Emily", "gender": "female"},
        {"id": "voai-en-male-1", "name": "John", "gender": "male"},
    ],
    "ja-JP": [
        {"id": "voai-ja-female-1", "name": "さくら", "gender": "female"},
    ],
    "ko-KR": [
        {"id": "voai-ko-female-1", "name": "수진", "gender": "female"},
    ],
}


class VoAITTSProvider(ITTSProvider):
    """VoAI TTS provider using REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        api_endpoint: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("VOAI_API_KEY", "")
        self._api_endpoint = api_endpoint or os.getenv(
            "VOAI_API_ENDPOINT", "https://api.voai.tw/v1"
        )

    @property
    def name(self) -> str:
        return "voai"

    @property
    def display_name(self) -> str:
        return "VoAI 台灣語音"

    @property
    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.MP3, AudioFormat.WAV]

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech in batch mode using VoAI API."""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self._api_endpoint}/tts/synthesize",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": request.text,
                        "voice_id": request.voice_id,
                        "language": request.language,
                        "speed": request.speed,
                        "output_format": request.output_format.value,
                    },
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise Exception(f"VoAI API error: {response.status_code} - {response.text}")

                audio_data = response.content
                latency_ms = int((time.time() - start_time) * 1000)

                # Estimate duration
                sample_rate = 24000
                bytes_per_sample = 2
                duration_ms = int((len(audio_data) / (sample_rate * bytes_per_sample)) * 1000)

                return TTSResult(
                    request=request,
                    audio=AudioData(data=audio_data, format=request.output_format),
                    duration_ms=duration_ms,
                    latency_ms=latency_ms,
                )

            except httpx.TimeoutException as e:
                raise Exception("VoAI API timeout") from e
            except httpx.RequestError as e:
                raise Exception(f"VoAI API request failed: {str(e)}") from e

    async def synthesize_stream(
        self, request: TTSRequest
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize speech with streaming output using VoAI API."""
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self._api_endpoint}/tts/stream",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": request.text,
                        "voice_id": request.voice_id,
                        "language": request.language,
                        "speed": request.speed,
                        "output_format": request.output_format.value,
                    },
                    timeout=60.0,
                ) as response:
                    if response.status_code != 200:
                        raise Exception(f"VoAI streaming error: {response.status_code}")

                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        yield chunk

            except httpx.TimeoutException as e:
                raise Exception("VoAI streaming timeout") from e
            except httpx.RequestError as e:
                raise Exception(f"VoAI streaming request failed: {str(e)}") from e

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available VoAI voices."""
        voices: list[VoiceProfile] = []

        if language:
            voice_data = VOAI_VOICES.get(language, [])
            for v in voice_data:
                voices.append(
                    VoiceProfile(
                        id=v["id"],
                        name=v["name"],
                        provider=self.name,
                        language=language,
                        gender=v.get("gender"),
                    )
                )
        else:
            for lang, voice_list in VOAI_VOICES.items():
                for v in voice_list:
                    voices.append(
                        VoiceProfile(
                            id=v["id"],
                            name=v["name"],
                            provider=self.name,
                            language=lang,
                            gender=v.get("gender"),
                        )
                    )

        return voices

    async def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Get a specific voice by ID."""
        for lang, voice_list in VOAI_VOICES.items():
            for v in voice_list:
                if v["id"] == voice_id:
                    return VoiceProfile(
                        id=v["id"],
                        name=v["name"],
                        provider=self.name,
                        language=lang,
                        gender=v.get("gender"),
                    )
        return None

    def get_supported_params(self) -> dict:
        """Get supported parameter ranges."""
        return {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0, "step": 0.1},
            "pitch": {"min": -20, "max": 20, "default": 0, "step": 1},
            "volume": {"min": 0.0, "max": 2.0, "default": 1.0, "step": 0.1},
        }

    def map_params(self, speed: float, pitch: float, volume: float) -> dict:
        """Map normalized parameters to VoAI format.

        VoAI uses similar format to normalized parameters.

        Args:
            speed: Speed value (0.5-2.0)
            pitch: Pitch value (-20 to 20)
            volume: Volume value (0.0-2.0)

        Returns:
            Dictionary with VoAI API parameters
        """
        return {
            "speed": speed,
            "pitch": pitch,
            "volume": volume,
        }

    async def health_check(self) -> bool:
        """Check if VoAI is configured and accessible."""
        if not self._api_key:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._api_endpoint}/health",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=5.0,
                )
                return response.status_code == 200
        except Exception:
            return False
