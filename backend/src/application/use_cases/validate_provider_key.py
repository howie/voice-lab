"""Validate Provider Key Use Case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.application.services.audit_service import AuditService
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)
from src.infrastructure.providers.validators import (
    ProviderValidatorRegistry,
)
from src.infrastructure.providers.validators import (
    ValidationResult as ProviderValidationResult,
)


@dataclass
class ValidateKeyInput:
    """Input for validating a provider key."""

    user_id: uuid.UUID
    credential_id: uuid.UUID
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class ValidateKeyOutput:
    """Output from validating a key."""

    is_valid: bool
    validated_at: datetime
    error_message: str | None = None
    quota_info: dict | None = None


class CredentialNotFoundError(Exception):
    """Raised when credential is not found."""

    pass


class UnauthorizedError(Exception):
    """Raised when user doesn't own the credential."""

    pass


class ValidateProviderKeyUseCase:
    """Use case for re-validating an existing provider credential.

    This use case:
    1. Retrieves the credential
    2. Validates ownership
    3. Re-validates the API key against the provider
    4. Updates the credential status
    5. Logs the operation to audit trail
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
        audit_service: AuditService,
    ):
        self._credential_repo = credential_repository
        self._audit_service = audit_service

    async def execute(self, input_data: ValidateKeyInput) -> ValidateKeyOutput:
        """Execute the validate key use case.

        Args:
            input_data: Input data for validation

        Returns:
            ValidateKeyOutput with validation result

        Raises:
            CredentialNotFoundError: If credential doesn't exist
            UnauthorizedError: If user doesn't own the credential
        """
        # 1. Get credential
        credential = await self._credential_repo.get_by_id(input_data.credential_id)
        if credential is None:
            raise CredentialNotFoundError(
                f"Credential '{input_data.credential_id}' not found"
            )

        # 2. Validate ownership
        if credential.user_id != input_data.user_id:
            raise UnauthorizedError("Not authorized to access this credential")

        # 3. Validate API key
        validator = ProviderValidatorRegistry.get_validator(credential.provider)
        validation_result = await validator.validate(credential.api_key)

        # 4. Update credential status
        validated_at = datetime.utcnow()
        if validation_result.is_valid:
            credential.mark_valid()
        else:
            credential.mark_invalid()

        await self._credential_repo.update(credential)

        # 5. Log to audit trail
        await self._audit_service.log_credential_validated(
            user_id=input_data.user_id,
            credential_id=credential.id,
            provider=credential.provider,
            is_valid=validation_result.is_valid,
            error_message=validation_result.error_message,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )

        return ValidateKeyOutput(
            is_valid=validation_result.is_valid,
            validated_at=validated_at,
            error_message=validation_result.error_message,
            quota_info=validation_result.quota_info,
        )


class ValidateApiKeyDirectUseCase:
    """Use case for validating an API key directly (without storing).

    Used during the add credential flow to validate before saving.
    """

    async def execute(
        self, provider: str, api_key: str
    ) -> ProviderValidationResult:
        """Validate an API key directly.

        Args:
            provider: Provider identifier
            api_key: API key to validate

        Returns:
            ValidationResult from the provider validator
        """
        if not ProviderValidatorRegistry.is_supported(provider):
            return ProviderValidationResult(
                is_valid=False,
                error_message=f"Unsupported provider: {provider}",
            )

        validator = ProviderValidatorRegistry.get_validator(provider)
        return await validator.validate(api_key)
