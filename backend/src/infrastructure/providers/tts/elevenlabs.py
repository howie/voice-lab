"""ElevenLabs TTS Provider implementation."""

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from pipecat.frames.frames import AudioRawFrame, ErrorFrame, TTSAudioRawFrame
from pipecat.services.elevenlabs import ElevenLabsTTSService

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult, VoiceProfile

# ElevenLabs voice mappings (multilingual voices)
ELEVENLABS_VOICES: list[dict[str, Any]] = [
    {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
    {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
    {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female"},
    {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male"},
    {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male"},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male"},
    {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male"},
]

# ElevenLabs supports multilingual
SUPPORTED_LANGUAGES = ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]


class ElevenLabsTTSProvider(ITTSProvider):
    """ElevenLabs TTS provider using Pipecat."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")

    def _get_service(self, voice_id: str) -> ElevenLabsTTSService:
        """Get TTS service with the specified voice."""
        return ElevenLabsTTSService(
            api_key=self._api_key,
            voice_id=voice_id,
        )

    @property
    def name(self) -> str:
        return "elevenlabs"

    @property
    def display_name(self) -> str:
        return "ElevenLabs"

    @property
    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.MP3, AudioFormat.PCM]

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech in batch mode."""
        start_time = time.time()
        service = self._get_service(request.voice_id)

        audio_chunks: list[bytes] = []

        try:
            async for frame in service.run_tts(request.text):
                if isinstance(frame, (AudioRawFrame, TTSAudioRawFrame)):
                    audio_chunks.append(frame.audio)
                elif isinstance(frame, ErrorFrame):
                    raise Exception(f"TTS Error: {frame.error}")
        except Exception as e:
            raise Exception(f"ElevenLabs TTS synthesis failed: {str(e)}") from e

        full_audio = b"".join(audio_chunks)
        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate duration
        sample_rate = 24000
        bytes_per_sample = 2
        duration_ms = int((len(full_audio) / (sample_rate * bytes_per_sample)) * 1000)

        return TTSResult(
            request=request,
            audio=AudioData(data=full_audio, format=request.output_format),
            duration_ms=duration_ms,
            latency_ms=latency_ms,
        )

    async def synthesize_stream(
        self, request: TTSRequest
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize speech with streaming output."""
        service = self._get_service(request.voice_id)

        try:
            async for frame in service.run_tts(request.text):
                if isinstance(frame, (AudioRawFrame, TTSAudioRawFrame)):
                    yield frame.audio
                elif isinstance(frame, ErrorFrame):
                    raise Exception(f"TTS Error: {frame.error}")
        except Exception as e:
            raise Exception(f"ElevenLabs TTS streaming failed: {str(e)}") from e

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available ElevenLabs voices.

        ElevenLabs voices are multilingual, so language filter is not strictly applied.
        """
        voices: list[VoiceProfile] = []

        for v in ELEVENLABS_VOICES:
            # For ElevenLabs, we list all voices for all supported languages
            if language:
                voices.append(
                    VoiceProfile(
                        id=v["id"],
                        name=v["name"],
                        provider=self.name,
                        language=language,  # Multilingual
                        gender=v.get("gender"),
                    )
                )
            else:
                # List with default language
                voices.append(
                    VoiceProfile(
                        id=v["id"],
                        name=v["name"],
                        provider=self.name,
                        language="multilingual",
                        gender=v.get("gender"),
                    )
                )

        return voices

    async def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Get a specific voice by ID."""
        for v in ELEVENLABS_VOICES:
            if v["id"] == voice_id:
                return VoiceProfile(
                    id=v["id"],
                    name=v["name"],
                    provider=self.name,
                    language="multilingual",
                    gender=v.get("gender"),
                )
        return None

    def get_supported_params(self) -> dict:
        """Get supported parameter ranges.

        Note: ElevenLabs uses different parameters than other providers:
        - stability: How consistent the voice is (0.0-1.0)
        - similarity_boost: How closely to match original voice (0.0-1.0)
        - style: Expressiveness (0.0-1.0, optional)
        """
        return {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0, "step": 0.1},
            "stability": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.1},
            "similarity_boost": {"min": 0.0, "max": 1.0, "default": 0.75, "step": 0.1},
            "style": {"min": 0.0, "max": 1.0, "default": 0.0, "step": 0.1},
        }

    def map_params(self, _speed: float, pitch: float, _volume: float) -> dict:
        """Map normalized parameters to ElevenLabs format.

        ElevenLabs doesn't support traditional pitch/volume, so we map
        pitch to stability and volume to similarity_boost.

        Args:
            speed: Speed value (0.5-2.0)
            pitch: Pitch value (-20 to 20) - mapped to stability
            volume: Volume value (0.0-2.0) - not directly supported

        Returns:
            Dictionary with ElevenLabs voice settings
        """
        # Map pitch variance to stability (inverted: more pitch variance = less stability)
        # pitch -20 to 20 -> stability 0.7 to 0.3
        stability = 0.5 - (pitch / 20) * 0.2
        stability = max(0.0, min(1.0, stability))

        return {
            "stability": stability,
            "similarity_boost": 0.75,  # Default
            "style": 0.0,  # Default, less expressive
            "use_speaker_boost": True,
        }

    async def health_check(self) -> bool:
        """Check if ElevenLabs is configured."""
        return bool(self._api_key)
