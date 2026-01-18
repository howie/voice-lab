"""List Provider Models Use Case.

T038: Use case for listing available models/voices for a provider.
"""

import uuid
from dataclasses import dataclass

from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
)
from src.infrastructure.providers.validators import ProviderValidatorRegistry


@dataclass
class ListModelsInput:
    """Input for listing provider models."""

    user_id: uuid.UUID
    credential_id: uuid.UUID
    language: str | None = None


@dataclass
class ProviderModelInfo:
    """Information about a provider model/voice."""

    id: str
    name: str
    language: str
    gender: str | None = None
    description: str | None = None


@dataclass
class ListModelsOutput:
    """Output from listing provider models."""

    models: list[ProviderModelInfo]


class ListProviderModelsError(Exception):
    """Base error for list models use case."""

    pass


class CredentialNotFoundError(ListProviderModelsError):
    """Raised when credential is not found."""

    pass


class UnauthorizedError(ListProviderModelsError):
    """Raised when user doesn't have access to the credential."""

    pass


class ListProviderModelsUseCase:
    """Use case for listing available models/voices for a provider.

    This use case:
    1. Retrieves the credential
    2. Verifies ownership
    3. Fetches available models from the provider
    4. Optionally filters by language
    """

    def __init__(
        self,
        credential_repository: IProviderCredentialRepository,
    ):
        self._credential_repo = credential_repository

    async def execute(self, input_data: ListModelsInput) -> ListModelsOutput:
        """Execute the list models use case.

        Args:
            input_data: Input data for listing models

        Returns:
            ListModelsOutput with available models

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

        # 3. Get models from provider
        validator = ProviderValidatorRegistry.get_validator(credential.provider)
        models_data = await validator.get_available_models(credential.api_key)

        # 4. Filter by language if specified
        if input_data.language:
            models_data = [
                m for m in models_data if m.get("language", "").startswith(input_data.language)
            ]

        # 5. Convert to output format
        models = [
            ProviderModelInfo(
                id=m.get("id", ""),
                name=m.get("name", ""),
                language=m.get("language", ""),
                gender=m.get("gender"),
                description=m.get("description"),
            )
            for m in models_data
        ]

        return ListModelsOutput(models=models)
