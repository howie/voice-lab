"""Unit tests for QuotaExceededError propagation through SynthesizeSpeech.

Verifies that QuotaExceededError raised by a TTS provider passes through
the SynthesizeSpeech use case without being re-wrapped as SynthesisError,
while other exceptions are still properly converted.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.synthesize_speech import SynthesizeSpeech
from src.domain.entities.audio import AudioData, AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.errors import ProviderError, QuotaExceededError, SynthesisError


@pytest.fixture()
def tts_request() -> TTSRequest:
    """Minimal TTS request for propagation tests."""
    return TTSRequest(
        text="Test",
        voice_id="test-voice",
        provider="gemini",
        language="zh-TW",
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


@pytest.fixture()
def mock_tts_result(tts_request: TTSRequest) -> TTSResult:
    """Successful TTS result."""
    return TTSResult(
        request=tts_request,
        audio=AudioData(data=b"\x00" * 100, format=AudioFormat.MP3),
        duration_ms=1000,
        latency_ms=200,
    )


@pytest.fixture()
def quota_error() -> QuotaExceededError:
    """QuotaExceededError with full Gemini details."""
    return QuotaExceededError(
        provider="gemini",
        quota_type="rpm",
        retry_after=3600,
        original_error="You exceeded your current quota",
    )


class TestBatchQuotaPropagation:
    """Tests for QuotaExceededError propagation through execute() (batch mode)."""

    @pytest.mark.asyncio()
    async def test_quota_error_propagates_unchanged(
        self, tts_request: TTSRequest, quota_error: QuotaExceededError
    ) -> None:
        """QuotaExceededError from provider must pass through without re-wrapping."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = quota_error

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(QuotaExceededError) as exc_info:
            await use_case.execute(tts_request)

        # Must be the exact same exception
        assert exc_info.value is quota_error
        assert exc_info.value.details["provider"] == "gemini"
        assert exc_info.value.details["retry_after"] == 3600
        assert exc_info.value.details["quota_type"] == "rpm"
        assert exc_info.value.details["original_error"] == "You exceeded your current quota"

    @pytest.mark.asyncio()
    async def test_quota_error_not_wrapped_as_synthesis_error(
        self, tts_request: TTSRequest
    ) -> None:
        """QuotaExceededError must NOT be caught by generic Exception handler."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = QuotaExceededError(
            provider="gemini",
            original_error="quota exceeded",
        )

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(QuotaExceededError):
            await use_case.execute(tts_request)

        # If it were wrapped, it would be SynthesisError instead

    @pytest.mark.asyncio()
    async def test_quota_error_preserves_details_with_storage(
        self, tts_request: TTSRequest, quota_error: QuotaExceededError
    ) -> None:
        """QuotaExceededError propagates even when storage is configured."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = quota_error
        mock_storage = AsyncMock()

        use_case = SynthesizeSpeech(provider=mock_provider, storage=mock_storage)

        with pytest.raises(QuotaExceededError) as exc_info:
            await use_case.execute(tts_request)

        assert exc_info.value is quota_error
        # Storage.save should NOT have been called
        mock_storage.save.assert_not_called()

    @pytest.mark.asyncio()
    async def test_quota_error_preserves_details_with_logger(
        self, tts_request: TTSRequest, quota_error: QuotaExceededError
    ) -> None:
        """QuotaExceededError propagates without logging (logger only for generic errors)."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = quota_error
        mock_logger = AsyncMock()

        use_case = SynthesizeSpeech(provider=mock_provider, logger=mock_logger)

        with pytest.raises(QuotaExceededError) as exc_info:
            await use_case.execute(tts_request)

        assert exc_info.value is quota_error
        # Logger should NOT be called for quota errors (they re-raise before logging)
        mock_logger.log_synthesis.assert_not_called()

    @pytest.mark.asyncio()
    async def test_generic_error_becomes_synthesis_error(self, tts_request: TTSRequest) -> None:
        """Non-quota exceptions should still be wrapped as SynthesisError."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = RuntimeError("unexpected failure")

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(SynthesisError) as exc_info:
            await use_case.execute(tts_request)

        assert "unexpected failure" in str(exc_info.value)

    @pytest.mark.asyncio()
    async def test_timeout_error_becomes_provider_error(self, tts_request: TTSRequest) -> None:
        """Timeout-related errors should become ProviderError."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = RuntimeError("Connection timeout occurred")

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(ProviderError):
            await use_case.execute(tts_request)

    @pytest.mark.asyncio()
    async def test_unavailable_error_becomes_provider_error(self, tts_request: TTSRequest) -> None:
        """'unavailable' errors should become ProviderError."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.side_effect = RuntimeError("Service unavailable")

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(ProviderError):
            await use_case.execute(tts_request)

    @pytest.mark.asyncio()
    async def test_successful_synthesis_works(
        self, tts_request: TTSRequest, mock_tts_result: TTSResult
    ) -> None:
        """Verify normal flow still works (sanity check)."""
        mock_provider = AsyncMock()
        mock_provider.synthesize.return_value = mock_tts_result

        use_case = SynthesizeSpeech(provider=mock_provider)
        result = await use_case.execute(tts_request)

        assert result is mock_tts_result


class TestStreamingQuotaPropagation:
    """Tests for QuotaExceededError propagation through execute_stream()."""

    @pytest.mark.asyncio()
    async def test_quota_error_propagates_in_stream(
        self, tts_request: TTSRequest, quota_error: QuotaExceededError
    ) -> None:
        """QuotaExceededError during streaming must propagate unchanged."""
        mock_provider = MagicMock()

        async def failing_stream(_request: TTSRequest) -> AsyncGenerator[bytes, None]:
            raise quota_error
            yield  # noqa: RET503 — unreachable but needed for generator type

        mock_provider.synthesize_stream = failing_stream

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(QuotaExceededError) as exc_info:
            async for _chunk in use_case.execute_stream(tts_request):
                pass

        assert exc_info.value is quota_error
        assert exc_info.value.details["provider"] == "gemini"

    @pytest.mark.asyncio()
    async def test_generic_error_in_stream_becomes_synthesis_error(
        self, tts_request: TTSRequest
    ) -> None:
        """Non-quota errors during streaming should become SynthesisError."""
        mock_provider = MagicMock()

        async def failing_stream(_request: TTSRequest) -> AsyncGenerator[bytes, None]:
            raise RuntimeError("stream broke")
            yield  # noqa: RET503

        mock_provider.synthesize_stream = failing_stream

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(SynthesisError):
            async for _chunk in use_case.execute_stream(tts_request):
                pass

    @pytest.mark.asyncio()
    async def test_quota_error_mid_stream_propagates(
        self, tts_request: TTSRequest, quota_error: QuotaExceededError
    ) -> None:
        """QuotaExceededError raised after partial data should still propagate."""
        mock_provider = MagicMock()
        chunks_received: list[bytes] = []

        async def partial_stream(_request: TTSRequest) -> AsyncGenerator[bytes, None]:
            yield b"\x00" * 100
            yield b"\x01" * 100
            raise quota_error

        mock_provider.synthesize_stream = partial_stream

        use_case = SynthesizeSpeech(provider=mock_provider)

        with pytest.raises(QuotaExceededError) as exc_info:
            async for chunk in use_case.execute_stream(tts_request):
                chunks_received.append(chunk)

        # Got partial data before the error
        assert len(chunks_received) == 2
        assert exc_info.value is quota_error
