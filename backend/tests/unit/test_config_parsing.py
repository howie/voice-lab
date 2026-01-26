"""Unit tests for configuration parsing.

These tests ensure that environment variables are correctly parsed,
especially for comma-separated list values like ALLOWED_DOMAINS and CORS_ORIGINS.

CRITICAL: These tests protect against the production bug where Terraform's
jsonencode() produced JSON arrays like '["domain.com"]' instead of
comma-separated strings like 'domain.com,other.com'.
"""

import importlib

import pytest


class TestAllowedDomainsParsing:
    """Test ALLOWED_DOMAINS environment variable parsing.

    The backend expects comma-separated format: "domain1.com,domain2.com"
    NOT JSON array format: ["domain1.com","domain2.com"]
    """

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache before each test."""
        from src.config import get_settings

        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_single_domain_parsed_correctly(self, monkeypatch):
        """Single domain should be parsed into a list with one item."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.allowed_domains == ["heyuai.com.tw"]

    def test_multiple_domains_comma_separated(self, monkeypatch):
        """Multiple domains separated by commas should all be parsed."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw,example.com,test.org")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.allowed_domains == ["heyuai.com.tw", "example.com", "test.org"]

    def test_domains_with_spaces_trimmed(self, monkeypatch):
        """Spaces around domains should be trimmed."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "heyuai.com.tw , example.com , test.org")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.allowed_domains == ["heyuai.com.tw", "example.com", "test.org"]

    def test_domains_lowercased(self, monkeypatch):
        """Domains should be lowercased for case-insensitive comparison."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "HeyUAI.COM.TW,EXAMPLE.COM")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.allowed_domains == ["heyuai.com.tw", "example.com"]

    def test_empty_string_returns_empty_list(self, monkeypatch):
        """Empty string should return empty list (allow all domains)."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.allowed_domains == []

    def test_asterisk_returns_empty_list(self, monkeypatch):
        """Asterisk (*) should return empty list (allow all domains)."""
        monkeypatch.setenv("ALLOWED_DOMAINS", "*")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.allowed_domains == []

    def test_json_array_format_is_wrong(self, monkeypatch):
        """JSON array format should NOT be correctly parsed.

        This test documents the bug that occurred when Terraform used
        jsonencode() instead of join(). The JSON array format results
        in incorrect parsing.
        """
        # This is the WRONG format that Terraform's jsonencode() produces
        monkeypatch.setenv("ALLOWED_DOMAINS", '["heyuai.com.tw"]')
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        # The JSON format is incorrectly parsed as a single string with brackets
        # This test documents the expected (incorrect) behavior to catch this bug
        assert settings.allowed_domains != ["heyuai.com.tw"]
        # It would be parsed as the literal string including brackets
        assert '["heyuai.com.tw"]' in str(settings.allowed_domains)


class TestCorsOriginsParsing:
    """Test CORS_ORIGINS environment variable parsing."""

    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset settings cache before each test."""
        from src.config import get_settings

        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_single_origin_parsed_correctly(self, monkeypatch):
        """Single origin should be parsed into a list with one item."""
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.cors_origins == ["https://example.com"]

    def test_multiple_origins_comma_separated(self, monkeypatch):
        """Multiple origins separated by commas should all be parsed."""
        monkeypatch.setenv(
            "CORS_ORIGINS", "https://example.com,http://localhost:5173,http://localhost:3000"
        )
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.cors_origins == [
            "https://example.com",
            "http://localhost:5173",
            "http://localhost:3000",
        ]

    def test_origins_with_spaces_trimmed(self, monkeypatch):
        """Spaces around origins should be trimmed."""
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com , http://localhost:5173")
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.cors_origins == ["https://example.com", "http://localhost:5173"]

    def test_json_array_format_is_wrong(self, monkeypatch):
        """JSON array format should NOT be correctly parsed.

        This test documents the bug that occurred when Terraform used
        jsonencode() instead of join().
        """
        monkeypatch.setenv("CORS_ORIGINS", '["https://example.com","http://localhost:5173"]')
        from src.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        # The JSON format is incorrectly parsed
        assert settings.cors_origins != ["https://example.com", "http://localhost:5173"]


class TestOAuthEnvVarNames:
    """Test that OAuth environment variables support both naming conventions.

    Terraform uses GOOGLE_OAUTH_CLIENT_ID/SECRET, but older code used
    GOOGLE_CLIENT_ID/SECRET. Both should work.
    """

    def test_google_oauth_client_id_preferred(self, monkeypatch):
        """GOOGLE_OAUTH_CLIENT_ID should be used when set."""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "oauth-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "old-client-id")

        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.GOOGLE_CLIENT_ID == "oauth-client-id"

    def test_google_client_id_fallback(self, monkeypatch):
        """GOOGLE_CLIENT_ID should be used as fallback when GOOGLE_OAUTH_CLIENT_ID is not set."""
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "fallback-client-id")

        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.GOOGLE_CLIENT_ID == "fallback-client-id"

    def test_google_oauth_client_secret_preferred(self, monkeypatch):
        """GOOGLE_OAUTH_CLIENT_SECRET should be used when set."""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "oauth-secret")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "old-secret")

        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.GOOGLE_CLIENT_SECRET == "oauth-secret"

    def test_google_client_secret_fallback(self, monkeypatch):
        """GOOGLE_CLIENT_SECRET should be used as fallback."""
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fallback-secret")

        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.GOOGLE_CLIENT_SECRET == "fallback-secret"

    def test_oauth_env_var_takes_precedence_over_dotenv(self, monkeypatch):
        """Environment variable should take precedence over .env file values."""
        # Set explicit env var (this overrides any .env file)
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "explicit-from-env")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "explicit-secret-from-env")

        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.GOOGLE_CLIENT_ID == "explicit-from-env"
        assert auth_module.GOOGLE_CLIENT_SECRET == "explicit-secret-from-env"
