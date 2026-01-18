"""List Provider Credentials Use Case.

T050: Use case for listing all provider credentials for a user.
"""

import uuid
from dataclasses import dataclass

from src.domain.entities.provider_credential import UserProviderCredential
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)


@dataclass
class ListCredentialsInput:
    """Input for listing provider credentials."""

    user_id: uuid.UUID


@dataclass
class ListCredentialsOutput:
    """Output from listing provider credentials."""

    credentials: list[UserProviderCredential]


class ListProviderCredentialsUseCase:
    """Use case for listing all provider credentials for a user.

    This use case:
    1. Retrieves all credentials owned by the user
    2. Returns them with masked API keys
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
    ):
        self._credential_repo = credential_repository

    async def execute(self, input_data: ListCredentialsInput) -> ListCredentialsOutput:
        """Execute the list credentials use case.

        Args:
            input_data: Input data for listing credentials

        Returns:
            ListCredentialsOutput with user's credentials
        """
        credentials = await self._credential_repo.list_by_user(input_data.user_id)

        return ListCredentialsOutput(credentials=credentials)
