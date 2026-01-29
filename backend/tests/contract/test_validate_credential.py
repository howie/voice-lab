"""Contract tests for Validate Credential API endpoint.

T065: Contract test for POST /credentials/{id}/validate
Tests the credential validation (revalidation) flow.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider_credential import UserProviderCredential
from src.infrastructure.providers.validators.base import ValidationResult
from src.main import app
from src.presentation.api.middleware.auth import CurrentUser, get_current_user
from src.presentation.api.routes import credentials as credentials_module


@pytest.fixture
def mock_user_id() -> uuid.UUID:
    """Generate a mock user ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def mock_credential(mock_user_id: uuid.UUID) -> UserProviderCredential:
    """Create a mock credential for testing."""
    cred = UserProviderCredential.create(
        user_id=mock_user_id,
        provider="elevenlabs",
        api_key="sk-test1234567890abcdef",
    )
    cred.mark_valid()
    return cred


class TestValidateCredentialEndpoint:
    """Contract tests for POST /api/v1/credentials/{id}/validate endpoint."""

    @pytest.mark.asyncio
    async def test_validate_credential_success(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T065: Test successful credential validation."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            validated_at=datetime.now(UTC),
        )

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        # Override FastAPI dependencies
        mock_current_user = CurrentUser(
            id=str(mock_user_id),
            email="test@example.com",
            name="Test User",
            picture_url=None,
            google_id="google-123",
        )

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
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
                    response = await ac.post(
                        f"/api/v1/credentials/{mock_credential.id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["is_valid"] is True
                mock_validator.validate.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_credential_fails_invalid_key(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T065: Test validation with invalid API key."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=False,
            error_message="Invalid API key",
        )

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        mock_current_user = CurrentUser(
            id=str(mock_user_id),
            email="test@example.com",
            name="Test User",
            picture_url=None,
            google_id="google-123",
        )

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
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
                    response = await ac.post(
                        f"/api/v1/credentials/{mock_credential.id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["is_valid"] is False
                assert "Invalid API key" in data.get("error_message", "")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_credential_not_found(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T065: Test validation of non-existent credential."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = None

        mock_audit_repo = AsyncMock()

        mock_session = MagicMock()

        mock_current_user = CurrentUser(
            id=str(mock_user_id),
            email="test@example.com",
            name="Test User",
            picture_url=None,
            google_id="google-123",
        )

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    fake_id = uuid.uuid4()
                    response = await ac.post(
                        f"/api/v1/credentials/{fake_id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_credential_unauthorized(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T065: Test validation of another user's credential."""
        different_user_id = uuid.uuid4()

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_session = MagicMock()

        mock_current_user = CurrentUser(
            id=str(different_user_id),
            email="test@example.com",
            name="Test User",
            picture_url=None,
            google_id="google-123",
        )

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
                ),
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.post(
                        f"/api/v1/credentials/{mock_credential.id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_credential_no_auth(
        self,
        mock_credential: UserProviderCredential,
    ):
        """T065: Test validation without authentication."""
        # Clear any existing overrides and don't set user_id override
        app.dependency_overrides.clear()

        # Mock get_current_user_id to raise 401
        from fastapi import HTTPException, status

        async def override_get_current_user():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post(f"/api/v1/credentials/{mock_credential.id}/validate")

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_credential_logs_audit_event(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T065: Test that validation creates an audit log entry."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(is_valid=True)

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        mock_current_user = CurrentUser(
            id=str(mock_user_id),
            email="test@example.com",
            name="Test User",
            picture_url=None,
            google_id="google-123",
        )

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
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
                    response = await ac.post(
                        f"/api/v1/credentials/{mock_credential.id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                # Verify audit log was created
                mock_audit_repo.save.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_credential_with_quota_info(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T065: Test validation returns quota information when available."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            validated_at=datetime.now(UTC),
            quota_info={
                "character_count": 10000,
                "character_limit": 100000,
                "remaining_characters": 90000,
            },
        )

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        mock_current_user = CurrentUser(
            id=str(mock_user_id),
            email="test@example.com",
            name="Test User",
            picture_url=None,
            google_id="google-123",
        )

        async def override_get_current_user():
            return mock_current_user

        async def override_get_db_session():
            return mock_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

        try:
            with (
                patch(
                    "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                    return_value=mock_credential_repo,
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
                    response = await ac.post(
                        f"/api/v1/credentials/{mock_credential.id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["is_valid"] is True
                assert "quota_info" in data
                assert data["quota_info"]["character_limit"] == 100000
        finally:
            app.dependency_overrides.clear()
