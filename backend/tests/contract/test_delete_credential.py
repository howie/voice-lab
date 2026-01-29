"""Contract tests for Delete Credential API endpoint.

T056: Contract test for DELETE /credentials/{id}
Tests the credential deletion flow.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider_credential import UserProviderCredential
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


class TestDeleteCredentialEndpoint:
    """Contract tests for DELETE /api/v1/credentials/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_credential_success(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T056: Test successful credential deletion."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.delete.return_value = None

        mock_audit_repo = AsyncMock()

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
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/credentials/{mock_credential.id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 204
                mock_credential_repo.delete.assert_called_once_with(mock_credential.id)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_credential_not_found(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T056: Test deletion of non-existent credential."""
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
                    response = await ac.delete(
                        f"/api/v1/credentials/{fake_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_credential_unauthorized(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T056: Test deletion of another user's credential."""
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
                    response = await ac.delete(
                        f"/api/v1/credentials/{mock_credential.id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 403
                mock_credential_repo.delete.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_credential_no_auth(
        self,
        mock_credential: UserProviderCredential,
    ):
        """T056: Test deletion without authentication."""
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
                response = await ac.delete(f"/api/v1/credentials/{mock_credential.id}")

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_credential_logs_audit_event(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T056: Test that deletion creates an audit log entry."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.delete.return_value = None

        mock_audit_repo = AsyncMock()

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
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.delete(
                        f"/api/v1/credentials/{mock_credential.id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 204
                # Verify audit log was created (via AuditService)
                mock_audit_repo.save.assert_called_once()
        finally:
            app.dependency_overrides.clear()
