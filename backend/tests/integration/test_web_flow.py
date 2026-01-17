"""Integration test for synthesis flow.

T037: Create integration test for synthesis flow
Tests the complete flow from web request to audio response.
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult
from src.main import app


@pytest.fixture
def mock_audio_bytes() -> bytes:
    """Generate realistic mock audio data."""
    # MP3 header magic bytes + some data
    return b"\xff\xfb\x90\x00" + b"\x00" * 4096


@pytest.fixture
def mock_tts_result(mock_audio_bytes: bytes) -> TTSResult:
    """Create a mock TTS result."""
    request = TTSRequest(
        text="測試文字轉語音",
        voice_id="zh-TW-HsiaoChenNeural",
        provider="azure",
        language="zh-TW",
    )
    return TTSResult(
        request=request,
        audio=AudioData(data=mock_audio_bytes, format=AudioFormat.MP3),
        duration_ms=2500,
        latency_ms=150,
    )


class TestSynthesisFlow:
    """Integration tests for the complete synthesis flow."""

    @pytest.mark.asyncio
    async def test_complete_synthesis_flow_batch_mode(
        self, mock_tts_result: TTSResult, mock_audio_bytes: bytes
    ):
        """Test complete synthesis flow from request to audio response (batch mode)."""
        with patch("src.presentation.api.routes.tts.AzureTTSProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Step 1: Submit synthesis request
                payload = {
                    "text": "測試文字轉語音",
                    "provider": "azure",
                    "voice_id": "zh-TW-HsiaoChenNeural",
                    "language": "zh-TW",
                    "speed": 1.0,
                    "pitch": 0.0,
                    "volume": 1.0,
                    "output_format": "mp3",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

                # Step 2: Verify response structure
                assert response.status_code == 200
                data = response.json()

                # Step 3: Verify audio content
                assert "audio_content" in data
                audio_base64 = data["audio_content"]
                audio_bytes = base64.b64decode(audio_base64)
                assert len(audio_bytes) > 0

                # Step 4: Verify metadata
                assert data["content_type"] == "audio/mpeg"
                assert data["duration_ms"] == 2500
                assert "latency_ms" in data

    @pytest.mark.asyncio
    async def test_complete_synthesis_flow_streaming_mode(self, mock_audio_bytes: bytes):
        """Test complete synthesis flow with streaming mode."""

        async def mock_stream():
            """Mock streaming generator."""
            chunk_size = 512
            for i in range(0, len(mock_audio_bytes), chunk_size):
                yield mock_audio_bytes[i : i + chunk_size]

        with patch("src.presentation.api.routes.tts.AzureTTSProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize_stream.return_value = mock_stream()
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "串流測試",
                    "provider": "azure",
                    "voice_id": "zh-TW-HsiaoChenNeural",
                    "language": "zh-TW",
                }
                response = await ac.post("/api/v1/tts/stream", json=payload)

                assert response.status_code == 200
                assert response.headers["content-type"].startswith("audio/")

                # Verify we receive streaming content
                content = await response.aread()
                assert len(content) > 0

    @pytest.mark.asyncio
    async def test_synthesis_flow_with_all_providers(self, mock_tts_result: TTSResult):
        """Test synthesis flow works with all supported providers."""
        providers = [
            ("azure", "src.presentation.api.routes.tts.AzureTTSProvider"),
            ("gcp", "src.presentation.api.routes.tts.GoogleTTSProvider"),
            ("elevenlabs", "src.presentation.api.routes.tts.ElevenLabsTTSProvider"),
            ("voai", "src.presentation.api.routes.tts.VoAITTSProvider"),
        ]

        for provider_name, provider_path in providers:
            with patch(provider_path) as mock_provider_class:
                mock_provider = AsyncMock()
                # Update mock result for each provider
                mock_tts_result.request = TTSRequest(
                    text="測試",
                    voice_id="test-voice",
                    provider=provider_name,
                    language="zh-TW",
                )
                mock_provider.synthesize.return_value = mock_tts_result
                mock_provider_class.return_value = mock_provider

                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    payload = {
                        "text": "測試",
                        "provider": provider_name,
                        "voice_id": "test-voice",
                        "language": "zh-TW",
                    }
                    response = await ac.post("/api/v1/tts/synthesize", json=payload)

                    assert response.status_code == 200, (
                        f"Provider {provider_name} failed: {response.text}"
                    )


class TestWebUIIntegration:
    """Tests simulating web UI interactions."""

    @pytest.mark.asyncio
    async def test_web_ui_synthesis_request(self, mock_tts_result: TTSResult):
        """Simulate a synthesis request from web UI."""
        with patch("src.presentation.api.routes.tts.AzureTTSProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.return_value = mock_tts_result
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Simulate request from browser with typical headers
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "http://localhost:5173",
                }
                payload = {
                    "text": "這是一段測試文字，用於驗證 TTS 功能是否正常運作。",
                    "provider": "azure",
                    "voice_id": "zh-TW-HsiaoChenNeural",
                    "language": "zh-TW",
                    "speed": 1.2,
                    "pitch": 0.0,
                    "volume": 1.0,
                }
                response = await ac.post(
                    "/api/v1/tts/synthesize",
                    json=payload,
                    headers=headers,
                )

                assert response.status_code == 200

                # Verify response can be consumed by frontend
                data = response.json()
                assert "audio_content" in data
                # Frontend expects base64 encoded audio
                assert isinstance(data["audio_content"], str)
                # Should be valid base64
                base64.b64decode(data["audio_content"])

    @pytest.mark.asyncio
    async def test_web_ui_streaming_playback(self, mock_audio_bytes: bytes):
        """Simulate streaming playback request from web UI."""

        async def mock_stream():
            for i in range(0, len(mock_audio_bytes), 1024):
                yield mock_audio_bytes[i : i + 1024]

        with patch("src.presentation.api.routes.tts.AzureTTSProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize_stream.return_value = mock_stream()
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "串流播放測試",
                    "provider": "azure",
                    "voice_id": "zh-TW-HsiaoChenNeural",
                }
                response = await ac.post("/api/v1/tts/stream", json=payload)

                assert response.status_code == 200
                # Should return audio stream
                content_type = response.headers.get("content-type", "")
                assert "audio" in content_type


class TestErrorHandling:
    """Test error handling in the synthesis flow."""

    @pytest.mark.asyncio
    async def test_empty_text_returns_validation_error(self):
        """Test that empty text returns proper validation error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "",
                "provider": "azure",
                "voice_id": "test-voice",
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_text_too_long_returns_error(self):
        """Test that text exceeding limit returns error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "x" * 5001,  # Exceeds 5000 char limit
                "provider": "azure",
                "voice_id": "test-voice",
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_provider_returns_error(self):
        """Test that invalid provider returns error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {
                "text": "Test",
                "provider": "invalid_provider",
                "voice_id": "test-voice",
            }
            response = await ac.post("/api/v1/tts/synthesize", json=payload)

            # Should return 422 validation error or 400 bad request
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_provider_unavailable_returns_service_error(self):
        """Test that provider unavailability returns service error."""
        with patch("src.presentation.api.routes.tts.AzureTTSProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.synthesize.side_effect = Exception("Service unavailable")
            mock_provider_class.return_value = mock_provider

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "text": "Test",
                    "provider": "azure",
                    "voice_id": "test-voice",
                }
                response = await ac.post("/api/v1/tts/synthesize", json=payload)

                # Should return 500 or 503 service error
                assert response.status_code in [500, 503]
