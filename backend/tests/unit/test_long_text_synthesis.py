"""Integration tests for SynthesizeLongText use case.

Uses mock TTS provider to test segmentation + merge pipeline end-to-end.
"""

import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydub import AudioSegment

from src.application.use_cases.synthesize_long_text import SynthesizeLongText
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult


def _make_mock_audio(duration_ms: int = 500) -> bytes:
    """Generate silent WAV audio bytes for testing (no ffmpeg needed)."""
    segment = AudioSegment.silent(duration=duration_ms)
    buffer = io.BytesIO()
    segment.export(buffer, format="wav")
    return buffer.getvalue()


def _create_mock_provider(provider_name: str = "gemini") -> MagicMock:
    """Create a mock TTS provider that returns fake WAV audio."""
    provider = MagicMock()
    provider.name = provider_name

    async def mock_synthesize(request: TTSRequest) -> TTSResult:
        audio_bytes = _make_mock_audio(duration_ms=500)
        return TTSResult(
            request=request,
            audio=AudioData(data=audio_bytes, format=AudioFormat.WAV),
            duration_ms=500,
            latency_ms=100,
        )

    provider.synthesize = AsyncMock(side_effect=mock_synthesize)
    return provider


class TestSynthesizeLongTextBasic:
    """Basic integration tests for long text synthesis."""

    @pytest.mark.asyncio
    async def test_three_segments_merge_correctly(self) -> None:
        """Text that splits into 3 segments produces merged audio with timings."""
        provider = _create_mock_provider("gemini")
        use_case = SynthesizeLongText(provider=provider)

        # ~1500 CJK chars = ~4500 bytes, well above Gemini's 4000 byte limit
        text = "。".join(["這是一段測試用的長句子大約有二十個字"] * 75)

        result = await use_case.execute(
            text=text,
            voice_id="Kore",
            provider_name="gemini",
            output_format=AudioFormat.WAV,
        )

        assert result.segment_count >= 2
        assert result.audio_content
        assert result.content_type == "audio/wav"
        assert result.duration_ms > 0
        assert result.latency_ms > 0
        assert result.provider == "gemini"
        assert result.total_text_length == len(text)
        assert result.total_byte_length == len(text.encode("utf-8"))

        # Verify segment timings
        assert result.segment_timings is not None
        assert len(result.segment_timings) == result.segment_count
        for i, timing in enumerate(result.segment_timings):
            assert timing.turn_index == i
            assert timing.start_ms >= 0
            assert timing.end_ms > timing.start_ms

    @pytest.mark.asyncio
    async def test_style_prompt_applied_to_all_segments(self) -> None:
        """Style prompt is passed through to each synthesis request."""
        provider = _create_mock_provider("gemini")
        use_case = SynthesizeLongText(provider=provider)

        text = "。".join(["這是一段測試句子有二十個左右的字元"] * 75)

        await use_case.execute(
            text=text,
            voice_id="Kore",
            provider_name="gemini",
            output_format=AudioFormat.WAV,
            style_prompt="Speak calmly and slowly",
        )

        # Verify all synthesis calls got the style prompt
        for call_args in provider.synthesize.call_args_list:
            request = call_args[0][0]
            assert request.style_prompt == "Speak calmly and slowly"

    @pytest.mark.asyncio
    async def test_single_segment_returns_result(self) -> None:
        """Short text that doesn't need splitting still returns valid result."""
        provider = _create_mock_provider("azure")
        use_case = SynthesizeLongText(provider=provider)

        result = await use_case.execute(
            text="短文字",
            voice_id="zh-TW-HsiaoChenNeural",
            provider_name="azure",
            output_format=AudioFormat.WAV,
        )

        assert result.segment_count == 1
        assert result.audio_content
        assert provider.synthesize.call_count == 1


class TestSynthesizeLongTextStorage:
    """Tests for storage integration."""

    @pytest.mark.asyncio
    async def test_storage_path_set_when_storage_available(self) -> None:
        """Audio is stored and path is set when storage service is provided."""
        provider = _create_mock_provider("gemini")
        storage = AsyncMock()
        storage.save.return_value = "storage/gemini/test-uuid.mp3"

        use_case = SynthesizeLongText(provider=provider, storage=storage)

        text = "。".join(["這是一段測試句子有二十個左右的字元"] * 75)

        result = await use_case.execute(
            text=text,
            voice_id="Kore",
            provider_name="gemini",
            output_format=AudioFormat.WAV,
        )

        assert result.storage_path == "storage/gemini/test-uuid.mp3"
        storage.save.assert_called_once()


class TestSynthesizeLongTextErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_provider_error_propagates(self) -> None:
        """If provider fails on one segment, the error propagates."""
        provider = _create_mock_provider("gemini")
        provider.synthesize.side_effect = ValueError("Provider API error")

        use_case = SynthesizeLongText(provider=provider)

        text = "。".join(["這是一段測試句子有二十個左右的字元"] * 75)

        with pytest.raises(ValueError, match="Provider API error"):
            await use_case.execute(
                text=text,
                voice_id="Kore",
                provider_name="gemini",
            )

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self) -> None:
        """Empty text raises ValueError from TextSplitter."""
        provider = _create_mock_provider("gemini")
        use_case = SynthesizeLongText(provider=provider)

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await use_case.execute(
                text="",
                voice_id="Kore",
                provider_name="gemini",
            )
