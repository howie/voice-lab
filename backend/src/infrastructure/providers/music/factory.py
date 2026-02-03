"""Music Provider Factory.

Factory for creating music generation provider instances.
Follows the same pattern as TTSProviderFactory.
"""

from typing import Any

from src.application.interfaces.music_provider import IMusicProvider


class MusicProviderNotSupportedError(Exception):
    """Raised when a music provider is not supported."""


class MusicProviderFactory:
    """Factory for creating music generation provider instances.

    Supports lazy imports to avoid loading unused provider dependencies.
    """

    SUPPORTED_PROVIDERS = ["mureka"]

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names."""
        return cls.SUPPORTED_PROVIDERS.copy()

    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        """Check if a provider is supported."""
        return provider_name.lower() in cls.SUPPORTED_PROVIDERS

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> IMusicProvider:
        """Create a music provider instance.

        Args:
            provider_name: Name of the provider (e.g., 'mureka')
            api_key: Optional API key override
            **kwargs: Additional provider-specific arguments

        Returns:
            IMusicProvider instance

        Raises:
            MusicProviderNotSupportedError: If provider is not supported
        """
        provider_name = provider_name.lower()

        if provider_name == "mureka":
            from src.infrastructure.providers.music.mureka_music import (
                MurekaMusicProvider,
            )

            return MurekaMusicProvider(
                api_key=api_key,
                base_url=kwargs.get("base_url"),
                timeout=kwargs.get("timeout", 60.0),
            )

        # Future: uncomment when Suno official API is available
        # if provider_name == "suno":
        #     from src.infrastructure.providers.music.suno_music import (
        #         SunoMusicProvider,
        #     )
        #     return SunoMusicProvider(api_key=api_key)

        raise MusicProviderNotSupportedError(
            f"Provider '{provider_name}' is not supported. "
            f"Supported: {', '.join(cls.SUPPORTED_PROVIDERS)}"
        )

    @classmethod
    def create_default(cls, provider_name: str = "mureka") -> IMusicProvider:
        """Create a provider with system credentials from environment.

        Args:
            provider_name: Provider identifier (default: 'mureka')

        Returns:
            IMusicProvider instance with system credentials
        """
        return cls.create(provider_name)
