"""VoAI Text-to-Speech Provider."""

import httpx

from src.domain.entities.audio import AudioData
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender, VoiceProfile
from src.infrastructure.providers.tts.base import BaseTTSProvider


class VoAITTSProvider(BaseTTSProvider):
    """VoAI TTS provider implementation.

    VoAI is a provider focused on Asian languages, particularly
    Chinese and Japanese.
    """

    BASE_URL = "https://api.voai.io/v1"

    def __init__(self, api_key: str):
        """Initialize VoAI TTS provider.

        Args:
            api_key: VoAI API key
        """
        super().__init__("voai")
        self._api_key = api_key

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using VoAI API."""
        audio_format = self._get_output_format(request)

        url = f"{self.BASE_URL}/tts"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "text": request.text,
            "voice_id": request.voice_id,
            "language": request.language,
            "speed": request.speed,
            "pitch": request.pitch,
            "output_format": audio_format.value,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"VoAI TTS failed with status {response.status_code}: {error_detail}"
                )

            # VoAI returns audio directly
            return AudioData(
                data=response.content,
                format=audio_format,
                sample_rate=24000,
            )

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available VoAI voices."""
        url = f"{self.BASE_URL}/voices"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }

        params = {}
        if language:
            params["language"] = language

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                raise RuntimeError(f"VoAI list voices failed: {response.status_code}")

            data = response.json()

        voices = []
        for voice in data.get("voices", []):
            gender = Gender.NEUTRAL
            if voice.get("gender") == "female":
                gender = Gender.FEMALE
            elif voice.get("gender") == "male":
                gender = Gender.MALE

            voices.append(
                VoiceProfile(
                    voice_id=voice["id"],
                    name=voice["name"],
                    provider="voai",
                    language=voice.get("language", "zh-TW"),
                    gender=gender,
                    sample_audio_url=voice.get("sample_url"),
                    description=voice.get("description", ""),
                )
            )

        return voices
