"""VoAI Text-to-Speech Provider."""

from typing import Any

import httpx

from src.domain.entities.audio import AudioData
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender, VoiceProfile
from src.infrastructure.providers.tts.base import BaseTTSProvider

# VoAI voice mappings (using actual VoAI speaker names)
VOAI_VOICES: dict[str, list[dict[str, Any]]] = {
    "zh-TW": [
        {"id": "voai-tw-female-1", "name": "佑希", "gender": "female"},
        {"id": "voai-tw-male-1", "name": "辰宇", "gender": "male"},
        {"id": "voai-tw-female-2", "name": "雅婷", "gender": "female"},
    ],
}


class VoAITTSProvider(BaseTTSProvider):
    """VoAI TTS provider implementation.

    VoAI is a provider focused on Asian languages, particularly
    Chinese and Japanese.
    """

    def __init__(self, api_key: str, api_endpoint: str | None = None):
        """Initialize VoAI TTS provider.

        Args:
            api_key: VoAI API key
            api_endpoint: VoAI API endpoint (e.g., "connect.voai.ai")
                         If not provided, defaults to "api.voai.io"
        """
        super().__init__("voai")
        self._api_key = api_key

        # Use provided endpoint or default
        endpoint = api_endpoint or "api.voai.io"
        # Remove https:// prefix if present
        endpoint = endpoint.replace("https://", "").replace("http://", "")
        self._base_url = f"https://{endpoint}/v1"

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using VoAI API.

        VoAI uses a different API format:
        - Endpoint: /TTS/Speech
        - Headers: x-api-key, x-output-format
        - Body: version, speaker, style, etc.
        """
        audio_format = self._get_output_format(request)

        # Remove /v1 suffix since VoAI uses /TTS/Speech directly
        base_url = self._base_url.replace("/v1", "")
        url = f"{base_url}/TTS/Speech"

        # Map format to VoAI output format
        format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "pcm": "wav",  # VoAI doesn't support raw PCM, use WAV
        }
        output_format = format_map.get(audio_format.value, "wav")

        headers = {
            "x-api-key": self._api_key,
            "x-output-format": output_format,
            "Content-Type": "application/json",
        }

        # Extract speaker name from voice_id (e.g., "voai-tw-female-1" -> "小美")
        # Map voice IDs to speaker names
        speaker_map = {
            "voai-tw-female-1": "佑希",
            "voai-tw-male-1": "辰宇",
            "voai-tw-female-2": "雅婷",
        }
        speaker = speaker_map.get(request.voice_id, "佑希")  # Default to 佑希

        body = {
            "version": "Neo",
            "text": request.text,
            "speaker": speaker,
            "style": "預設",
            "speed": request.speed,
            "pitch_shift": int(request.pitch),  # VoAI uses integer
            "style_weight": 0,
            "breath_pause": 0,
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
        """List available VoAI voices.

        Returns hardcoded voice list since VoAI doesn't provide a voices API endpoint.
        """
        voices = []

        if language:
            voice_data = VOAI_VOICES.get(language, [])
            for v in voice_data:
                gender = Gender.NEUTRAL
                if v.get("gender") == "female":
                    gender = Gender.FEMALE
                elif v.get("gender") == "male":
                    gender = Gender.MALE

                voices.append(
                    VoiceProfile(
                        id=v["id"],
                        voice_id=v["id"],
                        display_name=v["name"],
                        provider="voai",
                        language=language,
                        gender=gender,
                    )
                )
        else:
            # Return all voices for all languages
            for lang, voice_data in VOAI_VOICES.items():
                for v in voice_data:
                    gender = Gender.NEUTRAL
                    if v.get("gender") == "female":
                        gender = Gender.FEMALE
                    elif v.get("gender") == "male":
                        gender = Gender.MALE

                    voices.append(
                        VoiceProfile(
                            id=v["id"],
                            voice_id=v["id"],
                            display_name=v["name"],
                            provider="voai",
                            language=lang,
                            gender=gender,
                        )
                    )

        return voices
