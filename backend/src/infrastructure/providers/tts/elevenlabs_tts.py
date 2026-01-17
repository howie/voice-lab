"""ElevenLabs Text-to-Speech Provider."""

import httpx

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import VoiceProfile, Gender
from src.infrastructure.providers.tts.base import BaseTTSProvider


class ElevenLabsTTSProvider(BaseTTSProvider):
    """ElevenLabs TTS provider implementation."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    _FORMAT_MAP = {
        AudioFormat.MP3: "mp3_44100_128",
        AudioFormat.WAV: "pcm_44100",
        AudioFormat.OGG: "mp3_44100_128",  # ElevenLabs doesn't support OGG directly
    }

    def __init__(self, api_key: str, model_id: str = "eleven_multilingual_v2"):
        """Initialize ElevenLabs TTS provider.

        Args:
            api_key: ElevenLabs API key
            model_id: Model to use (default: eleven_multilingual_v2)
        """
        super().__init__("elevenlabs")
        self._api_key = api_key
        self._model_id = model_id

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using ElevenLabs API."""
        audio_format = self._get_output_format(request)
        output_format = self._FORMAT_MAP.get(audio_format, "mp3_44100_128")

        url = f"{self.BASE_URL}/text-to-speech/{request.voice_id}"

        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        # Build request body
        body = {
            "text": request.text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }

        # Add output format as query param
        params = {"output_format": output_format}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url, headers=headers, json=body, params=params
            )

            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"ElevenLabs TTS failed with status {response.status_code}: {error_detail}"
                )

            return AudioData(
                data=response.content,
                format=audio_format,
                sample_rate=44100,
            )

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available ElevenLabs voices."""
        url = f"{self.BASE_URL}/voices"

        headers = {
            "xi-api-key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                raise RuntimeError(
                    f"ElevenLabs list voices failed: {response.status_code}"
                )

            data = response.json()

        voices = []
        for voice in data.get("voices", []):
            # ElevenLabs voices are multilingual, so we include all
            # unless a specific language filter is applied
            labels = voice.get("labels", {})

            # Determine gender from labels
            gender = Gender.NEUTRAL
            if labels.get("gender") == "female":
                gender = Gender.FEMALE
            elif labels.get("gender") == "male":
                gender = Gender.MALE

            # Get language info
            voice_lang = labels.get("language", "multilingual")

            # Filter by language if specified
            if language:
                # Simple check - ElevenLabs labels use full names like "Chinese"
                lang_mapping = {
                    "zh-TW": ["chinese", "mandarin"],
                    "zh-CN": ["chinese", "mandarin"],
                    "en-US": ["english", "american"],
                    "ja-JP": ["japanese"],
                }
                allowed = lang_mapping.get(language, [language.lower()])
                if voice_lang.lower() not in allowed and voice_lang != "multilingual":
                    continue

            voices.append(
                VoiceProfile(
                    voice_id=voice["voice_id"],
                    name=voice["name"],
                    provider="elevenlabs",
                    language=voice_lang,
                    gender=gender,
                    sample_audio_url=voice.get("preview_url"),
                    description=voice.get("description", ""),
                )
            )

        return voices
