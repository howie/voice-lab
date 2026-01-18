"""Integration tests for Multi-Provider Management.

T049: Integration test for multi-provider management
Tests the complete flow of managing credentials for multiple providers.
"""

import uuid
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
def mock_user_id() -> uuid.UUID:
    """Generate a mock user ID for testing."""
    return uuid.uuid4()


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
def mock_providers() -> list[Provider]:
    """Create mock providers for testing."""
    return [
        Provider(
            id="elevenlabs",
            name="elevenlabs",
            display_name="ElevenLabs",
            type=["tts"],
            is_active=True,
        ),
        Provider(
            id="azure",
            name="azure",
            display_name="Azure Cognitive Services",
            type=["tts", "stt"],
            is_active=True,
        ),
        Provider(
            id="gemini",
            name="gemini",
            display_name="Google Gemini",
            type=["tts", "stt"],
            is_active=True,
        ),
    ]


class TestMultiProviderManagement:
    """Integration tests for managing multiple providers."""

    @pytest.mark.asyncio
    async def test_add_credentials_for_multiple_providers(
        self,
        mock_user_id: uuid.UUID,
        mock_providers: list[Provider],
    ):
        """T049: Test adding credentials for multiple providers sequentially."""
        credentials_db: dict[str, UserProviderCredential] = {}

        def create_credential(user_id: uuid.UUID, provider: str, api_key: str):
            cred = UserProviderCredential.create(
                user_id=user_id,
                provider=provider,
                api_key=api_key,
            )
            cred.mark_valid()
            credentials_db[provider] = cred
            return cred

        mock_credential_repo = AsyncMock()
        mock_credential_repo.exists.return_value = False
        mock_credential_repo.save.side_effect = lambda c: setattr(c, "id", c.id) or c
        mock_credential_repo.list_by_user.side_effect = lambda _uid: list(credentials_db.values())

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.side_effect = lambda pid: next(
            (p for p in mock_providers if p.id == pid), None
        )

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(is_valid=True)

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        providers_to_add = [
            ("elevenlabs", "sk-eleven-test-key"),
            ("azure", "azure-speech-test-key"),
            ("gemini", "gemini-api-test-key"),
        ]

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
                    # Add credentials for each provider
                    for provider_id, api_key in providers_to_add:
                        # Simulate credential creation
                        create_credential(mock_user_id, provider_id, api_key)

                        response = await ac.post(
                            "/api/v1/credentials",
                            json={"provider": provider_id, "api_key": api_key},
                            headers={"X-User-Id": str(mock_user_id)},
                        )
                        assert response.status_code == 201, f"Failed to add {provider_id}"

                    # List all credentials
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert len(data["credentials"]) == 3

                    # Verify all providers are present
                    providers_in_response = {c["provider"] for c in data["credentials"]}
                    assert providers_in_response == {"elevenlabs", "azure", "gemini"}
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_view_all_configured_providers_with_status(
        self,
        mock_user_id: uuid.UUID,
        mock_providers: list[Provider],
        mock_current_user: CurrentUser,
    ):
        """T049: Test viewing all providers with their credential status."""
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

        mock_provider_repo = AsyncMock()
        mock_provider_repo.list_all.return_value = mock_providers

        mock_session = MagicMock()

        async def override_get_current_user_id():
            return mock_user_id

        async def override_get_db_session():
            return mock_session

        async def override_get_current_user():
            return mock_current_user

        app.dependency_overrides[credentials_module.get_current_user_id] = (
            override_get_current_user_id
        )
        app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session
        app.dependency_overrides[get_current_user] = override_get_current_user

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
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    # Get all providers
                    providers_response = await ac.get("/api/v1/credentials/providers")
                    assert providers_response.status_code == 200
                    providers_data = providers_response.json()

                    # Get user credentials
                    credentials_response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )
                    assert credentials_response.status_code == 200
                    credentials_data = credentials_response.json()

                    # Verify we can map credentials to providers
                    credential_map = {c["provider"]: c for c in credentials_data["credentials"]}

                    for provider in providers_data["providers"]:
                        if provider["name"] in credential_map:
                            cred = credential_map[provider["name"]]
                            if provider["name"] == "elevenlabs":
                                assert cred["is_valid"] is True
                            elif provider["name"] == "azure":
                                assert cred["is_valid"] is False
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_one_provider_without_affecting_others(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T049: Test that updating one provider doesn't affect others."""
        # Create credentials for multiple providers
        elevenlabs_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="elevenlabs",
            api_key="sk-old-key",
        )
        elevenlabs_cred.mark_valid()

        azure_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="azure",
            api_key="azure-key",
        )
        azure_cred.mark_valid()

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = elevenlabs_cred
        mock_credential_repo.update.return_value = elevenlabs_cred
        mock_credential_repo.list_by_user.return_value = [elevenlabs_cred, azure_cred]

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(is_valid=True)

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
                    # Update elevenlabs key
                    response = await ac.put(
                        f"/api/v1/credentials/{elevenlabs_cred.id}",
                        json={"api_key": "sk-new-key"},
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                    assert response.status_code == 200

                    # List all credentials
                    list_response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                    assert list_response.status_code == 200
                    data = list_response.json()

                    # Both credentials should still be present
                    assert len(data["credentials"]) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_one_provider_keeps_others(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T049: Test that deleting one provider credential keeps others."""
        # Create credentials for multiple providers
        elevenlabs_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="elevenlabs",
            api_key="sk-eleven-key",
        )
        elevenlabs_cred.mark_valid()

        azure_cred = UserProviderCredential.create(
            user_id=mock_user_id,
            provider="azure",
            api_key="azure-key",
        )
        azure_cred.mark_valid()

        remaining_credentials = [azure_cred]

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = elevenlabs_cred
        mock_credential_repo.delete.return_value = None
        mock_credential_repo.list_by_user.return_value = remaining_credentials

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
                    # Delete elevenlabs credential
                    response = await ac.delete(
                        f"/api/v1/credentials/{elevenlabs_cred.id}",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                    assert response.status_code == 204

                    # List remaining credentials
                    list_response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(mock_user_id)},
                    )

                    assert list_response.status_code == 200
                    data = list_response.json()

                    # Only azure credential should remain
                    assert len(data["credentials"]) == 1
                    assert data["credentials"][0]["provider"] == "azure"
        finally:
            app.dependency_overrides.clear()
