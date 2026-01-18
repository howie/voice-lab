"""Update Provider Credential Use Case.

T039: Use case for updating provider credentials (API key and/or model selection).
"""

import uuid
from dataclasses import dataclass

from src.application.services.audit_service import AuditService
from src.domain.entities.provider_credential import UserProviderCredential
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)
from src.infrastructure.providers.validators import ProviderValidatorRegistry


@dataclass
class UpdateCredentialInput:
    """Input for updating a credential."""

    user_id: uuid.UUID
    credential_id: uuid.UUID
    api_key: str | None = None
    selected_model_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class UpdateCredentialOutput:
    """Output from updating a credential."""

    credential: UserProviderCredential
    key_updated: bool = False
    model_updated: bool = False


class UpdateProviderCredentialError(Exception):
    """Base error for update credential use case."""

    pass


class CredentialNotFoundError(UpdateProviderCredentialError):
    """Raised when credential is not found."""

    pass


class UnauthorizedError(UpdateProviderCredentialError):
    """Raised when user doesn't have access to the credential."""

    pass


class ValidationFailedError(UpdateProviderCredentialError):
    """Raised when API key validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UpdateProviderCredentialUseCase:
    """Use case for updating a provider credential.

    This use case supports:
    1. Updating the API key (with validation)
    2. Updating the selected model
    3. Both operations in a single call
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
        audit_service: AuditService,
    ):
        self._credential_repo = credential_repository
        self._audit_service = audit_service

    async def execute(self, input_data: UpdateCredentialInput) -> UpdateCredentialOutput:
        """Execute the update credential use case.

        Args:
            input_data: Input data for updating credential

        Returns:
            UpdateCredentialOutput with the updated credential

        Raises:
            CredentialNotFoundError: If credential doesn't exist
            UnauthorizedError: If user doesn't own the credential
            ValidationFailedError: If new API key validation fails
        """
        # 1. Get credential
        credential = await self._credential_repo.get_by_id(input_data.credential_id)

        if credential is None:
            raise CredentialNotFoundError(f"Credential '{input_data.credential_id}' not found")

        # 2. Verify ownership
        if credential.user_id != input_data.user_id:
            raise UnauthorizedError("Not authorized to access this credential")

        key_updated = False
        model_updated = False

        # 3. Update API key if provided
        if input_data.api_key:
            # Validate new key
            validator = ProviderValidatorRegistry.get_validator(credential.provider)
            validation_result = await validator.validate(input_data.api_key)

            if not validation_result.is_valid:
                raise ValidationFailedError(
                    validation_result.error_message or "API key validation failed"
                )

            credential.update_api_key(input_data.api_key)
            credential.mark_valid()
            key_updated = True

        # 4. Update model selection if provided
        if input_data.selected_model_id is not None:
            credential.select_model(input_data.selected_model_id)
            model_updated = True

            # Log model selection
            await self._audit_service.log_model_selected(
                user_id=input_data.user_id,
                credential_id=credential.id,
                provider=credential.provider,
                model_id=input_data.selected_model_id,
                ip_address=input_data.ip_address,
                user_agent=input_data.user_agent,
            )

        # 5. Save changes
        await self._credential_repo.update(credential)

        # 6. Log update
        await self._audit_service.log_credential_updated(
            user_id=input_data.user_id,
            credential_id=credential.id,
            provider=credential.provider,
            details={
                "key_updated": key_updated,
                "model_updated": model_updated,
            },
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )

        return UpdateCredentialOutput(
            credential=credential,
            key_updated=key_updated,
            model_updated=model_updated,
        )
