"""Unit tests for authentication middleware.

Tests verify that authentication behaves correctly in different modes:
- DISABLE_AUTH=true + APP_ENV=development: Skip authentication, return dev user
- DISABLE_AUTH=true + APP_ENV=production: Require authentication (safety check)
- DISABLE_AUTH=false: Always require authentication
"""

import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture(autouse=True)
def reset_auth_module(monkeypatch):
    """Reset auth module to default state before each test."""
    # Set default values before each test
    monkeypatch.setenv("DISABLE_AUTH", "false")
    monkeypatch.setenv("APP_ENV", "development")

    yield

    # Cleanup after each test - reload with defaults
    monkeypatch.setenv("DISABLE_AUTH", "false")
    monkeypatch.setenv("APP_ENV", "development")
    import src.presentation.api.middleware.auth as auth_module

    importlib.reload(auth_module)


class TestAuthMiddlewareDisableAuthMode:
    """Test authentication middleware with DISABLE_AUTH=true."""

    @pytest.fixture
    def reload_auth_module_disabled(self, monkeypatch):
        """Reload auth module with DISABLE_AUTH=true and APP_ENV=development."""
        monkeypatch.setenv("DISABLE_AUTH", "true")
        monkeypatch.setenv("APP_ENV", "development")
        # Need to reload the module to pick up new env vars
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)
        yield auth_module
        # Reset to default after test
        monkeypatch.setenv("DISABLE_AUTH", "false")
        importlib.reload(auth_module)

    @pytest.fixture
    def reload_auth_module_disabled_production(self, monkeypatch):
        """Reload auth module with DISABLE_AUTH=true but APP_ENV=production."""
        monkeypatch.setenv("DISABLE_AUTH", "true")
        monkeypatch.setenv("APP_ENV", "production")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)
        yield auth_module
        # Reset to default after test
        monkeypatch.setenv("DISABLE_AUTH", "false")
        monkeypatch.setenv("APP_ENV", "development")
        importlib.reload(auth_module)

    @pytest.mark.asyncio
    async def test_disable_auth_development_returns_dev_user(self, reload_auth_module_disabled):
        """When DISABLE_AUTH=true and APP_ENV=development, should return dev user."""
        auth_module = reload_auth_module_disabled

        # No credentials provided
        result = await auth_module.get_current_user(credentials=None)

        assert result is not None
        assert result.id == "00000000-0000-0000-0000-000000000001"
        assert result.email == "dev@localhost"
        assert result.name == "Development User"

    @pytest.mark.asyncio
    async def test_disable_auth_development_optional_returns_dev_user(
        self, reload_auth_module_disabled
    ):
        """When DISABLE_AUTH=true and APP_ENV=development, optional auth returns dev user."""
        auth_module = reload_auth_module_disabled

        result = await auth_module.get_current_user_optional(credentials=None)

        assert result is not None
        assert result.id == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    async def test_disable_auth_production_still_requires_auth(
        self, reload_auth_module_disabled_production
    ):
        """When DISABLE_AUTH=true but APP_ENV=production, should still require auth."""
        auth_module = reload_auth_module_disabled_production

        # No credentials provided - should raise 401
        with pytest.raises(HTTPException) as exc_info:
            await auth_module.get_current_user(credentials=None)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_disable_auth_production_optional_returns_none(
        self, reload_auth_module_disabled_production
    ):
        """When DISABLE_AUTH=true but APP_ENV=production, optional returns None."""
        auth_module = reload_auth_module_disabled_production

        result = await auth_module.get_current_user_optional(credentials=None)

        assert result is None


class TestAuthMiddlewareNormalMode:
    """Test authentication middleware with DISABLE_AUTH=false (normal mode)."""

    @pytest.fixture
    def reload_auth_module_enabled(self, monkeypatch):
        """Reload auth module with DISABLE_AUTH=false."""
        monkeypatch.setenv("DISABLE_AUTH", "false")
        monkeypatch.setenv("APP_ENV", "development")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)
        yield auth_module

    @pytest.mark.asyncio
    async def test_no_credentials_raises_401(self, reload_auth_module_enabled):
        """When no credentials provided and auth enabled, should raise 401."""
        auth_module = reload_auth_module_enabled

        with pytest.raises(HTTPException) as exc_info:
            await auth_module.get_current_user(credentials=None)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_no_credentials_optional_returns_none(self, reload_auth_module_enabled):
        """When no credentials and auth enabled, optional returns None."""
        auth_module = reload_auth_module_enabled

        result = await auth_module.get_current_user_optional(credentials=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, reload_auth_module_enabled):
        """When invalid token provided, should raise 401."""
        auth_module = reload_auth_module_enabled

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token-here"
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_module.get_current_user(credentials=credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, reload_auth_module_enabled):
        """When valid token provided, should return user."""
        auth_module = reload_auth_module_enabled

        # Mock the verify_access_token function
        mock_payload = MagicMock()
        mock_payload.sub = "user-123"
        mock_payload.email = "test@example.com"
        mock_payload.name = "Test User"
        mock_payload.picture_url = "https://example.com/pic.jpg"
        mock_payload.google_id = "google-123"

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        with patch.object(auth_module, "verify_access_token", return_value=mock_payload):
            result = await auth_module.get_current_user(credentials=credentials)

        assert result is not None
        assert result.id == "user-123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, reload_auth_module_enabled):
        """When expired token provided, should raise 401 with specific message."""
        auth_module = reload_auth_module_enabled
        from jwt.exceptions import ExpiredSignatureError

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired-token")

        with patch.object(auth_module, "verify_access_token", side_effect=ExpiredSignatureError()):
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.get_current_user(credentials=credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


class TestAuthModeFlags:
    """Test that auth mode flags are correctly set from environment."""

    def test_disable_auth_false_string(self, monkeypatch):
        """DISABLE_AUTH=false should set flag to False."""
        monkeypatch.setenv("DISABLE_AUTH", "false")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.DISABLE_AUTH is False

    def test_disable_auth_true_string(self, monkeypatch):
        """DISABLE_AUTH=true should set flag to True."""
        monkeypatch.setenv("DISABLE_AUTH", "true")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.DISABLE_AUTH is True

    def test_disable_auth_case_insensitive(self, monkeypatch):
        """DISABLE_AUTH should be case insensitive."""
        monkeypatch.setenv("DISABLE_AUTH", "TRUE")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.DISABLE_AUTH is True

    def test_disable_auth_random_string_is_false(self, monkeypatch):
        """DISABLE_AUTH with random string should be False."""
        monkeypatch.setenv("DISABLE_AUTH", "random")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.DISABLE_AUTH is False

    def test_app_env_production(self, monkeypatch):
        """APP_ENV=production should be set correctly."""
        monkeypatch.setenv("APP_ENV", "production")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.APP_ENV == "production"

    def test_app_env_development(self, monkeypatch):
        """APP_ENV=development should be set correctly."""
        monkeypatch.setenv("APP_ENV", "development")
        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        assert auth_module.APP_ENV == "development"
