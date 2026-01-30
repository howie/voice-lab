"""Provider Validators Registry."""

from src.infrastructure.providers.validators.anthropic_validator import (
    AnthropicValidator,
)
from src.infrastructure.providers.validators.azure import AzureValidator
from src.infrastructure.providers.validators.base import (
    BaseProviderValidator,
    ValidationResult,
)
from src.infrastructure.providers.validators.elevenlabs import ElevenLabsValidator
from src.infrastructure.providers.validators.gcp import GCPValidator
from src.infrastructure.providers.validators.gemini import GeminiValidator
from src.infrastructure.providers.validators.openai import OpenAIValidator
from src.infrastructure.providers.validators.speechmatics import SpeechmaticsValidator
from src.infrastructure.providers.validators.voai import VoAIValidator

# Registry of all available provider validators
PROVIDER_VALIDATORS: dict[str, type[BaseProviderValidator]] = {
    "elevenlabs": ElevenLabsValidator,
    "azure": AzureValidator,
    "gemini": GeminiValidator,
    "openai": OpenAIValidator,
    "anthropic": AnthropicValidator,
    "gcp": GCPValidator,
    "voai": VoAIValidator,
    "speechmatics": SpeechmaticsValidator,
}


class ProviderValidatorRegistry:
    """Registry for provider validators.

    Provides a centralized way to access validators for different providers.
    """

    _validators: dict[str, BaseProviderValidator] = {}

    @classmethod
    def get_validator(cls, provider_id: str) -> BaseProviderValidator:
        """Get a validator instance for the specified provider.

        Args:
            provider_id: The provider identifier

        Returns:
            A validator instance for the provider

        Raises:
            ValueError: If the provider is not supported
        """
        if provider_id not in PROVIDER_VALIDATORS:
            raise ValueError(f"Unsupported provider: {provider_id}")

        # Lazy instantiation of validators
        if provider_id not in cls._validators:
            cls._validators[provider_id] = PROVIDER_VALIDATORS[provider_id]()

        return cls._validators[provider_id]

    @classmethod
    def is_supported(cls, provider_id: str) -> bool:
        """Check if a provider is supported.

        Args:
            provider_id: The provider identifier

        Returns:
            True if the provider is supported
        """
        return provider_id in PROVIDER_VALIDATORS

    @classmethod
    def list_supported_providers(cls) -> list[str]:
        """Get a list of all supported provider IDs.

        Returns:
            List of supported provider identifiers
        """
        return list(PROVIDER_VALIDATORS.keys())


__all__ = [
    "BaseProviderValidator",
    "ValidationResult",
    "ElevenLabsValidator",
    "AzureValidator",
    "GeminiValidator",
    "OpenAIValidator",
    "AnthropicValidator",
    "GCPValidator",
    "VoAIValidator",
    "SpeechmaticsValidator",
    "ProviderValidatorRegistry",
    "PROVIDER_VALIDATORS",
]
