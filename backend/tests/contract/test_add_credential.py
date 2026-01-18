"""Contract tests for Credential API endpoints.

T023: Contract test for POST /credentials
Tests the credential creation and validation flow.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider import Provider
from src.domain.entities.provider_credential import UserProviderCredential
from src.infrastructure.providers.validators.base import ValidationResult
from src.main import app
from src.presentation.api.middleware.auth import CurrentUser, get_current_user
from src.presentation.api.routes import credentials as credentials_module


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Create a mock current user for authentication."""
    return CurrentUser(
        id="test-user-id",
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
    )


@pytest.fixture
def mock_user_id() -> uuid.UUID:
    """Generate a mock user ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def mock_provider() -> Provider:
    """Create a mock provider for testing."""
    return Provider(
        id="elevenlabs",
        name="elevenlabs",
        display_name="ElevenLabs",
        type=["tts"],
        is_active=True,
    )


@pytest.fixture
def mock_credential(mock_user_id: uuid.UUID) -> UserProviderCredential:
    """Create a mock credential for testing."""
    return UserProviderCredential.create(
        user_id=mock_user_id,
        provider="elevenlabs",
        api_key="sk-test1234567890abcdef",
    )


class TestAddCredentialEndpoint:
    """Contract tests for POST /api/v1/credentials endpoint."""

    @pytest.mark.asyncio
    async def test_add_credential_success(
        self,
        mock_user_id: uuid.UUID,
        mock_provider: Provider,
        mock_credential: UserProviderCredential,
    ):
        """T023: Test successful credential creation."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.exists.return_value = False
        mock_credential_repo.save.return_value = mock_credential

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.return_value = mock_provider

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            validated_at=datetime.now(UTC),
        )

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user_id():
            return mock_user_id

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[credentials_module.get_current_user_id] = (
            override_get_current_user_id
        )
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderRepository",
                    return_value=mock_provider_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
                patch(
                    "src.infrastructure.providers.validators.ProviderValidatorRegistry.get_validator",
                    return_value=mock_validator,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    payload = {
                        "provider": "elevenlabs",
                        "api_key": "sk-test1234567890abcdef",
                    }
                    response = await ac.post(
                        "/api/v1/credentials",
                        json=payload,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 201
                data = response.json()
                assert "id" in data
                assert data["provider"] == "elevenlabs"
                assert data["provider_display_name"] == "ElevenLabs"
                assert "masked_key" in data
                assert data["masked_key"].startswith("****")
                assert data["is_valid"] is True
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_credential_validation_failed(
        self,
        mock_user_id: uuid.UUID,
        mock_provider: Provider,
    ):
        """T023: Test credential creation with invalid API key."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.exists.return_value = False

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.return_value = mock_provider

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=False,
            error_message="Invalid API key",
            validated_at=datetime.now(UTC),
        )

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user_id():
            return mock_user_id

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[credentials_module.get_current_user_id] = (
            override_get_current_user_id
        )
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderRepository",
                    return_value=mock_provider_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
                patch(
                    "src.infrastructure.providers.validators.ProviderValidatorRegistry.get_validator",
                    return_value=mock_validator,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    payload = {
                        "provider": "elevenlabs",
                        "api_key": "invalid-key",
                    }
                    response = await ac.post(
                        "/api/v1/credentials",
                        json=payload,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_credential_duplicate(
        self,
        mock_user_id: uuid.UUID,
        mock_provider: Provider,
    ):
        """T023: Test credential creation when credential already exists."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.exists.return_value = True

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.return_value = mock_provider

        mock_audit_repo = AsyncMock()

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user_id():
            return mock_user_id

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[credentials_module.get_current_user_id] = (
            override_get_current_user_id
        )
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderRepository",
                    return_value=mock_provider_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    payload = {
                        "provider": "elevenlabs",
                        "api_key": "sk-test1234567890abcdef",
                    }
                    response = await ac.post(
                        "/api/v1/credentials",
                        json=payload,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 409
                data = response.json()
                assert "detail" in data
                assert "already exists" in data["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_credential_provider_not_found(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T023: Test credential creation with unsupported provider."""
        mock_credential_repo = AsyncMock()
        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.return_value = None

        mock_audit_repo = AsyncMock()

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        async def override_get_current_user_id():
            return mock_user_id

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[credentials_module.get_current_user_id] = (
            override_get_current_user_id
        )
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderRepository",
                    return_value=mock_provider_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    payload = {
                        "provider": "unknown_provider",
                        "api_key": "sk-test1234567890abcdef",
                    }
                    response = await ac.post(
                        "/api/v1/credentials",
                        json=payload,
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                # API returns 422 for validation errors (unknown provider)
                # or 400 for business logic errors
                assert response.status_code in [400, 422]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_credential_unauthorized(self):
        """T023: Test credential creation without authentication."""
        from fastapi import HTTPException, status

        async def override_get_current_user_id():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        app.dependency_overrides[credentials_module.get_current_user_id] = (
            override_get_current_user_id
        )

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "provider": "elevenlabs",
                    "api_key": "sk-test1234567890abcdef",
                }
                response = await ac.post("/api/v1/credentials", json=payload)

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()


class TestListProvidersEndpoint:
    """Contract tests for GET /api/v1/credentials/providers endpoint."""

    @pytest.mark.asyncio
    async def test_list_providers_success(
        self, mock_provider: Provider, mock_current_user: CurrentUser
    ):
        """T023: Test listing all supported providers."""
        mock_provider_repo = AsyncMock()
        mock_provider_repo.list_all.return_value = [mock_provider]

        mock_session = MagicMock()

        # Override authentication dependency
        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderRepository",
                return_value=mock_provider_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get("/api/v1/credentials/providers")

                assert response.status_code == 200
                data = response.json()
                assert "providers" in data
                # Verify we get at least one provider
                assert len(data["providers"]) >= 1
                # Verify each provider has required fields
                for provider in data["providers"]:
                    assert "id" in provider
                    assert "name" in provider
                    assert "display_name" in provider
                    assert "type" in provider
        finally:
            app.dependency_overrides.clear()
