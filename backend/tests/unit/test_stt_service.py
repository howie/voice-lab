"""Unit tests for STT Service (TranscribeAudioUseCase).

Feature: 003-stt-testing-module
T025: Unit test for STTService.transcribe() (TranscribeAudioUseCase.execute())

Tests the transcription use case business logic.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.transcribe_audio import (
    TranscribeAudioInput,
    TranscribeAudioOutput,
    TranscribeAudioUseCase,
)
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult, WordTiming


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
    """Create a mock STT result."""
    request = STTRequest(
        provider="azure",
        language="zh-TW",
        audio=mock_audio_data,
    )
    return STTResult(
        request=request,
        transcript="你好世界",
        confidence=0.92,
        latency_ms=150,
        words=[
            WordTiming(word="你好", start_ms=0, end_ms=500, confidence=0.95),
            WordTiming(word="世界", start_ms=500, end_ms=1000, confidence=0.90),
        ],
    )


@pytest.fixture
def mock_stt_provider(mock_stt_result: STTResult) -> MagicMock:
    """Create a mock STT provider."""
    provider = AsyncMock()
    provider.transcribe.return_value = mock_stt_result
    provider.supports_streaming = True
    return provider


@pytest.fixture
def mock_test_record_repo() -> AsyncMock:
    """Create a mock test record repository."""
    repo = AsyncMock()
    mock_record = MagicMock()
    mock_record.id = "test-record-123"
    repo.save.return_value = mock_record
    return repo


class TestTranscribeAudioUseCase:
    """Unit tests for TranscribeAudioUseCase."""

    def test_init_with_providers(self, mock_stt_provider: MagicMock):
        """Test use case initialization with providers."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        assert use_case._stt_providers == providers

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
        mock_stt_result: STTResult,
    ):
        """Test successful transcription execution."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="zh-TW",
        )

        output = await use_case.execute(input_data)

        assert isinstance(output, TranscribeAudioOutput)
        assert output.result.transcript == "你好世界"
        assert output.result.provider == "azure"
        assert output.result.confidence == 0.92

        # Verify provider was called correctly
        mock_stt_provider.transcribe.assert_called_once()
        call_args = mock_stt_provider.transcribe.call_args[0][0]
        assert isinstance(call_args, STTRequest)
        assert call_args.provider == "azure"
        assert call_args.language == "zh-TW"

    @pytest.mark.asyncio
    async def test_execute_provider_not_found(self, mock_audio_data: AudioData):
        """Test error when provider not found."""
        providers = {"azure": MagicMock()}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="invalid_provider",
            audio=mock_audio_data,
        )

        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(input_data)

        assert "not found" in str(exc_info.value).lower()
        assert "invalid_provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_with_ground_truth_calculates_wer(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
    ):
        """Test WER calculation when ground truth is provided."""
        # Set up result with English transcript
        english_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=mock_audio_data,
        )
        english_result = STTResult(
            request=english_request,
            transcript="hello world",
            confidence=0.92,
            latency_ms=150,
        )
        mock_stt_provider.transcribe.return_value = english_result

        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="en-US",
            ground_truth="hello world",
        )

        output = await use_case.execute(input_data)

        # WER should be 0 for exact match
        assert output.wer is not None
        assert output.wer == 0.0
        assert output.cer is not None

    @pytest.mark.asyncio
    async def test_execute_wer_calculation_with_errors(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
    ):
        """Test WER calculation with transcription errors."""
        english_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=mock_audio_data,
        )
        result_with_errors = STTResult(
            request=english_request,
            transcript="hello word",  # "world" -> "word" is a substitution
            confidence=0.85,
            latency_ms=150,
        )
        mock_stt_provider.transcribe.return_value = result_with_errors

        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="en-US",
            ground_truth="hello world",
        )

        output = await use_case.execute(input_data)

        # WER should be > 0 due to error
        assert output.wer is not None
        assert output.wer > 0.0
        # 1 substitution out of 2 words = 0.5 WER
        assert output.wer == 0.5

    @pytest.mark.asyncio
    async def test_execute_with_child_mode(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
    ):
        """Test child mode is passed to provider."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="zh-TW",
            child_mode=True,
        )

        await use_case.execute(input_data)

        # Verify child_mode was passed in the request
        call_args = mock_stt_provider.transcribe.call_args[0][0]
        assert call_args.child_mode is True

    @pytest.mark.asyncio
    async def test_execute_saves_to_history(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
        mock_test_record_repo: AsyncMock,
    ):
        """Test transcription saves to history when enabled."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(
            stt_providers=providers,
            test_record_repo=mock_test_record_repo,
        )

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="zh-TW",
            user_id="user-123",
            save_to_history=True,
        )

        output = await use_case.execute(input_data)

        # Verify record was saved
        mock_test_record_repo.save.assert_called_once()
        assert output.record_id == "test-record-123"

    @pytest.mark.asyncio
    async def test_execute_does_not_save_when_disabled(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
        mock_test_record_repo: AsyncMock,
    ):
        """Test transcription does not save when save_to_history is False."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(
            stt_providers=providers,
            test_record_repo=mock_test_record_repo,
        )

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="zh-TW",
            user_id="user-123",
            save_to_history=False,
        )

        output = await use_case.execute(input_data)

        # Verify record was NOT saved
        mock_test_record_repo.save.assert_not_called()
        assert output.record_id is None

    @pytest.mark.asyncio
    async def test_execute_with_audio_url(
        self,
        mock_stt_provider: MagicMock,
        mock_stt_result: STTResult,
    ):
        """Test transcription with audio URL instead of data."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio_url="https://example.com/audio.mp3",
            language="zh-TW",
        )

        output = await use_case.execute(input_data)

        assert output.result.transcript == "你好世界"

        # Verify audio_url was passed
        call_args = mock_stt_provider.transcribe.call_args[0][0]
        assert call_args.audio_url == "https://example.com/audio.mp3"

    @pytest.mark.asyncio
    async def test_execute_multiple_providers(
        self,
        mock_audio_data: AudioData,
    ):
        """Test use case works with multiple providers."""
        azure_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=mock_audio_data,
        )
        azure_result = STTResult(
            request=azure_request,
            transcript="Azure transcript",
            confidence=0.90,
            latency_ms=100,
        )
        gcp_request = STTRequest(
            provider="gcp",
            language="en-US",
            audio=mock_audio_data,
        )
        gcp_result = STTResult(
            request=gcp_request,
            transcript="GCP transcript",
            confidence=0.88,
            latency_ms=120,
        )

        mock_azure = AsyncMock()
        mock_azure.transcribe.return_value = azure_result

        mock_gcp = AsyncMock()
        mock_gcp.transcribe.return_value = gcp_result

        providers = {"azure": mock_azure, "gcp": mock_gcp}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        # Test Azure
        input_azure = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
        )
        output_azure = await use_case.execute(input_azure)
        assert output_azure.result.transcript == "Azure transcript"

        # Test GCP
        input_gcp = TranscribeAudioInput(
            provider_name="gcp",
            audio=mock_audio_data,
        )
        output_gcp = await use_case.execute(input_gcp)
        assert output_gcp.result.transcript == "GCP transcript"

    @pytest.mark.asyncio
    async def test_execute_preserves_word_timings(
        self,
        mock_audio_data: AudioData,
        mock_stt_provider: MagicMock,
        mock_stt_result: STTResult,
    ):
        """Test word timings are preserved in output."""
        providers = {"azure": mock_stt_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
            language="zh-TW",
        )

        output = await use_case.execute(input_data)

        assert output.result.words is not None
        assert len(output.result.words) == 2
        assert output.result.words[0].word == "你好"
        assert output.result.words[0].start_ms == 0
        assert output.result.words[0].end_ms == 500

    @pytest.mark.asyncio
    async def test_execute_handles_provider_error(
        self,
        mock_audio_data: AudioData,
    ):
        """Test error handling when provider fails."""
        mock_provider = AsyncMock()
        mock_provider.transcribe.side_effect = Exception("Provider error")

        providers = {"azure": mock_provider}
        use_case = TranscribeAudioUseCase(stt_providers=providers)

        input_data = TranscribeAudioInput(
            provider_name="azure",
            audio=mock_audio_data,
        )

        with pytest.raises(Exception) as exc_info:
            await use_case.execute(input_data)

        assert "Provider error" in str(exc_info.value)


class TestTranscribeAudioInput:
    """Tests for TranscribeAudioInput data class."""

    def test_default_values(self):
        """Test default values are set correctly."""
        input_data = TranscribeAudioInput(provider_name="azure")

        assert input_data.provider_name == "azure"
        assert input_data.audio is None
        assert input_data.audio_url is None
        assert input_data.language == "zh-TW"
        assert input_data.child_mode is False
        assert input_data.ground_truth is None
        assert input_data.save_to_history is True

    def test_custom_values(self, mock_audio_data: AudioData):
        """Test custom values are set correctly."""
        input_data = TranscribeAudioInput(
            provider_name="gcp",
            audio=mock_audio_data,
            language="en-US",
            child_mode=True,
            ground_truth="test text",
            user_id="user-456",
            save_to_history=False,
        )

        assert input_data.provider_name == "gcp"
        assert input_data.audio == mock_audio_data
        assert input_data.language == "en-US"
        assert input_data.child_mode is True
        assert input_data.ground_truth == "test text"
        assert input_data.user_id == "user-456"
        assert input_data.save_to_history is False
