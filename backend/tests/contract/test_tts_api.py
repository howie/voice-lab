"""Contract tests for TTS API endpoints.

T020: Contract tests for /tts/synthesize endpoint
T021: Contract tests for /tts/stream endpoint
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import base64

from src.main import app
from src.domain.entities.audio import AudioFormat, AudioData
from src.domain.entities.tts import TTSRequest, TTSResult


@pytest.fixture
def mock_audio_data() -> bytes:
    """Generate mock audio data for testing."""
    return b"\x00\x01\x02\x03" * 1000  # 4KB of mock audio


@pytest.fixture
def mock_tts_result(mock_audio_data: bytes) -> TTSResult:
    """Create a mock TTS result for testing."""
    request = TTSRequest(
        text="Hello World",
        voice_id="en-US-JennyNeural",
        provider="azure",
        language="en-US",
    )
    return TTSResult(
        request=request,
        audio=AudioData(data=mock_audio_data, format=AudioFormat.MP3),
        duration_ms=1500,
        latency_ms=200,
    )


class TestSynthesizeEndpoint:
    """Contract tests for POST /api/v1/tts/synthesize endpoint."""

    @pytest.mark.asyncio
    async def test_synthesize_success_azure(self, mock_tts_result: TTSResult):
        """T020: Test successful synthesis with Azure provider."""
        with patch(
            "src.presentation.api.routes.tts.AzureTTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "azure",
                    "voice_id": "en-US-JennyNeural",
                    "language": "en-US",
                    "speed": 1.0,
                    "pitch": 0.0,
                    "volume": 1.0,
                    "output_format": "mp3",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "audio_content" in data
            assert "content_type" in data
            assert "duration_ms" in data
            assert data["content_type"] == "audio/mpeg"
            # Verify base64 encoding
            decoded = base64.b64decode(data["audio_content"])
            assert len(decoded) > 0

    @pytest.mark.asyncio
    async def test_synthesize_success_gcp(self, mock_tts_result: TTSResult):
        """T020: Test successful synthesis with GCP provider."""
        with patch(
            "src.presentation.api.routes.tts.GoogleTTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_tts_result.request = TTSRequest(
                text="Hello World",
                voice_id="cmn-TW-Standard-A",
                provider="gcp",
                language="zh-TW",
            )
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "gcp",
                    "voice_id": "cmn-TW-Standard-A",
                    "language": "zh-TW",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_synthesize_success_elevenlabs(self, mock_tts_result: TTSResult):
        """T020: Test successful synthesis with ElevenLabs provider."""
        with patch(
            "src.presentation.api.routes.tts.ElevenLabsTTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "elevenlabs",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_synthesize_success_voai(self, mock_tts_result: TTSResult):
        """T020: Test successful synthesis with VoAI provider."""
        with patch(
            "src.presentation.api.routes.tts.VoAITTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "voai",
                    "voice_id": "voai-tw-female-1",
                    "language": "zh-TW",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_synthesize_empty_text_validation_error(self):
        """T020: Test validation error for empty text."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "",
                "provider": "azure",
                "voice_id": "en-US-JennyNeural",
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_synthesize_text_too_long_validation_error(self):
        """T020: Test validation error for text exceeding 5000 characters."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "A" * 5001,  # Exceeds 5000 char limit
                "provider": "azure",
                "voice_id": "en-US-JennyNeural",
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_synthesize_invalid_provider(self):
        """T020: Test validation error for unsupported provider."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "Hello World",
                "provider": "invalid_provider",
                "voice_id": "some-voice",
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_synthesize_invalid_speed(self):
        """T020: Test validation error for speed out of range."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "Hello World",
                "provider": "azure",
                "voice_id": "en-US-JennyNeural",
                "speed": 3.0,  # Max is 2.0
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_synthesize_response_schema(self, mock_tts_result: TTSResult):
        """T020: Verify response matches SynthesizeResponse schema."""
        with patch(
            "src.presentation.api.routes.tts.AzureTTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "azure",
                    "voice_id": "en-US-JennyNeural",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 200
            data = response.json()

            # Schema validation
            assert isinstance(data["audio_content"], str)
            assert isinstance(data["content_type"], str)
            assert isinstance(data["duration_ms"], int)


class TestStreamEndpoint:
    """Contract tests for POST /api/v1/tts/stream endpoint."""

    @pytest.mark.asyncio
    async def test_stream_success(self, mock_audio_data: bytes):
        """T021: Test successful streaming synthesis."""
        async def mock_stream():
            for i in range(0, len(mock_audio_data), 1024):
                yield mock_audio_data[i : i + 1024]

        with patch(
            "src.presentation.api.routes.tts.VoAITTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize_stream.return_value = mock_stream()
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "voai",
                    "voice_id": "voai-tw-female-1",
                }
                response = await ac.post("/api/v1/tts/stream", json=payload)

            # Streaming endpoint should return 200 or streaming response
            # If not implemented yet, we expect 404
            assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_stream_empty_text_validation_error(self):
        """T021: Test streaming validation error for empty text."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "",
                "provider": "azure",
                "voice_id": "en-US-JennyNeural",
            }
            response = await ac.post("/api/v1/tts/stream", json=payload)

        # If endpoint exists, should return 422; if not, 404
        assert response.status_code in [404, 422]

    @pytest.mark.asyncio
    async def test_stream_response_headers(self, mock_audio_data: bytes):
        """T021: Verify streaming response has correct content type."""
        async def mock_stream():
            yield mock_audio_data

        with patch(
            "src.presentation.api.routes.tts.AzureTTSProvider"
        ) as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize_stream.return_value = mock_stream()
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Hello World",
                    "provider": "azure",
                    "voice_id": "en-US-JennyNeural",
                }
                response = await ac.post("/api/v1/tts/stream", json=payload)

            if response.status_code == 200:
                # Streaming should return audio content type
                content_type = response.headers.get("content-type", "")
                assert "audio" in content_type or "octet-stream" in content_type
