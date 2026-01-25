"""Realtime API mode factory and services.

Feature: 004-interaction-module
T027d: Factory for creating realtime mode services.

Provides factory function to create the appropriate realtime mode service
based on provider configuration (OpenAI or Gemini).
"""

import os
from typing import Any

from src.domain.services.interaction.base import InteractionModeService
from src.domain.services.interaction.gemini_realtime import GeminiRealtimeService
from src.domain.services.interaction.openai_realtime import OpenAIRealtimeService

# Supported realtime providers
SUPPORTED_PROVIDERS = ["openai", "gemini"]


class RealtimeModeFactory:
    """Factory for creating realtime mode services.

    Creates the appropriate InteractionModeService implementation
    based on the provider specified in the configuration.
    """

    @staticmethod
    def create(
        config: dict[str, Any],
        api_key: str | None = None,
    ) -> InteractionModeService:
        """Create a realtime mode service based on configuration.

        Args:
            config: Provider configuration containing 'provider' key
            api_key: Optional API key (defaults to environment variable)

        Returns:
            InteractionModeService implementation for the provider

        Raises:
            ValueError: If provider is not supported
            ValueError: If API key is not provided or found
        """
        provider = config.get("provider", "openai").lower()

        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported realtime provider: {provider}. "
                f"Supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        if provider == "openai":
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                    "or provide api_key parameter."
                )
            return OpenAIRealtimeService(api_key=key)

        elif provider == "gemini":
            key = api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError(
                    "Google AI API key required. Set GOOGLE_AI_API_KEY or GEMINI_API_KEY "
                    "environment variable or provide api_key parameter."
                )
            return GeminiRealtimeService(api_key=key)

        # This should never be reached due to the check above
        raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported realtime providers.

        Returns:
            List of provider names
        """
        return SUPPORTED_PROVIDERS.copy()

    @staticmethod
    def get_provider_info(provider: str) -> dict[str, Any]:
        """Get information about a specific provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary with provider information

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        if provider == "openai":
            return {
                "name": "openai",
                "display_name": "OpenAI Realtime API",
                "models": [
                    "gpt-4o-realtime-preview",
                    "gpt-4o-realtime-preview-2024-10-01",
                ],
                "voices": ["alloy", "echo", "shimmer", "ash", "ballad", "coral", "sage", "verse"],
                "features": [
                    "voice-to-voice",
                    "server-vad",
                    "transcription",
                    "function-calling",
                ],
                "audio_formats": ["pcm16"],
                "sample_rate": 24000,
                "env_var": "OPENAI_API_KEY",
            }

        elif provider == "gemini":
            return {
                "name": "gemini",
                "display_name": "Google Gemini Live API",
                "models": [
                    "gemini-2.5-flash-preview-native-audio-dialog",
                    "gemini-2.5-pro-preview-native-audio-dialog",
                    "gemini-2.5-flash",
                    "gemini-2.0-flash-exp",
                ],
                "voices": ["Puck", "Charon", "Kore", "Fenrir", "Aoede"],
                "features": [
                    "voice-to-voice",
                    "multimodal",
                    "function-calling",
                    "native-audio",
                    "24-languages",
                ],
                "audio_formats": ["pcm16"],
                "sample_rate": 16000,
                "env_var": "GOOGLE_AI_API_KEY",
            }

        return {}


# Convenience function for creating services
def create_realtime_service(
    provider: str = "openai",
    api_key: str | None = None,
    **config: Any,
) -> InteractionModeService:
    """Create a realtime mode service.

    Convenience function that wraps RealtimeModeFactory.create().

    Args:
        provider: Provider name ('openai' or 'gemini')
        api_key: Optional API key
        **config: Additional provider configuration

    Returns:
        InteractionModeService implementation

    Example:
        service = create_realtime_service(
            provider="openai",
            voice="alloy",
            model="gpt-4o-realtime-preview"
        )
    """
    full_config = {"provider": provider, **config}
    return RealtimeModeFactory.create(full_config, api_key=api_key)
