"""Contract tests for Lyria Vertex AI predict endpoint.

Feature: 016-integration-gemini-lyria-music
Tests verify that LyriaVertexAIClient builds correct request payloads
and parses Vertex AI responses properly.
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.adapters.lyria.client import (
    LyriaAPIError,
    LyriaAuthError,
    LyriaRateLimitError,
    LyriaSafetyFilterError,
    LyriaVertexAIClient,
    convert_wav_to_mp3,
)


# Minimal valid WAV header (44 bytes) + tiny payload for testing
def _make_wav_bytes(duration_samples: int = 100) -> bytes:
    """Create a minimal valid WAV file for testing."""
    import struct

    sample_rate = 48000
    num_channels = 1
    bits_per_sample = 16
    data_size = duration_samples * num_channels * (bits_per_sample // 8)
    header_size = 44

    wav = bytearray()
    wav.extend(b"RIFF")
    wav.extend(struct.pack("<I", data_size + header_size - 8))
    wav.extend(b"WAVE")
    wav.extend(b"fmt ")
    wav.extend(struct.pack("<I", 16))  # PCM format chunk size
    wav.extend(struct.pack("<H", 1))  # PCM format
    wav.extend(struct.pack("<H", num_channels))
    wav.extend(struct.pack("<I", sample_rate))
    wav.extend(struct.pack("<I", sample_rate * num_channels * bits_per_sample // 8))
    wav.extend(struct.pack("<H", num_channels * bits_per_sample // 8))
    wav.extend(struct.pack("<H", bits_per_sample))
    wav.extend(b"data")
    wav.extend(struct.pack("<I", data_size))
    wav.extend(b"\x00" * data_size)
    return bytes(wav)


WAV_BYTES = _make_wav_bytes()
WAV_B64 = base64.b64encode(WAV_BYTES).decode()


def _mock_vertex_response(
    predictions: list[dict] | None = None,
    status_code: int = 200,
) -> httpx.Response:
    """Create a mock Vertex AI response."""
    if predictions is None:
        predictions = [{"audioContent": WAV_B64, "mimeType": "audio/wav"}]

    return httpx.Response(
        status_code=status_code,
        json={"predictions": predictions},
        request=httpx.Request("POST", "https://example.com"),
    )


def _mock_error_response(status_code: int, message: str = "error") -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json={"error": {"message": message}},
        request=httpx.Request("POST", "https://example.com"),
    )


@pytest.fixture
def client() -> LyriaVertexAIClient:
    """Create a LyriaVertexAIClient with mocked credentials."""
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

        c = LyriaVertexAIClient(
            project_id="test-project",
            location="us-central1",
            model="lyria-002",
            timeout=30.0,
        )
        # Replace credentials refresh to avoid real HTTP
        c._credentials = mock_creds
        return c


class TestLyriaVertexAIClientPayload:
    """T016: Verify correct Vertex AI request payload construction."""

    @pytest.mark.asyncio
    async def test_basic_prompt_payload(self, client: LyriaVertexAIClient) -> None:
        """Basic prompt should produce correct instances payload."""
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response())

        await client.generate_instrumental(prompt="calm acoustic guitar")

        call_kwargs = client._http_client.post.call_args
        payload = call_kwargs.kwargs["json"]

        assert payload["instances"] == [{"prompt": "calm acoustic guitar"}]
        assert "parameters" not in payload

    @pytest.mark.asyncio
    async def test_negative_prompt_in_payload(self, client: LyriaVertexAIClient) -> None:
        """Negative prompt should be included in instances."""
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response())

        await client.generate_instrumental(
            prompt="calm guitar",
            negative_prompt="drums, bass",
        )

        payload = client._http_client.post.call_args.kwargs["json"]
        assert payload["instances"][0]["negative_prompt"] == "drums, bass"

    @pytest.mark.asyncio
    async def test_seed_in_payload(self, client: LyriaVertexAIClient) -> None:
        """Seed should be included in instances."""
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response())

        await client.generate_instrumental(prompt="piano", seed=42)

        payload = client._http_client.post.call_args.kwargs["json"]
        assert payload["instances"][0]["seed"] == 42

    @pytest.mark.asyncio
    async def test_sample_count_in_parameters(self, client: LyriaVertexAIClient) -> None:
        """Sample count > 1 should be in parameters section."""
        client._http_client = AsyncMock()
        multi_predictions = [
            {"audioContent": WAV_B64, "mimeType": "audio/wav"},
            {"audioContent": WAV_B64, "mimeType": "audio/wav"},
            {"audioContent": WAV_B64, "mimeType": "audio/wav"},
        ]
        client._http_client.post = AsyncMock(
            return_value=_mock_vertex_response(predictions=multi_predictions)
        )

        results = await client.generate_instrumental(prompt="epic", sample_count=3)

        payload = client._http_client.post.call_args.kwargs["json"]
        assert payload["parameters"]["sample_count"] == 3
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_authorization_header(self, client: LyriaVertexAIClient) -> None:
        """Request should include Bearer token in Authorization header."""
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response())

        await client.generate_instrumental(prompt="test")

        headers = client._http_client.post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer test-token"

    @pytest.mark.asyncio
    async def test_endpoint_url(self, client: LyriaVertexAIClient) -> None:
        """Request should target correct Vertex AI predict endpoint."""
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response())

        await client.generate_instrumental(prompt="test")

        url = client._http_client.post.call_args.args[0]
        assert "us-central1-aiplatform.googleapis.com" in url
        assert "lyria-002:predict" in url
        assert "test-project" in url


class TestLyriaVertexAIClientResponse:
    """T013: Verify correct parsing of Vertex AI responses."""

    @pytest.mark.asyncio
    async def test_parse_single_prediction(self, client: LyriaVertexAIClient) -> None:
        """Single prediction should produce one LyriaGenerationResult."""
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response())

        results = await client.generate_instrumental(prompt="test")

        assert len(results) == 1
        assert results[0].audio_content == WAV_BYTES
        assert results[0].mime_type == "audio/wav"

    @pytest.mark.asyncio
    async def test_parse_multiple_predictions(self, client: LyriaVertexAIClient) -> None:
        """Multiple predictions should produce multiple results."""
        client._http_client = AsyncMock()
        preds = [
            {"audioContent": WAV_B64, "mimeType": "audio/wav"},
            {"audioContent": WAV_B64, "mimeType": "audio/wav"},
        ]
        client._http_client.post = AsyncMock(return_value=_mock_vertex_response(predictions=preds))

        results = await client.generate_instrumental(prompt="test", sample_count=2)

        assert len(results) == 2


class TestLyriaVertexAIClientErrors:
    """T022: Verify error handling for Vertex AI responses."""

    @pytest.mark.asyncio
    async def test_auth_error_401(self, client: LyriaVertexAIClient) -> None:
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_error_response(401, "Unauthorized"))
        with pytest.raises(LyriaAuthError):
            await client.generate_instrumental(prompt="test")

    @pytest.mark.asyncio
    async def test_safety_filter_400(self, client: LyriaVertexAIClient) -> None:
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(
            return_value=_mock_error_response(400, "Safety filter")
        )
        with pytest.raises(LyriaSafetyFilterError):
            await client.generate_instrumental(prompt="test")

    @pytest.mark.asyncio
    async def test_rate_limit_429(self, client: LyriaVertexAIClient) -> None:
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(return_value=_mock_error_response(429, "Rate limited"))
        with pytest.raises(LyriaRateLimitError):
            await client.generate_instrumental(prompt="test")

    @pytest.mark.asyncio
    async def test_server_error_500(self, client: LyriaVertexAIClient) -> None:
        client._http_client = AsyncMock()
        client._http_client.post = AsyncMock(
            return_value=_mock_error_response(500, "Internal error")
        )
        with pytest.raises(LyriaAPIError):
            await client.generate_instrumental(prompt="test")


def _ffmpeg_available() -> bool:
    import shutil

    return shutil.which("ffmpeg") is not None


class TestWavToMp3Conversion:
    """T015: Verify WAV→MP3 conversion utility."""

    @pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg not installed")
    def test_convert_valid_wav(self) -> None:
        """Valid WAV bytes should convert to MP3 bytes."""
        mp3_bytes = convert_wav_to_mp3(WAV_BYTES)
        assert len(mp3_bytes) > 0
        # MP3 files start with ID3 tag or frame sync (0xFF 0xFB)
        assert mp3_bytes[:3] == b"ID3" or mp3_bytes[0] == 0xFF

    def test_convert_invalid_wav_raises(self) -> None:
        """Invalid WAV bytes should raise an exception."""
        with pytest.raises((ValueError, EOFError, OSError)):
            convert_wav_to_mp3(b"not a wav file")
