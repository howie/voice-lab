"""Integration tests for STT file upload flow.

Feature: 003-stt-testing-module
T026: Integration test for file upload flow

Tests the complete flow from file upload to transcription result.
"""

import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.use_cases.transcribe_audio import TranscribeAudioUseCase
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import (
    get_stt_providers,
    get_transcribe_audio_use_case,
)


@pytest.fixture
def mock_audio_data() -> AudioData:
    """Create mock audio data for testing."""
    return AudioData(
        data=b"\x00\x01" * 500,
        format=AudioFormat.WAV,
        sample_rate=16000,
    )


@pytest.fixture
def mock_wav_audio() -> bytes:
    """Generate realistic mock WAV audio data."""
    # Simple WAV header (44 bytes) + audio data
    wav_header = (
        b"RIFF"  # ChunkID
        + b"\x00\x00\x00\x00"  # ChunkSize (placeholder)
        + b"WAVE"  # Format
        + b"fmt "  # Subchunk1ID
        + b"\x10\x00\x00\x00"  # Subchunk1Size (16 for PCM)
        + b"\x01\x00"  # AudioFormat (1 = PCM)
        + b"\x01\x00"  # NumChannels (1 = mono)
        + b"\x80\x3e\x00\x00"  # SampleRate (16000)
        + b"\x00\x7d\x00\x00"  # ByteRate (16000 * 1 * 2)
        + b"\x02\x00"  # BlockAlign (1 * 2)
        + b"\x10\x00"  # BitsPerSample (16)
        + b"data"  # Subchunk2ID
        + b"\x00\x00\x00\x00"  # Subchunk2Size (placeholder)
    )
    # Add some sample audio data (simulating 1 second of audio)
    audio_data = b"\x00\x01" * 16000  # 1 second at 16kHz mono 16-bit
    return wav_header + audio_data


@pytest.fixture
def mock_mp3_audio() -> bytes:
    """Generate mock MP3 audio data."""
    # MP3 frame header + data (simplified)
    mp3_header = b"\xff\xfb\x90\x00"  # MP3 sync word + header
    return mp3_header + b"\x00" * 4096


class TestSTTUploadIntegration:
    """Integration tests for STT upload flow."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self):
        """Override database dependencies for testing."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        async def get_mock_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = get_mock_session
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_full_transcription_flow(self, mock_wav_audio: bytes, mock_audio_data: AudioData):
        """Integration test: Complete upload → transcribe → result flow."""
        # Set up mock STT provider
        mock_request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=mock_audio_data,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="這是一段測試音訊",
            confidence=0.94,
            latency_ms=250,
            words=[
                WordTiming(word="這是", start_ms=0, end_ms=300, confidence=0.95),
                WordTiming(word="一段", start_ms=300, end_ms=600, confidence=0.93),
                WordTiming(word="測試", start_ms=600, end_ms=900, confidence=0.94),
                WordTiming(word="音訊", start_ms=900, end_ms=1200, confidence=0.95),
            ],
        )

        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_result
        mock_provider.supports_streaming = True

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Step 1: Upload audio file
                files = {"audio": ("test_audio.wav", io.BytesIO(mock_wav_audio), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "save_to_history": "false",
                }

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            # Step 2: Verify response
            assert response.status_code == 200
            result = response.json()

            # Verify transcription result
            assert result["transcript"] == "這是一段測試音訊"
            assert result["provider"] == "azure"
            assert result["language"] == "zh-TW"
            assert result["confidence"] == 0.94
            assert result["latency_ms"] == 250

            # Verify word timings
            assert "words" in result
            assert len(result["words"]) == 4
            assert result["words"][0]["word"] == "這是"
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_upload_with_wer_analysis(
        self, mock_wav_audio: bytes, mock_audio_data: AudioData
    ):
        """Integration test: Upload with ground truth for WER calculation."""
        mock_request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=mock_audio_data,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="你好世界",
            confidence=0.90,
            latency_ms=200,
        )

        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_result
        mock_provider.supports_streaming = True

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_wav_audio), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "ground_truth": "你好世界",  # Exact match
                }

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Verify WER analysis is included
            assert "wer_analysis" in result
            if result["wer_analysis"]:
                analysis = result["wer_analysis"]
                assert analysis["error_type"] == "CER"  # Chinese uses CER
                assert analysis["error_rate"] == 0.0  # Exact match
                assert analysis["substitutions"] == 0
                assert analysis["insertions"] == 0
                assert analysis["deletions"] == 0
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_upload_different_providers(
        self, mock_wav_audio: bytes, mock_audio_data: AudioData
    ):
        """Integration test: Upload same audio to different providers."""
        azure_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=mock_audio_data,
        )
        azure_result = STTResult(
            request=azure_request,
            transcript="Hello from Azure",
            confidence=0.92,
            latency_ms=180,
        )
        gcp_request = STTRequest(
            provider="gcp",
            language="en-US",
            audio=mock_audio_data,
        )
        gcp_result = STTResult(
            request=gcp_request,
            transcript="Hello from GCP",
            confidence=0.90,
            latency_ms=200,
        )
        whisper_request = STTRequest(
            provider="whisper",
            language="en-US",
            audio=mock_audio_data,
        )
        whisper_result = STTResult(
            request=whisper_request,
            transcript="Hello from Whisper",
            confidence=0.88,
            latency_ms=350,
        )

        mock_azure = AsyncMock()
        mock_azure.transcribe.return_value = azure_result

        mock_gcp = AsyncMock()
        mock_gcp.transcribe.return_value = gcp_result

        mock_whisper = AsyncMock()
        mock_whisper.transcribe.return_value = whisper_result

        mock_providers = {
            "azure": mock_azure,
            "gcp": mock_gcp,
            "whisper": mock_whisper,
        }
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            results = {}

            for provider_name in ["azure", "gcp", "whisper"]:
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    files = {
                        "audio": (
                            "test.wav",
                            io.BytesIO(mock_wav_audio),
                            "audio/wav",
                        )
                    }
                    data = {"provider": provider_name, "language": "en-US"}

                    response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

                assert response.status_code == 200
                results[provider_name] = response.json()

            # Verify each provider returned different results
            assert results["azure"]["transcript"] == "Hello from Azure"
            assert results["gcp"]["transcript"] == "Hello from GCP"
            assert results["whisper"]["transcript"] == "Hello from Whisper"

            # Verify latencies are captured
            assert results["azure"]["latency_ms"] == 180
            assert results["gcp"]["latency_ms"] == 200
            assert results["whisper"]["latency_ms"] == 350
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_upload_large_file_rejected(self):
        """Integration test: Large files are rejected based on provider limits."""
        # Create a 30MB file (exceeds Whisper's 25MB limit)
        large_audio = b"\x00" * (30 * 1024 * 1024)

        mock_provider = AsyncMock()
        mock_providers = {"whisper": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("large.wav", io.BytesIO(large_audio), "audio/wav")}
                data = {"provider": "whisper"}

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 400
            result = response.json()
            assert "size" in result["detail"].lower() or "limit" in result["detail"].lower()

            # Verify provider was NOT called
            mock_provider.transcribe.assert_not_called()
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_upload_mp3_format(self, mock_mp3_audio: bytes, mock_audio_data: AudioData):
        """Integration test: MP3 files are processed correctly."""
        mock_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=mock_audio_data,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="MP3 audio test",
            confidence=0.91,
            latency_ms=150,
        )

        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.mp3", io.BytesIO(mock_mp3_audio), "audio/mpeg")}
                data = {"provider": "azure"}

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()
            assert result["transcript"] == "MP3 audio test"

            # Verify audio format was correctly identified
            call_args = mock_provider.transcribe.call_args[0][0]
            assert call_args.audio.format == AudioFormat.MP3
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_upload_with_child_mode(self, mock_wav_audio: bytes, mock_audio_data: AudioData):
        """Integration test: Child mode is passed through the flow."""
        mock_request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=mock_audio_data,
            child_mode=True,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="兒童語音測試",
            confidence=0.85,
            latency_ms=200,
        )

        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_wav_audio), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "child_mode": "true",
                }

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200

            # Verify child_mode was passed to provider
            call_args = mock_provider.transcribe.call_args[0][0]
            assert call_args.child_mode is True
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_provider_error_handling(self, mock_wav_audio: bytes):
        """Integration test: Provider errors are handled gracefully."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.side_effect = Exception("Provider service unavailable")

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_wav_audio), "audio/wav")}
                data = {"provider": "azure"}

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 500
            result = response.json()
            assert "detail" in result
            assert "failed" in result["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_list_then_transcribe_flow(
        self, mock_wav_audio: bytes, mock_audio_data: AudioData
    ):
        """Integration test: List providers then transcribe with selected provider."""
        mock_request = STTRequest(
            provider="gcp",
            language="en-US",
            audio=mock_audio_data,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="Integration test successful",
            confidence=0.93,
            latency_ms=180,
        )

        mock_azure = MagicMock()
        mock_azure.supports_streaming = True

        mock_gcp = AsyncMock()
        mock_gcp.supports_streaming = True
        mock_gcp.transcribe.return_value = mock_result

        mock_providers = {"azure": mock_azure, "gcp": mock_gcp}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Step 1: List available providers
                list_response = await ac.get("/api/v1/stt/providers")
                assert list_response.status_code == 200
                providers = list_response.json()["providers"]

                # Find GCP provider
                gcp_provider = next((p for p in providers if p["name"] == "gcp"), None)
                assert gcp_provider is not None

                # Step 2: Use selected provider to transcribe
                files = {"audio": ("test.wav", io.BytesIO(mock_wav_audio), "audio/wav")}
                data = {
                    "provider": gcp_provider["name"],
                    "language": "en-US",
                }

                transcribe_response = await ac.post(
                    "/api/v1/stt/transcribe", files=files, data=data
                )

            assert transcribe_response.status_code == 200
            result = transcribe_response.json()
            assert result["transcript"] == "Integration test successful"
            assert result["provider"] == "gcp"
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)
