"""Integration tests for authentication flow.

Tests verify that protected endpoints behave correctly in different auth modes.

Note: These tests require a running database and proper environment setup.
Run with: pytest tests/integration/test_auth_integration.py -v

To skip these tests when database is not available, use:
pytest tests/integration/test_auth_integration.py -v -m "not integration"
"""

import importlib
import os

import pytest
from fastapi.testclient import TestClient

# Mark all tests in this module as integration tests requiring database
pytestmark = [
    pytest.mark.integration,
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]


@pytest.fixture(scope="module")
def setup_env():
    """Setup environment for testing."""
    # Store original values
    original_disable_auth = os.environ.get("DISABLE_AUTH", "false")
    original_app_env = os.environ.get("APP_ENV", "development")

    yield

    # Restore original values
    os.environ["DISABLE_AUTH"] = original_disable_auth
    os.environ["APP_ENV"] = original_app_env

    import src.presentation.api.middleware.auth as auth_module

    importlib.reload(auth_module)


@pytest.fixture
def client_with_auth_disabled(setup_env):
    """Create a test client with auth disabled."""
    os.environ["DISABLE_AUTH"] = "true"
    os.environ["APP_ENV"] = "development"

    import src.presentation.api.middleware.auth as auth_module

    importlib.reload(auth_module)

    from src.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    # Reset
    os.environ["DISABLE_AUTH"] = "false"
    importlib.reload(auth_module)


@pytest.fixture
def client_with_auth_enabled(setup_env):
    """Create a test client with auth enabled."""
    os.environ["DISABLE_AUTH"] = "false"
    os.environ["APP_ENV"] = "development"

    import src.presentation.api.middleware.auth as auth_module

    importlib.reload(auth_module)

    from src.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


class TestHealthEndpoint:
    """Test health endpoint (always public)."""

    def test_health_no_auth_required(self, client_with_auth_enabled):
        """Health endpoint should not require authentication."""
        response = client_with_auth_enabled.get("/api/v1/health")
        assert response.status_code == 200


class TestAuthMeEndpoint:
    """Test /auth/me endpoint in different auth modes."""

    def test_requires_auth_when_enabled(self, client_with_auth_enabled):
        """GET /auth/me should require authentication when auth is enabled."""
        response = client_with_auth_enabled.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    def test_returns_dev_user_when_disabled(self, client_with_auth_disabled):
        """GET /auth/me should return dev user when auth is disabled."""
        response = client_with_auth_disabled.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "dev@localhost"
        assert data["name"] == "Development User"
        assert data["id"] == "00000000-0000-0000-0000-000000000001"


class TestAuthDisabledInProduction:
    """Test that DISABLE_AUTH doesn't work in production mode."""

    def test_auth_required_even_with_disable_flag(self, setup_env):
        """Production mode should require auth even with DISABLE_AUTH=true."""
        os.environ["DISABLE_AUTH"] = "true"
        os.environ["APP_ENV"] = "production"

        import src.presentation.api.middleware.auth as auth_module

        importlib.reload(auth_module)

        from src.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/auth/me")
            # Should require authentication even though DISABLE_AUTH is set
            assert response.status_code == 401

        # Cleanup
        os.environ["DISABLE_AUTH"] = "false"
        os.environ["APP_ENV"] = "development"
        importlib.reload(auth_module)


class TestOAuthEndpoints:
    """Test OAuth-related endpoints."""

    def test_google_auth_redirects_or_unavailable(self, client_with_auth_enabled):
        """GET /auth/google should redirect or return 503 if not configured."""
        response = client_with_auth_enabled.get(
            "/api/v1/auth/google", follow_redirects=False
        )

        # Should either redirect to Google OAuth or return 503 if not configured
        assert response.status_code in [307, 503]

        if response.status_code == 307:
            assert "accounts.google.com" in response.headers.get("location", "")

    def test_domain_restriction_is_public(self, client_with_auth_enabled):
        """GET /auth/domain-restriction should be publicly accessible."""
        response = client_with_auth_enabled.get("/api/v1/auth/domain-restriction")

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "allowed_domains" in data


class TestLogoutEndpoint:
    """Test logout functionality."""

    def test_logout_succeeds_when_authenticated(self, client_with_auth_disabled):
        """POST /auth/logout should succeed when authenticated (using dev user)."""
        response = client_with_auth_disabled.post("/api/v1/auth/logout")
        assert response.status_code == 204

    def test_logout_requires_auth_when_enabled(self, client_with_auth_enabled):
        """POST /auth/logout should require authentication when auth is enabled."""
        response = client_with_auth_enabled.post("/api/v1/auth/logout")
        assert response.status_code == 401
