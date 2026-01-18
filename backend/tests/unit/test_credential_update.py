"""Unit tests for Credential Update with Revalidation.

T057: Unit test for key update with revalidation
Tests the credential update use case with API key rotation.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services.audit_service import AuditService
from src.application.use_cases.update_provider_credential import (
    CredentialNotFoundError,
    UnauthorizedError,
    UpdateCredentialInput,
    UpdateProviderCredentialUseCase,
    ValidationFailedError,
)
from src.domain.entities.provider_credential import UserProviderCredential
from src.infrastructure.providers.validators.base import ValidationResult


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
        api_key="sk-old-key-1234567890",
    )
    cred.mark_valid()
    return cred


class TestUpdateCredentialWithRevalidation:
    """Unit tests for updating credentials with API key rotation."""

    @pytest.mark.asyncio
    async def test_update_api_key_triggers_validation(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T057: Test that updating API key triggers revalidation."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()
        audit_service = AuditService(mock_audit_repo)

        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=ValidationResult(
                is_valid=True,
                validated_at=datetime.now(UTC),
            )
        )

        use_case = UpdateProviderCredentialUseCase(
            credential_repository=mock_credential_repo,
            audit_service=audit_service,
        )

        # Patch the validator registry
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.application.use_cases.update_provider_credential.ProviderValidatorRegistry.get_validator",
                lambda _: mock_validator,
            )

            result = await use_case.execute(
                UpdateCredentialInput(
                    user_id=mock_user_id,
                    credential_id=mock_credential.id,
                    api_key="sk-new-key-0987654321",
                )
            )

        # Verify validation was called
        mock_validator.validate.assert_called_once_with("sk-new-key-0987654321")
        assert result.key_updated is True

    @pytest.mark.asyncio
    async def test_update_invalid_key_fails(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T057: Test that updating with invalid key raises error."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_audit_repo = AsyncMock()
        audit_service = AuditService(mock_audit_repo)

        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(
            return_value=ValidationResult(
                is_valid=False,
                error_message="Invalid API key format",
            )
        )

        use_case = UpdateProviderCredentialUseCase(
            credential_repository=mock_credential_repo,
            audit_service=audit_service,
        )

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.application.use_cases.update_provider_credential.ProviderValidatorRegistry.get_validator",
                lambda _: mock_validator,
            )

            with pytest.raises(ValidationFailedError) as exc_info:
                await use_case.execute(
                    UpdateCredentialInput(
                        user_id=mock_user_id,
                        credential_id=mock_credential.id,
                        api_key="invalid-key",
                    )
                )

            assert "Invalid API key format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_model_without_key_no_validation(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T057: Test that updating only model doesn't trigger validation."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()
        audit_service = AuditService(mock_audit_repo)

        use_case = UpdateProviderCredentialUseCase(
            credential_repository=mock_credential_repo,
            audit_service=audit_service,
        )

        result = await use_case.execute(
            UpdateCredentialInput(
                user_id=mock_user_id,
                credential_id=mock_credential.id,
                selected_model_id="new-model-id",
            )
        )

        assert result.key_updated is False
        assert result.model_updated is True

    @pytest.mark.asyncio
    async def test_update_credential_not_found(
        self,
        mock_user_id: uuid.UUID,
    ):
        """T057: Test updating non-existent credential."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = None

        mock_audit_repo = AsyncMock()
        audit_service = AuditService(mock_audit_repo)

        use_case = UpdateProviderCredentialUseCase(
            credential_repository=mock_credential_repo,
            audit_service=audit_service,
        )

        with pytest.raises(CredentialNotFoundError):
            await use_case.execute(
                UpdateCredentialInput(
                    user_id=mock_user_id,
                    credential_id=uuid.uuid4(),
                    api_key="new-key",
                )
            )

    @pytest.mark.asyncio
    async def test_update_credential_unauthorized(
        self,
        mock_credential: UserProviderCredential,
    ):
        """T057: Test updating another user's credential."""
        different_user_id = uuid.uuid4()

        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential

        mock_audit_repo = AsyncMock()
        audit_service = AuditService(mock_audit_repo)

        use_case = UpdateProviderCredentialUseCase(
            credential_repository=mock_credential_repo,
            audit_service=audit_service,
        )

        with pytest.raises(UnauthorizedError):
            await use_case.execute(
                UpdateCredentialInput(
                    user_id=different_user_id,
                    credential_id=mock_credential.id,
                    api_key="new-key",
                )
            )

    @pytest.mark.asyncio
    async def test_update_creates_audit_log(
        self,
        mock_user_id: uuid.UUID,
        mock_credential: UserProviderCredential,
    ):
        """T057: Test that update creates audit log entries."""
        mock_credential_repo = AsyncMock()
        mock_credential_repo.get_by_id.return_value = mock_credential
        mock_credential_repo.update.return_value = mock_credential

        mock_audit_repo = AsyncMock()
        audit_service = AuditService(mock_audit_repo)

        mock_validator = MagicMock()
        mock_validator.validate = AsyncMock(return_value=ValidationResult(is_valid=True))

        use_case = UpdateProviderCredentialUseCase(
            credential_repository=mock_credential_repo,
            audit_service=audit_service,
        )

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.application.use_cases.update_provider_credential.ProviderValidatorRegistry.get_validator",
                lambda _: mock_validator,
            )

            await use_case.execute(
                UpdateCredentialInput(
                    user_id=mock_user_id,
                    credential_id=mock_credential.id,
                    api_key="sk-new-key",
                    selected_model_id="new-model",
                )
            )

        # Verify audit logs were created (at least for update event)
        assert mock_audit_repo.save.call_count >= 1
