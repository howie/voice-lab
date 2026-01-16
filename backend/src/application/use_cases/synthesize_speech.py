"""Synthesize Speech Use Case."""

from dataclasses import dataclass

from src.application.interfaces.tts_provider import ITTSProvider
from src.application.interfaces.storage_service import IStorageService
from src.domain.entities.audio import AudioFormat
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.entities.test_record import TestRecord
from src.domain.repositories.test_record_repository import ITestRecordRepository


@dataclass
class SynthesizeSpeechInput:
    """Input for synthesize speech use case."""

    text: str
    provider_name: str
    voice_id: str
    language: str = "zh-TW"
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    output_format: AudioFormat = AudioFormat.MP3
    user_id: str = ""
    save_to_storage: bool = True
    save_to_history: bool = True


@dataclass
class SynthesizeSpeechOutput:
    """Output from synthesize speech use case."""

    result: TTSResult
    audio_url: str | None = None
    record_id: str | None = None


class SynthesizeSpeechUseCase:
    """Use case for synthesizing speech from text.

    This use case orchestrates:
    1. Validating and creating the TTS request
    2. Calling the appropriate TTS provider
    3. Optionally saving audio to storage
    4. Optionally saving test record to history
    """

    def __init__(
        self,
        tts_providers: dict[str, ITTSProvider],
        storage_service: IStorageService | None = None,
        test_record_repo: ITestRecordRepository | None = None,
    ):
        """Initialize use case with dependencies.

        Args:
            tts_providers: Dictionary of provider name to provider instance
            storage_service: Optional storage service for audio files
            test_record_repo: Optional repository for test records
        """
        self._tts_providers = tts_providers
        self._storage = storage_service
        self._test_record_repo = test_record_repo

    async def execute(self, input_data: SynthesizeSpeechInput) -> SynthesizeSpeechOutput:
        """Execute the synthesize speech use case.

        Args:
            input_data: Use case input

        Returns:
            Use case output with synthesis result

        Raises:
            ValueError: If provider not found or invalid parameters
            TTSProviderError: If synthesis fails
        """
        # Get provider
        provider = self._tts_providers.get(input_data.provider_name)
        if not provider:
            available = list(self._tts_providers.keys())
            raise ValueError(
                f"Provider '{input_data.provider_name}' not found. "
                f"Available: {available}"
            )

        # Create domain request
        request = TTSRequest(
            text=input_data.text,
            voice_id=input_data.voice_id,
            provider=input_data.provider_name,
            language=input_data.language,
            speed=input_data.speed,
            pitch=input_data.pitch,
            volume=input_data.volume,
            output_format=input_data.output_format,
        )

        # Call provider
        result = await provider.synthesize(request)

        # Save to storage if requested
        audio_url = None
        if input_data.save_to_storage and self._storage:
            import uuid

            key = f"tts/{uuid.uuid4()}.{result.audio.format.value}"
            stored = await self._storage.upload(
                key=key,
                data=result.audio.data,
                content_type=result.audio.format.mime_type,
            )
            audio_url = stored.url

        # Save to history if requested
        record_id = None
        if input_data.save_to_history and self._test_record_repo and input_data.user_id:
            record = TestRecord.from_tts_result(input_data.user_id, result)
            if audio_url:
                record.metadata["audio_url"] = audio_url
            saved = await self._test_record_repo.save(record)
            record_id = str(saved.id)

        return SynthesizeSpeechOutput(
            result=result,
            audio_url=audio_url,
            record_id=record_id,
        )
