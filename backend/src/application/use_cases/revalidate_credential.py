"""Revalidate Provider Credential Use Case.

T067: Use case for revalidating an existing provider credential.
"""

import uuid
from dataclasses import dataclass

from src.application.services.audit_service import AuditService
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)
from src.infrastructure.providers.validators import ProviderValidatorRegistry


@dataclass
class RevalidateCredentialInput:
    """Input for revalidating a credential."""

    user_id: uuid.UUID
    credential_id: uuid.UUID
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class RevalidateCredentialOutput:
    """Output from revalidating a credential."""

    is_valid: bool
    error_message: str | None = None
    quota_info: dict | None = None


class RevalidateCredentialError(Exception):
    """Base error for revalidate credential use case."""

    pass


class CredentialNotFoundError(RevalidateCredentialError):
    """Raised when credential is not found."""

    pass


class UnauthorizedError(RevalidateCredentialError):
    """Raised when user doesn't have access to the credential."""

    pass


class ValidationError(RevalidateCredentialError):
    """Raised when validation fails due to external error."""

    pass


class RevalidateCredentialUseCase:
    """Use case for revalidating an existing provider credential.

    This use case:
    1. Retrieves the credential
    2. Verifies ownership
    3. Calls the provider validator to re-check the API key
    4. Updates the credential status
    5. Logs the validation to audit trail
    6. Returns validation result with quota info if available
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
        audit_service: AuditService,
    ):
        self._credential_repo = credential_repository
        self._audit_service = audit_service

    async def execute(self, input_data: RevalidateCredentialInput) -> RevalidateCredentialOutput:
        """Execute the revalidate credential use case.

        Args:
            input_data: Input data for revalidation

        Returns:
            RevalidateCredentialOutput with validation result

        Raises:
            CredentialNotFoundError: If credential doesn't exist
            UnauthorizedError: If user doesn't own the credential
            ValidationError: If validation fails due to external error
        """
        # 1. Get credential
        credential = await self._credential_repo.get_by_id(input_data.credential_id)

        if credential is None:
            raise CredentialNotFoundError(f"Credential '{input_data.credential_id}' not found")

        # 2. Verify ownership
        if credential.user_id != input_data.user_id:
            raise UnauthorizedError("Not authorized to access this credential")

        # 3. Get validator for the provider
        validator = ProviderValidatorRegistry.get_validator(credential.provider)

        try:
            # 4. Validate the API key
            result = await validator.validate(credential.api_key)

            # 5. Update credential status
            if result.is_valid:
                credential.mark_valid()
            else:
                credential.mark_invalid(result.error_message)

            await self._credential_repo.update(credential)

            # 6. Log to audit trail
            await self._audit_service.log_credential_validated(
                user_id=input_data.user_id,
                credential_id=credential.id,
                provider=credential.provider,
                is_valid=result.is_valid,
                ip_address=input_data.ip_address,
                user_agent=input_data.user_agent,
            )

            return RevalidateCredentialOutput(
                is_valid=result.is_valid,
                error_message=result.error_message,
                quota_info=result.quota_info,
            )

        except TimeoutError as e:
            raise ValidationError(f"Validation timed out: {e}") from e
        except Exception as e:
            raise ValidationError(f"Validation failed: {e}") from e
