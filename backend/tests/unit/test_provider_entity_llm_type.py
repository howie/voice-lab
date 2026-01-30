"""Unit tests for Provider entity LLM type support."""

import pytest

from src.domain.entities.provider import Provider


class TestProviderLLMType:
    """Tests for Provider entity with LLM type support."""

    def test_provider_with_llm_type(self):
        """Test creating a provider with only llm type."""
        provider = Provider(
            id="anthropic",
            name="anthropic",
            display_name="Anthropic",
            type=["llm"],
        )
        assert provider.supports_llm is True
        assert provider.supports_tts is False
        assert provider.supports_stt is False

    def test_provider_with_mixed_types(self):
        """Test creating a provider with tts, stt, and llm types."""
        provider = Provider(
            id="azure",
            name="azure",
            display_name="Azure",
            type=["tts", "stt", "llm"],
        )
        assert provider.supports_tts is True
        assert provider.supports_stt is True
        assert provider.supports_llm is True

    def test_provider_rejects_invalid_type(self):
        """Test that an invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Provider type must be a list"):
            Provider(
                id="bad",
                name="bad",
                display_name="Bad",
                type=["invalid"],
            )

    def test_supports_llm_property_false(self):
        """Test supports_llm returns False when type does not include llm."""
        provider = Provider(
            id="elevenlabs",
            name="elevenlabs",
            display_name="ElevenLabs",
            type=["tts"],
        )
        assert provider.supports_llm is False

    def test_provider_tts_and_llm(self):
        """Test provider with tts and llm types."""
        provider = Provider(
            id="gemini",
            name="gemini",
            display_name="Google Gemini",
            type=["tts", "llm"],
        )
        assert provider.supports_tts is True
        assert provider.supports_stt is False
        assert provider.supports_llm is True

    def test_provider_stt_and_llm(self):
        """Test provider with stt and llm types."""
        provider = Provider(
            id="openai",
            name="openai",
            display_name="OpenAI",
            type=["stt", "llm"],
        )
        assert provider.supports_tts is False
        assert provider.supports_stt is True
        assert provider.supports_llm is True
