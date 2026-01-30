"""Integration tests for Credential CRUD operations.

T025: Integration test for credential creation flow.
Tests the full credential lifecycle including validation, storage, and retrieval.
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


class TestCredentialCRUDIntegration:
    """Integration tests for full credential CRUD lifecycle."""

    @pytest.mark.asyncio
    async def test_full_credential_lifecycle(
        self,
        mock_user_id: uuid.UUID,
        mock_providers: list[Provider],
    ):
        """T025: Test complete credential lifecycle: create -> read -> update -> delete."""
        credential_storage: dict[uuid.UUID, UserProviderCredential] = {}

        # Mock repository that maintains state
        mock_credential_repo = AsyncMock()

        async def mock_save(cred):
            credential_storage[cred.id] = cred
            return cred

        async def mock_get_by_id(cred_id):
            return credential_storage.get(cred_id)

        async def mock_exists(user_id, provider):
            for cred in credential_storage.values():
                if cred.user_id == user_id and cred.provider == provider:
                    return True
            return False

        async def mock_list_by_user(user_id):
            return [c for c in credential_storage.values() if c.user_id == user_id]

        async def mock_delete(cred_id):
            if cred_id in credential_storage:
                del credential_storage[cred_id]
                return True
            return False

        async def mock_update(cred):
            credential_storage[cred.id] = cred
            return cred

        mock_credential_repo.save = mock_save
        mock_credential_repo.get_by_id = mock_get_by_id
        mock_credential_repo.exists = mock_exists
        mock_credential_repo.list_by_user = mock_list_by_user
        mock_credential_repo.delete = mock_delete
        mock_credential_repo.update = mock_update

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.side_effect = lambda pid: next(
            (p for p in mock_providers if p.id == pid), None
        )
        mock_provider_repo.list_all.return_value = mock_providers

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(
            is_valid=True,
            quota_info={"used": 0, "limit": 10000},
        )
        mock_validator.get_available_models.return_value = [
            {"id": "voice1", "name": "Voice 1", "language": "en"},
        ]

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
                patch(
                    "src.presentation.api.routes.credentials.ProviderValidatorRegistry.get_validator",
                    return_value=mock_validator,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    headers = {"X-User-Id": str(mock_user_id)}

                    # Step 1: Create credential
                    create_response = await ac.post(
                        "/api/v1/credentials",
                        json={"provider": "elevenlabs", "api_key": "sk-test-key-12345"},
                        headers=headers,
                    )
                    assert create_response.status_code == 201
                    created_data = create_response.json()
                    credential_id = created_data["id"]
                    assert created_data["provider"] == "elevenlabs"
                    assert created_data["is_valid"] is True

                    # Step 2: Read credential
                    get_response = await ac.get(
                        f"/api/v1/credentials/{credential_id}",
                        headers=headers,
                    )
                    assert get_response.status_code == 200
                    get_data = get_response.json()
                    assert get_data["id"] == credential_id
                    assert get_data["provider"] == "elevenlabs"

                    # Step 3: List credentials
                    list_response = await ac.get("/api/v1/credentials", headers=headers)
                    assert list_response.status_code == 200
                    list_data = list_response.json()
                    assert len(list_data["credentials"]) == 1

                    # Step 4: Update credential (model selection)
                    update_response = await ac.put(
                        f"/api/v1/credentials/{credential_id}",
                        json={"selected_model_id": "voice1"},
                        headers=headers,
                    )
                    assert update_response.status_code == 200
                    update_data = update_response.json()
                    assert update_data["selected_model_id"] == "voice1"

                    # Step 5: Validate credential
                    validate_response = await ac.post(
                        f"/api/v1/credentials/{credential_id}/validate",
                        headers=headers,
                    )
                    assert validate_response.status_code == 200
                    validate_data = validate_response.json()
                    assert validate_data["is_valid"] is True

                    # Step 6: Get available models
                    models_response = await ac.get(
                        f"/api/v1/credentials/{credential_id}/models",
                        headers=headers,
                    )
                    assert models_response.status_code == 200
                    models_data = models_response.json()
                    assert len(models_data["models"]) >= 1

                    # Step 7: Delete credential
                    delete_response = await ac.delete(
                        f"/api/v1/credentials/{credential_id}",
                        headers=headers,
                    )
                    assert delete_response.status_code == 204

                    # Step 8: Verify deleted
                    list_response = await ac.get("/api/v1/credentials", headers=headers)
                    assert list_response.status_code == 200
                    list_data = list_response.json()
                    assert len(list_data["credentials"]) == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_multi_provider_credentials(
        self,
        mock_user_id: uuid.UUID,
        mock_providers: list[Provider],
    ):
        """T025: Test managing credentials for multiple providers."""
        credential_storage: dict[uuid.UUID, UserProviderCredential] = {}

        mock_credential_repo = AsyncMock()

        async def mock_save(cred):
            credential_storage[cred.id] = cred
            return cred

        async def mock_exists(user_id, provider):
            for cred in credential_storage.values():
                if cred.user_id == user_id and cred.provider == provider:
                    return True
            return False

        async def mock_list_by_user(user_id):
            return [c for c in credential_storage.values() if c.user_id == user_id]

        mock_credential_repo.save = mock_save
        mock_credential_repo.exists = mock_exists
        mock_credential_repo.list_by_user = mock_list_by_user

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.side_effect = lambda pid: next(
            (p for p in mock_providers if p.id == pid), None
        )

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
                    headers = {"X-User-Id": str(mock_user_id)}

                    # Add credentials for each provider
                    for provider in ["elevenlabs", "azure", "gemini"]:
                        response = await ac.post(
                            "/api/v1/credentials",
                            json={
                                "provider": provider,
                                "api_key": f"key-{provider}-12345",
                            },
                            headers=headers,
                        )
                        assert response.status_code == 201
                        assert response.json()["provider"] == provider

                    # List all credentials
                    list_response = await ac.get("/api/v1/credentials", headers=headers)
                    assert list_response.status_code == 200
                    credentials = list_response.json()["credentials"]
                    assert len(credentials) == 3

                    # Verify each provider is present
                    providers = {c["provider"] for c in credentials}
                    assert providers == {"elevenlabs", "azure", "gemini"}
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_user_isolation(
        self,
        mock_providers: list[Provider],
    ):
        """T025: Test that users can only access their own credentials."""
        user_1 = uuid.uuid4()
        user_2 = uuid.uuid4()
        credential_storage: dict[uuid.UUID, UserProviderCredential] = {}

        # Use a mutable container to allow dynamic user switching
        current_user = {"id": user_1}

        mock_credential_repo = AsyncMock()

        async def mock_save(cred):
            credential_storage[cred.id] = cred
            return cred

        async def mock_get_by_id(cred_id):
            return credential_storage.get(cred_id)

        async def mock_exists(user_id, provider):
            for cred in credential_storage.values():
                if cred.user_id == user_id and cred.provider == provider:
                    return True
            return False

        async def mock_list_by_user(user_id):
            return [c for c in credential_storage.values() if c.user_id == user_id]

        mock_credential_repo.save = mock_save
        mock_credential_repo.get_by_id = mock_get_by_id
        mock_credential_repo.exists = mock_exists
        mock_credential_repo.list_by_user = mock_list_by_user

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.side_effect = lambda pid: next(
            (p for p in mock_providers if p.id == pid), None
        )

        mock_audit_repo = AsyncMock()

        mock_validator = AsyncMock()
        mock_validator.validate.return_value = ValidationResult(is_valid=True)

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        # Dynamic user override - constructs CurrentUser from current_user["id"] at call time
        async def override_get_current_user():
            return CurrentUser(
                id=str(current_user["id"]),
                email="test@example.com",
                name="Test User",
                picture_url=None,
                google_id="google-123",
            )

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
                    # User 1 creates a credential
                    current_user["id"] = user_1
                    response = await ac.post(
                        "/api/v1/credentials",
                        json={"provider": "elevenlabs", "api_key": "user1-key"},
                        headers={"X-User-Id": str(user_1)},
                    )
                    assert response.status_code == 201
                    user_1_cred_id = response.json()["id"]

                    # User 2 creates a credential (same provider, different user)
                    current_user["id"] = user_2
                    response = await ac.post(
                        "/api/v1/credentials",
                        json={"provider": "elevenlabs", "api_key": "user2-key"},
                        headers={"X-User-Id": str(user_2)},
                    )
                    assert response.status_code == 201

                    # User 1 can only see their credential
                    current_user["id"] = user_1
                    response = await ac.get(
                        "/api/v1/credentials",
                        headers={"X-User-Id": str(user_1)},
                    )
                    assert response.status_code == 200
                    assert len(response.json()["credentials"]) == 1

                    # User 2 cannot access User 1's credential
                    current_user["id"] = user_2
                    response = await ac.get(
                        f"/api/v1/credentials/{user_1_cred_id}",
                        headers={"X-User-Id": str(user_2)},
                    )
                    # Should be 403 Forbidden (not authorized)
                    assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


class TestCredentialAPIKeyRotation:
    """Integration tests for API key rotation scenarios."""

    @pytest.mark.asyncio
    async def test_key_rotation_with_revalidation(
        self,
        mock_user_id: uuid.UUID,
        mock_providers: list[Provider],
    ):
        """T025: Test updating API key triggers revalidation."""
        credential_storage: dict[uuid.UUID, UserProviderCredential] = {}

        mock_credential_repo = AsyncMock()

        async def mock_save(cred):
            credential_storage[cred.id] = cred
            return cred

        async def mock_get_by_id(cred_id):
            return credential_storage.get(cred_id)

        async def mock_exists(user_id, provider):
            return False

        async def mock_update(cred):
            credential_storage[cred.id] = cred
            return cred

        mock_credential_repo.save = mock_save
        mock_credential_repo.get_by_id = mock_get_by_id
        mock_credential_repo.exists = mock_exists
        mock_credential_repo.update = mock_update

        mock_provider_repo = AsyncMock()
        mock_provider_repo.get_by_id.return_value = mock_providers[0]

        mock_audit_repo = AsyncMock()

        # First validation succeeds, second validation also succeeds
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
                patch(
                    "src.presentation.api.routes.credentials.ProviderValidatorRegistry.get_validator",
                    return_value=mock_validator,
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    headers = {"X-User-Id": str(mock_user_id)}

                    # Create credential
                    create_response = await ac.post(
                        "/api/v1/credentials",
                        json={"provider": "elevenlabs", "api_key": "old-key-12345"},
                        headers=headers,
                    )
                    assert create_response.status_code == 201
                    credential_id = create_response.json()["id"]

                    # Update with new key
                    update_response = await ac.put(
                        f"/api/v1/credentials/{credential_id}",
                        json={"api_key": "new-key-67890"},
                        headers=headers,
                    )
                    assert update_response.status_code == 200
                    assert update_response.json()["is_valid"] is True

                    # Verify validation was called for new key
                    assert mock_validator.validate.call_count >= 2
        finally:
            app.dependency_overrides.clear()
