"""Integration tests for STT recording → transcribe flow.

Feature: 003-stt-testing-module
T038: Integration test for recording → transcribe flow

Tests the complete flow from receiving recorded audio blob to transcription.
"""

import io
import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.interfaces.storage_service import StoredFile
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.main import app
from src.presentation.api.dependencies import (
    get_stt_service,
    get_storage_service,
    get_transcription_repository,
)


@pytest.fixture
def mock_audio_data() -> AudioData:
    """Create mock audio data for testing."""
    return AudioData(
        data=b"\x00\x01" * 500,
        format=AudioFormat.WEBM,
        sample_rate=16000,
    )


@pytest.fixture
def mock_stt_result(mock_audio_data: AudioData) -> STTResult:
    """Create a mock STT result."""
    request = STTRequest(
        provider="azure",
        language="zh-TW",
        audio=mock_audio_data,
    )
    return STTResult(
        request=request,
        transcript="這是一段測試錄音",
        confidence=0.92,
        latency_ms=180,
        words=[
            WordTiming(word="這是", start_ms=0, end_ms=300, confidence=0.95),
            WordTiming(word="一段", start_ms=300, end_ms=600, confidence=0.90),
            WordTiming(word="測試", start_ms=600, end_ms=900, confidence=0.92),
            WordTiming(word="錄音", start_ms=900, end_ms=1200, confidence=0.88),
        ],
    )


class TestSTTRecordingIntegration:
    """Integration tests for recording → transcription flow."""

    @pytest.mark.asyncio
    async def test_webm_recording_transcription(self, mock_stt_result: STTResult):
        """Test transcription of WebM recorded audio (Chrome/Firefox)."""
        # Mock storage service
        mock_storage = AsyncMock()
        webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.webm",
            url="http://storage/test.webm",
            size_bytes=len(webm_audio),
            content_type="audio/webm",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            assert result["transcript"] == "這是一段測試錄音"
            assert result["provider"] == "azure"
            assert result["language"] == "zh-TW"
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_mp4_recording_transcription(self, mock_stt_result: STTResult):
        """Test transcription of MP4 recorded audio (Safari fallback)."""
        # Mock storage service
        mock_storage = AsyncMock()
        mp4_audio = b"\x00\x00\x00\x20ftyp" + b"\x00" * 100
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.mp4",
            url="http://storage/test.mp4",
            size_bytes=len(mp4_audio),
            content_type="audio/mp4",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("recording.mp4", io.BytesIO(mp4_audio), "audio/mp4")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            assert result["transcript"] == "這是一段測試錄音"
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_recording_with_child_mode(self, mock_stt_result: STTResult):
        """Test recording transcription with child mode enabled."""
        webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.webm",
            url="http://storage/test.webm",
            size_bytes=len(webm_audio),
            content_type="audio/webm",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
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
    async def test_recording_with_ground_truth(self, mock_stt_result: STTResult):
        """Test recording transcription with ground truth for WER calculation."""
        webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.webm",
            url="http://storage/test.webm",
            size_bytes=len(webm_audio),
            content_type="audio/webm",
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
            mock_stt_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "ground_truth": "這是一段測試錄音",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Chinese uses CER
            if result.get("wer_analysis"):
                assert result["wer_analysis"]["error_type"] == "CER"

            # Verify ground truth was saved
            mock_repo.save_ground_truth.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_recording_with_multiple_providers(self, mock_audio_data: AudioData):
        """Test recording transcription with different providers."""
        webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

        # Setup Azure result
        azure_request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=mock_audio_data,
        )
        azure_result = STTResult(
            request=azure_request,
            transcript="Azure 辨識結果",
            confidence=0.92,
            latency_ms=150,
        )

        # Setup GCP result
        gcp_request = STTRequest(
            provider="gcp",
            language="zh-TW",
            audio=mock_audio_data,
        )
        gcp_result = STTResult(
            request=gcp_request,
            transcript="GCP 辨識結果",
            confidence=0.88,
            latency_ms=180,
        )

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.webm",
            url="http://storage/test.webm",
            size_bytes=len(webm_audio),
            content_type="audio/webm",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service - will return different results based on provider
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Test Azure
                mock_stt_service.transcribe_audio.return_value = (
                    azure_result,
                    test_record_id,
                    test_result_id,
                )
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {"provider": "azure", "language": "zh-TW"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

                assert response.status_code == 200
                assert response.json()["transcript"] == "Azure 辨識結果"

                # Test GCP
                mock_stt_service.transcribe_audio.return_value = (
                    gcp_result,
                    test_record_id,
                    test_result_id,
                )
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {"provider": "gcp", "language": "zh-TW"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

                assert response.status_code == 200
                assert response.json()["transcript"] == "GCP 辨識結果"
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_recording_word_timings_preserved(self, mock_stt_result: STTResult):
        """Test that word timings are preserved in transcription response."""
        webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.webm",
            url="http://storage/test.webm",
            size_bytes=len(webm_audio),
            content_type="audio/webm",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {"provider": "azure", "language": "zh-TW"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Check word timings
            assert "words" in result
            assert len(result["words"]) == 4

            # Verify first word
            assert result["words"][0]["word"] == "這是"
            assert result["words"][0]["start_ms"] == 0
            assert result["words"][0]["end_ms"] == 300
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_recording_saves_to_history(self, mock_stt_result: STTResult):
        """Test that recording transcription can be saved to history."""
        webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/test-user/test.webm",
            url="http://storage/test.webm",
            size_bytes=len(webm_audio),
            content_type="audio/webm",
        )

        # Mock transcription repository
        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        # Mock STT service
        mock_stt_service = AsyncMock()
        test_record_id = uuid.uuid4()
        test_result_id = uuid.uuid4()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            test_record_id,
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "save_to_history": "true",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Should have ID (result_id is returned as id)
            assert "id" in result
            assert result["id"] == str(test_result_id)

            # Verify audio file and transcription were saved
            mock_repo.save_audio_file.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)
