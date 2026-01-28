"""TTS Provider Factory.

T043: Factory for creating TTS providers with credential injection support.
T074: Extended to support audit logging for credential.used events.
"""

import os
import uuid
from dataclasses import dataclass
from typing import Any

from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)


class ProviderNotSupportedError(Exception):
    """Raised when a provider is not supported."""

    pass


@dataclass
class ProviderCreationResult:
    """Result of provider creation, including credential metadata for audit logging."""

    provider: ITTSProvider
    used_user_credential: bool
    credential_id: uuid.UUID | None = None
    provider_name: str = ""


class TTSProviderFactory:
    """Factory for creating TTS provider instances.

    This factory supports:
    1. Creating providers with user credentials (BYOL model)
    2. Falling back to system-level credentials
    3. Caching provider instances
    """

    # Supported providers
    SUPPORTED_PROVIDERS = ["elevenlabs", "azure", "gemini", "voai"]

    # Provider aliases for backwards compatibility (gcp/google -> gemini)
    PROVIDER_ALIASES: dict[str, str] = {
        "gcp": "gemini",
        "google": "gemini",
    }

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names.

        Returns:
            List of supported provider identifiers
        """
        return cls.SUPPORTED_PROVIDERS.copy()

    @classmethod
    def _normalize_provider_name(cls, provider_name: str) -> str:
        """Normalize provider name, resolving aliases.

        Args:
            provider_name: Provider identifier (may be an alias)

        Returns:
            Normalized provider name
        """
        name = provider_name.lower()
        return cls.PROVIDER_ALIASES.get(name, name)

    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        """Check if a provider is supported.

        Args:
            provider_name: Provider identifier

        Returns:
            True if the provider is supported
        """
        normalized = cls._normalize_provider_name(provider_name)
        return normalized in cls.SUPPORTED_PROVIDERS

    @classmethod
    def _create_provider(
        cls, provider_name: str, api_key: str | None = None, **kwargs: Any
    ) -> ITTSProvider:
        """Internal method to create provider with given credentials.

        Args:
            provider_name: Name of the provider (may be an alias like 'gcp' or 'google')
            api_key: Optional API key override
            **kwargs: Additional provider-specific arguments

        Returns:
            ITTSProvider instance
        """
        provider_name = cls._normalize_provider_name(provider_name)

        if provider_name == "elevenlabs":
            from src.infrastructure.providers.tts.elevenlabs_tts import (
                ElevenLabsTTSProvider,
            )

            return ElevenLabsTTSProvider(api_key=api_key or os.getenv("ELEVENLABS_API_KEY", ""))

        elif provider_name == "azure":
            from src.infrastructure.providers.tts.azure_tts import AzureTTSProvider

            return AzureTTSProvider(
                subscription_key=api_key or os.getenv("AZURE_SPEECH_KEY", ""),
                region=kwargs.get("region") or os.getenv("AZURE_SPEECH_REGION", "eastasia"),
            )

        elif provider_name == "gemini":
            from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider

            return GeminiTTSProvider(
                api_key=api_key or os.getenv("GOOGLE_AI_API_KEY", ""),
                model=kwargs.get("model")
                or os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-pro-preview-tts"),
            )

        elif provider_name == "voai":
            from src.infrastructure.providers.tts.voai_tts import VoAITTSProvider

            return VoAITTSProvider(
                api_key=api_key or os.getenv("VOAI_API_KEY", ""),
                api_endpoint=kwargs.get("api_endpoint")
                or os.getenv("VOAI_API_ENDPOINT", "connect.voai.ai"),
            )

        raise ProviderNotSupportedError(
            f"Provider '{provider_name}' is not supported. "
            f"Supported providers: {', '.join(cls.SUPPORTED_PROVIDERS)}"
        )

    @classmethod
    async def create(
        cls,
        provider_name: str,
        user_id: uuid.UUID | None = None,
        credential_repo: IProviderCredentialRepository | None = None,
        **kwargs: Any,
    ) -> ITTSProvider:
        """Create a TTS provider instance.

        If user_id and credential_repo are provided, attempts to use
        user credentials first. Falls back to system credentials.

        Args:
            provider_name: Name of the provider (e.g., 'elevenlabs', 'azure')
            user_id: Optional user ID for BYOL credential lookup
            credential_repo: Optional repository for looking up user credentials
            **kwargs: Additional provider-specific arguments

        Returns:
            ITTSProvider instance configured for the provider

        Raises:
            ProviderNotSupportedError: If the provider is not supported
        """
        result = await cls.create_with_metadata(
            provider_name=provider_name,
            user_id=user_id,
            credential_repo=credential_repo,
            **kwargs,
        )
        return result.provider

    @classmethod
    async def create_with_metadata(
        cls,
        provider_name: str,
        user_id: uuid.UUID | None = None,
        credential_repo: IProviderCredentialRepository | None = None,
        **kwargs: Any,
    ) -> ProviderCreationResult:
        """Create a TTS provider instance with credential metadata for audit logging.

        If user_id and credential_repo are provided, attempts to use
        user credentials first. Falls back to system credentials.

        Args:
            provider_name: Name of the provider (e.g., 'elevenlabs', 'azure')
            user_id: Optional user ID for BYOL credential lookup
            credential_repo: Optional repository for looking up user credentials
            **kwargs: Additional provider-specific arguments

        Returns:
            ProviderCreationResult with provider and credential metadata

        Raises:
            ProviderNotSupportedError: If the provider is not supported
        """
        provider_name = cls._normalize_provider_name(provider_name)

        if not cls.is_supported(provider_name):
            raise ProviderNotSupportedError(
                f"Provider '{provider_name}' is not supported. "
                f"Supported providers: {', '.join(cls.SUPPORTED_PROVIDERS)}"
            )

        # Try to get user credential if user_id is provided
        api_key: str | None = None
        used_user_credential = False
        credential_id: uuid.UUID | None = None

        if user_id and credential_repo:
            user_credential = await credential_repo.get_by_user_and_provider(user_id, provider_name)
            if user_credential and user_credential.is_valid:
                api_key = user_credential.api_key
                used_user_credential = True
                credential_id = user_credential.id

        provider = cls._create_provider(provider_name, api_key=api_key, **kwargs)

        return ProviderCreationResult(
            provider=provider,
            used_user_credential=used_user_credential,
            credential_id=credential_id,
            provider_name=provider_name,
        )

    @classmethod
    def create_with_key(cls, provider_name: str, api_key: str, **kwargs: Any) -> ITTSProvider:
        """Create a TTS provider instance with a specific API key.

        Args:
            provider_name: Name of the provider (may be an alias like 'gcp')
            api_key: API key to use
            **kwargs: Additional provider-specific arguments

        Returns:
            ITTSProvider instance configured with the given key

        Raises:
            ProviderNotSupportedError: If the provider is not supported
        """
        normalized = cls._normalize_provider_name(provider_name)
        if not cls.is_supported(normalized):
            raise ProviderNotSupportedError(f"Provider '{provider_name}' is not supported")

        return cls._create_provider(normalized, api_key=api_key, **kwargs)

    @classmethod
    def create_default(cls, provider_name: str, **kwargs: Any) -> ITTSProvider:
        """Create a TTS provider with default system credentials.

        Uses environment variables for credential lookup.

        Args:
            provider_name: Name of the provider (may be an alias like 'gcp')
            **kwargs: Additional provider-specific arguments

        Returns:
            ITTSProvider instance with system credentials

        Raises:
            ProviderNotSupportedError: If the provider is not supported
        """
        normalized = cls._normalize_provider_name(provider_name)
        if not cls.is_supported(normalized):
            raise ProviderNotSupportedError(f"Provider '{provider_name}' is not supported")

        return cls._create_provider(normalized, **kwargs)
