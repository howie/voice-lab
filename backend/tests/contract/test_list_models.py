"""Contract tests for List Models API endpoint.

T036: Contract test for GET /credentials/{id}/models
Tests the model listing flow for provider credentials.
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


class TestListModelsEndpoint:
    """Contract tests for GET /api/v1/credentials/{id}/models endpoint."""

    @pytest.mark.asyncio
    async def test_list_models_success(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T036: Test successful model listing."""
        mock_models = [
            {
                "id": "eleven_multilingual_v2",
                "name": "Eleven Multilingual v2",
                "language": "en-US",
                "gender": "neutral",
                "description": "High quality multilingual model",
            },
            {
                "id": "eleven_turbo_v2",
                "name": "Eleven Turbo v2",
                "language": "en-US",
                "gender": "neutral",
                "description": "Fast synthesis model",
            },
        ]

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_validator = AsyncMock()
        mock_validator.get_available_models.return_value = mock_models

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
                    "src.infrastructure.providers.validators.ProviderValidatorRegistry.get_validator",
                    return_value=mock_validator,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/credentials/{mock_credential.id}/models",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert "models" in data
                assert len(data["models"]) == 2
                assert data["models"][0]["id"] == "eleven_multilingual_v2"
                assert data["models"][0]["name"] == "Eleven Multilingual v2"
                assert data["models"][0]["language"] == "en-US"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_models_with_language_filter(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T036: Test model listing with language filter."""
        mock_models = [
            {
                "id": "zh-TW-HsiaoChenNeural",
                "name": "Hsiao Chen",
                "language": "zh-TW",
                "gender": "female",
            },
            {
                "id": "zh-TW-YunJheNeural",
                "name": "Yun Jhe",
                "language": "zh-TW",
                "gender": "male",
            },
        ]

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_validator = AsyncMock()
        mock_validator.get_available_models.return_value = mock_models

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
                    "src.infrastructure.providers.validators.ProviderValidatorRegistry.get_validator",
                    return_value=mock_validator,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/credentials/{mock_credential.id}/models",
                        params={"language": "zh-TW"},
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert "models" in data
                # All returned models should match the language filter
                for model in data["models"]:
                    assert model["language"].startswith("zh-TW")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_models_credential_not_found(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T036: Test model listing with non-existent credential."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = None

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
                    fake_id = uuid.uuid4()
                    response = await ac.get(
                        f"/api/v1/credentials/{fake_id}/models",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 404
                data = response.json()
                assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_models_unauthorized(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T036: Test model listing with different user's credential."""
        different_user_id = uuid.uuid4()

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

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
            with patch(
                "src.presentation.api.routes.credentials.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get(
                        f"/api/v1/credentials/{mock_credential.id}/models",
                        headers={"Authorization": "Bearer test-token"},
                    )

                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_models_no_auth(self, mock_credential: UserProviderCredential):
        """T036: Test model listing without authentication."""
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
                response = await ac.get(f"/api/v1/credentials/{mock_credential.id}/models")

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()
