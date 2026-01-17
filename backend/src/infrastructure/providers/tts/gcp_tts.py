"""Google Cloud Text-to-Speech Provider."""

from google.cloud import texttospeech_v1 as texttospeech

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender, VoiceProfile
from src.infrastructure.providers.tts.base import BaseTTSProvider


class GCPTTSProvider(BaseTTSProvider):
    """Google Cloud TTS provider implementation."""

    # Format mapping
    _FORMAT_MAP = {
        AudioFormat.MP3: texttospeech.AudioEncoding.MP3,
        AudioFormat.WAV: texttospeech.AudioEncoding.LINEAR16,
        AudioFormat.OGG: texttospeech.AudioEncoding.OGG_OPUS,
    }

    _GENDER_MAP = {
        texttospeech.SsmlVoiceGender.MALE: Gender.MALE,
        texttospeech.SsmlVoiceGender.FEMALE: Gender.FEMALE,
        texttospeech.SsmlVoiceGender.NEUTRAL: Gender.NEUTRAL,
    }

    def __init__(self, credentials_path: str | None = None):
        """Initialize GCP TTS provider.

        Args:
            credentials_path: Path to GCP service account JSON file.
                            If None, uses default credentials.
        """
        super().__init__("gcp")

        if credentials_path:
            self._client = texttospeech.TextToSpeechClient.from_service_account_json(
                credentials_path
            )
        else:
            self._client = texttospeech.TextToSpeechClient()

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using GCP TTS."""
        # Build synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=request.text)

        # Build voice selection
        voice = texttospeech.VoiceSelectionParams(
            language_code=self._map_language(request.language),
            name=request.voice_id,
        )

        # Build audio config
        audio_format = self._get_output_format(request)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=self._FORMAT_MAP.get(
                audio_format, texttospeech.AudioEncoding.MP3
            ),
            speaking_rate=request.speed,
            pitch=request.pitch,
            volume_gain_db=self._volume_to_db(request.volume),
        )

        # Call API (sync client, but we're in async context)
        import asyncio

        response = await asyncio.to_thread(
            self._client.synthesize_speech,
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        return AudioData(
            data=response.audio_content,
            format=audio_format,
            sample_rate=24000,
        )

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available GCP voices."""
        import asyncio

        language_code = self._map_language(language) if language else None

        response = await asyncio.to_thread(
            self._client.list_voices,
            language_code=language_code,
        )

        voices = []
        for voice in response.voices:
            # Get primary language code
            lang = voice.language_codes[0] if voice.language_codes else "unknown"

            voices.append(
                VoiceProfile(
                    voice_id=voice.name,
                    name=voice.name,
                    provider="gcp",
                    language=lang,
                    gender=self._GENDER_MAP.get(voice.ssml_gender, Gender.NEUTRAL),
                    sample_audio_url=None,
                    description=f"GCP voice: {voice.name}",
                )
            )

        return voices

    def _map_language(self, language: str) -> str:
        """Map language code to GCP format."""
        mapping = {
            "zh-TW": "cmn-TW",
            "zh-CN": "cmn-CN",
            "en-US": "en-US",
            "ja-JP": "ja-JP",
        }
        return mapping.get(language, language)

    def _volume_to_db(self, volume: float) -> float:
        """Convert volume (0-1) to dB gain (-96 to 16)."""
        import math

        if volume <= 0:
            return -96.0
        if volume >= 1:
            return 0.0
        # Convert linear to dB
        return 20 * math.log10(volume)
