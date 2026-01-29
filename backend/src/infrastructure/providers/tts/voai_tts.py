"""VoAI Text-to-Speech Provider."""

from typing import Any

import httpx

from src.domain.entities.audio import AudioData
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender, VoiceProfile
from src.infrastructure.providers.tts.base import BaseTTSProvider

# VoAI voice mappings (using actual VoAI speaker names)
# Reference: https://connect.voai.ai/TTS/GetSpeaker
VOAI_VOICES: dict[str, list[dict[str, Any]]] = {
    "zh-TW": [
        # Popular speakers for general use
        {
            "id": "voai-tw-male-1",
            "name": "佑希",
            "gender": "male",
            "age": 22,
            "styles": ["預設", "聊天", "穩重", "激昂"],
        },
        {
            "id": "voai-tw-female-1",
            "name": "雨榛",
            "gender": "female",
            "age": 25,
            "styles": ["預設", "聊天", "輕柔", "輕鬆"],
        },
        {
            "id": "voai-tw-male-2",
            "name": "子墨",
            "gender": "male",
            "age": 37,
            "styles": ["預設", "穩健"],
        },
        {
            "id": "voai-tw-female-2",
            "name": "柔洢",
            "gender": "female",
            "age": 26,
            "styles": ["預設", "輕柔"],
        },
        {
            "id": "voai-tw-female-3",
            "name": "竹均",
            "gender": "female",
            "age": 22,
            "styles": ["預設", "難過", "開心", "生氣"],
        },
        # Additional speakers
        {
            "id": "voai-tw-male-3",
            "name": "昊宇",
            "gender": "male",
            "age": 36,
            "styles": ["預設", "溫暖", "開心", "難過"],
        },
        {
            "id": "voai-tw-female-4",
            "name": "采芸",
            "gender": "female",
            "age": 25,
            "styles": ["預設", "感性", "難過", "懸疑", "生氣"],
        },
        {
            "id": "voai-tw-female-5",
            "name": "樂晰",
            "gender": "female",
            "age": 30,
            "styles": ["預設", "聊天", "可愛"],
        },
        {
            "id": "voai-tw-male-4",
            "name": "汪一誠",
            "gender": "male",
            "age": 55,
            "styles": ["預設", "聊天"],
        },
        {
            "id": "voai-tw-female-6",
            "name": "璦廷",
            "gender": "female",
            "age": 38,
            "styles": ["預設"],
        },
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

        # Map voice IDs to speaker names
        speaker_map = {
            "voai-tw-male-1": "佑希",
            "voai-tw-female-1": "雨榛",
            "voai-tw-male-2": "子墨",
            "voai-tw-female-2": "柔洢",
            "voai-tw-female-3": "竹均",
            "voai-tw-male-3": "昊宇",
            "voai-tw-female-4": "采芸",
            "voai-tw-female-5": "樂晰",
            "voai-tw-male-4": "汪一誠",
            "voai-tw-female-6": "璦廷",
        }
        speaker = speaker_map.get(request.voice_id, "佑希")  # Default to 佑希

        # Clamp parameters to VoAI API limits
        # VoAI speed range: [0.5, 1.5]
        # VoAI pitch_shift range: [-5, 5]
        speed = max(0.5, min(1.5, request.speed))
        pitch_shift = max(-5, min(5, int(request.pitch)))

        body = {
            "version": "Neo",
            "text": request.text,
            "speaker": speaker,
            "style": "預設",
            "speed": speed,
            "pitch_shift": pitch_shift,
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

    def get_supported_params(self) -> dict:
        """Get VoAI-specific supported parameter ranges.

        VoAI has different limits than other providers:
        - speed: [0.5, 1.5] (not 2.0)
        - pitch: [-5, 5] (not [-20, 20])
        """
        return {
            "speed": {"min": 0.5, "max": 1.5, "default": 1.0},
            "pitch": {"min": -5.0, "max": 5.0, "default": 0.0},
            "volume": {"min": 0.0, "max": 2.0, "default": 1.0},
        }
