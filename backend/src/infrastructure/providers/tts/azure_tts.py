"""Azure Cognitive Services Text-to-Speech Provider."""

import azure.cognitiveservices.speech as speechsdk

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender, VoiceProfile
from src.domain.errors import QuotaExceededError
from src.infrastructure.providers.tts.base import BaseTTSProvider


class AzureTTSProvider(BaseTTSProvider):
    """Azure Cognitive Services TTS provider implementation."""

    _FORMAT_MAP = {
        AudioFormat.MP3: speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
        AudioFormat.WAV: speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
        AudioFormat.OGG: speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
    }

    def __init__(self, subscription_key: str, region: str):
        """Initialize Azure TTS provider.

        Args:
            subscription_key: Azure subscription key
            region: Azure region (e.g., "eastasia")
        """
        super().__init__("azure")
        self._subscription_key = subscription_key
        self._region = region

    def _create_speech_config(self, request: TTSRequest) -> speechsdk.SpeechConfig:
        """Create speech config for synthesis."""
        config = speechsdk.SpeechConfig(
            subscription=self._subscription_key,
            region=self._region,
        )

        audio_format = self._get_output_format(request)
        config.set_speech_synthesis_output_format(
            self._FORMAT_MAP.get(
                audio_format,
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
            )
        )

        return config

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using Azure TTS."""
        import asyncio

        config = self._create_speech_config(request)

        # Build SSML for better control
        ssml = self._build_ssml(request)

        # Use pull audio output stream to get bytes
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=config,
            audio_config=None,  # No audio output, we'll get bytes
        )

        # Run sync operation in thread
        result = await asyncio.to_thread(synthesizer.speak_ssml_async(ssml).get)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_format = self._get_output_format(request)
            return AudioData(
                data=result.audio_data,
                format=audio_format,
                sample_rate=16000,
            )
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_details = cancellation.error_details or ""

            # T010: Detect 429 quota exceeded from Azure error details
            if "429" in error_details or "quota" in error_details.lower():
                raise QuotaExceededError(
                    provider="azure",
                    original_error=error_details,
                )

            raise RuntimeError(
                f"Azure TTS synthesis canceled: {cancellation.reason}. Error: {error_details}"
            )
        else:
            raise RuntimeError(f"Azure TTS synthesis failed: {result.reason}")

    def _build_ssml(self, request: TTSRequest) -> str:
        """Build SSML for speech synthesis."""
        # Map language to Azure locale
        lang = self._map_language(request.language)

        # Strip provider prefix if present (e.g., "azure:zh-TW-HsiaoChenNeural" -> "zh-TW-HsiaoChenNeural")
        voice_id = request.voice_id
        if voice_id.startswith("azure:"):
            voice_id = voice_id[6:]

        # Build prosody attributes (relative percentage: 1.0 → "+0%", 1.5 → "+50%")
        rate_percent = (request.speed - 1.0) * 100
        rate = f"+{rate_percent:.0f}%" if rate_percent >= 0 else f"{rate_percent:.0f}%"
        pitch_val = f"{int(request.pitch * 10):+d}Hz" if request.pitch else "+0Hz"

        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">
            <voice name="{voice_id}">
                <prosody rate="{rate}" pitch="{pitch_val}">
                    {self._escape_xml(request.text)}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available Azure voices."""
        import asyncio

        config = speechsdk.SpeechConfig(
            subscription=self._subscription_key,
            region=self._region,
        )

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=config,
            audio_config=None,
        )

        result = await asyncio.to_thread(synthesizer.get_voices_async().get)

        voices = []
        for voice in result.voices:
            # Filter by language if specified
            if language:
                mapped_lang = self._map_language(language)
                if not voice.locale.startswith(mapped_lang.split("-")[0]):
                    continue

            gender = Gender.NEUTRAL
            if voice.gender == speechsdk.SynthesisVoiceGender.Female:
                gender = Gender.FEMALE
            elif voice.gender == speechsdk.SynthesisVoiceGender.Male:
                gender = Gender.MALE

            voices.append(
                VoiceProfile(
                    id=f"azure:{voice.short_name}",
                    voice_id=voice.short_name,
                    display_name=voice.local_name,
                    provider="azure",
                    language=voice.locale,
                    gender=gender,
                    sample_audio_url=None,
                    description=f"Azure voice: {voice.local_name} ({voice.voice_type.name})",
                )
            )

        return voices

    def _map_language(self, language: str) -> str:
        """Map language code to Azure format."""
        mapping = {
            "zh-TW": "zh-TW",
            "zh-CN": "zh-CN",
            "en-US": "en-US",
            "ja-JP": "ja-JP",
        }
        return mapping.get(language, language)

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
