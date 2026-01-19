"""Contract tests for STT Transcribe API endpoint.

Feature: 003-stt-testing-module
T023: Contract test for POST /stt/transcribe endpoint

Tests the transcription endpoint request/response contract.
"""

import io
import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.interfaces.storage_service import StoredFile
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import (
    get_storage_service,
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
def mock_audio_file() -> bytes:
    """Generate mock audio file content."""
    # Minimal WAV header + data for testing
    return b"RIFF" + b"\x00" * 40 + b"\x00\x01" * 500


@pytest.fixture
def mock_audio_data() -> AudioData:
    """Create mock audio data for testing."""
    return AudioData(
        data=b"\x00\x01" * 500,
        format=AudioFormat.WAV,
        sample_rate=16000,
    )


@pytest.fixture
def mock_stt_result(mock_audio_data: AudioData) -> STTResult:
    """Create a mock STT result for testing."""
    request = STTRequest(
        provider="azure",
        language="en-US",
        audio=mock_audio_data,
    )
    return STTResult(
        request=request,
        transcript="Hello world, this is a test.",
        confidence=0.95,
        latency_ms=150,
        words=[
            WordTiming(word="Hello", start_ms=0, end_ms=500, confidence=0.98),
            WordTiming(word="world", start_ms=500, end_ms=1000, confidence=0.96),
        ],
    )


class TestTranscribeEndpoint:
    """Contract tests for POST /api/v1/stt/transcribe endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_current_user):
        """Override database and auth dependencies."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        async def get_mock_session():
            yield mock_session

        async def get_mock_current_user():
            return mock_current_user

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_current_user] = get_mock_current_user
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_audio_file: bytes, mock_stt_result: STTResult):
        """T023: Test successful transcription with required response fields."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/user-id/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_audio_file),
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
                files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "en-US",
                    "child_mode": "false",
                    "save_to_history": "true",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Verify required response fields per frontend TranscriptionResponse type
            assert "transcript" in result
            assert "provider" in result
            assert "language" in result
            assert "latency_ms" in result
            assert "confidence" in result

            # Verify types
            assert isinstance(result["transcript"], str)
            assert isinstance(result["provider"], str)
            assert isinstance(result["language"], str)
            assert isinstance(result["latency_ms"], int)
            assert isinstance(result["confidence"], float)

            # Verify values
            assert result["transcript"] == "Hello world, this is a test."
            assert result["provider"] == "azure"
            assert result["confidence"] == 0.95
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_transcribe_with_word_timings(
        self, mock_audio_file: bytes, mock_stt_result: STTResult
    ):
        """T023: Test transcription returns word timings in correct format."""
        # Mock dependencies
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/user-id/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_audio_file),
            content_type="audio/wav",
        )

        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        mock_stt_service = AsyncMock()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            uuid.uuid4(),
            uuid.uuid4(),
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
                data = {"provider": "azure", "language": "en-US"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Check 'words' field (new format)
            assert "words" in result
            assert isinstance(result["words"], list)
            assert len(result["words"]) == 2

            # Verify word timing schema
            word = result["words"][0]
            assert "word" in word
            assert "start_ms" in word
            assert "end_ms" in word

            assert word["word"] == "Hello"
            assert isinstance(word["start_ms"], int)
            assert isinstance(word["end_ms"], int)
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_transcribe_with_ground_truth(
        self, mock_audio_file: bytes, mock_audio_data: AudioData
    ):
        """T023: Test transcription with ground truth returns WER analysis."""
        # Create result matching the ground truth exactly (0% error)
        request = STTRequest(provider="azure", language="en-US", audio=mock_audio_data)
        result_with_gt = STTResult(
            request=request,
            transcript="Hello world, this is a test.",
            confidence=0.95,
            latency_ms=150,
        )

        # Mock dependencies
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/user-id/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_audio_file),
            content_type="audio/wav",
        )

        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None
        mock_repo.save_ground_truth.return_value = None

        mock_stt_service = AsyncMock()
        mock_stt_service.transcribe_audio.return_value = (
            result_with_gt,
            uuid.uuid4(),
            uuid.uuid4(),
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "en-US",
                    "ground_truth": "Hello world, this is a test.",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Check WER analysis
            assert "wer_analysis" in result
            if result["wer_analysis"]:
                analysis = result["wer_analysis"]
                assert "error_rate" in analysis
                assert "error_type" in analysis
                assert "insertions" in analysis
                assert "deletions" in analysis
                assert "substitutions" in analysis
                assert "total_reference" in analysis

                assert analysis["error_type"] in ["WER", "CER"]
                assert isinstance(analysis["error_rate"], float)
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_transcribe_missing_audio_file(self):
        """T023: Test validation error when audio file is missing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            data = {"provider": "azure", "language": "en-US"}
            response = await ac.post("/api/v1/stt/transcribe", data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transcribe_missing_provider(self, mock_audio_file: bytes):
        """T023: Test validation error when provider is missing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
            data = {"language": "en-US"}
            response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transcribe_invalid_provider(self, mock_audio_file: bytes):
        """T023: Test error when provider is not supported."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
            data = {"provider": "invalid_provider", "language": "en-US"}
            response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

        assert response.status_code == 400
        result = response.json()
        assert "detail" in result

    @pytest.mark.asyncio
    async def test_transcribe_file_too_large(self):
        """T023: Test error when file exceeds provider limit."""
        # Create a large file (> 25MB for Whisper)
        large_audio = b"\x00" * (26 * 1024 * 1024)  # 26MB

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            files = {"audio": ("test.wav", io.BytesIO(large_audio), "audio/wav")}
            data = {"provider": "whisper", "language": "en-US"}
            response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "size" in result["detail"].lower() or "limit" in result["detail"].lower()

    @pytest.mark.asyncio
    async def test_transcribe_with_child_mode(
        self, mock_audio_file: bytes, mock_stt_result: STTResult
    ):
        """T023: Test transcription with child mode enabled."""
        # Mock dependencies
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/user-id/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_audio_file),
            content_type="audio/wav",
        )

        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        mock_stt_service = AsyncMock()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            uuid.uuid4(),
            uuid.uuid4(),
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "child_mode": "true",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200

            # Verify child_mode was passed to STT service
            call_args = mock_stt_service.transcribe_audio.call_args
            assert call_args[1]["child_mode"] is True
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_transcribe_chinese_uses_cer(
        self, mock_audio_file: bytes, mock_audio_data: AudioData
    ):
        """T023: Test that Chinese language uses CER instead of WER."""
        # Create Chinese result
        chinese_request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=mock_audio_data,
        )
        chinese_result = STTResult(
            request=chinese_request,
            transcript="你好世界",
            confidence=0.92,
            latency_ms=150,
        )

        # Mock dependencies
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/user-id/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_audio_file),
            content_type="audio/wav",
        )

        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None
        mock_repo.save_ground_truth.return_value = None

        mock_stt_service = AsyncMock()
        mock_stt_service.transcribe_audio.return_value = (
            chinese_result,
            uuid.uuid4(),
            uuid.uuid4(),
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
                data = {
                    "provider": "azure",
                    "language": "zh-TW",
                    "ground_truth": "你好世界",
                }
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # For Chinese, should use CER
            if result.get("wer_analysis"):
                assert result["wer_analysis"]["error_type"] == "CER"
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_transcribe_response_includes_id(
        self, mock_audio_file: bytes, mock_stt_result: STTResult
    ):
        """T023: Test transcription response includes result ID."""
        # Mock dependencies
        mock_storage = AsyncMock()
        mock_storage.upload.return_value = StoredFile(
            key="stt/uploads/user-id/test.wav",
            url="http://storage/test.wav",
            size_bytes=len(mock_audio_file),
            content_type="audio/wav",
        )

        mock_repo = AsyncMock()
        mock_repo.save_audio_file.return_value = None

        test_result_id = uuid.uuid4()
        mock_stt_service = AsyncMock()
        mock_stt_service.transcribe_audio.return_value = (
            mock_stt_result,
            uuid.uuid4(),
            test_result_id,
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_transcription_repository] = lambda: mock_repo
        app.dependency_overrides[get_stt_service] = lambda: mock_stt_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                files = {"audio": ("test.wav", io.BytesIO(mock_audio_file), "audio/wav")}
                data = {"provider": "azure", "save_to_history": "true"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Should have an ID when saved to history
            assert "id" in result
            assert result["id"] == str(test_result_id)
        finally:
            app.dependency_overrides.pop(get_storage_service, None)
            app.dependency_overrides.pop(get_transcription_repository, None)
            app.dependency_overrides.pop(get_stt_service, None)

    @pytest.mark.asyncio
    async def test_transcribe_different_audio_formats(self, mock_stt_result: STTResult):
        """T023: Test transcription accepts different audio formats."""
        formats = [
            ("test.mp3", "audio/mpeg"),
            ("test.wav", "audio/wav"),
            ("test.webm", "audio/webm"),
            ("test.m4a", "audio/mp4"),
            ("test.flac", "audio/flac"),
        ]

        for filename, content_type in formats:
            mock_audio = b"\x00\x01" * 500

            # Mock dependencies for each iteration
            mock_storage = AsyncMock()
            mock_storage.upload.return_value = StoredFile(
                key=f"stt/uploads/user-id/{filename}",
                url=f"http://storage/{filename}",
                size_bytes=len(mock_audio),
                content_type=content_type,
            )

            mock_repo = AsyncMock()
            mock_repo.save_audio_file.return_value = None

            mock_stt_service = AsyncMock()
            mock_stt_service.transcribe_audio.return_value = (
                mock_stt_result,
                uuid.uuid4(),
                uuid.uuid4(),
            )

            app.dependency_overrides[get_storage_service] = lambda storage=mock_storage: storage
            app.dependency_overrides[get_transcription_repository] = lambda repo=mock_repo: repo
            app.dependency_overrides[get_stt_service] = lambda service=mock_stt_service: service

            try:
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    files = {"audio": (filename, io.BytesIO(mock_audio), content_type)}
                    data = {"provider": "azure"}
                    response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

                assert response.status_code == 200, f"Failed for format: {filename}"
            finally:
                app.dependency_overrides.pop(get_storage_service, None)
                app.dependency_overrides.pop(get_transcription_repository, None)
                app.dependency_overrides.pop(get_stt_service, None)
