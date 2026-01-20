"""Synthesize Multi-Role TTS Use Case.

Orchestrates multi-role dialogue synthesis by automatically selecting
native or segmented mode based on provider capability.
"""

from dataclasses import dataclass

from src.application.use_cases.base import UseCase
from src.domain.entities.audio import AudioFormat
from src.domain.entities.multi_role_tts import (
    DialogueTurn,
    MultiRoleSupportType,
    MultiRoleTTSResult,
    VoiceAssignment,
)
from src.infrastructure.providers.tts.factory import (
    ProviderNotSupportedError,
    TTSProviderFactory,
)
from src.infrastructure.providers.tts.multi_role import (
    MergeConfig,
    SegmentedMergerService,
    get_provider_capability,
)


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


class SynthesizeMultiRoleUseCase(UseCase[SynthesizeMultiRoleInput, MultiRoleTTSResult]):
    """Use case for synthesizing multi-role dialogue.

    Automatically selects native or segmented synthesis mode
    based on provider capability.
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

        # Select synthesis mode
        if capability.support_type == MultiRoleSupportType.NATIVE:
            return await self._synthesize_native(input_data, voice_map)
        else:
            return await self._synthesize_segmented(input_data, voice_map)

    async def _synthesize_native(
        self,
        input_data: SynthesizeMultiRoleInput,
        voice_map: dict[str, str],
    ) -> MultiRoleTTSResult:
        """Synthesize using native multi-role support.

        For providers like ElevenLabs with Audio Tags or Azure with SSML.

        Args:
            input_data: Synthesis parameters.
            voice_map: Speaker to voice ID mapping.

        Returns:
            MultiRoleTTSResult with synthesized audio.
        """
        # For now, fall back to segmented mode
        # Native implementations for specific providers will be added later
        # This placeholder allows the API to work while we build out native support
        return await self._synthesize_segmented(input_data, voice_map)

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

        config = MergeConfig(
            gap_ms=input_data.gap_ms,
            crossfade_ms=input_data.crossfade_ms,
            output_format=audio_format,
        )
        merger = SegmentedMergerService(provider=provider, config=config)

        # Synthesize and merge
        result = await merger.synthesize_and_merge(
            turns=input_data.turns,
            voice_map=voice_map,
            language=input_data.language,
        )

        return result
