"""FastAPI Dependencies - Dependency Injection Container.

This module wires together all the layers of the application
following Clean Architecture principles.
"""

import os

from src.application.interfaces.llm_provider import ILLMProvider
from src.application.interfaces.storage_service import IStorageService
from src.application.interfaces.stt_provider import ISTTProvider
from src.application.interfaces.tts_provider import ITTSProvider
from src.application.use_cases.compare_providers import CompareProvidersUseCase

# Use Cases
from src.application.use_cases.synthesize_speech import (
    SynthesizeSpeech as SynthesizeSpeechUseCase,
)
from src.application.use_cases.transcribe_audio import TranscribeAudioUseCase
from src.application.use_cases.voice_interaction import VoiceInteractionUseCase
from src.domain.repositories.test_record_repository import ITestRecordRepository
from src.domain.repositories.voice_repository import IVoiceRepository

# Infrastructure
from src.infrastructure.persistence import (
    InMemoryTestRecordRepository,
    InMemoryVoiceRepository,
)
from src.infrastructure.storage import LocalStorageService


class Container:
    """Dependency Injection Container.

    Manages the lifecycle and creation of all application dependencies.
    """

    _instance: "Container | None" = None
    _tts_providers: dict[str, ITTSProvider] | None = None
    _stt_providers: dict[str, ISTTProvider] | None = None
    _llm_providers: dict[str, ILLMProvider] | None = None
    _storage_service: IStorageService | None = None
    _test_record_repo: ITestRecordRepository | None = None
    _voice_repo: IVoiceRepository | None = None

    @classmethod
    def get_instance(cls) -> "Container":
        """Get singleton container instance."""
        if cls._instance is None:
            cls._instance = Container()
        return cls._instance

    def get_tts_providers(self) -> dict[str, ITTSProvider]:
        """Get TTS providers (lazy initialization)."""
        if self._tts_providers is None:
            self._tts_providers = self._create_tts_providers()
        return self._tts_providers

    def get_stt_providers(self) -> dict[str, ISTTProvider]:
        """Get STT providers (lazy initialization)."""
        if self._stt_providers is None:
            self._stt_providers = self._create_stt_providers()
        return self._stt_providers

    def get_llm_providers(self) -> dict[str, ILLMProvider]:
        """Get LLM providers (lazy initialization)."""
        if self._llm_providers is None:
            self._llm_providers = self._create_llm_providers()
        return self._llm_providers

    def get_storage_service(self) -> IStorageService:
        """Get storage service."""
        if self._storage_service is None:
            self._storage_service = self._create_storage_service()
        return self._storage_service

    def get_test_record_repository(self) -> ITestRecordRepository:
        """Get test record repository."""
        if self._test_record_repo is None:
            self._test_record_repo = InMemoryTestRecordRepository()
        return self._test_record_repo

    def get_voice_repository(self) -> IVoiceRepository:
        """Get voice repository."""
        if self._voice_repo is None:
            self._voice_repo = InMemoryVoiceRepository()
        return self._voice_repo

    def _create_tts_providers(self) -> dict[str, ITTSProvider]:
        """Create TTS provider instances based on configuration."""
        providers: dict[str, ITTSProvider] = {}

        # GCP TTS
        gcp_credentials = os.getenv("GCP_CREDENTIALS_PATH")
        if gcp_credentials or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                from src.infrastructure.providers.tts import GCPTTSProvider

                providers["gcp"] = GCPTTSProvider(credentials_path=gcp_credentials)
            except Exception as e:
                print(f"Failed to initialize GCP TTS: {e}")

        # Azure TTS
        azure_key = os.getenv("AZURE_SPEECH_KEY")
        azure_region = os.getenv("AZURE_SPEECH_REGION")
        if azure_key and azure_region:
            try:
                from src.infrastructure.providers.tts import AzureTTSProvider

                providers["azure"] = AzureTTSProvider(
                    subscription_key=azure_key,
                    region=azure_region,
                )
            except Exception as e:
                print(f"Failed to initialize Azure TTS: {e}")

        # ElevenLabs TTS
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            try:
                from src.infrastructure.providers.tts import ElevenLabsTTSProvider

                providers["elevenlabs"] = ElevenLabsTTSProvider(api_key=elevenlabs_key)
            except Exception as e:
                print(f"Failed to initialize ElevenLabs TTS: {e}")

        # VoAI TTS
        voai_key = os.getenv("VOAI_API_KEY")
        voai_endpoint = os.getenv("VOAI_API_ENDPOINT")
        if voai_key:
            try:
                from src.infrastructure.providers.tts import VoAITTSProvider

                providers["voai"] = VoAITTSProvider(api_key=voai_key, api_endpoint=voai_endpoint)
            except Exception as e:
                print(f"Failed to initialize VoAI TTS: {e}")

        return providers

    def _create_stt_providers(self) -> dict[str, ISTTProvider]:
        """Create STT provider instances based on configuration."""
        providers: dict[str, ISTTProvider] = {}

        # GCP STT
        gcp_credentials = os.getenv("GCP_CREDENTIALS_PATH")
        if gcp_credentials or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                from src.infrastructure.providers.stt import GCPSTTProvider

                providers["gcp"] = GCPSTTProvider(credentials_path=gcp_credentials)
            except Exception as e:
                print(f"Failed to initialize GCP STT: {e}")

        # Azure STT
        azure_key = os.getenv("AZURE_SPEECH_KEY")
        azure_region = os.getenv("AZURE_SPEECH_REGION")
        if azure_key and azure_region:
            try:
                from src.infrastructure.providers.stt import AzureSTTProvider

                providers["azure"] = AzureSTTProvider(
                    subscription_key=azure_key,
                    region=azure_region,
                )
            except Exception as e:
                print(f"Failed to initialize Azure STT: {e}")

        # Whisper STT
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from src.infrastructure.providers.stt import WhisperSTTProvider

                providers["whisper"] = WhisperSTTProvider(api_key=openai_key)
            except Exception as e:
                print(f"Failed to initialize Whisper STT: {e}")

        return providers

    def _create_llm_providers(self) -> dict[str, ILLMProvider]:
        """Create LLM provider instances based on configuration."""
        providers: dict[str, ILLMProvider] = {}

        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from src.infrastructure.providers.llm import OpenAILLMProvider

                providers["openai"] = OpenAILLMProvider(
                    api_key=openai_key,
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                )
            except Exception as e:
                print(f"Failed to initialize OpenAI LLM: {e}")

        # Azure OpenAI
        azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if azure_openai_key and azure_openai_endpoint and azure_openai_deployment:
            try:
                from src.infrastructure.providers.llm import AzureOpenAILLMProvider

                providers["azure-openai"] = AzureOpenAILLMProvider(
                    api_key=azure_openai_key,
                    endpoint=azure_openai_endpoint,
                    deployment_name=azure_openai_deployment,
                )
            except Exception as e:
                print(f"Failed to initialize Azure OpenAI LLM: {e}")

        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                from src.infrastructure.providers.llm import AnthropicLLMProvider

                providers["anthropic"] = AnthropicLLMProvider(
                    api_key=anthropic_key,
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                )
            except Exception as e:
                print(f"Failed to initialize Anthropic LLM: {e}")

        # Google Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                from src.infrastructure.providers.llm import GeminiLLMProvider

                providers["gemini"] = GeminiLLMProvider(
                    api_key=gemini_key,
                    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                )
            except Exception as e:
                print(f"Failed to initialize Gemini LLM: {e}")

        return providers

    def _create_storage_service(self) -> IStorageService:
        """Create storage service based on configuration."""
        storage_type = os.getenv("STORAGE_TYPE", "local")

        if storage_type == "s3":
            from src.infrastructure.storage import S3StorageService

            return S3StorageService(
                bucket_name=os.getenv("S3_BUCKET_NAME", "voice-lab"),
                region=os.getenv("AWS_REGION", "us-east-1"),
                access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            )
        else:
            return LocalStorageService(
                base_path=os.getenv("LOCAL_STORAGE_PATH", "./storage"),
            )


# FastAPI dependency functions


def get_container() -> Container:
    """Get the DI container."""
    return Container.get_instance()


def get_tts_providers() -> dict[str, ITTSProvider]:
    """FastAPI dependency for TTS providers."""
    return get_container().get_tts_providers()


def get_stt_providers() -> dict[str, ISTTProvider]:
    """FastAPI dependency for STT providers."""
    return get_container().get_stt_providers()


def get_llm_providers() -> dict[str, ILLMProvider]:
    """FastAPI dependency for LLM providers."""
    return get_container().get_llm_providers()


def get_storage_service() -> IStorageService:
    """FastAPI dependency for storage service."""
    return get_container().get_storage_service()


def get_test_record_repository() -> ITestRecordRepository:
    """FastAPI dependency for test record repository."""
    return get_container().get_test_record_repository()


def get_voice_repository() -> IVoiceRepository:
    """FastAPI dependency for voice repository."""
    return get_container().get_voice_repository()


def get_synthesize_speech_use_case() -> SynthesizeSpeechUseCase:
    """FastAPI dependency for synthesize speech use case."""
    container = get_container()
    return SynthesizeSpeechUseCase(
        tts_providers=container.get_tts_providers(),
        storage_service=container.get_storage_service(),
        test_record_repo=container.get_test_record_repository(),
    )


def get_transcribe_audio_use_case() -> TranscribeAudioUseCase:
    """FastAPI dependency for transcribe audio use case."""
    container = get_container()
    return TranscribeAudioUseCase(
        stt_providers=container.get_stt_providers(),
        test_record_repo=container.get_test_record_repository(),
    )


def get_compare_providers_use_case() -> CompareProvidersUseCase:
    """FastAPI dependency for compare providers use case."""
    container = get_container()
    return CompareProvidersUseCase(
        tts_providers=container.get_tts_providers(),
        stt_providers=container.get_stt_providers(),
    )


def get_voice_interaction_use_case() -> VoiceInteractionUseCase:
    """FastAPI dependency for voice interaction use case."""
    container = get_container()
    return VoiceInteractionUseCase(
        stt_providers=container.get_stt_providers(),
        llm_providers=container.get_llm_providers(),
        tts_providers=container.get_tts_providers(),
    )
