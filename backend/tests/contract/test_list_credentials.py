"""Contract tests for List Credentials API endpoint.

T048: Contract test for GET /credentials (list all)
Tests the credential listing flow.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider_credential import UserProviderCredential
from src.main import app
from src.presentation.api.routes import credentials as credentials_module


@pytest.fixture
def mock_user_id() -> uuid.UUID:
    """Generate a mock user ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def mock_credentials(mock_user_id: uuid.UUID) -> list[UserProviderCredential]:
    """Create mock credentials for testing."""
    elevenlabs_cred = UserProviderCredential.create(
        user_id=mock_user_id,
        provider="elevenlabs",
        api_key="sk-eleven-test1234",
    )
    elevenlabs_cred.mark_valid()

    azure_cred = UserProviderCredential.create(
        user_id=mock_user_id,
        provider="azure",
        api_key="azure-key-5678",
    )
    azure_cred.mark_valid()

    gemini_cred = UserProviderCredential.create(
        user_id=mock_user_id,
        provider="gemini",
        api_key="gemini-key-9012",
    )
    gemini_cred.mark_invalid()  # mark_invalid doesn't take error message

    return [elevenlabs_cred, azure_cred, gemini_cred]


class TestListCredentialsEndpoint:
    """Contract tests for GET /api/v1/credentials endpoint."""

    @pytest.mark.asyncio
    async def test_list_credentials_success(
        self,
        mock_user_id: uuid.UUID,
        mock_credentials: list[UserProviderCredential],
    ):
        """T048: Test successful credential listing."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.list_by_user.return_value = mock_credentials

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
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()
                assert "credentials" in data
                assert len(data["credentials"]) == 3
                mock_credential_repo.list_by_user.assert_called_once_with(mock_user_id)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_credentials_empty(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T048: Test listing credentials when user has none."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.list_by_user.return_value = []

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
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["credentials"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_credentials_response_format(
        self,
        mock_user_id: uuid.UUID,
        mock_credentials: list[UserProviderCredential],
    ):
        """T048: Test response format includes all expected fields."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.list_by_user.return_value = mock_credentials[:1]

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
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                data = response.json()
                cred = data["credentials"][0]

                # Check required fields
                assert "id" in cred
                assert "provider" in cred
                assert "provider_display_name" in cred
                assert "masked_key" in cred
                assert "is_valid" in cred
                assert "created_at" in cred

                # Verify masked key format
                assert cred["masked_key"].startswith("****")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_credentials_only_returns_user_owned(
        self,
        mock_user_id: uuid.UUID,
        mock_credentials: list[UserProviderCredential],
    ):
        """T048: Test that only user's own credentials are returned."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.list_by_user.return_value = mock_credentials

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
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                assert response.status_code == 200
                # Verify repository was called with correct user ID
                mock_credential_repo.list_by_user.assert_called_once_with(mock_user_id)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_credentials_no_auth(self):
        """T048: Test listing credentials without authentication."""
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
                response = await ac.get("/api/v1/credentials")

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()
