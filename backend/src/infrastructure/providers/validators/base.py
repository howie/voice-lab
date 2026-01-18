"""Base Provider Validator."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of API key validation."""

    is_valid: bool
    error_message: str | None = None
    quota_info: dict | None = None  # Optional quota information


class BaseProviderValidator(ABC):
    """Abstract base class for provider API key validators.

    Each provider must implement its own validator to verify
    that an API key is valid and functional.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Get the provider identifier."""
        pass

    @abstractmethod
    async def validate(self, api_key: str) -> ValidationResult:
        """Validate an API key against the provider's API.

        This method should make a lightweight API call to verify
        that the key is valid without consuming significant quota.

        Args:
            api_key: The API key to validate

        Returns:
            ValidationResult indicating if the key is valid
        """
        pass

    @abstractmethod
    async def get_available_models(self, api_key: str) -> list[dict]:
        """Get available models/voices for this provider.

        Args:
            api_key: The API key to use for the request

        Returns:
            List of available models/voices with metadata
        """
        pass
