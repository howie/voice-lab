"""STT Provider Factory.

Feature: 003-stt-testing-module
Creates STT provider instances based on configuration and credentials.
"""

from typing import Any

from src.application.interfaces.stt_provider import ISTTProvider
from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider
from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider
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
    }

    @classmethod
    def create(cls, provider_name: str, credentials: dict[str, Any]) -> ISTTProvider:
        """Create an STT provider instance.

        Args:
            provider_name: Name of the provider ('azure', 'gcp', 'whisper')
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
        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")

    @classmethod
    def _create_azure(cls, credentials: dict[str, Any]) -> AzureSTTProvider:
        """Create Azure STT provider."""
        subscription_key = credentials.get("subscription_key") or credentials.get("api_key")
        region = credentials.get("region", "eastasia")

        if not subscription_key:
            raise ValueError("Azure STT requires 'subscription_key' or 'api_key'")

        return AzureSTTProvider(
            subscription_key=subscription_key,
            region=region,
        )

    @classmethod
    def _create_gcp(cls, credentials: dict[str, Any]) -> GCPSTTProvider:
        """Create GCP STT provider."""
        # GCP can use service account JSON or application default credentials
        service_account_json = credentials.get("service_account_json")
        project_id = credentials.get("project_id")

        return GCPSTTProvider(
            service_account_json=service_account_json,
            project_id=project_id,
        )

    @classmethod
    def _create_whisper(cls, credentials: dict[str, Any]) -> WhisperSTTProvider:
        """Create OpenAI Whisper STT provider."""
        api_key = credentials.get("api_key")

        if not api_key:
            raise ValueError("Whisper STT requires 'api_key'")

        return WhisperSTTProvider(api_key=api_key)

    @classmethod
    def get_provider_info(cls, provider_name: str) -> dict[str, Any]:
        """Get provider metadata.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider information dictionary

        Raises:
            ValueError: If provider name is unknown
        """
        provider_name = provider_name.lower()
        if provider_name not in cls.PROVIDER_INFO:
            raise ValueError(f"Unknown STT provider: {provider_name}")
        return cls.PROVIDER_INFO[provider_name]

    @classmethod
    def list_providers(cls) -> list[dict[str, Any]]:
        """List all available STT providers with their metadata.

        Returns:
            List of provider information dictionaries
        """
        return list(cls.PROVIDER_INFO.values())

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names.

        Returns:
            List of provider names
        """
        return list(cls.PROVIDER_INFO.keys())
