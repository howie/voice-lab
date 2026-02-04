"""Unit tests for Gemini TTS provider.

Tests for the Gemini TTS provider implementation including:
- Voice listing and retrieval
- Synthesis with style prompts
- PCM to audio format conversion
- Health check functionality
- Error code routing (each Gemini HTTP error → correct exception)
"""

import base64
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender
from src.domain.errors import QuotaExceededError, RateLimitError
from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider


@pytest.fixture
def gemini_provider() -> GeminiTTSProvider:
    """Create a Gemini TTS provider for testing."""
    return GeminiTTSProvider(api_key="test-api-key")


@pytest.fixture
def sample_request() -> TTSRequest:
    """Create a sample TTS request for testing."""
    return TTSRequest(
        text="Hello, this is a test.",
        voice_id="Kore",
        provider="gemini",
        language="zh-TW",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


@pytest.fixture
def sample_request_with_style() -> TTSRequest:
    """Create a sample TTS request with style prompt."""
    return TTSRequest(
        text="Hello, this is a test.",
        voice_id="Kore",
        provider="gemini",
        language="zh-TW",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
        style_prompt="Say this cheerfully with excitement",
    )


class TestGeminiTTSProvider:
    """Tests for Gemini TTS provider."""

    def test_provider_name(self, gemini_provider: GeminiTTSProvider):
        """Test provider name property."""
        assert gemini_provider.name == "gemini"

    def test_display_name(self, gemini_provider: GeminiTTSProvider):
        """Test display name property."""
        assert gemini_provider.display_name == "Gemini TTS"

    def test_supported_formats(self, gemini_provider: GeminiTTSProvider):
        """Test supported audio formats."""
        formats = gemini_provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats
        assert AudioFormat.OGG in formats

    def test_default_model(self):
        """Test default model is set correctly."""
        provider = GeminiTTSProvider(api_key="test-key")
        assert provider._model == "gemini-2.5-pro-preview-tts"

    def test_custom_model(self):
        """Test custom model can be specified."""
        provider = GeminiTTSProvider(
            api_key="test-key",
            model="gemini-2.5-flash-preview-tts",
        )
        assert provider._model == "gemini-2.5-flash-preview-tts"

    @pytest.mark.asyncio
    async def test_list_voices_all(self, gemini_provider: GeminiTTSProvider):
        """Test listing all voices."""
        voices = await gemini_provider.list_voices()

        assert len(voices) == 30  # 30 prebuilt Gemini voices
        assert all(v.provider == "gemini" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_with_language(self, gemini_provider: GeminiTTSProvider):
        """Test listing voices with language filter."""
        voices = await gemini_provider.list_voices(language="zh-TW")

        assert len(voices) == 30
        assert all(v.language == "zh-TW" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_multilingual_default(self, gemini_provider: GeminiTTSProvider):
        """Test voices default to multilingual when no language specified."""
        voices = await gemini_provider.list_voices()

        assert all(v.language == "multilingual" for v in voices)

    @pytest.mark.asyncio
    async def test_get_voice_exists(self, gemini_provider: GeminiTTSProvider):
        """Test getting a specific voice that exists."""
        voice = await gemini_provider.get_voice("Kore")

        assert voice is not None
        assert voice.voice_id == "Kore"
        assert voice.display_name == "Kore"
        assert voice.gender == Gender.FEMALE
        assert "friendly" in voice.description.lower()

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self, gemini_provider: GeminiTTSProvider):
        """Test getting a voice that doesn't exist."""
        voice = await gemini_provider.get_voice("non-existent-voice")

        assert voice is None

    def test_get_supported_params(self, gemini_provider: GeminiTTSProvider):
        """Test getting supported parameter ranges."""
        params = gemini_provider.get_supported_params()

        assert "speed" in params
        assert "pitch" in params
        assert "volume" in params
        assert "style_prompt" in params
        assert params["style_prompt"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_health_check_configured(self, gemini_provider: GeminiTTSProvider):
        """Test health check when properly configured."""
        with patch.object(gemini_provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            is_healthy = await gemini_provider.health_check()
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        """Test health check when not configured."""
        provider = GeminiTTSProvider(api_key="")
        is_healthy = await provider.health_check()
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self, gemini_provider: GeminiTTSProvider):
        """Test health check when API returns error."""
        with patch.object(gemini_provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection error")

            is_healthy = await gemini_provider.health_check()
            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_synthesize_success(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test successful synthesis."""
        # Create mock PCM data (simple silence)
        pcm_data = b"\x00\x00" * 24000  # 1 second of silence at 24kHz
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        # Mock the PCM conversion to avoid ffmpeg dependency
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            result = await gemini_provider.synthesize(sample_request)

            assert result is not None
            assert result.audio.data is not None
            assert len(result.audio.data) > 0
            assert result.audio.format == AudioFormat.MP3

    @pytest.mark.asyncio
    async def test_synthesize_with_style_prompt(
        self, gemini_provider: GeminiTTSProvider, sample_request_with_style: TTSRequest
    ):
        """Test synthesis with style prompt."""
        pcm_data = b"\x00\x00" * 24000
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        # Mock the PCM conversion to avoid ffmpeg dependency
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            await gemini_provider.synthesize(sample_request_with_style)

            # Verify style prompt was included in the request
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            text_content = payload["contents"][0]["parts"][0]["text"]
            assert "Say this cheerfully with excitement" in text_content

    @pytest.mark.asyncio
    async def test_synthesize_api_error(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test handling of API errors."""
        with patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.json.return_value = {"error": {"message": "Model overloaded"}}
            mock_post.return_value = mock_response

            with pytest.raises(
                RuntimeError, match="Gemini TTS API error.*status 500.*Model overloaded"
            ):
                await gemini_provider.synthesize(sample_request)

    @pytest.mark.asyncio
    async def test_synthesize_stream(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test streaming synthesis."""
        pcm_data = b"\x00\x00" * 24000
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        # Mock the PCM conversion to avoid ffmpeg dependency
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            chunks = []
            async for chunk in gemini_provider.synthesize_stream(sample_request):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert all(isinstance(c, bytes) for c in chunks)


class TestGeminiVoices:
    """Tests for Gemini voice definitions."""

    def test_voices_have_required_fields(self):
        """Test all Gemini voices have required fields."""
        for _voice_id, info in GeminiTTSProvider.VOICES.items():
            assert "gender" in info
            assert "description" in info
            assert info["gender"] in ("male", "female")

    def test_expected_voices_exist(self):
        """Test expected voices are defined."""
        expected_voices = ["Kore", "Charon", "Aoede", "Puck", "Zephyr"]
        for voice in expected_voices:
            assert voice in GeminiTTSProvider.VOICES

    def test_voice_count(self):
        """Test correct number of voices defined."""
        assert len(GeminiTTSProvider.VOICES) == 30

    def test_kore_recommended_for_chinese(self):
        """Test Kore is recommended for Chinese."""
        kore_info = GeminiTTSProvider.VOICES["Kore"]
        assert "chinese" in kore_info["description"].lower()


class TestGeminiByteValidation:
    """Tests for Gemini TTS byte-level input validation."""

    @pytest.mark.asyncio
    async def test_synthesize_byte_limit_cjk_text(self, gemini_provider: GeminiTTSProvider):
        """Test that CJK text exceeding 4000 bytes is rejected before API call."""
        # 1400 CJK characters × 3 bytes = 4200 bytes > 4000 limit
        long_cjk_text = "你" * 1400
        request = TTSRequest(
            text=long_cjk_text,
            voice_id="Kore",
            provider="gemini",
            language="zh-TW",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        with pytest.raises(ValueError, match="4000-byte limit"):
            await gemini_provider.synthesize(request)

    @pytest.mark.asyncio
    async def test_synthesize_byte_limit_with_style_prompt(
        self, gemini_provider: GeminiTTSProvider
    ):
        """Test that style_prompt + text combined byte count is validated."""
        # style_prompt (~40 bytes) + 1330 CJK chars (3990 bytes) + ": " (2 bytes) > 4000
        long_cjk_text = "你" * 1330
        request = TTSRequest(
            text=long_cjk_text,
            voice_id="Kore",
            provider="gemini",
            language="zh-TW",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
            style_prompt="Say this cheerfully with excitement",
        )

        with pytest.raises(ValueError, match="4000-byte limit"):
            await gemini_provider.synthesize(request)

    @pytest.mark.asyncio
    async def test_synthesize_byte_limit_within_limit(self, gemini_provider: GeminiTTSProvider):
        """Test that text within byte limit passes validation and calls API normally."""
        # 100 CJK characters × 3 bytes = 300 bytes, well within limit
        short_text = "你" * 100
        request = TTSRequest(
            text=short_text,
            voice_id="Kore",
            provider="gemini",
            language="zh-TW",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        pcm_data = b"\x00\x00" * 24000
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            result = await gemini_provider.synthesize(request)
            assert result is not None
            assert result.audio.data == mock_mp3_data
            mock_post.assert_called_once()


class TestGeminiFinishReasonRetry:
    """Tests for Gemini TTS finishReason=OTHER retry logic."""

    @pytest.mark.asyncio
    async def test_synthesize_finish_reason_other_retries_exhausted(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test that finishReason=OTHER retries 3 times then raises error."""
        other_response_data = {"candidates": [{"finishReason": "OTHER"}]}

        with patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = other_response_data
            mock_post.return_value = mock_response

            with pytest.raises(ValueError, match="finishReason=OTHER"):
                await gemini_provider.synthesize(sample_request)

            # Should have been called 3 times (1 initial + 2 retries)
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_synthesize_finish_reason_other_succeeds_on_retry(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test that finishReason=OTHER succeeds on second attempt."""
        pcm_data = b"\x00\x00" * 24000
        other_response_data = {"candidates": [{"finishReason": "OTHER"}]}
        success_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            # First call returns OTHER, second call succeeds
            fail_response = MagicMock()
            fail_response.status_code = 200
            fail_response.json.return_value = other_response_data

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = success_response_data

            mock_post.side_effect = [fail_response, success_response]
            mock_convert.return_value = mock_mp3_data

            result = await gemini_provider.synthesize(sample_request)
            assert result is not None
            assert result.audio.data == mock_mp3_data
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_synthesize_finish_reason_safety_no_retry(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test that finishReason=SAFETY does not retry and raises immediately."""
        safety_response_data = {"candidates": [{"finishReason": "SAFETY"}]}

        with patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = safety_response_data
            mock_post.return_value = mock_response

            with pytest.raises(ValueError, match="safety filters"):
                await gemini_provider.synthesize(sample_request)

            # Should only be called once — no retries for SAFETY
            assert mock_post.call_count == 1


class TestGeminiErrorCodeRouting:
    """Tests that each Gemini API error code is routed to the correct exception.

    Covers every branch in _do_synthesize error handling:
    - HTTP 4xx/5xx → RuntimeError (general), QuotaExceededError, or RateLimitError
    - HTTP 200 with problematic response body → ValueError
    """

    @staticmethod
    def _make_gemini_request() -> TTSRequest:
        return TTSRequest(
            text="Test",
            voice_id="Kore",
            provider="gemini",
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

    @staticmethod
    def _mock_error_response(
        status_code: int,
        error_message: str,
        *,
        headers: dict | None = None,
    ) -> Mock:
        """Create a mock httpx response for a Gemini API error."""
        resp = Mock()
        resp.status_code = status_code
        resp.text = error_message
        resp.json.return_value = {"error": {"message": error_message}}
        resp.headers = headers or {}
        return resp

    # ------------------------------------------------------------------
    # Non-429, non-quota HTTP errors → RuntimeError
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("status_code", "error_message", "gemini_status"),
        [
            (400, "Invalid value at 'contents[0].parts'", "INVALID_ARGUMENT"),
            (401, "API key not valid. Please pass a valid API key.", "UNAUTHENTICATED"),
            (403, "Permission denied on resource project.", "PERMISSION_DENIED"),
            (404, "models/gemini-2.5-pro-preview-tts is not found", "NOT_FOUND"),
            (500, "An internal error has occurred.", "INTERNAL"),
            (503, "The model is overloaded. Please try again later.", "UNAVAILABLE"),
        ],
    )
    async def test_http_error_codes_raise_runtime_error(
        self,
        status_code: int,
        error_message: str,
        gemini_status: str,
    ) -> None:
        """HTTP {status_code} ({gemini_status}) should raise RuntimeError."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = self._mock_error_response(status_code, error_message)
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(RuntimeError, match=rf"Gemini TTS API error \(status {status_code}\)"):
            await provider._do_synthesize(self._make_gemini_request())

    # ------------------------------------------------------------------
    # 400 with "exceeded your current quota" → QuotaExceededError
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_400_with_quota_message_raises_quota_exceeded_error(self) -> None:
        """HTTP 400 containing quota exhaustion message → QuotaExceededError."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = self._mock_error_response(
            400, "You exceeded your current quota, please check your plan and billing."
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(QuotaExceededError) as exc_info:
            await provider._do_synthesize(self._make_gemini_request())

        assert exc_info.value.details["provider"] == "gemini"

    # ------------------------------------------------------------------
    # 429 (any message) → retry → RateLimitError
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_429_always_raises_rate_limit_error(self) -> None:
        """HTTP 429 should always raise RateLimitError, regardless of message."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = self._mock_error_response(
            429, "You exceeded your current quota", headers={"retry-after": "60"}
        )
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RateLimitError) as exc_info,
        ):
            await provider._do_synthesize(self._make_gemini_request())

        assert exc_info.value.details["provider"] == "gemini"

    # ------------------------------------------------------------------
    # 200 edge cases → ValueError
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_200_empty_candidates_raises_value_error(self) -> None:
        """HTTP 200 with empty candidates list → ValueError."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": []}
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(ValueError, match="no candidates"):
            await provider._do_synthesize(self._make_gemini_request())

    @pytest.mark.asyncio
    async def test_200_missing_candidates_key_raises_value_error(self) -> None:
        """HTTP 200 with no 'candidates' key at all → ValueError."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"promptFeedback": {"blockReason": "SAFETY"}}
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(ValueError, match="no candidates"):
            await provider._do_synthesize(self._make_gemini_request())

    @pytest.mark.asyncio
    async def test_200_invalid_audio_structure_raises_value_error(self) -> None:
        """HTTP 200 with malformed content structure → ValueError."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = Mock()
        mock_resp.status_code = 200
        # Has content and finishReason but parts structure is wrong (missing inlineData)
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "unexpected text part"}]},
                    "finishReason": "STOP",
                }
            ]
        }
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(ValueError, match="Invalid API response structure"):
            await provider._do_synthesize(self._make_gemini_request())

    # ------------------------------------------------------------------
    # Error response with unparseable JSON → fallback to response.text
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_error_response_with_broken_json_falls_back_to_text(self) -> None:
        """If error response JSON parsing fails, use response.text for the message."""
        provider = GeminiTTSProvider(api_key="test-key")
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "raw error text from server"
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.headers = {}
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(RuntimeError, match="raw error text from server"):
            await provider._do_synthesize(self._make_gemini_request())
