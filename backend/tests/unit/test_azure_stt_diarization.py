"""Unit tests for Azure STT Speaker Diarization.

Tests the ConversationTranscriber-based diarization path and
the _build_speaker_segments() aggregation logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.stt import SpeakerSegment, STTRequest, WordTiming
from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider
from src.infrastructure.providers.stt.base import BaseSTTProvider

# ============================================================
# _build_speaker_segments() tests
# ============================================================


class TestBuildSpeakerSegments:
    """Test the static _build_speaker_segments helper."""

    def test_empty_words_returns_empty(self) -> None:
        result = BaseSTTProvider._build_speaker_segments([])
        assert result == []

    def test_no_speaker_id_returns_empty(self) -> None:
        words = [
            WordTiming(word="hello", start_ms=0, end_ms=500),
            WordTiming(word="world", start_ms=500, end_ms=1000),
        ]
        result = BaseSTTProvider._build_speaker_segments(words)
        assert result == []

    def test_single_speaker(self) -> None:
        words = [
            WordTiming(word="hello", start_ms=0, end_ms=500, speaker_id="Guest-1"),
            WordTiming(word="world", start_ms=500, end_ms=1000, speaker_id="Guest-1"),
        ]
        result = BaseSTTProvider._build_speaker_segments(words)
        assert len(result) == 1
        assert result[0] == SpeakerSegment(
            speaker_id="Guest-1", text="hello world", start_ms=0, end_ms=1000
        )

    def test_multiple_speakers(self) -> None:
        words = [
            WordTiming(word="你好", start_ms=0, end_ms=500, speaker_id="Guest-1"),
            WordTiming(word="請問", start_ms=500, end_ms=1000, speaker_id="Guest-1"),
            WordTiming(word="我想", start_ms=1500, end_ms=2000, speaker_id="Guest-2"),
            WordTiming(word="查詢", start_ms=2000, end_ms=2500, speaker_id="Guest-2"),
            WordTiming(word="好的", start_ms=3000, end_ms=3500, speaker_id="Guest-1"),
        ]
        result = BaseSTTProvider._build_speaker_segments(words)
        assert len(result) == 3
        assert result[0].speaker_id == "Guest-1"
        assert result[0].text == "你好 請問"
        assert result[0].start_ms == 0
        assert result[0].end_ms == 1000
        assert result[1].speaker_id == "Guest-2"
        assert result[1].text == "我想 查詢"
        assert result[2].speaker_id == "Guest-1"
        assert result[2].text == "好的"

    def test_mixed_speaker_id_and_none(self) -> None:
        """Words without speaker_id are skipped; same-speaker continuity preserved."""
        words = [
            WordTiming(word="hello", start_ms=0, end_ms=500, speaker_id="Guest-1"),
            WordTiming(word="noise", start_ms=500, end_ms=800),  # no speaker_id — skipped
            WordTiming(word="world", start_ms=800, end_ms=1200, speaker_id="Guest-1"),
        ]
        result = BaseSTTProvider._build_speaker_segments(words)
        # None words are skipped but don't break the current speaker run
        assert len(result) == 1
        assert result[0].text == "hello world"
        assert result[0].start_ms == 0
        assert result[0].end_ms == 1200


# ============================================================
# Azure diarization routing tests
# ============================================================


class TestAzureDiarizationRouting:
    """Test that enable_diarization routes to ConversationTranscriber."""

    @pytest.fixture()
    def provider(self) -> AzureSTTProvider:
        return AzureSTTProvider(subscription_key="test-key", region="eastasia")

    def test_supports_diarization_property(self, provider: AzureSTTProvider) -> None:
        assert provider.supports_diarization is True

    @patch("src.infrastructure.providers.stt.azure_stt.speechsdk")
    async def test_diarization_false_uses_speech_recognizer(
        self, mock_sdk: MagicMock, provider: AzureSTTProvider
    ) -> None:
        """When enable_diarization=False, _recognize is called (not _recognize_with_diarization)."""
        from src.domain.entities.audio import AudioData, AudioFormat

        with (
            patch.object(provider, "_recognize", new_callable=AsyncMock) as mock_recognize,
            patch.object(
                provider, "_recognize_with_diarization", new_callable=AsyncMock
            ) as mock_diarize,
        ):
            mock_recognize.return_value = ("hello", None, None)

            # Use a real AudioData with WAV format to skip _convert_to_wav
            audio = AudioData(data=b"RIFF" + b"\x00" * 100, format=AudioFormat.WAV)
            request = STTRequest(
                provider="azure",
                language="zh-TW",
                audio=audio,
                enable_diarization=False,
            )

            await provider._do_transcribe(request)
            mock_recognize.assert_called_once()
            mock_diarize.assert_not_called()

    @patch("src.infrastructure.providers.stt.azure_stt.speechsdk")
    async def test_diarization_true_uses_conversation_transcriber(
        self, mock_sdk: MagicMock, provider: AzureSTTProvider
    ) -> None:
        """When enable_diarization=True, _recognize_with_diarization is called."""
        from src.domain.entities.audio import AudioData, AudioFormat

        with (
            patch.object(provider, "_recognize", new_callable=AsyncMock) as mock_recognize,
            patch.object(
                provider, "_recognize_with_diarization", new_callable=AsyncMock
            ) as mock_diarize,
        ):
            mock_diarize.return_value = ("hello", None, None)

            audio = AudioData(data=b"RIFF" + b"\x00" * 100, format=AudioFormat.WAV)
            request = STTRequest(
                provider="azure",
                language="zh-TW",
                audio=audio,
                enable_diarization=True,
            )

            await provider._do_transcribe(request)
            mock_diarize.assert_called_once()
            mock_recognize.assert_not_called()


# ============================================================
# API schema serialization tests
# ============================================================


class TestSpeakerSchemas:
    """Test that speaker-related schemas serialize correctly."""

    def test_word_timing_response_with_speaker_id(self) -> None:
        from src.presentation.schemas.stt import WordTimingResponse

        resp = WordTimingResponse(
            word="hello",
            start_ms=0,
            end_ms=500,
            confidence=0.95,
            speaker_id="Guest-1",
        )
        data = resp.model_dump()
        assert data["speaker_id"] == "Guest-1"

    def test_word_timing_response_without_speaker_id(self) -> None:
        from src.presentation.schemas.stt import WordTimingResponse

        resp = WordTimingResponse(word="hello", start_ms=0, end_ms=500, confidence=0.95)
        data = resp.model_dump()
        assert data["speaker_id"] is None

    def test_speaker_segment_response(self) -> None:
        from src.presentation.schemas.stt import SpeakerSegmentResponse

        resp = SpeakerSegmentResponse(
            speaker_id="Guest-1",
            text="你好請問",
            start_ms=0,
            end_ms=1000,
        )
        data = resp.model_dump()
        assert data["speaker_id"] == "Guest-1"
        assert data["text"] == "你好請問"
        assert data["start_ms"] == 0
        assert data["end_ms"] == 1000

    def test_transcribe_response_with_speaker_segments(self) -> None:
        from src.presentation.schemas.stt import (
            SpeakerSegmentResponse,
            STTTranscribeResponse,
        )

        resp = STTTranscribeResponse(
            id="test-id",
            transcript="你好 請問",
            provider="azure",
            language="zh-TW",
            latency_ms=500,
            confidence=0.9,
            speaker_segments=[
                SpeakerSegmentResponse(
                    speaker_id="Guest-1", text="你好 請問", start_ms=0, end_ms=1000
                )
            ],
        )
        data = resp.model_dump()
        assert len(data["speaker_segments"]) == 1
        assert data["speaker_segments"][0]["speaker_id"] == "Guest-1"

    def test_transcribe_response_without_speaker_segments(self) -> None:
        from src.presentation.schemas.stt import STTTranscribeResponse

        resp = STTTranscribeResponse(
            id="test-id",
            transcript="你好",
            provider="azure",
            language="zh-TW",
            latency_ms=500,
            confidence=0.9,
        )
        data = resp.model_dump()
        assert data["speaker_segments"] is None

    def test_provider_response_with_diarization(self) -> None:
        from src.presentation.schemas.stt import STTProviderResponse

        resp = STTProviderResponse(
            name="azure",
            display_name="Azure Speech Services",
            supports_streaming=True,
            supports_child_mode=True,
            supports_diarization=True,
            max_duration_sec=600,
            max_file_size_mb=200,
            supported_formats=["wav"],
            supported_languages=["zh-TW"],
        )
        data = resp.model_dump()
        assert data["supports_diarization"] is True
