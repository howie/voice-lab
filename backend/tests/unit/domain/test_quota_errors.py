"""Unit tests for QuotaExceededError and ProviderQuotaInfo.

T005: Unit test for QuotaExceededError
T006: Unit test for ProviderQuotaInfo.get()
T017: Unit test for suggestion content per provider
T022: Unit test for retry_after parsing
"""

import pytest

from src.domain.errors import (
    ErrorCode,
    ProviderQuotaInfo,
    QuotaExceededError,
)


class TestQuotaExceededError:
    """T005: Unit tests for QuotaExceededError class."""

    def test_basic_creation_with_provider(self) -> None:
        """QuotaExceededError should populate from ProviderQuotaInfo defaults."""
        error = QuotaExceededError(provider="gemini")

        assert error.code == ErrorCode.QUOTA_EXCEEDED
        assert error.status_code == 429
        assert "Gemini TTS" in error.message
        assert "配額已用盡" in error.message
        assert error.details["provider"] == "gemini"
        assert error.details["provider_display_name"] == "Gemini TTS"

    def test_custom_display_name_overrides_default(self) -> None:
        """Custom provider_display_name should override ProviderQuotaInfo default."""
        error = QuotaExceededError(
            provider="gemini",
            provider_display_name="Custom Gemini",
        )

        assert error.details["provider_display_name"] == "Custom Gemini"
        assert "Custom Gemini" in error.message

    def test_quota_type_included_in_details(self) -> None:
        """quota_type should be included in details when provided."""
        error = QuotaExceededError(
            provider="elevenlabs",
            quota_type="characters",
        )

        assert error.details["quota_type"] == "characters"

    def test_retry_after_overrides_default(self) -> None:
        """Custom retry_after should override ProviderQuotaInfo default."""
        error = QuotaExceededError(
            provider="gemini",
            retry_after=120,
        )

        assert error.details["retry_after"] == 120

    def test_retry_after_uses_default_when_not_provided(self) -> None:
        """retry_after should use ProviderQuotaInfo default when not provided."""
        error = QuotaExceededError(provider="gemini")

        # gemini default_retry_after is 3600
        assert error.details["retry_after"] == 3600

    def test_help_url_included_in_details(self) -> None:
        """help_url should be included from ProviderQuotaInfo defaults."""
        error = QuotaExceededError(provider="elevenlabs")

        assert error.details["help_url"] == "https://elevenlabs.io/subscription"

    def test_custom_help_url_overrides_default(self) -> None:
        """Custom help_url should override ProviderQuotaInfo default."""
        error = QuotaExceededError(
            provider="elevenlabs",
            help_url="https://custom-url.com",
        )

        assert error.details["help_url"] == "https://custom-url.com"

    def test_suggestions_included_from_defaults(self) -> None:
        """Suggestions should be populated from ProviderQuotaInfo defaults."""
        error = QuotaExceededError(provider="azure")

        suggestions = error.details["suggestions"]
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Azure suggestions should mention Azure Portal
        assert any("Azure Portal" in s for s in suggestions)

    def test_custom_suggestions_override_defaults(self) -> None:
        """Custom suggestions should override ProviderQuotaInfo defaults."""
        custom = ["自訂建議一", "自訂建議二"]
        error = QuotaExceededError(
            provider="azure",
            suggestions=custom,
        )

        assert error.details["suggestions"] == custom

    def test_original_error_included_when_provided(self) -> None:
        """original_error should be included in details for debugging."""
        error = QuotaExceededError(
            provider="gemini",
            original_error="429: Resource has been exhausted",
        )

        assert error.details["original_error"] == "429: Resource has been exhausted"

    def test_original_error_absent_when_not_provided(self) -> None:
        """original_error should not be in details when not provided."""
        error = QuotaExceededError(provider="gemini")

        assert "original_error" not in error.details

    def test_unknown_provider_uses_fallback(self) -> None:
        """Unknown provider should use fallback display name and suggestions."""
        error = QuotaExceededError(provider="unknown_provider")

        assert error.details["provider_display_name"] == "Unknown_Provider"
        assert error.details["provider"] == "unknown_provider"
        assert error.status_code == 429

    def test_to_dict_format(self) -> None:
        """to_dict should return correct API response structure."""
        error = QuotaExceededError(provider="gemini")
        result = error.to_dict()

        assert "error" in result
        assert result["error"]["code"] == "QUOTA_EXCEEDED"
        assert "配額已用盡" in result["error"]["message"]
        assert "provider" in result["error"]["details"]

    @pytest.mark.parametrize(
        "provider",
        ["gemini", "elevenlabs", "azure", "gcp", "openai", "deepgram", "voai"],
    )
    def test_all_known_providers_produce_valid_error(self, provider: str) -> None:
        """All known providers should produce a valid QuotaExceededError."""
        error = QuotaExceededError(provider=provider)

        assert error.code == ErrorCode.QUOTA_EXCEEDED
        assert error.status_code == 429
        assert error.details["provider"] == provider
        assert error.details["provider_display_name"]
        assert error.details["retry_after"] > 0
        assert "配額已用盡" in error.message


class TestProviderQuotaInfo:
    """T006: Unit tests for ProviderQuotaInfo.get()."""

    def test_known_provider_returns_info(self) -> None:
        """Known provider should return full info dict."""
        info = ProviderQuotaInfo.get("gemini")

        assert info["display_name"] == "Gemini TTS"
        assert info["help_url"] == "https://ai.google.dev/pricing"
        assert info["default_retry_after"] == 3600
        assert isinstance(info["suggestions"], list)
        assert len(info["suggestions"]) > 0

    def test_unknown_provider_returns_fallback(self) -> None:
        """Unknown provider should return fallback with title-cased name."""
        info = ProviderQuotaInfo.get("some_unknown")

        assert info["display_name"] == "Some_Unknown"
        assert info["help_url"] is None
        assert info["default_retry_after"] == 60
        assert isinstance(info["suggestions"], list)
        assert len(info["suggestions"]) > 0

    @pytest.mark.parametrize(
        "provider,expected_display_name",
        [
            ("gemini", "Gemini TTS"),
            ("elevenlabs", "ElevenLabs"),
            ("azure", "Azure Speech"),
            ("gcp", "Google Cloud Speech"),
            ("openai", "OpenAI Whisper"),
            ("deepgram", "Deepgram"),
            ("voai", "VoAI TTS"),
        ],
    )
    def test_display_names(self, provider: str, expected_display_name: str) -> None:
        """Each provider should have the correct display name."""
        info = ProviderQuotaInfo.get(provider)
        assert info["display_name"] == expected_display_name

    @pytest.mark.parametrize(
        "provider",
        ["gemini", "elevenlabs", "azure", "gcp", "openai", "deepgram", "voai"],
    )
    def test_all_providers_have_help_url(self, provider: str) -> None:
        """All known providers should have a help URL."""
        info = ProviderQuotaInfo.get(provider)
        assert info["help_url"] is not None
        assert info["help_url"].startswith("https://")

    @pytest.mark.parametrize(
        "provider",
        ["gemini", "elevenlabs", "azure", "gcp", "openai", "deepgram", "voai"],
    )
    def test_all_providers_have_suggestions(self, provider: str) -> None:
        """All known providers should have at least one suggestion."""
        info = ProviderQuotaInfo.get(provider)
        assert isinstance(info["suggestions"], list)
        assert len(info["suggestions"]) >= 1

    @pytest.mark.parametrize(
        "provider",
        ["gemini", "elevenlabs", "azure", "gcp", "openai", "deepgram", "voai"],
    )
    def test_all_providers_have_positive_retry_after(self, provider: str) -> None:
        """All known providers should have positive default_retry_after."""
        info = ProviderQuotaInfo.get(provider)
        assert info["default_retry_after"] > 0


class TestProviderSuggestions:
    """T017: Unit test for suggestion content per provider."""

    @pytest.mark.parametrize(
        "provider,expected_keyword",
        [
            ("gemini", "Google AI Studio"),
            ("elevenlabs", "ElevenLabs"),
            ("azure", "Azure Portal"),
            ("gcp", "GCP Console"),
            ("openai", "OpenAI"),
            ("deepgram", "Deepgram Console"),
            ("voai", "VoAI"),
        ],
    )
    def test_suggestions_mention_provider_platform(
        self, provider: str, expected_keyword: str
    ) -> None:
        """Each provider's suggestions should reference its platform."""
        info = ProviderQuotaInfo.get(provider)
        suggestions_text = " ".join(info["suggestions"])
        assert expected_keyword in suggestions_text

    @pytest.mark.parametrize(
        "provider",
        ["gemini", "elevenlabs", "azure", "gcp", "openai", "deepgram", "voai"],
    )
    def test_suggestions_are_in_chinese(self, provider: str) -> None:
        """All suggestions should contain Chinese characters."""
        info = ProviderQuotaInfo.get(provider)
        for suggestion in info["suggestions"]:
            has_chinese = any("\u4e00" <= c <= "\u9fff" for c in suggestion)
            assert has_chinese, f"Suggestion not in Chinese: {suggestion}"


class TestRetryAfterParsing:
    """T022: Unit test for retry_after parsing in QuotaExceededError."""

    def test_retry_after_as_integer(self) -> None:
        """retry_after should accept integer seconds."""
        error = QuotaExceededError(provider="gemini", retry_after=3600)
        assert error.details["retry_after"] == 3600

    def test_retry_after_zero_uses_default(self) -> None:
        """retry_after=0 is falsy, should fall back to default."""
        error = QuotaExceededError(provider="gemini", retry_after=0)
        # 0 is falsy in Python, so it falls back to default
        assert error.details["retry_after"] == 3600

    def test_retry_after_none_uses_default(self) -> None:
        """retry_after=None should use provider default."""
        error = QuotaExceededError(provider="azure", retry_after=None)
        assert error.details["retry_after"] == 60

    def test_retry_after_custom_value_preserved(self) -> None:
        """Custom retry_after value should be preserved exactly."""
        error = QuotaExceededError(provider="gemini", retry_after=42)
        assert error.details["retry_after"] == 42

    def test_retry_after_large_value(self) -> None:
        """Large retry_after value should be preserved."""
        error = QuotaExceededError(provider="gemini", retry_after=86400)
        assert error.details["retry_after"] == 86400
