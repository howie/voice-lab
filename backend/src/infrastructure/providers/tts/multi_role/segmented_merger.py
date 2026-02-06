"""Segmented Merger Service.

Synthesizes multi-role dialogue by making separate TTS requests per turn
and merging the audio segments using pydub.
"""

import asyncio
import io
import time
from collections.abc import Callable
from dataclasses import dataclass

from pydub import AudioSegment
from pydub.effects import normalize

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioFormat
from src.domain.entities.multi_role_tts import (
    DialogueTurn,
    MultiRoleSupportType,
    MultiRoleTTSResult,
    TurnTiming,
)
from src.domain.entities.tts import TTSRequest
from src.infrastructure.providers.tts.multi_role.azure_ssml_builder import (
    strip_style_tags,
)


@dataclass
class MergeConfig:
    """Configuration for audio merging."""

    gap_ms: int = 300
    """Gap between turns in milliseconds."""

    crossfade_ms: int = 50
    """Crossfade duration in milliseconds."""

    target_dbfs: float = -20.0
    """Target volume level in dBFS for normalization."""

    output_format: AudioFormat = AudioFormat.MP3
    """Output audio format."""

    request_delay_ms: int = 0
    """Delay between TTS requests in milliseconds (to avoid rate limiting)."""


class SegmentedMergerService:
    """Service for synthesizing multi-role dialogue with segmented merging.

    For providers that don't natively support multi-role synthesis,
    this service makes separate TTS requests for each turn and merges
    the audio segments using pydub.
    """

    def __init__(
        self,
        provider: ITTSProvider,
        config: MergeConfig | None = None,
    ):
        """Initialize the merger service.

        Args:
            provider: TTS provider instance to use for synthesis.
            config: Optional merge configuration.
        """
        self._provider = provider
        self._config = config or MergeConfig()

    async def synthesize_and_merge(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
        language: str = "zh-TW",
        on_turn_complete: Callable[[int, int], None] | None = None,
        style_map: dict[str, str] | None = None,
    ) -> MultiRoleTTSResult:
        """Synthesize dialogue turns and merge into single audio.

        Args:
            turns: List of dialogue turns to synthesize.
            voice_map: Mapping of speaker identifiers to voice IDs.
            language: Language code for synthesis.
            on_turn_complete: Optional callback called after each turn (turn_index, total).

        Returns:
            MultiRoleTTSResult with merged audio and metadata.

        Raises:
            ValueError: If voice_map doesn't cover all speakers.
            TTSProviderError: If synthesis fails.
        """
        start_time = time.time()

        # Validate voice mapping
        speakers = {turn.speaker for turn in turns}
        missing = speakers - set(voice_map.keys())
        if missing:
            raise ValueError(f"Missing voice assignments for speakers: {missing}")

        # Synthesize each turn
        segments: list[AudioSegment] = []
        turn_timings: list[TurnTiming] = []
        current_position_ms = 0

        for i, turn in enumerate(turns):
            voice_id = voice_map[turn.speaker]

            # Create TTS request for this turn
            # Strip known style tags so they aren't spoken aloud in segmented mode
            clean_text = strip_style_tags(turn.text)
            turn_style = style_map.get(turn.speaker) if style_map else None
            request = TTSRequest(
                text=clean_text,
                voice_id=voice_id,
                provider=self._provider.name,
                language=language,
                output_format=self._config.output_format,
                style_prompt=turn_style,
            )

            # Synthesize
            result = await self._provider.synthesize(request)
            audio_data = result.audio.data

            # Convert to AudioSegment
            segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=self._config.output_format.value,
            )

            # Record timing before adding gap
            turn_start = current_position_ms
            turn_end = current_position_ms + len(segment)

            turn_timings.append(
                TurnTiming(
                    turn_index=turn.index,
                    start_ms=turn_start,
                    end_ms=turn_end,
                )
            )

            segments.append(segment)
            current_position_ms = turn_end + self._config.gap_ms

            # Callback for progress tracking
            if on_turn_complete:
                on_turn_complete(i, len(turns))

            # Delay between requests to avoid rate limiting
            if self._config.request_delay_ms > 0 and i < len(turns) - 1:
                await asyncio.sleep(self._config.request_delay_ms / 1000)

        # Merge segments
        merged = self._merge_segments(segments)

        # Normalize audio
        merged = normalize(merged, headroom=abs(self._config.target_dbfs))

        # Export to bytes
        output_buffer = io.BytesIO()
        merged.export(output_buffer, format=self._config.output_format.value)
        audio_content = output_buffer.getvalue()

        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        duration_ms = len(merged)

        # Determine content type
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "opus": "audio/opus",
            "ogg": "audio/ogg",
        }
        content_type = content_type_map.get(self._config.output_format.value, "audio/mpeg")

        return MultiRoleTTSResult(
            audio_content=audio_content,
            content_type=content_type,
            duration_ms=duration_ms,
            latency_ms=latency_ms,
            provider=self._provider.name,
            synthesis_mode=MultiRoleSupportType.SEGMENTED,
            turn_timings=turn_timings,
        )

    def _merge_segments(self, segments: list[AudioSegment]) -> AudioSegment:
        """Merge audio segments with gaps and optional crossfade.

        Args:
            segments: List of audio segments to merge.

        Returns:
            Merged AudioSegment.
        """
        if not segments:
            return AudioSegment.empty()

        if len(segments) == 1:
            return segments[0]

        # Start with first segment
        merged = segments[0]

        # Add remaining segments with gap and crossfade
        gap = AudioSegment.silent(duration=self._config.gap_ms)

        for segment in segments[1:]:
            if self._config.crossfade_ms > 0:
                # Add gap then crossfade
                merged = merged + gap
                merged = merged.append(segment, crossfade=self._config.crossfade_ms)
            else:
                # Simple concatenation with gap
                merged = merged + gap + segment

        return merged
