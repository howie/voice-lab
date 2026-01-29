"""Integration tests for Provider Status Refresh.

T066: Integration test for status refresh
Tests the complete flow of provider status and quota refresh.
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


class TestProviderStatusRefresh:
    """Integration tests for provider status refresh flow."""

    @pytest.mark.asyncio
    async def test_refresh_status_updates_validation_state(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T066: Test that status refresh updates credential validation state."""
        # Initially the credential is valid
        assert mock_credential.is_valid is True

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        # Simulate the API key becoming invalid
        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=False,
            error_message="API key expired",
            validated_at=datetime.now(UTC),
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
                assert "API key expired" in data.get("error_message", "")

                # Verify credential was updated
                mock_credential_repo.update.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_status_recovers_from_invalid(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T066: Test that invalid credentials can recover on re-validation."""
        # Create an initially invalid credential
        invalid_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="elevenlabs",
            api_key="sk-test1234567890abcdef",
        )
        invalid_cred.mark_invalid()  # mark_invalid doesn't take error message
        assert invalid_cred.is_valid is False

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = invalid_cred
        mock_credential_repo.update.return_value = invalid_cred

        mock_audit_repo = AsyncMock()

        # Now the API key is valid again (user may have renewed subscription)
        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            validated_at=datetime.now(UTC),
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
                        f"/api/v1/credentials/{invalid_cred.id}/validate",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["is_valid"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_status_fetches_quota_info(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T066: Test that status refresh fetches quota information."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            validated_at=datetime.now(UTC),
            quota_info={
                "character_count": 5000,
                "character_limit": 10000,
                "remaining_characters": 5000,
                "tier": "Starter",
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
                assert data["quota_info"]["character_limit"] == 10000
                assert data["quota_info"]["remaining_characters"] == 5000
                assert data["quota_info"]["tier"] == "Starter"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_credentials_shows_current_status(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T066: Test that listing credentials shows current validation status."""
        # Create credentials with different statuses
        valid_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="elevenlabs",
            api_key="sk-valid-key",
        )
        valid_cred.mark_valid()

        invalid_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="azure",
            api_key="invalid-azure-key",
        )
        invalid_cred.mark_invalid()  # mark_invalid doesn't take error message

        mock_credential_repo = AsyncMock()
        mock_credential_repo.list_by_user.return_value = [valid_cred, invalid_cred]

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
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert len(data["credentials"]) == 2

                # Find credentials by provider
                creds_by_provider = {c["provider"]: c for c in data["credentials"]}

                assert creds_by_provider["elevenlabs"]["is_valid"] is True
                assert creds_by_provider["azure"]["is_valid"] is False
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_status_refresh_handles_network_error(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T066: Test that status refresh handles network errors gracefully.

        Note: The actual validators catch network errors and return a ValidationResult
        with is_valid=False and an error message. This test simulates that behavior.
        """
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        # Simulate network timeout - validators catch exceptions and return error results
        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=False,
            error_message="Request timed out",
            validated_at=datetime.now(UTC),
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

                # Network errors are returned as validation failures with error message
                assert response.status_code == 200
                data = response.json()
                assert data["is_valid"] is False
                assert "timed out" in data.get("error_message", "").lower()
        finally:
            app.dependency_overrides.clear()
