"""Transcribe Audio Use Case."""

from dataclasses import dataclass

from src.application.interfaces.stt_provider import ISTTProvider
from src.domain.entities.audio import AudioData
from src.domain.entities.stt import STTRequest, STTResult
from src.domain.entities.test_record import TestRecord
from src.domain.repositories.test_record_repository import ITestRecordRepository


@dataclass
class TranscribeAudioInput:
    """Input for transcribe audio use case."""

    provider_name: str
    audio: AudioData | None = None
    audio_url: str | None = None
    language: str = "zh-TW"
    child_mode: bool = False
    ground_truth: str | None = None  # For WER calculation
    user_id: str = ""
    save_to_history: bool = True


@dataclass
class TranscribeAudioOutput:
    """Output from transcribe audio use case."""

    result: STTResult
    wer: float | None = None
    cer: float | None = None
    record_id: str | None = None


class TranscribeAudioUseCase:
    """Use case for transcribing audio to text.

    This use case orchestrates:
    1. Validating the transcription request
    2. Calling the appropriate STT provider
    3. Optionally calculating WER/CER
    4. Optionally saving test record to history
    """

    def __init__(
        self,
        stt_providers: dict[str, ISTTProvider],
        test_record_repo: ITestRecordRepository | None = None,
    ):
        """Initialize use case with dependencies.

        Args:
            stt_providers: Dictionary of provider name to provider instance
            test_record_repo: Optional repository for test records
        """
        self._stt_providers = stt_providers
        self._test_record_repo = test_record_repo

    async def execute(self, input_data: TranscribeAudioInput) -> TranscribeAudioOutput:
        """Execute the transcribe audio use case.

        Args:
            input_data: Use case input

        Returns:
            Use case output with transcription result

        Raises:
            ValueError: If provider not found or invalid parameters
            STTProviderError: If transcription fails
        """
        # Get provider
        provider = self._stt_providers.get(input_data.provider_name)
        if not provider:
            available = list(self._stt_providers.keys())
            raise ValueError(
                f"Provider '{input_data.provider_name}' not found. "
                f"Available: {available}"
            )

        # Create domain request
        request = STTRequest(
            provider=input_data.provider_name,
            audio=input_data.audio,
            audio_url=input_data.audio_url,
            language=input_data.language,
            child_mode=input_data.child_mode,
        )

        # Call provider
        result = await provider.transcribe(request)

        # Calculate WER/CER if ground truth provided
        wer = None
        cer = None
        if input_data.ground_truth:
            from src.domain.services import calculate_cer, calculate_wer

            wer = calculate_wer(input_data.ground_truth, result.transcript)
            cer = calculate_cer(input_data.ground_truth, result.transcript)

        # Save to history if requested
        record_id = None
        if input_data.save_to_history and self._test_record_repo and input_data.user_id:
            record = TestRecord.from_stt_result(input_data.user_id, result)
            if wer is not None:
                record.metadata["wer"] = wer
            if cer is not None:
                record.metadata["cer"] = cer
            if input_data.ground_truth:
                record.metadata["ground_truth"] = input_data.ground_truth
            saved = await self._test_record_repo.save(record)
            record_id = str(saved.id)

        return TranscribeAudioOutput(
            result=result,
            wer=wer,
            cer=cer,
            record_id=record_id,
        )
