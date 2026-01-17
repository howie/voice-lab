"""Azure Speech Services TTS Provider implementation."""

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from pipecat.services.azure import AzureTTSService
from pipecat.frames.frames import AudioRawFrame, TTSAudioRawFrame, ErrorFrame

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioFormat, AudioData
from src.domain.entities.tts import TTSRequest, TTSResult, VoiceProfile


# Azure voice mappings by language
AZURE_VOICES: dict[str, list[dict[str, Any]]] = {
    "zh-TW": [
        {"id": "zh-TW-HsiaoChenNeural", "name": "HsiaoChen", "gender": "female"},
        {"id": "zh-TW-YunJheNeural", "name": "YunJhe", "gender": "male"},
        {"id": "zh-TW-HsiaoYuNeural", "name": "HsiaoYu", "gender": "female"},
    ],
    "zh-CN": [
        {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao", "gender": "female"},
        {"id": "zh-CN-YunxiNeural", "name": "Yunxi", "gender": "male"},
    ],
    "en-US": [
        {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female"},
        {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male"},
    ],
    "ja-JP": [
        {"id": "ja-JP-NanamiNeural", "name": "Nanami", "gender": "female"},
        {"id": "ja-JP-KeitaNeural", "name": "Keita", "gender": "male"},
    ],
    "ko-KR": [
        {"id": "ko-KR-SunHiNeural", "name": "SunHi", "gender": "female"},
        {"id": "ko-KR-InJoonNeural", "name": "InJoon", "gender": "male"},
    ],
}


class AzureTTSProvider(ITTSProvider):
    """Azure Speech Services TTS provider using Pipecat."""

    def __init__(
        self,
        api_key: str | None = None,
        region: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("AZURE_SPEECH_KEY", "")
        self._region = region or os.getenv("AZURE_SPEECH_REGION", "eastasia")
        self._service: AzureTTSService | None = None

    def _get_service(self, voice_id: str) -> AzureTTSService:
        """Get or create TTS service with the specified voice."""
        return AzureTTSService(
            api_key=self._api_key,
            region=self._region,
            voice=voice_id,
        )

    @property
    def name(self) -> str:
        return "azure"

    @property
    def display_name(self) -> str:
        return "Azure Speech Services"

    @property
    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OPUS, AudioFormat.OGG]

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
            raise Exception(f"Azure TTS synthesis failed: {str(e)}")

        full_audio = b"".join(audio_chunks)
        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate duration (rough: assume 24kHz, 16-bit mono)
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
            raise Exception(f"Azure TTS streaming failed: {str(e)}")

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available Azure voices."""
        voices: list[VoiceProfile] = []

        if language:
            voice_data = AZURE_VOICES.get(language, [])
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
            for lang, voice_list in AZURE_VOICES.items():
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
        for lang, voice_list in AZURE_VOICES.items():
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

    def map_params_to_ssml(self, speed: float, pitch: float, volume: float) -> dict:
        """Map normalized parameters to Azure SSML format.

        Args:
            speed: Speed value (0.5-2.0)
            pitch: Pitch value (-20 to 20)
            volume: Volume value (0.0-2.0)

        Returns:
            Dictionary with Azure SSML prosody attributes
        """
        # Azure uses percentage format: +0%, +100%, -50%
        rate_percent = (speed - 1.0) * 100
        rate_str = f"+{rate_percent:.0f}%" if rate_percent >= 0 else f"{rate_percent:.0f}%"

        # Azure pitch: -20 to 20 maps to -50% to +50%
        pitch_percent = (pitch / 20) * 50
        pitch_str = f"+{pitch_percent:.0f}%" if pitch_percent >= 0 else f"{pitch_percent:.0f}%"

        # Azure volume: 0-2.0 maps to 0% to 200% (or use x-soft, soft, medium, loud, x-loud)
        volume_percent = volume * 100
        volume_str = f"{volume_percent:.0f}%"

        return {
            "rate": rate_str,
            "pitch": pitch_str,
            "volume": volume_str,
        }

    async def health_check(self) -> bool:
        """Check if Azure Speech is configured and accessible."""
        return bool(self._api_key and self._region)
