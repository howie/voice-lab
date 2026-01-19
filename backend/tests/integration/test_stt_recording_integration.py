"""Integration tests for STT recording → transcribe flow.

Feature: 003-stt-testing-module
T038: Integration test for recording → transcribe flow

Tests the complete flow from receiving recorded audio blob to transcription.
"""

import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.use_cases.transcribe_audio import (
    TranscribeAudioOutput,
    TranscribeAudioUseCase,
)
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


@pytest.fixture
def mock_transcribe_output(mock_stt_result: STTResult) -> TranscribeAudioOutput:
    """Create a mock transcribe use case output."""
    return TranscribeAudioOutput(
        result=mock_stt_result,
        wer=None,
        cer=None,
        record_id="test-record-456",
    )


class TestSTTRecordingIntegration:
    """Integration tests for recording → transcription flow."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self):
        """Override database dependencies."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        async def get_mock_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = get_mock_session
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_webm_recording_transcription(
        self, mock_audio_data: AudioData, mock_transcribe_output: TranscribeAudioOutput
    ):
        """Test transcription of WebM recorded audio (Chrome/Firefox)."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_transcribe_output.result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            # Simulate WebM audio blob from browser recording
            webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100  # WebM header signature

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
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_mp4_recording_transcription(
        self, mock_audio_data: AudioData, mock_transcribe_output: TranscribeAudioOutput
    ):
        """Test transcription of MP4 recorded audio (Safari fallback)."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_transcribe_output.result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            # Simulate MP4/M4A audio blob from Safari recording
            mp4_audio = b"\x00\x00\x00\x20ftyp" + b"\x00" * 100  # MP4 header signature

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
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_recording_with_child_mode(
        self, mock_audio_data: AudioData, mock_transcribe_output: TranscribeAudioOutput
    ):
        """Test recording transcription with child mode enabled."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_transcribe_output.result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

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

            # Verify child_mode was passed to use case
            call_args = mock_provider.transcribe.call_args[0][0]
            assert call_args.child_mode is True
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_recording_with_ground_truth(
        self, mock_audio_data: AudioData, mock_stt_result: STTResult
    ):
        """Test recording transcription with ground truth for WER calculation."""
        # Create output with CER (since it's Chinese)
        output_with_cer = TranscribeAudioOutput(
            result=mock_stt_result,
            wer=0.15,
            cer=0.08,
            record_id="test-record-789",
        )

        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = output_with_cer.result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

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
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_recording_with_multiple_providers(self, mock_audio_data: AudioData):
        """Test recording transcription with different providers."""
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

        mock_azure = AsyncMock()
        mock_azure.transcribe.return_value = azure_result

        mock_gcp = AsyncMock()
        mock_gcp.transcribe.return_value = gcp_result

        mock_providers = {"azure": mock_azure, "gcp": mock_gcp}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Test Azure
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {"provider": "azure", "language": "zh-TW"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

                assert response.status_code == 200
                assert response.json()["transcript"] == "Azure 辨識結果"

                # Test GCP
                files = {"audio": ("recording.webm", io.BytesIO(webm_audio), "audio/webm")}
                data = {"provider": "gcp", "language": "zh-TW"}
                response = await ac.post("/api/v1/stt/transcribe", files=files, data=data)

                assert response.status_code == 200
                assert response.json()["transcript"] == "GCP 辨識結果"
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_recording_word_timings_preserved(
        self, mock_audio_data: AudioData, mock_transcribe_output: TranscribeAudioOutput
    ):
        """Test that word timings are preserved in transcription response."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_transcribe_output.result

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=mock_providers)

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

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
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)

    @pytest.mark.asyncio
    async def test_recording_saves_to_history(
        self, mock_audio_data: AudioData, mock_transcribe_output: TranscribeAudioOutput
    ):
        """Test that recording transcription can be saved to history."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.return_value = mock_transcribe_output.result

        # Create mock repository to enable saving to history
        mock_repo = AsyncMock()
        mock_record = MagicMock()
        mock_record.id = "test-record-456"
        mock_repo.save.return_value = mock_record

        mock_providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(
            stt_providers=mock_providers,
            test_record_repo=mock_repo,
        )

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers
        app.dependency_overrides[get_transcribe_audio_use_case] = lambda: use_case

        try:
            webm_audio = b"\x1a\x45\xdf\xa3" + b"\x00" * 100

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

            # Should have ID when saved to history
            assert "id" in result
            assert result["id"] == "test-record-456"

            # Verify repo was called
            mock_repo.save.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
            app.dependency_overrides.pop(get_transcribe_audio_use_case, None)
