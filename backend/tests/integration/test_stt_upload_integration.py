"""Integration tests for STT file upload flow.

Feature: 003-stt-testing-module
T026: Integration test for file upload flow

Tests the complete flow from file upload to transcription result.
"""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.interfaces.storage_service import StoredFile
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import (
    get_storage_service,
    get_stt_providers,
    get_stt_service,
    get_transcription_repository,
)
from src.presentation.api.middleware.auth import CurrentUser, get_current_user


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Create a mock current user for authentication."""
    return CurrentUser(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
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
    def setup_auth(self, mock_current_user: CurrentUser):
        """Override authentication for all tests."""

        async def get_mock_current_user():
            return mock_current_user

        app.dependency_overrides[get_current_user] = get_mock_current_user
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_full_transcription_flow(self, mock_wav_audio: bytes, mock_audio_data: AudioData):
        """Integration test: Complete upload → transcribe → result flow."""
        # Set up mock STT result
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

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_wav_audio),
            content_type="audio/wav",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

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
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

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

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_wav_audio),
            content_type="audio/wav",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None
        mock_repo.save_ground_truth.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

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
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

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

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_wav_audio),
            content_type="audio/wav",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            results = {}
            provider_results = {
                "azure": azure_result,
                "gcp": gcp_result,
                "whisper": whisper_result,
            }

            for provider_name in ["azure", "gcp", "whisper"]:
                mock_stt_service.transcribe_audio.return_value = (
                    provider_results[provider_name],
                    test_record_id,
                    test_result_id,
                )

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
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_upload_large_file_rejected(self):
        """Integration test: Large files are rejected based on provider limits."""
        # Create a 30MB file (exceeds Whisper's 25MB limit)
        large_audio = b"\x00" * (30 * 1024 * 1024)

        # No need to mock dependencies since validation happens before service call
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("large.wav", io.BytesIO(large_audio), "audio/wav")}
                data = {"provider": "whisper"}

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 400
            result = response.json()
            assert "size" in result["detail"].lower() or "limit" in result["detail"].lower()
        finally:
            pass  # No cleanup needed for this test

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

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.mp3",
            url="http://storage/test.mp3",
            size_bytes=len(mock_mp3_audio),
            content_type="audio/mpeg",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.mp3", io.BytesIO(mock_mp3_audio), "audio/mpeg")}
                data = {"provider": "azure"}

                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()
            assert result["transcript"] == "MP3 audio test"
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

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

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_wav_audio),
            content_type="audio/wav",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

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

            # Verify child_mode was passed to STT service
            call_kwargs = mock_stt_service.transcribe_audio.call_args[1]
            assert call_kwargs["child_mode"] is True
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_provider_error_handling(self, mock_wav_audio: bytes):
        """Integration test: Provider errors are handled gracefully."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_wav_audio),
            content_type="audio/wav",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service that raises an exception
        mock_stt_service = AsyncMock()
        mock_stt_service.transcribe_audio.side_effect = RuntimeError("Provider service unavailable")

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

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
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_list_then_transcribe_flow(
        self, mock_wav_audio: bytes, mock_audio_data: AudioData
    ):
        """Integration test: List providers then transcribe with selected provider."""
        mock_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=mock_audio_data,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="Integration test successful",
            confidence=0.93,
            latency_ms=180,
        )

        # Mock STT providers dict (used by list_providers endpoint)
        mock_providers_dict = {"azure": AsyncMock(), "deepgram": AsyncMock()}

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_wav_audio),
            content_type="audio/wav",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_result,
            test_record_id,
            test_result_id,
        )

        # Mock DB session for list_providers endpoint (uses get_db_session)
        mock_session = MagicMock()

        # Mock credential repo to avoid real DB calls in list_providers
        mock_credential_repo = AsyncMock()
        mock_credential_repo.list_by_user = AsyncMock(return_value=[])

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers_dict
        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service
        app.dependency_overrides[get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.stt.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    # Step 1: List available providers
                    list_response = await ac.get("/api/v1/stt/providers")
                    assert list_response.status_code == 200
                    providers = list_response.json()["providers"]

                    # Find Azure provider
                    azure_provider = next((p for p in providers if p["name"] == "azure"), None)
                    assert azure_provider is not None

                    # Step 2: Use selected provider to transcribe
                    files = {"audio": ("test.wav", io.BytesIO(mock_wav_audio), "audio/wav")}
                    data = {
                        "provider": azure_provider["name"],
                        "language": "en-US",
                    }

                    transcribe_response = await ac.post(
                        "/api/v1/stt/transcribe", files=files, data=data
                    )

            assert transcribe_response.status_code == 200
            result = transcribe_response.json()
            assert result["transcript"] == "Integration test successful"
            assert result["provider"] == "azure"
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)
            app.dependency_overrides.pop(get_db_session, None)
