"""LLM Provider Factory.

Feature: 004-interaction-module
T043: Factory for creating LLM providers for Cascade mode.
"""

import os
from typing import Any

from src.application.interfaces.llm_provider import ILLMProvider
from src.infrastructure.providers.llm.anthropic_llm import AnthropicLLMProvider
from src.infrastructure.providers.llm.azure_openai_llm import AzureOpenAILLMProvider
from src.infrastructure.providers.llm.gemini_llm import GeminiLLMProvider
from src.infrastructure.providers.llm.openai_llm import OpenAILLMProvider


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    PROVIDER_INFO = {
        "openai": {
            "name": "openai",
            "display_name": "OpenAI GPT-4o",
            "default_model": "gpt-4o-mini",
            "supports_streaming": True,
            "max_tokens": 4096,
        },
        "anthropic": {
            "name": "anthropic",
            "display_name": "Anthropic Claude",
            "default_model": "claude-3-5-sonnet-latest",
            "supports_streaming": True,
            "max_tokens": 4096,
        },
        "gemini": {
            "name": "gemini",
            "display_name": "Google Gemini",
            "default_model": "gemini-2.0-flash",
            "supports_streaming": True,
            "max_tokens": 8192,
        },
        "azure-openai": {
            "name": "azure-openai",
            "display_name": "Azure OpenAI",
            "default_model": "gpt-4o-mini",
            "supports_streaming": True,
            "max_tokens": 4096,
        },
    }

    @classmethod
    def create(cls, provider_name: str, credentials: dict[str, Any]) -> ILLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_name: Name of the provider
            credentials: Provider-specific credentials

        Returns:
            Configured LLM provider instance

        Raises:
            ValueError: If provider name is unknown or credentials are invalid
        """
        provider_name = provider_name.lower()

        if provider_name == "openai":
            return cls._create_openai(credentials)
        elif provider_name == "anthropic":
            return cls._create_anthropic(credentials)
        elif provider_name == "gemini":
            return cls._create_gemini(credentials)
        elif provider_name == "azure-openai":
            return cls._create_azure_openai(credentials)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    @classmethod
    def create_default(cls, provider_name: str) -> ILLMProvider:
        """Create an LLM provider with default system credentials from env vars.

        Args:
            provider_name: Name of the provider

        Returns:
            Configured LLM provider instance
        """
        provider_name = provider_name.lower()

        if provider_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")
            return OpenAILLMProvider(api_key=api_key)
        elif provider_name == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            return AnthropicLLMProvider(api_key=api_key)
        elif provider_name == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY", "")
            return GeminiLLMProvider(api_key=api_key)
        elif provider_name == "azure-openai":
            api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            return AzureOpenAILLMProvider(
                api_key=api_key,
                endpoint=endpoint,
                deployment_name=deployment,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    @classmethod
    def _create_openai(cls, credentials: dict[str, Any]) -> OpenAILLMProvider:
        api_key = credentials.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        model = credentials.get("model", "gpt-4o-mini")
        if not api_key:
            raise ValueError("OpenAI LLM requires 'api_key'")
        return OpenAILLMProvider(api_key=api_key, model=model)

    @classmethod
    def _create_anthropic(cls, credentials: dict[str, Any]) -> AnthropicLLMProvider:
        api_key = credentials.get("api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        model = credentials.get("model", "claude-3-5-sonnet-latest")
        if not api_key:
            raise ValueError("Anthropic LLM requires 'api_key'")
        return AnthropicLLMProvider(api_key=api_key, model=model)

    @classmethod
    def _create_gemini(cls, credentials: dict[str, Any]) -> GeminiLLMProvider:
        api_key = credentials.get("api_key") or os.getenv("GOOGLE_API_KEY", "")
        model = credentials.get("model", "gemini-2.0-flash")
        if not api_key:
            raise ValueError("Gemini LLM requires 'api_key'")
        return GeminiLLMProvider(api_key=api_key, model=model)

    @classmethod
    def _create_azure_openai(cls, credentials: dict[str, Any]) -> AzureOpenAILLMProvider:
        api_key = credentials.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY", "")
        endpoint = credentials.get("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        deployment = credentials.get("deployment") or os.getenv(
            "AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"
        )
        if not api_key or not endpoint:
            raise ValueError("Azure OpenAI LLM requires 'api_key' and 'endpoint'")
        return AzureOpenAILLMProvider(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment,
        )

    @classmethod
    def get_provider_info(cls, provider_name: str) -> dict[str, Any]:
        """Get provider metadata."""
        provider_name = provider_name.lower()
        if provider_name not in cls.PROVIDER_INFO:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
        return cls.PROVIDER_INFO[provider_name]

    @classmethod
    def list_providers(cls) -> list[dict[str, Any]]:
        """List all available providers with metadata."""
        return list(cls.PROVIDER_INFO.values())

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names."""
        return list(cls.PROVIDER_INFO.keys())
