"""STT Service."""

import logging
import os
from uuid import UUID

from src.application.interfaces.storage_service import IStorageService
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult
from src.domain.repositories.provider_credential_repository import IProviderCredentialRepository
from src.domain.repositories.transcription_repository import ITranscriptionRepository
from src.infrastructure.providers.stt.factory import STTProviderFactory

logger = logging.getLogger(__name__)


class STTService:
    """Service for orchestrating STT operations."""

    def __init__(
        self,
        transcription_repo: ITranscriptionRepository,
        credential_repo: IProviderCredentialRepository,
        storage_service: IStorageService,
    ):
        self._transcription_repo = transcription_repo
        self._credential_repo = credential_repo
        self._storage_service = storage_service

    async def transcribe_audio(
        self,
        user_id: UUID,
        audio_file_id: UUID,
        provider_name: str,
        language: str = "zh-TW",
        child_mode: bool = False,
        enable_diarization: bool = False,
    ) -> tuple[STTResult, UUID, UUID]:
        """Transcribe an audio file using the specified provider.

        Args:
            user_id: ID of the user requesting transcription
            audio_file_id: ID of the audio file to transcribe
            provider_name: Name of the STT provider (e.g., 'azure', 'deepgram')
            language: Language code (default: zh-TW)
            child_mode: Whether to enable child voice optimization
            enable_diarization: Whether to enable speaker diarization

        Returns:
            Tuple of (STTResult object, transcription_record_id, result_id)

        Raises:
            ValueError: If audio file not found, access denied, or provider error
            RuntimeError: If transcription fails
        """
        logger.info(
            f"Starting STT transcription: user_id={user_id}, audio_file_id={audio_file_id}, "
            f"provider={provider_name}, language={language}, child_mode={child_mode}, "
            f"enable_diarization={enable_diarization}"
        )

        # 1. Get Audio File Info
        audio_file = await self._transcription_repo.get_audio_file(audio_file_id)
        if not audio_file:
            logger.error(f"Audio file not found: {audio_file_id}")
            raise ValueError(f"Audio file {audio_file_id} not found")

        if str(audio_file.user_id) != str(user_id):
            logger.warning(f"Access denied to audio file {audio_file_id} for user {user_id}")
            raise ValueError("Access denied to audio file")

        # 2. Load Audio Data
        logger.debug(f"Loading audio data from storage: {audio_file.storage_path}")
        try:
            audio_bytes = await self._storage_service.download(audio_file.storage_path)
        except Exception as e:
            logger.error(f"Failed to load audio file from storage: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load audio file: {e}") from e

        # Ensure we have bytes
        if not isinstance(audio_bytes, bytes):
            raise RuntimeError("Storage service returned non-bytes data")

        audio_data = AudioData(
            data=audio_bytes,
            format=AudioFormat(audio_file.format),
            sample_rate=audio_file.sample_rate,
        )

        # 3. Get Credentials (BYOL or System Fallback)
        logger.debug(f"Fetching credentials for provider: {provider_name}")
        credentials = {}
        user_cred = await self._credential_repo.get_by_user_and_provider(user_id, provider_name)

        if user_cred:
            logger.info(f"Using user BYOL credential for provider: {provider_name}")
            credentials["api_key"] = user_cred.api_key
            if provider_name == "azure":
                # Azure needs subscription_key, map api_key to it if needed, or Factory handles it
                # Factory _create_azure checks 'subscription_key' or 'api_key'. So 'api_key' is fine.
                pass

        # 4. Create Provider
        try:
            # Try with user credentials (or empty if none)
            provider = STTProviderFactory.create(provider_name, credentials)
        except ValueError:
            # Fallback to system credentials from environment variables
            system_creds = {}
            if provider_name == "azure":
                system_creds["subscription_key"] = os.getenv("AZURE_SPEECH_KEY")
                system_creds["region"] = os.getenv("AZURE_SPEECH_REGION")
            elif provider_name == "deepgram":
                system_creds["api_key"] = os.getenv("DEEPGRAM_API_KEY")
            elif provider_name == "assemblyai":
                system_creds["api_key"] = os.getenv("ASSEMBLYAI_API_KEY")
            elif provider_name == "elevenlabs":
                system_creds["api_key"] = os.getenv("ELEVENLABS_API_KEY")
            elif provider_name == "speechmatics":
                system_creds["api_key"] = os.getenv("SPEECHMATICS_API_KEY")
            elif provider_name == "whisper":
                system_creds["api_key"] = os.getenv("OPENAI_API_KEY")
            elif provider_name == "gcp":
                # GCP often uses ADC, so empty credentials might work if environment is set up
                # Factory looks for 'service_account_json' or 'project_id'
                pass

            # Filter out None values
            system_creds = {k: v for k, v in system_creds.items() if v}

            if system_creds or provider_name == "gcp":
                logger.info(f"Using system credentials for provider: {provider_name}")
                provider = STTProviderFactory.create(provider_name, system_creds)
            else:
                # If we really can't create it (and original error was due to missing creds)
                logger.error(f"No credentials available for provider: {provider_name}")
                raise ValueError(
                    f"Provider '{provider_name}' not configured (no user or system credentials)"
                ) from None

        # 5. Transcribe
        request = STTRequest(
            provider=provider_name,
            language=language,
            audio=audio_data,
            child_mode=child_mode,
            enable_diarization=enable_diarization,
        )

        logger.debug(f"Calling provider.transcribe for: {provider_name}")
        result = await provider.transcribe(request)

        logger.info(
            f"Transcription completed: provider={provider_name}, "
            f"latency_ms={result.latency_ms}, confidence={result.confidence}"
        )

        # 6. Save Result
        record_id, result_id = await self._transcription_repo.save_transcription(
            result, audio_file_id, user_id
        )

        logger.info(f"Transcription saved: record_id={record_id}, result_id={result_id}")

        return result, record_id, result_id
