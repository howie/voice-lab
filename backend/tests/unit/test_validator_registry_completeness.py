"""Unit tests for Validator Registry completeness."""

import pytest

from src.infrastructure.providers.validators import (
    PROVIDER_VALIDATORS,
    ProviderValidatorRegistry,
)


class TestValidatorRegistryCompleteness:
    """Tests for validator registry having all expected providers."""

    EXPECTED_PROVIDERS = [
        "elevenlabs",
        "azure",
        "gemini",
        "openai",
        "anthropic",
        "gcp",
        "voai",
        "speechmatics",
    ]

    def test_all_providers_have_validators(self):
        """All 8 expected providers should be in PROVIDER_VALIDATORS."""
        for provider_id in self.EXPECTED_PROVIDERS:
            assert provider_id in PROVIDER_VALIDATORS, (
                f"Missing validator for provider: {provider_id}"
            )

    def test_registry_count(self):
        """Registry should have exactly 8 validators."""
        assert len(PROVIDER_VALIDATORS) == 8

    def test_registry_get_validator(self):
        """ProviderValidatorRegistry.get_validator() should return correct instances."""
        for provider_id in self.EXPECTED_PROVIDERS:
            validator = ProviderValidatorRegistry.get_validator(provider_id)
            assert validator.provider_id == provider_id

    def test_registry_unsupported_provider(self):
        """Unsupported provider should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            ProviderValidatorRegistry.get_validator("nonexistent")

    def test_registry_is_supported(self):
        """is_supported should return True for all expected providers."""
        for provider_id in self.EXPECTED_PROVIDERS:
            assert ProviderValidatorRegistry.is_supported(provider_id) is True

    def test_registry_is_not_supported(self):
        """is_supported should return False for unknown providers."""
        assert ProviderValidatorRegistry.is_supported("nonexistent") is False

    def test_list_supported_providers(self):
        """list_supported_providers should return all expected providers."""
        supported = ProviderValidatorRegistry.list_supported_providers()
        for provider_id in self.EXPECTED_PROVIDERS:
            assert provider_id in supported
