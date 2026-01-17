"""Google Cloud TTS Provider implementation."""

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from pipecat.frames.frames import AudioRawFrame, ErrorFrame, TTSAudioRawFrame
from pipecat.services.google.tts import GoogleTTSService

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult, VoiceProfile

# Google Cloud TTS voice mappings by language
GOOGLE_VOICES: dict[str, list[dict[str, Any]]] = {
    "zh-TW": [
        {"id": "cmn-TW-Standard-A", "name": "Standard-A", "gender": "female"},
        {"id": "cmn-TW-Standard-B", "name": "Standard-B", "gender": "male"},
        {"id": "cmn-TW-Wavenet-A", "name": "Wavenet-A", "gender": "female"},
        {"id": "cmn-TW-Wavenet-B", "name": "Wavenet-B", "gender": "male"},
    ],
    "zh-CN": [
        {"id": "cmn-CN-Standard-A", "name": "Standard-A", "gender": "female"},
        {"id": "cmn-CN-Standard-B", "name": "Standard-B", "gender": "male"},
        {"id": "cmn-CN-Wavenet-A", "name": "Wavenet-A", "gender": "female"},
    ],
    "en-US": [
        {"id": "en-US-Neural2-A", "name": "Neural2-A", "gender": "male"},
        {"id": "en-US-Neural2-C", "name": "Neural2-C", "gender": "female"},
        {"id": "en-US-Wavenet-D", "name": "Wavenet-D", "gender": "male"},
    ],
    "ja-JP": [
        {"id": "ja-JP-Neural2-B", "name": "Neural2-B", "gender": "female"},
        {"id": "ja-JP-Neural2-C", "name": "Neural2-C", "gender": "male"},
    ],
    "ko-KR": [
        {"id": "ko-KR-Neural2-A", "name": "Neural2-A", "gender": "female"},
        {"id": "ko-KR-Neural2-B", "name": "Neural2-B", "gender": "female"},
    ],
}


class GoogleTTSProvider(ITTSProvider):
    """Google Cloud TTS provider using Pipecat."""

    def __init__(self, credentials_path: str | None = None) -> None:
        self._credentials_path = credentials_path or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS", ""
        )

    def _get_service(self, voice_id: str) -> GoogleTTSService:
        """Get TTS service with the specified voice."""
        return GoogleTTSService(
            credentials_path=self._credentials_path if self._credentials_path else None,
            voice_id=voice_id,
        )

    @property
    def name(self) -> str:
        return "gcp"

    @property
    def display_name(self) -> str:
        return "Google Cloud TTS"

    @property
    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OGG, AudioFormat.OPUS]

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
            raise Exception(f"Google TTS synthesis failed: {str(e)}") from e

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
            raise Exception(f"Google TTS streaming failed: {str(e)}") from e

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available Google TTS voices."""
        voices: list[VoiceProfile] = []

        if language:
            voice_data = GOOGLE_VOICES.get(language, [])
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
            for lang, voice_list in GOOGLE_VOICES.items():
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
        for lang, voice_list in GOOGLE_VOICES.items():
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
            "speed": {"min": 0.25, "max": 4.0, "default": 1.0, "step": 0.1},
            "pitch": {"min": -20.0, "max": 20.0, "default": 0.0, "step": 0.5},
            "volume": {"min": -96.0, "max": 16.0, "default": 0.0, "step": 1.0},
        }

    def map_params(self, speed: float, pitch: float, volume: float) -> dict:
        """Map normalized parameters to Google Cloud TTS format.

        Args:
            speed: Speed value (0.5-2.0 normalized)
            pitch: Pitch value (-20 to 20 normalized)
            volume: Volume value (0.0-2.0 normalized)

        Returns:
            Dictionary with Google Cloud TTS parameters
        """
        # Google speed: direct multiplier 0.25-4.0
        # Map normalized 0.5-2.0 to 0.25-4.0
        if speed <= 1.0:
            gcp_speed = 0.25 + (speed - 0.5) * (1.0 - 0.25) / (1.0 - 0.5)
        else:
            gcp_speed = 1.0 + (speed - 1.0) * (4.0 - 1.0) / (2.0 - 1.0)

        # Google pitch: semitones -20 to 20 (direct mapping)
        gcp_pitch = float(pitch)

        # Google volume: dB gain -96 to 16
        # Map normalized 0.0-2.0 to -96 to 16
        # 1.0 (normal) = 0dB
        if volume <= 0.0:
            gcp_volume = -96.0
        elif volume >= 2.0:
            gcp_volume = 16.0
        else:
            # Logarithmic scale: 1.0 -> 0dB
            import math
            gcp_volume = 20 * math.log10(volume) if volume > 0 else -96.0

        return {
            "speaking_rate": gcp_speed,
            "pitch": gcp_pitch,
            "volume_gain_db": gcp_volume,
        }

    async def health_check(self) -> bool:
        """Check if Google TTS is configured."""
        return bool(self._credentials_path)
