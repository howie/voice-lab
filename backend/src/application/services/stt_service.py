"""STT Service."""

import os
from uuid import UUID

from src.application.interfaces.storage_service import IStorageService
from src.domain.entities.audio import AudioData
from src.domain.entities.stt import STTRequest, STTResult
from src.domain.repositories.provider_credential_repository import IProviderCredentialRepository
from src.domain.repositories.transcription_repository import ITranscriptionRepository
from src.infrastructure.providers.stt.factory import STTProviderFactory


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
    ) -> tuple[STTResult, UUID, UUID]:
        """Transcribe an audio file using the specified provider.

        Args:
            user_id: ID of the user requesting transcription
            audio_file_id: ID of the audio file to transcribe
            provider_name: Name of the STT provider (e.g., 'azure', 'deepgram')
            language: Language code (default: zh-TW)
            child_mode: Whether to enable child voice optimization

        Returns:
            Tuple of (STTResult object, transcription_record_id, result_id)

        Raises:
            ValueError: If audio file not found, access denied, or provider error
            RuntimeError: If transcription fails
        """
        # 1. Get Audio File Info
        audio_file = await self._transcription_repo.get_audio_file(audio_file_id)
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")

        if str(audio_file.user_id) != str(user_id):
            raise ValueError("Access denied to audio file")

        # 2. Load Audio Data
        try:
            audio_bytes = await self._storage_service.load(audio_file.storage_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file: {e}") from e

        # Ensure we have bytes
        if not isinstance(audio_bytes, bytes):
            raise RuntimeError("Storage service returned non-bytes data")

        audio_data = AudioData(
            data=audio_bytes,
            format=audio_file.format,
            sample_rate=audio_file.sample_rate,
        )

        # 3. Get Credentials (BYOL or System Fallback)
        credentials = {}
        user_cred = await self._credential_repo.get_by_user_and_provider(user_id, provider_name)

        if user_cred:
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
                provider = STTProviderFactory.create(provider_name, system_creds)
            else:
                # If we really can't create it (and original error was due to missing creds)
                raise ValueError(
                    f"Provider '{provider_name}' not configured (no user or system credentials)"
                ) from None

        # 5. Transcribe
        request = STTRequest(
            provider=provider_name,
            language=language,
            audio=audio_data,
            child_mode=child_mode,
        )

        result = await provider.transcribe(request)

        # 6. Save Result
        record_id, result_id = await self._transcription_repo.save_transcription(
            result, audio_file_id, user_id
        )

        return result, record_id, result_id
