"""Contract tests for Update Credential API endpoint.

T037: Contract test for PUT /credentials/{id} (model selection and key update)
Tests the credential update flow including model selection.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider_credential import UserProviderCredential
from src.infrastructure.providers.validators.base import ValidationResult
from src.main import app
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


class TestUpdateCredentialEndpoint:
    """Contract tests for PUT /api/v1/credentials/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_model_selection_success(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T037: Test successful model selection update."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

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
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.put(
                        f"/api/v1/credentials/{mock_credential.id}",
                        json={"selected_model_id": "eleven_multilingual_v2"},
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert data["provider"] == "elevenlabs"
                assert "selected_model_id" in data
                assert "updated_at" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_api_key_success(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T037: Test successful API key update with validation."""
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
                    response = await ac.put(
                        f"/api/v1/credentials/{mock_credential.id}",
                        json={"api_key": "sk-newkey1234567890abcdef"},
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert data["is_valid"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_api_key_validation_failed(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T037: Test API key update with failed validation."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=False,
            error_message="Invalid API key",
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
                    response = await ac.put(
                        f"/api/v1/credentials/{mock_credential.id}",
                        json={"api_key": "invalid-key"},
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_both_key_and_model(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T037: Test updating both API key and model selection."""
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
                    response = await ac.put(
                        f"/api/v1/credentials/{mock_credential.id}",
                        json={
                            "api_key": "sk-newkey1234567890",
                            "selected_model_id": "eleven_turbo_v2",
                        },
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_credential_not_found(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T037: Test updating non-existent credential."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = None

        mock_audit_repo = AsyncMock()

        mock_session = MagicMock()

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
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    fake_id = uuid.uuid4()
                    response = await ac.put(
                        f"/api/v1/credentials/{fake_id}",
                        json={"selected_model_id": "some-model"},
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_credential_unauthorized(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T037: Test updating another user's credential."""
        different_user_id = uuid.uuid4()

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_audit_repo = AsyncMock()

        mock_session = MagicMock()

        async def override_get_current_user_id():
            return different_user_id

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
                    "src.presentation.api.routes.credentials.SQLAlchemyAuditLogRepository",
                    return_value=mock_audit_repo,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.put(
                        f"/api/v1/credentials/{mock_credential.id}",
                        json={"selected_model_id": "some-model"},
                        headers={"X-User-Id": str(different_user_id)},
                    )

                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_credential_no_auth(
        self,
        mock_credential: UserProviderCredential,
    ):
        """T037: Test updating credential without authentication."""
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
                response = await ac.put(
                    f"/api/v1/credentials/{mock_credential.id}",
                    json={"selected_model_id": "some-model"},
                )

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()
