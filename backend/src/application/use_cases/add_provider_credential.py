"""Add Provider Credential Use Case."""

import uuid
from dataclasses import dataclass

from src.application.services.audit_service import AuditService
from src.domain.entities.provider_credential import UserProviderCredential
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
    IProviderRepository,
)
from src.infrastructure.providers.validators import ProviderValidatorRegistry


@dataclass
class AddCredentialInput:
    """Input for adding a new credential."""

    user_id: uuid.UUID
    provider: str
    api_key: str
    selected_model_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class AddCredentialOutput:
    """Output from adding a credential."""

    credential: UserProviderCredential
    validation_error: str | None = None


class AddProviderCredentialError(Exception):
    """Base error for add credential use case."""

    pass


class ProviderNotFoundError(AddProviderCredentialError):
    """Raised when provider is not found."""

    pass


class CredentialAlreadyExistsError(AddProviderCredentialError):
    """Raised when credential already exists for user/provider."""

    pass


class ValidationFailedError(AddProviderCredentialError):
    """Raised when API key validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AddProviderCredentialUseCase:
    """Use case for adding a new provider credential.

    This use case:
    1. Validates the provider exists
    2. Checks no duplicate credential exists
    3. Validates the API key against the provider
    4. Stores the credential
    5. Logs the operation to audit trail
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
        provider_repository: IProviderRepository,
        audit_service: AuditService,
    ):
        self._credential_repo = credential_repository
        self._provider_repo = provider_repository
        self._audit_service = audit_service

    async def execute(self, input_data: AddCredentialInput) -> AddCredentialOutput:
        """Execute the add credential use case.

        Args:
            input_data: Input data for adding credential

        Returns:
            AddCredentialOutput with the created credential

        Raises:
            ProviderNotFoundError: If provider doesn't exist
            CredentialAlreadyExistsError: If credential already exists
            ValidationFailedError: If API key validation fails
        """
        # 1. Validate provider exists
        provider = await self._provider_repo.get_by_id(input_data.provider)
        if provider is None:
            raise ProviderNotFoundError(f"Provider '{input_data.provider}' not found")

        # 2. Check for existing credential
        if await self._credential_repo.exists(input_data.user_id, input_data.provider):
            raise CredentialAlreadyExistsError(
                f"Credential already exists for provider '{input_data.provider}'"
            )

        # 3. Validate API key
        validator = ProviderValidatorRegistry.get_validator(input_data.provider)
        validation_result = await validator.validate(input_data.api_key)

        if not validation_result.is_valid:
            raise ValidationFailedError(
                validation_result.error_message or "API key validation failed"
            )

        # 4. Create and save credential
        credential = UserProviderCredential.create(
            user_id=input_data.user_id,
            provider=input_data.provider,
            api_key=input_data.api_key,
            selected_model_id=input_data.selected_model_id,
        )
        credential.mark_valid()

        await self._credential_repo.save(credential)

        # 5. Log to audit trail
        await self._audit_service.log_credential_created(
            user_id=input_data.user_id,
            credential_id=credential.id,
            provider=input_data.provider,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )

        return AddCredentialOutput(credential=credential)
