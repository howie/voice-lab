"""Unit tests for OAuth domain validation.

These tests ensure that email domain validation works correctly,
especially after the ALLOWED_DOMAINS config is properly parsed.
"""

import pytest

from src.infrastructure.auth.domain_validator import (
    DomainValidationError,
    get_allowed_domains,
    is_domain_restriction_enabled,
    validate_email_domain,
)


class TestDomainValidation:
    """Test email domain validation logic."""

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache before each test."""
        from src.config import get_settings

        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_allowed_domain_passes(self, monkeypatch):
        """Email with allowed domain should pass validation."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw,example.com")
        from src.config import get_settings

        get_settings.cache_clear()

        result = validate_email_domain("user@heyuai.com.tw")
        assert result is True

    def test_disallowed_domain_raises_error(self, monkeypatch):
        """Email with disallowed domain should raise DomainValidationError."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw")
        from src.config import get_settings

        get_settings.cache_clear()

        with pytest.raises(DomainValidationError) as exc_info:
            validate_email_domain("user@gmail.com")

        assert "gmail.com" in str(exc_info.value)
        assert exc_info.value.email == "user@gmail.com"
        assert "heyuai.com.tw" in exc_info.value.allowed_domains

    def test_case_insensitive_domain_matching(self, monkeypatch):
        """Domain matching should be case insensitive."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw")
        from src.config import get_settings

        get_settings.cache_clear()

        # Email with uppercase domain should still match
        result = validate_email_domain("user@HEYUAI.COM.TW")
        assert result is True

    def test_no_restriction_allows_all(self, monkeypatch):
        """Empty ALLOWED_DOMAINS should allow all domains."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "")
        from src.config import get_settings

        get_settings.cache_clear()

        result = validate_email_domain("anyone@anydomain.com")
        assert result is True

    def test_asterisk_allows_all(self, monkeypatch):
        """Asterisk in ALLOWED_DOMAINS should allow all domains."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "*")
        from src.config import get_settings

        get_settings.cache_clear()

        result = validate_email_domain("anyone@anydomain.com")
        assert result is True

    def test_invalid_email_format_raises_error(self, monkeypatch):
        """Email without @ should raise DomainValidationError."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw")
        from src.config import get_settings

        get_settings.cache_clear()

        with pytest.raises(DomainValidationError):
            validate_email_domain("invalid-email")


class TestDomainRestrictionStatus:
    """Test domain restriction status helpers."""

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache before each test."""
        from src.config import get_settings

        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_restriction_enabled_when_domains_configured(self, monkeypatch):
        """is_domain_restriction_enabled should return True when domains are set."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw")
        from src.config import get_settings

        get_settings.cache_clear()

        assert is_domain_restriction_enabled() is True

    def test_restriction_disabled_when_empty(self, monkeypatch):
        """is_domain_restriction_enabled should return False when empty."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "")
        from src.config import get_settings

        get_settings.cache_clear()

        assert is_domain_restriction_enabled() is False

    def test_get_allowed_domains_returns_list(self, monkeypatch):
        """get_allowed_domains should return the configured domains."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw,example.com")
        from src.config import get_settings

        get_settings.cache_clear()

        domains = get_allowed_domains()
        assert domains == ["heyuai.com.tw", "example.com"]


class TestProductionScenario:
    """Test the exact production scenario that caused the bug.

    The bug occurred when:
    1. Terraform used jsonencode() producing '["heyuai.com.tw"]'
    2. Backend parsed this as a single string including brackets
    3. Domain 'heyuai.com.tw' did not match '["heyuai.com.tw"]'
    4. Users were blocked from logging in
    """

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache before each test."""
        from src.config import get_settings

        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_correct_format_allows_login(self, monkeypatch):
        """Correct comma-separated format should allow login."""
        # This is the CORRECT format from join(",", var.allowed_domains)
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw")
        from src.config import get_settings

        get_settings.cache_clear()

        # User with heyuai.com.tw email should be allowed
        result = validate_email_domain("user@heyuai.com.tw")
        assert result is True

    def test_json_format_blocks_login(self, monkeypatch):
        """JSON array format should block login (documenting the bug).

        This test ensures we catch if the Terraform config is accidentally
        changed back to using jsonencode().
        """
        # This is the WRONG format from jsonencode(var.allowed_domains)
        monkeypatch.setenv("ALLOWED_DOMAINS", '["heyuai.com.tw"]')
        from src.config import get_settings

        get_settings.cache_clear()

        # The domain 'heyuai.com.tw' will NOT match because allowed_domains
        # is incorrectly parsed as ['["heyuai.com.tw"]']
        with pytest.raises(DomainValidationError):
            validate_email_domain("user@heyuai.com.tw")
