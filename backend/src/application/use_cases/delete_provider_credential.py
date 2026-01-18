"""Delete Provider Credential Use Case.

T058: Use case for deleting a provider credential.
"""

import uuid
from dataclasses import dataclass

from src.application.services.audit_service import AuditService
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)


@dataclass
class DeleteCredentialInput:
    """Input for deleting a credential."""

    user_id: uuid.UUID
    credential_id: uuid.UUID
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class DeleteCredentialOutput:
    """Output from deleting a credential."""

    success: bool
    provider: str


class DeleteProviderCredentialError(Exception):
    """Base error for delete credential use case."""

    pass


class CredentialNotFoundError(DeleteProviderCredentialError):
    """Raised when credential is not found."""

    pass


class UnauthorizedError(DeleteProviderCredentialError):
    """Raised when user doesn't have access to the credential."""

    pass


class DeleteProviderCredentialUseCase:
    """Use case for deleting a provider credential.

    This use case:
    1. Retrieves the credential
    2. Verifies ownership
    3. Logs the deletion to audit trail
    4. Deletes the credential
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
        audit_service: AuditService,
    ):
        self._credential_repo = credential_repository
        self._audit_service = audit_service

    async def execute(self, input_data: DeleteCredentialInput) -> DeleteCredentialOutput:
        """Execute the delete credential use case.

        Args:
            input_data: Input data for deleting credential

        Returns:
            DeleteCredentialOutput indicating success

        Raises:
            CredentialNotFoundError: If credential doesn't exist
            UnauthorizedError: If user doesn't own the credential
        """
        # 1. Get credential
        credential = await self._credential_repo.get_by_id(input_data.credential_id)

        if credential is None:
            raise CredentialNotFoundError(f"Credential '{input_data.credential_id}' not found")

        # 2. Verify ownership
        if credential.user_id != input_data.user_id:
            raise UnauthorizedError("Not authorized to access this credential")

        provider = credential.provider

        # 3. Log deletion to audit trail (before deleting)
        await self._audit_service.log_credential_deleted(
            user_id=input_data.user_id,
            credential_id=credential.id,
            provider=provider,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )

        # 4. Delete the credential
        await self._credential_repo.delete(input_data.credential_id)

        return DeleteCredentialOutput(
            success=True,
            provider=provider,
        )
