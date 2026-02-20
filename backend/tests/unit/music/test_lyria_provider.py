"""Unit tests for LyriaMusicProvider.

Feature: 016-integration-gemini-lyria-music
Tests verify that LyriaMusicProvider correctly implements IMusicProvider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.interfaces.music_provider import MusicSubmitResult, MusicTaskStatus
from src.infrastructure.adapters.lyria.client import LyriaGenerationResult
from src.infrastructure.providers.music.lyria_music import (
    LyriaMusicProvider,
    NotSupportedError,
)


# Minimal WAV for testing
def _make_wav_bytes() -> bytes:
    import struct

    sample_rate = 48000
    data_size = 200
    wav = bytearray()
    wav.extend(b"RIFF")
    wav.extend(struct.pack("<I", data_size + 36))
    wav.extend(b"WAVE")
    wav.extend(b"fmt ")
    wav.extend(struct.pack("<I", 16))
    wav.extend(struct.pack("<H", 1))
    wav.extend(struct.pack("<H", 1))
    wav.extend(struct.pack("<I", sample_rate))
    wav.extend(struct.pack("<I", sample_rate * 2))
    wav.extend(struct.pack("<H", 2))
    wav.extend(struct.pack("<H", 16))
    wav.extend(b"data")
    wav.extend(struct.pack("<I", data_size))
    wav.extend(b"\x00" * data_size)
    return bytes(wav)


WAV_BYTES = _make_wav_bytes()


@pytest.fixture
def provider() -> LyriaMusicProvider:
    """Create a LyriaMusicProvider with mocked client."""
    with (
        patch("src.infrastructure.adapters.lyria.client.google.auth.default") as mock_auth,
        patch("src.infrastructure.adapters.lyria.client.get_settings") as mock_settings,
    ):
        mock_creds = MagicMock()
        mock_creds.token = "test-token"
        mock_auth.return_value = (mock_creds, "test-project")

        settings = MagicMock()
        settings.lyria_gcp_project_id = "test-project"
        settings.lyria_gcp_location = "us-central1"
        settings.lyria_model = "lyria-002"
        settings.lyria_timeout = 30.0
        settings.gcp_project_id = "test-project"
        mock_settings.return_value = settings

        return LyriaMusicProvider(
            project_id="test-project",
            location="us-central1",
            model="lyria-002",
            timeout=30.0,
        )


class TestLyriaMusicProviderProperties:
    """Verify provider properties."""

    def test_name(self, provider: LyriaMusicProvider) -> None:
        assert provider.name == "lyria"

    def test_display_name(self, provider: LyriaMusicProvider) -> None:
        assert provider.display_name == "Google Lyria"

    def test_capabilities(self, provider: LyriaMusicProvider) -> None:
        assert provider.capabilities == ["instrumental"]


class TestLyriaMusicProviderUnsupported:
    """Verify NotSupportedError for unsupported operations."""

    @pytest.mark.asyncio
    async def test_generate_song_raises(self, provider: LyriaMusicProvider) -> None:
        with pytest.raises(NotSupportedError, match="song"):
            await provider.generate_song(prompt="test")

    @pytest.mark.asyncio
    async def test_generate_lyrics_raises(self, provider: LyriaMusicProvider) -> None:
        with pytest.raises(NotSupportedError, match="lyrics"):
            await provider.generate_lyrics(prompt="test")


class TestLyriaMusicProviderGenerateInstrumental:
    """T014: Verify generate_instrumental returns MusicSubmitResult."""

    @pytest.mark.asyncio
    async def test_returns_completed_result(self, provider: LyriaMusicProvider) -> None:
        """Lyria synchronous API should return COMPLETED status."""
        mock_results = [LyriaGenerationResult(audio_content=WAV_BYTES)]
        provider._client.generate_instrumental = AsyncMock(return_value=mock_results)

        result = await provider.generate_instrumental(prompt="calm guitar")

        assert isinstance(result, MusicSubmitResult)
        assert result.status == MusicTaskStatus.COMPLETED
        assert result.provider == "lyria"
        assert result.task_id  # Should be a UUID string
        assert result.audio_bytes is not None
        assert len(result.audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_returns_mp3_or_wav(self, provider: LyriaMusicProvider) -> None:
        """WAV should be converted to MP3 (or fall back to WAV if ffmpeg unavailable)."""
        mock_results = [LyriaGenerationResult(audio_content=WAV_BYTES)]
        provider._client.generate_instrumental = AsyncMock(return_value=mock_results)

        result = await provider.generate_instrumental(prompt="piano")

        assert result.file_ext in ("mp3", "wav")
        assert result.audio_bytes is not None

    @pytest.mark.asyncio
    async def test_wav_fallback_on_conversion_failure(self, provider: LyriaMusicProvider) -> None:
        """EC-004: If MP3 conversion fails, fall back to WAV."""
        mock_results = [LyriaGenerationResult(audio_content=WAV_BYTES)]
        provider._client.generate_instrumental = AsyncMock(return_value=mock_results)

        with patch(
            "src.infrastructure.providers.music.lyria_music.convert_wav_to_mp3",
            side_effect=Exception("ffmpeg not found"),
        ):
            result = await provider.generate_instrumental(prompt="test")

        assert result.file_ext == "wav"
        assert result.audio_bytes == WAV_BYTES

    @pytest.mark.asyncio
    async def test_returns_failed_on_empty_results(self, provider: LyriaMusicProvider) -> None:
        """Empty results from API should return FAILED status."""
        provider._client.generate_instrumental = AsyncMock(return_value=[])

        result = await provider.generate_instrumental(prompt="test")

        assert result.status == MusicTaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_passes_negative_prompt(self, provider: LyriaMusicProvider) -> None:
        """Negative prompt should be forwarded to client."""
        mock_results = [LyriaGenerationResult(audio_content=WAV_BYTES)]
        provider._client.generate_instrumental = AsyncMock(return_value=mock_results)

        await provider.generate_instrumental(
            prompt="guitar",
            negative_prompt="drums",
        )

        provider._client.generate_instrumental.assert_called_once_with(
            prompt="guitar",
            negative_prompt="drums",
            seed=None,
            sample_count=None,
        )

    @pytest.mark.asyncio
    async def test_passes_seed(self, provider: LyriaMusicProvider) -> None:
        """Seed should be forwarded to client."""
        mock_results = [LyriaGenerationResult(audio_content=WAV_BYTES)]
        provider._client.generate_instrumental = AsyncMock(return_value=mock_results)

        await provider.generate_instrumental(prompt="piano", seed=42)

        provider._client.generate_instrumental.assert_called_once_with(
            prompt="piano",
            negative_prompt=None,
            seed=42,
            sample_count=None,
        )

    @pytest.mark.asyncio
    async def test_duration_ms_from_result(self, provider: LyriaMusicProvider) -> None:
        """Duration should come from LyriaGenerationResult."""
        mock_results = [LyriaGenerationResult(audio_content=WAV_BYTES, duration_ms=32800)]
        provider._client.generate_instrumental = AsyncMock(return_value=mock_results)

        result = await provider.generate_instrumental(prompt="test")

        assert result.duration_ms == 32800


class TestLyriaMusicProviderQueryTask:
    """T021: Verify query_task always returns COMPLETED."""

    @pytest.mark.asyncio
    async def test_query_task_returns_completed(self, provider: LyriaMusicProvider) -> None:
        result = await provider.query_task("some-task-id", "instrumental")

        assert result.status == MusicTaskStatus.COMPLETED
        assert result.provider == "lyria"
        assert result.task_id == "some-task-id"
