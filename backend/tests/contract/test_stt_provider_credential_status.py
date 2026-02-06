"""Contract tests for STT provider credential status logic.

Regression tests ensuring that providers initialized via system env vars
default to has_credentials=True, is_valid=True when the user has no
DB-level credentials. Previously, these defaulted to False/False, which
caused the frontend to show "請先至 Provider 管理頁面設定 API Key" even
though transcription worked via system fallback credentials.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider_credential import UserProviderCredential
from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import get_stt_providers
from src.presentation.api.middleware.auth import CurrentUser, get_current_user

TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
TEST_USER = CurrentUser(
    id=str(TEST_USER_ID),
    email="test@example.com",
    name="Test User",
    picture_url=None,
    google_id="google-test-id-12345",
)


def _make_mock_session(credentials: list[UserProviderCredential] | None = None):
    """Create a mock DB session that returns the given credentials."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = credentials or []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


def _make_mock_provider(name: str):
    """Create a mock STT provider."""
    provider = MagicMock()
    provider.name = name
    provider.supports_streaming = True
    return provider


class TestSTTProviderCredentialStatus:
    """Tests for has_credentials / is_valid behavior on GET /api/v1/stt/providers."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Override auth dependency."""

        async def get_mock_user():
            return TEST_USER

        app.dependency_overrides[get_current_user] = get_mock_user
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_system_provider_without_user_creds_defaults_to_valid(self):
        """Provider initialized via env vars but no user DB credentials
        should still report has_credentials=True, is_valid=True."""
        mock_session = _make_mock_session(credentials=[])

        async def get_mock_session():
            yield mock_session

        mock_providers = {"azure": _make_mock_provider("azure")}

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            data = response.json()
            azure = next(p for p in data["providers"] if p["name"] == "azure")

            assert azure["has_credentials"] is True
            assert azure["is_valid"] is True
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_multiple_providers_without_user_creds_all_valid(self):
        """All system-initialized providers should default to valid
        when user has no DB credentials."""
        mock_session = _make_mock_session(credentials=[])

        async def get_mock_session():
            yield mock_session

        mock_providers = {
            "azure": _make_mock_provider("azure"),
            "gcp": _make_mock_provider("gcp"),
            "whisper": _make_mock_provider("whisper"),
        }

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            for provider in response.json()["providers"]:
                assert provider["has_credentials"] is True, (
                    f"Provider {provider['name']} should have has_credentials=True"
                )
                assert provider["is_valid"] is True, (
                    f"Provider {provider['name']} should have is_valid=True"
                )
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_user_creds_override_system_defaults(self):
        """When user has DB credentials for a provider, those should be used
        instead of the system defaults."""
        user_cred = UserProviderCredential(
            id=uuid.uuid4(),
            user_id=TEST_USER_ID,
            provider="azure",
            api_key="user-azure-key",
            is_valid=True,
        )
        mock_session = _make_mock_session(credentials=[user_cred])

        async def get_mock_session():
            yield mock_session

        mock_providers = {"azure": _make_mock_provider("azure")}

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            azure = next(p for p in response.json()["providers"] if p["name"] == "azure")
            assert azure["has_credentials"] is True
            assert azure["is_valid"] is True
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_invalid_user_creds_reflected_in_response(self):
        """When user has invalid DB credentials, has_credentials=True
        but is_valid=False."""
        user_cred = UserProviderCredential(
            id=uuid.uuid4(),
            user_id=TEST_USER_ID,
            provider="azure",
            api_key="bad-key",
            is_valid=False,
        )
        mock_session = _make_mock_session(credentials=[user_cred])

        async def get_mock_session():
            yield mock_session

        mock_providers = {"azure": _make_mock_provider("azure")}

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            azure = next(p for p in response.json()["providers"] if p["name"] == "azure")
            assert azure["has_credentials"] is True
            assert azure["is_valid"] is False
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_whisper_maps_to_openai_credentials(self):
        """Whisper STT provider should look up 'openai' credentials,
        not 'whisper'."""
        # User has openai credentials (not whisper)
        user_cred = UserProviderCredential(
            id=uuid.uuid4(),
            user_id=TEST_USER_ID,
            provider="openai",
            api_key="user-openai-key",
            is_valid=True,
        )
        mock_session = _make_mock_session(credentials=[user_cred])

        async def get_mock_session():
            yield mock_session

        mock_providers = {"whisper": _make_mock_provider("whisper")}

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            whisper = next(p for p in response.json()["providers"] if p["name"] == "whisper")
            # Should pick up openai credentials via stt_mapping
            assert whisper["has_credentials"] is True
            assert whisper["is_valid"] is True
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_stt_providers, None)
