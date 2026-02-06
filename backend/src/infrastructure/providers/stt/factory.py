"""STT Provider Factory.

Feature: 003-stt-testing-module
Creates STT provider instances based on configuration and credentials.
"""

import os
from typing import Any

from src.application.interfaces.stt_provider import ISTTProvider

# from src.infrastructure.providers.stt.assemblyai_stt import AssemblyAISTTProvider
from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider

# from src.infrastructure.providers.stt.deepgram_stt import DeepgramSTTProvider
# from src.infrastructure.providers.stt.elevenlabs_stt import ElevenLabsSTTProvider
from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider
from src.infrastructure.providers.stt.speechmatics_stt import SpeechmaticsSTTProvider
from src.infrastructure.providers.stt.whisper_stt import WhisperSTTProvider


class STTProviderFactory:
    """Factory for creating STT provider instances."""

    # Provider metadata for API responses
    PROVIDER_INFO = {
        "azure": {
            "name": "azure",
            "display_name": "Azure Speech Services",
            "supports_streaming": True,
            "supports_child_mode": True,  # Via phrase hints
            "supports_diarization": True,
            "max_duration_sec": 600,
            "max_file_size_mb": 200,
            "supported_formats": ["mp3", "wav", "ogg", "flac", "webm"],
            "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        },
        "gcp": {
            "name": "gcp",
            "display_name": "Google Cloud STT",
            "supports_streaming": True,
            "supports_child_mode": True,  # Via model selection
            "max_duration_sec": 600,
            "max_file_size_mb": 480,
            "supported_formats": ["mp3", "wav", "ogg", "flac", "webm"],
            "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        },
        "whisper": {
            "name": "whisper",
            "display_name": "OpenAI Whisper",
            "supports_streaming": False,  # Batch only
            "supports_child_mode": False,
            "max_duration_sec": 600,
            "max_file_size_mb": 25,
            "supported_formats": ["mp3", "mp4", "wav", "webm", "m4a"],
            "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        },
        "deepgram": {
            "name": "deepgram",
            "display_name": "Deepgram Nova-2",
            "supports_streaming": True,
            "supports_child_mode": False,
            "max_duration_sec": 3600,
            "max_file_size_mb": 2000,
            "supported_formats": ["mp3", "wav", "ogg", "flac", "webm", "m4a"],
            "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        },
        "assemblyai": {
            "name": "assemblyai",
            "display_name": "AssemblyAI",
            "supports_streaming": True,
            "supports_child_mode": False,
            "max_duration_sec": 3600,
            "max_file_size_mb": 2000,
            "supported_formats": ["mp3", "wav", "ogg", "flac", "webm", "m4a"],
            "supported_languages": ["zh-TW", "en-US", "ja-JP", "ko-KR"],
        },
        "elevenlabs": {
            "name": "elevenlabs",
            "display_name": "ElevenLabs Scribe",
            "supports_streaming": False,
            "supports_child_mode": False,
            "max_duration_sec": 600,
            "max_file_size_mb": 25,
            "supported_formats": ["mp3", "wav", "flac", "m4a"],
            "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        },
        "speechmatics": {
            "name": "speechmatics",
            "display_name": "Speechmatics",
            "supports_streaming": True,
            "supports_child_mode": True,  # 兒童語音辨識業界最佳 (91.8% 準確度)
            "max_duration_sec": 7200,
            "max_file_size_mb": 2000,
            "supported_formats": ["mp3", "wav", "ogg", "flac"],
            "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
            "child_mode_note": "使用 enhanced operating_point + additional_vocab 優化",
        },
    }

    @classmethod
    def create(cls, provider_name: str, credentials: dict[str, Any]) -> ISTTProvider:
        """Create an STT provider instance.

        Args:
            provider_name: Name of the provider
            credentials: Provider-specific credentials

        Returns:
            Configured STT provider instance

        Raises:
            ValueError: If provider name is unknown or credentials are invalid
        """
        provider_name = provider_name.lower()

        if provider_name == "azure":
            return cls._create_azure(credentials)
        elif provider_name == "gcp":
            return cls._create_gcp(credentials)
        elif provider_name == "whisper":
            return cls._create_whisper(credentials)
        elif provider_name == "speechmatics":
            return cls._create_speechmatics(credentials)
        # TODO: Re-enable after fixing SDK compatibility
        # elif provider_name == "deepgram":
        #     return cls._create_deepgram(credentials)
        # elif provider_name == "assemblyai":
        #     return cls._create_assemblyai(credentials)
        # elif provider_name == "elevenlabs":
        #     return cls._create_elevenlabs(credentials)
        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")

    @classmethod
    def create_default(cls, provider_name: str) -> ISTTProvider:
        """Create an STT provider with default system credentials from env vars.

        Args:
            provider_name: Name of the provider

        Returns:
            Configured STT provider instance

        Raises:
            ValueError: If provider is unknown or system credentials are missing
        """
        provider_name = provider_name.lower()

        if provider_name == "azure":
            api_key = os.getenv("AZURE_SPEECH_KEY", "")
            region = os.getenv("AZURE_SPEECH_REGION", "eastasia")
            if not api_key:
                raise ValueError("Azure STT requires 'AZURE_SPEECH_KEY' environment variable")
            return AzureSTTProvider(subscription_key=api_key, region=region)
        elif provider_name == "gcp":
            return GCPSTTProvider()
        elif provider_name == "whisper":
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("Whisper STT requires 'OPENAI_API_KEY' environment variable")
            return WhisperSTTProvider(api_key=api_key)
        elif provider_name == "speechmatics":
            api_key = os.getenv("SPEECHMATICS_API_KEY", "")
            if not api_key:
                raise ValueError(
                    "Speechmatics STT requires 'SPEECHMATICS_API_KEY' environment variable"
                )
            return SpeechmaticsSTTProvider(api_key=api_key)
        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")

    @classmethod
    def _create_azure(cls, credentials: dict[str, Any]) -> AzureSTTProvider:
        subscription_key = credentials.get("subscription_key") or credentials.get("api_key")
        region = credentials.get("region", "eastasia")
        if not subscription_key:
            raise ValueError("Azure STT requires 'subscription_key' or 'api_key'")
        return AzureSTTProvider(subscription_key=subscription_key, region=region)

    @classmethod
    def _create_gcp(cls, credentials: dict[str, Any]) -> GCPSTTProvider:
        return GCPSTTProvider(
            credentials_path=credentials.get("credentials_path")
            or credentials.get("service_account_json"),
        )

    @classmethod
    def _create_whisper(cls, credentials: dict[str, Any]) -> WhisperSTTProvider:
        api_key = credentials.get("api_key")
        if not api_key:
            raise ValueError("Whisper STT requires 'api_key'")
        return WhisperSTTProvider(api_key=api_key)

    @classmethod
    def _create_speechmatics(cls, credentials: dict[str, Any]) -> SpeechmaticsSTTProvider:
        """Create Speechmatics STT provider.

        Speechmatics 是兒童語音辨識的業界領導者 (91.8% 準確度)。
        """
        api_key = credentials.get("api_key")
        if not api_key:
            raise ValueError("Speechmatics STT requires 'api_key'")
        return SpeechmaticsSTTProvider(api_key=api_key)

    # TODO: Re-enable after fixing provider SDK compatibility
    # @classmethod
    # def _create_deepgram(cls, credentials: dict[str, Any]) -> DeepgramSTTProvider:
    #     api_key = credentials.get("api_key")
    #     if not api_key:
    #         raise ValueError("Deepgram STT requires 'api_key'")
    #     return DeepgramSTTProvider(api_key=api_key)
    #
    # @classmethod
    # def _create_assemblyai(cls, credentials: dict[str, Any]) -> AssemblyAISTTProvider:
    #     api_key = credentials.get("api_key")
    #     if not api_key:
    #         raise ValueError("AssemblyAI STT requires 'api_key'")
    #     return AssemblyAISTTProvider(api_key=api_key)
    #
    # @classmethod
    # def _create_elevenlabs(cls, credentials: dict[str, Any]) -> ElevenLabsSTTProvider:
    #     api_key = credentials.get("api_key")
    #     if not api_key:
    #         raise ValueError("ElevenLabs STT requires 'api_key'")
    #     return ElevenLabsSTTProvider(api_key=api_key)

    @classmethod
    def get_provider_info(cls, provider_name: str) -> dict[str, Any]:
        provider_name = provider_name.lower()
        if provider_name not in cls.PROVIDER_INFO:
            raise ValueError(f"Unknown STT provider: {provider_name}")
        return cls.PROVIDER_INFO[provider_name]

    @classmethod
    def list_providers(cls) -> list[dict[str, Any]]:
        return list(cls.PROVIDER_INFO.values())

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        return list(cls.PROVIDER_INFO.keys())
