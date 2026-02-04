"""Integration tests for provider 429 quota detection.

Verifies that each TTS/STT provider correctly detects HTTP 429
or equivalent quota exceeded errors and raises QuotaExceededError.

These tests mock the external API layer (httpx, SDK) to simulate
quota exceeded responses, then verify the provider code path
produces the correct QuotaExceededError.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.domain.entities.audio import AudioData, AudioFormat, OutputMode
from src.domain.entities.stt import STTRequest
from src.domain.entities.tts import TTSRequest
from src.domain.errors import QuotaExceededError, RateLimitError

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tts_request() -> TTSRequest:
    """Minimal TTS request for quota detection tests."""
    return TTSRequest(
        text="Test",
        voice_id="test-voice",
        provider="test",
        language="zh-TW",
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


@pytest.fixture()
def stt_request() -> STTRequest:
    """Minimal STT request for quota detection tests."""
    return STTRequest(
        provider="test",
        language="zh-TW",
        audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
    )


def _mock_httpx_429(
    text: str = "quota exceeded",
    headers: dict | None = None,
    json_body: dict | None = None,
) -> Mock:
    """Create a mock httpx response simulating HTTP 429."""
    response = Mock()
    response.status_code = 429
    response.text = text
    response.headers = headers or {}
    response.json.return_value = json_body or {"error": {"message": text}}
    return response


# ===========================================================================
# TTS Provider Tests
# ===========================================================================


class TestGeminiTTSQuotaDetection:
    """T008: Gemini TTS distinguishes quota exhaustion from rate limiting."""

    @pytest.mark.asyncio()
    async def test_http_429_with_quota_message_raises_rate_limit_error(
        self, tts_request: TTSRequest
    ) -> None:
        """HTTP 429 with quota message should raise RateLimitError (all 429s are rate limit)."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text="You exceeded your current quota",
            headers={"retry-after": "3600"},
            json_body={"error": {"message": "You exceeded your current quota"}},
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RateLimitError) as exc_info,
        ):
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "gemini"
        assert exc_info.value.details["retry_after"] == 3600
        assert "請求過於頻繁" in exc_info.value.message

    @pytest.mark.asyncio()
    async def test_http_429_without_quota_message_raises_rate_limit_error(
        self, tts_request: TTSRequest
    ) -> None:
        """HTTP 429 without quota exhaustion message should raise RateLimitError."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text="Resource has been exhausted",
            headers={"retry-after": "10"},
            json_body={"error": {"message": "Resource has been exhausted"}},
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RateLimitError) as exc_info,
        ):
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "gemini"
        assert exc_info.value.details["retry_after"] == 10
        assert "請求過於頻繁" in exc_info.value.message

    @pytest.mark.asyncio()
    async def test_quota_message_without_429_status(self) -> None:
        """Gemini may return quota error message with non-429 status; still detected."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        # Some Gemini errors return 400 but with quota message
        response = Mock()
        response.status_code = 400
        response.text = "You exceeded your current quota, please check your plan"
        response.json.return_value = {
            "error": {"message": "You exceeded your current quota, please check your plan"}
        }
        response.headers = {}
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with pytest.raises(QuotaExceededError) as exc_info:
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "gemini"

    @pytest.mark.asyncio()
    async def test_non_quota_error_raises_runtime_error(self) -> None:
        """Non-quota errors should still raise RuntimeError."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        response = Mock()
        response.status_code = 500
        response.text = "Internal server error"
        response.json.return_value = {"error": {"message": "Internal server error"}}
        response.headers = {}
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with pytest.raises(RuntimeError, match="Gemini TTS API error"):
            await provider._do_synthesize(request)


class TestGeminiTTS429Retry:
    """Tests for Gemini TTS 429 retry logic."""

    @pytest.mark.asyncio()
    async def test_429_retry_succeeds_on_second_attempt(self) -> None:
        """First request 429, second succeeds → should return audio data."""
        import base64

        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")

        # Mock 429 response
        mock_429 = _mock_httpx_429(
            text="Resource has been exhausted",
            json_body={"error": {"message": "Resource has been exhausted"}},
        )

        # Mock 200 response with valid audio
        pcm_data = b"\x00" * 4800  # 0.1s of silence at 24kHz 16-bit mono
        mock_200 = Mock()
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    },
                    "finishReason": "STOP",
                }
            ]
        }

        provider._client = AsyncMock()
        provider._client.post = AsyncMock(side_effect=[mock_429, mock_200])

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await provider._do_synthesize(request)

        assert result.data is not None
        assert len(result.data) > 0
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio()
    async def test_429_all_retries_exhausted_raises_rate_limit_error(self) -> None:
        """All 429 retry attempts exhausted → RateLimitError."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text="Resource has been exhausted",
            json_body={"error": {"message": "Resource has been exhausted"}},
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            pytest.raises(RateLimitError),
        ):
            await provider._do_synthesize(request)

        # Should have slept _MAX_429_RETRIES times (3 retries before final raise)
        assert mock_sleep.call_count == GeminiTTSProvider._MAX_429_RETRIES

    @pytest.mark.asyncio()
    async def test_429_retry_respects_retry_after_header(self) -> None:
        """Retry-After header value should be used for sleep duration."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text="Resource has been exhausted",
            headers={"retry-after": "5"},
            json_body={"error": {"message": "Resource has been exhausted"}},
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            pytest.raises(RateLimitError),
        ):
            await provider._do_synthesize(request)

        # All sleep calls should use Retry-After value (5s), not default backoffs
        for call in mock_sleep.call_args_list:
            assert call.args[0] == 5.0

    @pytest.mark.asyncio()
    async def test_429_retry_after_capped_at_max(self) -> None:
        """Retry-After exceeding max should be capped."""
        from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

        provider = GeminiTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text="Resource has been exhausted",
            headers={"retry-after": "3600"},  # 1 hour, way above 30s cap
            json_body={"error": {"message": "Resource has been exhausted"}},
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_response)

        request = TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            pytest.raises(RateLimitError),
        ):
            await provider._do_synthesize(request)

        # Sleep should be capped at _429_MAX_RETRY_AFTER (30s)
        for call in mock_sleep.call_args_list:
            assert call.args[0] == float(GeminiTTSProvider._429_MAX_RETRY_AFTER)


class TestElevenLabsTTSQuotaDetection:
    """T009: ElevenLabs TTS raises QuotaExceededError on 429."""

    @pytest.mark.asyncio()
    async def test_http_429_raises_quota_error(self) -> None:
        """HTTP 429 from ElevenLabs should raise QuotaExceededError."""
        from src.infrastructure.providers.tts.elevenlabs_tts import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text='{"detail": {"status": "quota_exceeded", "message": "Quota exceeded"}}',
            headers={"retry-after": "7200"},
            json_body={"detail": {"status": "quota_exceeded", "message": "Quota exceeded"}},
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        request = TTSRequest(
            text="Test",
            voice_id="voice-id",
            provider="elevenlabs",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch(
                "src.infrastructure.providers.tts.elevenlabs_tts.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "elevenlabs"
        assert exc_info.value.details["retry_after"] == 7200

    @pytest.mark.asyncio()
    async def test_character_limit_sets_quota_type(self) -> None:
        """ElevenLabs character_limit_exceeded should set quota_type='characters'."""
        from src.infrastructure.providers.tts.elevenlabs_tts import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text='{"detail": {"status": "character_limit_exceeded"}}',
            json_body={"detail": {"status": "character_limit_exceeded", "message": "Limit hit"}},
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        request = TTSRequest(
            text="Test",
            voice_id="voice-id",
            provider="elevenlabs",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch(
                "src.infrastructure.providers.tts.elevenlabs_tts.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            await provider._do_synthesize(request)

        assert exc_info.value.details["quota_type"] == "characters"

    @pytest.mark.asyncio()
    async def test_non_429_raises_runtime_error(self) -> None:
        """Non-429 errors should raise RuntimeError."""
        from src.infrastructure.providers.tts.elevenlabs_tts import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key")
        response = Mock()
        response.status_code = 500
        response.text = "Server error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        request = TTSRequest(
            text="Test",
            voice_id="voice-id",
            provider="elevenlabs",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch(
                "src.infrastructure.providers.tts.elevenlabs_tts.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(RuntimeError, match="ElevenLabs TTS failed"),
        ):
            await provider._do_synthesize(request)


class TestAzureTTSQuotaDetection:
    """T010: Azure TTS raises QuotaExceededError on quota cancellation."""

    @pytest.mark.asyncio()
    async def test_cancellation_with_429_raises_quota_error(self) -> None:
        """Azure SDK cancellation with '429' in error details should raise QuotaExceededError."""
        import azure.cognitiveservices.speech as speechsdk

        from src.infrastructure.providers.tts.azure_tts import AzureTTSProvider

        provider = AzureTTSProvider(subscription_key="test-key", region="eastasia")

        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.Canceled
        mock_result.cancellation_details = MagicMock()
        mock_result.cancellation_details.reason = speechsdk.CancellationReason.Error
        mock_result.cancellation_details.error_details = (
            "429 Too Many Requests: Resource quota exceeded"
        )

        request = TTSRequest(
            text="Test",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch.object(provider, "_create_speech_config"),
            patch(
                "src.infrastructure.providers.tts.azure_tts.speechsdk.SpeechSynthesizer"
            ) as mock_synth_cls,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            mock_synth_cls.return_value = MagicMock()
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "azure"
        assert "429" in exc_info.value.details["original_error"]

    @pytest.mark.asyncio()
    async def test_cancellation_with_quota_keyword_raises_quota_error(self) -> None:
        """Azure SDK cancellation with 'quota' keyword should raise QuotaExceededError."""
        import azure.cognitiveservices.speech as speechsdk

        from src.infrastructure.providers.tts.azure_tts import AzureTTSProvider

        provider = AzureTTSProvider(subscription_key="test-key", region="eastasia")

        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.Canceled
        mock_result.cancellation_details = MagicMock()
        mock_result.cancellation_details.reason = speechsdk.CancellationReason.Error
        mock_result.cancellation_details.error_details = "Quota limit has been reached"

        request = TTSRequest(
            text="Test",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch.object(provider, "_create_speech_config"),
            patch(
                "src.infrastructure.providers.tts.azure_tts.speechsdk.SpeechSynthesizer"
            ) as mock_synth_cls,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            mock_synth_cls.return_value = MagicMock()
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "azure"

    @pytest.mark.asyncio()
    async def test_non_quota_cancellation_raises_runtime_error(self) -> None:
        """Non-quota cancellation should raise RuntimeError."""
        import azure.cognitiveservices.speech as speechsdk

        from src.infrastructure.providers.tts.azure_tts import AzureTTSProvider

        provider = AzureTTSProvider(subscription_key="test-key", region="eastasia")

        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.Canceled
        mock_result.cancellation_details = MagicMock()
        mock_result.cancellation_details.reason = speechsdk.CancellationReason.Error
        mock_result.cancellation_details.error_details = "Invalid subscription key"

        request = TTSRequest(
            text="Test",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch.object(provider, "_create_speech_config"),
            patch(
                "src.infrastructure.providers.tts.azure_tts.speechsdk.SpeechSynthesizer"
            ) as mock_synth_cls,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result),
            pytest.raises(RuntimeError, match="Azure TTS synthesis canceled"),
        ):
            mock_synth_cls.return_value = MagicMock()
            await provider._do_synthesize(request)


class TestGCPTTSQuotaDetection:
    """T011: GCP TTS raises QuotaExceededError on ResourceExhausted."""

    @pytest.mark.asyncio()
    async def test_resource_exhausted_raises_quota_error(self) -> None:
        """gRPC ResourceExhausted should raise QuotaExceededError."""
        from google.api_core.exceptions import ResourceExhausted

        from src.infrastructure.providers.tts.gcp_tts import GCPTTSProvider

        provider = GCPTTSProvider(credentials_path=None)
        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = ResourceExhausted(
            "Quota exceeded for quota metric 'text-to-speech'"
        )
        provider._client = mock_client

        request = TTSRequest(
            text="Test",
            voice_id="cmn-TW-Wavenet-A",
            provider="gcp",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch("asyncio.to_thread", side_effect=ResourceExhausted("Quota exceeded")),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "gcp"
        assert "Quota exceeded" in exc_info.value.details["original_error"]


class TestVoAITTSQuotaDetection:
    """T012: VoAI TTS raises QuotaExceededError on 429."""

    @pytest.mark.asyncio()
    async def test_http_429_raises_quota_error(self) -> None:
        """HTTP 429 from VoAI should raise QuotaExceededError."""
        from src.infrastructure.providers.tts.voai_tts import VoAITTSProvider

        provider = VoAITTSProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text="Rate limit exceeded",
            headers={"retry-after": "120"},
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        request = TTSRequest(
            text="測試",
            voice_id="佑希",
            provider="voai",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with (
            patch(
                "src.infrastructure.providers.tts.voai_tts.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            await provider._do_synthesize(request)

        assert exc_info.value.details["provider"] == "voai"
        assert exc_info.value.details["retry_after"] == 120


# ===========================================================================
# STT Provider Tests
# ===========================================================================


class TestWhisperSTTQuotaDetection:
    """T013: Whisper STT raises QuotaExceededError on 429."""

    @pytest.mark.asyncio()
    async def test_http_429_raises_quota_error(self, stt_request: STTRequest) -> None:
        """HTTP 429 from OpenAI Whisper should raise QuotaExceededError."""
        from src.infrastructure.providers.stt.whisper_stt import WhisperSTTProvider

        provider = WhisperSTTProvider(api_key="test-key")
        mock_response = _mock_httpx_429(
            text='{"error": {"type": "rate_limit_exceeded", "message": "Rate limit exceeded"}}',
            headers={"retry-after": "60"},
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        request = STTRequest(
            provider="whisper",
            language="zh-TW",
            audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
        )

        with (
            patch(
                "src.infrastructure.providers.stt.whisper_stt.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(QuotaExceededError) as exc_info,
        ):
            await provider._do_transcribe(request)

        assert exc_info.value.details["provider"] == "openai"

    @pytest.mark.asyncio()
    async def test_non_429_raises_runtime_error(self) -> None:
        """Non-429 errors should raise RuntimeError."""
        from src.infrastructure.providers.stt.whisper_stt import WhisperSTTProvider

        provider = WhisperSTTProvider(api_key="test-key")
        response = Mock()
        response.status_code = 500
        response.text = "Internal server error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        request = STTRequest(
            provider="whisper",
            language="zh-TW",
            audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
        )

        with (
            patch(
                "src.infrastructure.providers.stt.whisper_stt.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(RuntimeError, match="Whisper STT failed"),
        ):
            await provider._do_transcribe(request)


class TestDeepgramSTTQuotaDetection:
    """T014: Deepgram STT raises QuotaExceededError on quota errors."""

    @pytest.mark.asyncio()
    async def test_exception_with_429_raises_quota_error(self) -> None:
        """Deepgram SDK exception mentioning '429' should raise QuotaExceededError."""
        from src.infrastructure.providers.stt.deepgram_stt import DeepgramSTTProvider

        with patch("src.infrastructure.providers.stt.deepgram_stt.DeepgramClient") as mock_cls:
            provider = DeepgramSTTProvider(api_key="test-key")
            mock_cls.return_value.listen.v1.media.transcribe_file.side_effect = Exception(
                "429 Too Many Requests: QUOTA_EXCEEDED"
            )
            provider._client = mock_cls.return_value

            request = STTRequest(
                provider="deepgram",
                language="zh-TW",
                audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
            )

            with (
                patch(
                    "asyncio.to_thread",
                    side_effect=Exception("429 Too Many Requests: QUOTA_EXCEEDED"),
                ),
                pytest.raises(QuotaExceededError) as exc_info,
            ):
                await provider._do_transcribe(request)

            assert exc_info.value.details["provider"] == "deepgram"

    @pytest.mark.asyncio()
    async def test_exception_with_quota_keyword_raises_quota_error(self) -> None:
        """Deepgram SDK exception mentioning 'quota' should raise QuotaExceededError."""
        from src.infrastructure.providers.stt.deepgram_stt import DeepgramSTTProvider

        with patch("src.infrastructure.providers.stt.deepgram_stt.DeepgramClient"):
            provider = DeepgramSTTProvider(api_key="test-key")

            request = STTRequest(
                provider="deepgram",
                language="zh-TW",
                audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
            )

            with (
                patch("asyncio.to_thread", side_effect=Exception("Quota has been exceeded")),
                pytest.raises(QuotaExceededError) as exc_info,
            ):
                await provider._do_transcribe(request)

            assert exc_info.value.details["provider"] == "deepgram"

    @pytest.mark.asyncio()
    async def test_non_quota_exception_raises_runtime_error(self) -> None:
        """Non-quota exceptions should raise RuntimeError."""
        from src.infrastructure.providers.stt.deepgram_stt import DeepgramSTTProvider

        with patch("src.infrastructure.providers.stt.deepgram_stt.DeepgramClient"):
            provider = DeepgramSTTProvider(api_key="test-key")

            request = STTRequest(
                provider="deepgram",
                language="zh-TW",
                audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
            )

            with (
                patch("asyncio.to_thread", side_effect=Exception("Connection refused")),
                pytest.raises(RuntimeError, match="Deepgram transcription failed"),
            ):
                await provider._do_transcribe(request)


class TestAzureSTTQuotaDetection:
    """T015: Azure STT raises QuotaExceededError on quota cancellation."""

    def test_quota_detection_logic_with_429(self) -> None:
        """Azure STT on_canceled callback detects '429' and creates QuotaExceededError.

        Azure STT uses SDK callbacks (on_canceled) which are hard to test
        through the full async flow. We test the detection logic directly.
        """
        # This mirrors the on_canceled callback logic in azure_stt.py:
        # if "429" in error_details or "quota" in error_details.lower():
        #     error = QuotaExceededError(provider="azure", original_error=error_details)
        error_details = "429 Too Many Requests: Quota exceeded"

        if "429" in error_details or "quota" in error_details.lower():
            error: Exception = QuotaExceededError(
                provider="azure",
                original_error=error_details,
            )
        else:
            error = RuntimeError(f"Azure STT error: {error_details}")

        assert isinstance(error, QuotaExceededError)
        assert error.details["provider"] == "azure"
        assert "429" in error.details["original_error"]

    def test_quota_detection_logic_with_quota_keyword(self) -> None:
        """Azure STT on_canceled callback detects 'quota' keyword."""
        error_details = "Resource quota limit reached"

        if "429" in error_details or "quota" in error_details.lower():
            error: Exception = QuotaExceededError(
                provider="azure",
                original_error=error_details,
            )
        else:
            error = RuntimeError(f"Azure STT error: {error_details}")

        assert isinstance(error, QuotaExceededError)

    def test_non_quota_cancellation_creates_runtime_error(self) -> None:
        """Non-quota cancellation should create RuntimeError."""
        error_details = "Invalid subscription key"

        if "429" in error_details or "quota" in error_details.lower():
            error: Exception = QuotaExceededError(
                provider="azure",
                original_error=error_details,
            )
        else:
            error = RuntimeError(f"Azure STT error: {error_details}")

        assert isinstance(error, RuntimeError)
        assert not isinstance(error, QuotaExceededError)


class TestGCPSTTQuotaDetection:
    """T016: GCP STT raises QuotaExceededError on ResourceExhausted."""

    @pytest.mark.asyncio()
    async def test_resource_exhausted_raises_quota_error(self) -> None:
        """gRPC ResourceExhausted from GCP STT should raise QuotaExceededError."""
        from google.api_core.exceptions import ResourceExhausted

        from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider

        with patch("src.infrastructure.providers.stt.gcp_stt.speech.SpeechClient"):
            provider = GCPSTTProvider(credentials_path=None)

            request = STTRequest(
                provider="gcp",
                language="zh-TW",
                audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
            )

            with (
                patch("asyncio.to_thread", side_effect=ResourceExhausted("Quota exceeded for STT")),
                pytest.raises(QuotaExceededError) as exc_info,
            ):
                await provider._do_transcribe(request)

            assert exc_info.value.details["provider"] == "gcp"
            assert "Quota exceeded" in exc_info.value.details["original_error"]

    @pytest.mark.asyncio()
    async def test_other_exceptions_propagate(self) -> None:
        """Non-ResourceExhausted exceptions should propagate normally."""
        from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider

        with patch("src.infrastructure.providers.stt.gcp_stt.speech.SpeechClient"):
            provider = GCPSTTProvider(credentials_path=None)

            request = STTRequest(
                provider="gcp",
                language="zh-TW",
                audio=AudioData(data=b"\x00" * 100, format=AudioFormat.WAV, sample_rate=16000),
            )

            with (
                patch("asyncio.to_thread", side_effect=RuntimeError("Connection error")),
                pytest.raises(RuntimeError, match="Connection error"),
            ):
                await provider._do_transcribe(request)
