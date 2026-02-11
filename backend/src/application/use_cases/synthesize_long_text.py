"""Synthesize Long Text Use Case.

Orchestrates segmented synthesis for text exceeding provider limits.
Splits text at semantic boundaries, synthesizes each segment, and merges audio.
"""

import logging
import time

from src.application.interfaces.storage_service import IStorageService
from src.application.interfaces.tts_provider import ITTSProvider
from src.application.use_cases.synthesize_speech import ISynthesisLogger
from src.domain.config.provider_limits import get_split_config
from src.domain.entities.audio import AudioFormat
from src.domain.entities.long_text_tts import LongTextTTSResult
from src.domain.entities.multi_role_tts import DialogueTurn
from src.domain.services.text_splitter import TextSplitter
from src.infrastructure.providers.tts.multi_role.segmented_merger import (
    MergeConfig,
    SegmentedMergerService,
)

logger = logging.getLogger(__name__)

# Provider-specific request delays to avoid rate limiting (ms)
_PROVIDER_REQUEST_DELAYS: dict[str, int] = {
    "gemini": 200,
    "voai": 200,
}

_SPEAKER_NAME = "narrator"


class SynthesizeLongText:
    """Use case for synthesizing long text that exceeds provider limits.

    Splits text into segments at semantic boundaries, synthesizes each
    segment via the existing SegmentedMergerService, and returns merged audio.
    """

    def __init__(
        self,
        provider: ITTSProvider,
        storage: IStorageService | None = None,
        logger_service: ISynthesisLogger | None = None,
    ) -> None:
        self._provider = provider
        self._storage = storage
        self._logger = logger_service

    async def execute(
        self,
        text: str,
        voice_id: str,
        provider_name: str,
        language: str = "zh-TW",
        output_format: AudioFormat = AudioFormat.MP3,
        style_prompt: str | None = None,
        gap_ms: int = 100,
        crossfade_ms: int = 30,
    ) -> LongTextTTSResult:
        """Execute long text synthesis with automatic segmentation.

        Args:
            text: Full input text (may exceed provider limits).
            voice_id: Provider-specific voice ID.
            provider_name: TTS provider identifier.
            language: Language code for synthesis.
            output_format: Output audio format.
            style_prompt: Optional style prompt (applied to all segments).
            gap_ms: Gap between segments in milliseconds.
            crossfade_ms: Crossfade between segments in milliseconds.

        Returns:
            LongTextTTSResult with merged audio and segment metadata.
        """
        start_time = time.time()

        # Get split config for this provider
        split_config = get_split_config(provider_name)
        splitter = TextSplitter(split_config)
        segments = splitter.split(text)

        logger.info(
            "Long text synthesis: provider=%s, total_chars=%d, total_bytes=%d, segments=%d",
            provider_name,
            len(text),
            len(text.encode("utf-8")),
            len(segments),
        )

        # Wrap segments as DialogueTurns (single speaker)
        turns = [
            DialogueTurn(speaker=_SPEAKER_NAME, text=seg.text, index=seg.index) for seg in segments
        ]

        # Build voice map (single speaker → single voice)
        voice_map = {_SPEAKER_NAME: voice_id}

        # Build style map if style_prompt provided
        style_map = {_SPEAKER_NAME: style_prompt} if style_prompt else None

        # Configure merge settings
        request_delay = _PROVIDER_REQUEST_DELAYS.get(provider_name, 0)
        merge_config = MergeConfig(
            gap_ms=gap_ms,
            crossfade_ms=crossfade_ms,
            output_format=output_format,
            request_delay_ms=request_delay,
        )

        # Synthesize and merge via existing SegmentedMergerService
        merger = SegmentedMergerService(
            provider=self._provider,
            config=merge_config,
        )
        multi_role_result = await merger.synthesize_and_merge(
            turns=turns,
            voice_map=voice_map,
            language=language,
            style_map=style_map,
        )

        # Store merged audio if storage is available
        storage_path: str | None = None
        if self._storage:
            from src.domain.entities.audio import AudioData

            audio_data = AudioData(
                data=multi_role_result.audio_content,
                format=output_format,
            )
            storage_path = await self._storage.save(audio_data, provider_name)

        latency_ms = int((time.time() - start_time) * 1000)

        result = LongTextTTSResult(
            audio_content=multi_role_result.audio_content,
            content_type=multi_role_result.content_type,
            duration_ms=multi_role_result.duration_ms,
            latency_ms=latency_ms,
            provider=provider_name,
            segment_count=len(segments),
            segment_timings=multi_role_result.turn_timings,
            storage_path=storage_path,
            total_text_length=len(text),
            total_byte_length=len(text.encode("utf-8")),
        )

        logger.info(
            "Long text synthesis complete: segments=%d, duration_ms=%d, latency_ms=%d",
            result.segment_count,
            result.duration_ms,
            result.latency_ms,
        )

        return result
