"""Synthesize Multi-Role TTS Use Case.

Orchestrates multi-role dialogue synthesis by automatically selecting
native or segmented mode based on provider capability.

Feature: 008-voai-multi-role-voice-generation
T013-T017: Native synthesis with limit validation and auto-fallback
"""

import asyncio
import logging
import time
from dataclasses import dataclass

import azure.cognitiveservices.speech as speechsdk

from src.application.use_cases.base import UseCase
from src.domain.entities.audio import AudioFormat
from src.domain.entities.multi_role_tts import (
    DialogueTurn,
    MultiRoleSupportType,
    MultiRoleTTSResult,
    VoiceAssignment,
)
from src.domain.errors import QuotaExceededError, RateLimitError
from src.infrastructure.providers.tts.factory import (
    ProviderNotSupportedError,
    TTSProviderFactory,
)
from src.infrastructure.providers.tts.multi_role import (
    AzureSSMLBuilder,
    ElevenLabsDialogueBuilder,
    GeminiDialogueBuilder,
    MergeConfig,
    SegmentedMergerService,
    get_provider_capability,
)

logger = logging.getLogger(__name__)

# Per-provider delay between segmented TTS requests (ms) to avoid RPM limits
PROVIDER_REQUEST_DELAYS: dict[str, int] = {
    "gemini": 200,
}


@dataclass
class SynthesizeMultiRoleInput:
    """Input for multi-role TTS synthesis."""

    provider: str
    turns: list[DialogueTurn]
    voice_assignments: list[VoiceAssignment]
    language: str = "zh-TW"
    output_format: str = "mp3"
    gap_ms: int = 300
    crossfade_ms: int = 50
    style_prompt: str | None = None


class SynthesizeMultiRoleUseCase(UseCase[SynthesizeMultiRoleInput, MultiRoleTTSResult]):
    """Use case for synthesizing multi-role dialogue.

    Automatically selects native or segmented synthesis mode
    based on provider capability and content limits.

    Native Mode Support:
        - Azure: SSML with multiple <voice> tags (limit: 50,000 chars)
        - ElevenLabs: Text to Dialogue API (limit: 5,000 chars)

    Auto-fallback:
        If content exceeds native limits, automatically falls back to segmented mode.
    """

    async def execute(self, input_data: SynthesizeMultiRoleInput) -> MultiRoleTTSResult:
        """Execute multi-role TTS synthesis.

        Args:
            input_data: Synthesis request parameters.

        Returns:
            MultiRoleTTSResult with synthesized audio.

        Raises:
            ValueError: If provider is unsupported or validation fails.
            ProviderNotSupportedError: If provider doesn't support TTS.
        """
        # Validate provider capability
        capability = get_provider_capability(input_data.provider)
        if not capability:
            raise ValueError(f"Provider '{input_data.provider}' not found in capability registry")

        if capability.support_type == MultiRoleSupportType.UNSUPPORTED:
            raise ValueError(f"Provider '{input_data.provider}' does not support multi-role TTS")

        # Validate voice assignments
        speakers = {turn.speaker for turn in input_data.turns}
        assigned_speakers = {va.speaker for va in input_data.voice_assignments}
        missing = speakers - assigned_speakers
        if missing:
            raise ValueError(f"Missing voice assignments for speakers: {missing}")

        # Validate turn count
        if not input_data.turns:
            raise ValueError("Turns cannot be empty")

        # Validate speaker count
        if len(speakers) > capability.max_speakers:
            raise ValueError(
                f"Too many speakers ({len(speakers)}). "
                f"Provider '{input_data.provider}' supports max {capability.max_speakers}"
            )

        # Build voice map
        voice_map = {va.speaker: va.voice_id for va in input_data.voice_assignments}

        # Select synthesis mode with auto-fallback for native providers
        if capability.support_type == MultiRoleSupportType.NATIVE:
            # Check if native mode is feasible
            can_use_native = self._can_use_native(input_data, voice_map)

            if can_use_native:
                try:
                    return await self._synthesize_native(input_data, voice_map)
                except ValueError as e:
                    # Limit exceeded during build, fall back to segmented
                    logger.warning(
                        f"Native synthesis failed for {input_data.provider}, "
                        f"falling back to segmented: {e}"
                    )
                    return await self._synthesize_segmented(input_data, voice_map)
            else:
                logger.info(
                    f"Content exceeds native limits for {input_data.provider}, using segmented mode"
                )
                return await self._synthesize_segmented(input_data, voice_map)
        else:
            return await self._synthesize_segmented(input_data, voice_map)

    def _can_use_native(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> bool:
        """Check if native mode can be used based on content size.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            True if native mode is feasible, False otherwise.
        """
        provider = input_data.provider.lower()

        if provider == "azure":
            builder = AzureSSMLBuilder()
            return builder.can_use_native(input_data.turns, voice_map)
        elif provider == "elevenlabs":
            builder = ElevenLabsDialogueBuilder()
            return builder.can_use_native(input_data.turns, voice_map)
        elif provider == "gemini":
            gemini_builder = GeminiDialogueBuilder()
            return gemini_builder.can_use_native(
                input_data.turns, voice_map, style_prompt=input_data.style_prompt
            )
        else:
            # For other providers marked as NATIVE but without specific builder,
            # use simple character limit check
            total_chars = sum(len(t.text) for t in input_data.turns)
            capability = get_provider_capability(provider)
            if capability:
                return total_chars <= capability.character_limit
            return False

    async def _synthesize_native(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> MultiRoleTTSResult:
        """Synthesize using native multi-role support.

        Routes to provider-specific native synthesis implementation.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            MultiRoleTTSResult with synthesized audio.

        Raises:
            ValueError: If synthesis fails or limits exceeded.
        """
        provider = input_data.provider.lower()

        if provider == "azure":
            return await self._synthesize_azure_native(input_data, voice_map)
        elif provider == "elevenlabs":
            return await self._synthesize_elevenlabs_native(input_data, voice_map)
        elif provider == "gemini":
            return await self._synthesize_gemini_native(input_data, voice_map)
        else:
            logger.info(f"Native synthesis not implemented for {provider}, using segmented mode")
            return await self._synthesize_segmented(input_data, voice_map)

    async def _synthesize_azure_native(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> MultiRoleTTSResult:
        """Synthesize using Azure SSML multi-voice.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            MultiRoleTTSResult with synthesized audio.
        """
        import os

        start_time = time.time()

        # Build SSML
        builder = AzureSSMLBuilder()
        ssml = builder.build_multi_voice_ssml(
            turns=input_data.turns,
            voice_map=voice_map,
            language=input_data.language,
            gap_ms=input_data.gap_ms,
        )

        # Get Azure credentials from environment
        subscription_key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")

        if not subscription_key or not region:
            raise ValueError("Azure Speech credentials not configured")

        # Create speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region,
        )

        # Set output format
        format_map = {
            "mp3": speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
            "wav": speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
            "ogg": speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
        }
        output_format = format_map.get(
            input_data.output_format.lower(),
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
        )
        speech_config.set_speech_synthesis_output_format(output_format)

        # Synthesize
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None,
        )

        result = await asyncio.to_thread(synthesizer.speak_ssml_async(ssml).get)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            latency_ms = int((time.time() - start_time) * 1000)

            # Estimate duration (rough: 150 words/minute for Chinese)
            total_chars = sum(len(t.text) for t in input_data.turns)
            estimated_duration_ms = int(total_chars * 200)  # ~200ms per character

            content_type_map = {
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "ogg": "audio/ogg",
            }

            return MultiRoleTTSResult(
                audio_content=result.audio_data,
                content_type=content_type_map.get(input_data.output_format.lower(), "audio/mpeg"),
                duration_ms=estimated_duration_ms,
                latency_ms=latency_ms,
                provider="azure",
                synthesis_mode=MultiRoleSupportType.NATIVE,
                turn_timings=None,
            )
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            raise ValueError(
                f"Azure TTS synthesis canceled: {cancellation.reason}. "
                f"Error: {cancellation.error_details}"
            )
        else:
            raise ValueError(f"Azure TTS synthesis failed: {result.reason}")

    async def _synthesize_elevenlabs_native(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> MultiRoleTTSResult:
        """Synthesize using ElevenLabs Text to Dialogue API.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            MultiRoleTTSResult with synthesized audio.
        """
        import os

        import httpx

        start_time = time.time()

        # Build request
        builder = ElevenLabsDialogueBuilder()
        request = builder.build_dialogue_request(
            turns=input_data.turns,
            voice_map=voice_map,
        )
        payload = builder.to_api_payload(request)

        # Get API key
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key not configured")

        # Call Text to Dialogue API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.elevenlabs.io/v1/text-to-dialogue",
                json=payload,
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                raise ValueError(f"ElevenLabs API error ({response.status_code}): {error_detail}")

            audio_data = response.content

        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate duration
        total_chars = sum(len(t.text) for t in input_data.turns)
        estimated_duration_ms = int(total_chars * 200)

        return MultiRoleTTSResult(
            audio_content=audio_data,
            content_type="audio/mpeg",
            duration_ms=estimated_duration_ms,
            latency_ms=latency_ms,
            provider="elevenlabs",
            synthesis_mode=MultiRoleSupportType.NATIVE,
            turn_timings=None,
        )

    async def _synthesize_gemini_native(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> MultiRoleTTSResult:
        """Synthesize using Gemini native multi-speaker API.

        Uses multiSpeakerVoiceConfig for native multi-speaker synthesis
        in a single API call.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            MultiRoleTTSResult with synthesized audio.

        Raises:
            ValueError: If synthesis fails.
        """
        import base64
        import io
        import os

        import httpx
        from pydub import AudioSegment

        start_time = time.time()

        # Build payload
        builder = GeminiDialogueBuilder()
        payload = builder.build_multi_speaker_payload(
            turns=input_data.turns,
            voice_map=voice_map,
            style_prompt=input_data.style_prompt,
        )

        # Get API key and model
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not configured (GEMINI_API_KEY or GOOGLE_API_KEY)")

        model = builder.config.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        # Call Gemini API with retry for 429
        max_429_retries = 3
        retry_backoffs = (1.0, 2.0, 4.0)

        async with httpx.AsyncClient(timeout=180.0) as client:
            for retry_429 in range(max_429_retries + 1):
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 429:
                    break

                if retry_429 < max_429_retries:
                    wait = retry_backoffs[retry_429]
                    if "retry-after" in response.headers:
                        import contextlib

                        with contextlib.suppress(ValueError, TypeError):
                            ra = int(response.headers["retry-after"])
                            wait = min(float(ra), 30.0)
                    logger.warning(
                        "Gemini multi-speaker 429 on attempt %d/%d, retrying after %.1fs",
                        retry_429 + 1,
                        max_429_retries + 1,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                # All 429 retries exhausted
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise RateLimitError(
                    provider="gemini",
                    retry_after=None,
                    original_error=error_msg,
                )

        if response.status_code != 200:
            try:
                error_json = response.json()
                error_message = error_json.get("error", {}).get("message", response.text)
            except Exception:
                error_message = response.text

            if "exceeded your current quota" in error_message.lower():
                raise QuotaExceededError(
                    provider="gemini",
                    retry_after=None,
                    original_error=error_message,
                )
            raise ValueError(
                f"Gemini multi-speaker API error (status {response.status_code}): {error_message}"
            )

        result_json = response.json()

        # Extract audio
        candidates = result_json.get("candidates", [])
        if not candidates:
            raise ValueError(
                "Gemini multi-speaker returned no candidates. "
                "The input may have been blocked by safety filters."
            )

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason", "")

        if "content" not in candidate:
            if finish_reason == "SAFETY":
                raise ValueError(
                    "Gemini multi-speaker blocked by safety filters. "
                    "Try rephrasing the text or using a different style prompt."
                )
            raise ValueError(
                f"Gemini multi-speaker returned no audio (finishReason={finish_reason})."
            )

        try:
            audio_base64 = candidate["content"]["parts"][0]["inlineData"]["data"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid Gemini multi-speaker response structure: {e}") from e

        # Convert PCM 24kHz to target format
        pcm_data = base64.b64decode(audio_base64)
        audio = AudioSegment(
            data=pcm_data,
            sample_width=2,
            frame_rate=24000,
            channels=1,
        )

        output_buffer = io.BytesIO()
        format_map = {"mp3": "mp3", "wav": "wav", "ogg": "ogg", "opus": "opus", "flac": "flac"}
        export_format = format_map.get(input_data.output_format.lower(), "mp3")
        audio.export(output_buffer, format=export_format)
        audio_content = output_buffer.getvalue()

        latency_ms = int((time.time() - start_time) * 1000)
        duration_ms = len(audio)

        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "opus": "audio/opus",
            "flac": "audio/flac",
        }

        return MultiRoleTTSResult(
            audio_content=audio_content,
            content_type=content_type_map.get(input_data.output_format.lower(), "audio/mpeg"),
            duration_ms=duration_ms,
            latency_ms=latency_ms,
            provider="gemini",
            synthesis_mode=MultiRoleSupportType.NATIVE,
            turn_timings=None,
        )

    async def _synthesize_segmented(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> MultiRoleTTSResult:
        """Synthesize using segmented merge approach.

        Makes separate TTS requests per turn and merges audio.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            MultiRoleTTSResult with merged audio.
        """
        # Create provider
        try:
            provider = TTSProviderFactory.create_default(input_data.provider)
        except ProviderNotSupportedError as e:
            raise ValueError(str(e)) from e

        # Create merger service
        # Convert string output_format to AudioFormat enum
        try:
            audio_format = AudioFormat(input_data.output_format.lower())
        except ValueError:
            audio_format = AudioFormat.MP3  # Default to MP3

        request_delay_ms = PROVIDER_REQUEST_DELAYS.get(input_data.provider.lower(), 0)
        config = MergeConfig(
            gap_ms=input_data.gap_ms,
            crossfade_ms=input_data.crossfade_ms,
            output_format=audio_format,
            request_delay_ms=request_delay_ms,
        )
        merger = SegmentedMergerService(provider=provider, config=config)

        # Build style map from voice assignments and global style_prompt
        style_map: dict[str, str] | None = None
        per_speaker_styles = {
            va.speaker: va.style_prompt for va in input_data.voice_assignments if va.style_prompt
        }
        if per_speaker_styles or input_data.style_prompt:
            style_map = {}
            speakers = {turn.speaker for turn in input_data.turns}
            for speaker in speakers:
                # Per-speaker style takes priority over global style
                if speaker in per_speaker_styles:
                    style_map[speaker] = per_speaker_styles[speaker]
                elif input_data.style_prompt:
                    style_map[speaker] = input_data.style_prompt

        # Synthesize and merge
        result = await merger.synthesize_and_merge(
            turns=input_data.turns,
            voice_map=voice_map,
            language=input_data.language,
            style_map=style_map,
        )

        return result
