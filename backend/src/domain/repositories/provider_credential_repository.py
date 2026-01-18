"""Provider Credential Repository Interface."""

import uuid
from abc import ABC, abstractmethod

from src.domain.entities.provider import Provider
from src.domain.entities.provider_credential import UserProviderCredential


class IProviderCredentialRepository(ABC):
    """Abstract repository interface for provider credentials.

    This interface defines the contract for credential storage operations.
    """

    @abstractmethod
    async def save(self, credential: UserProviderCredential) -> UserProviderCredential:
        """Save a provider credential.

        Args:
            credential: Credential to save

        Returns:
            Saved credential
        """
        pass

    @abstractmethod
    async def get_by_id(self, credential_id: uuid.UUID) -> UserProviderCredential | None:
        """Get a credential by ID.

        Args:
            credential_id: Credential ID

        Returns:
            Credential if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_and_provider(
        self, user_id: uuid.UUID, provider: str
    ) -> UserProviderCredential | None:
        """Get a credential by user ID and provider.

        Args:
            user_id: User ID
            provider: Provider identifier

        Returns:
            Credential if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_user(self, user_id: uuid.UUID) -> list[UserProviderCredential]:
        """List all credentials for a user.

        Args:
            user_id: User ID

        Returns:
            List of credentials for the user
        """
        pass

    @abstractmethod
    async def update(self, credential: UserProviderCredential) -> UserProviderCredential:
        """Update an existing credential.

        Args:
            credential: Credential to update

        Returns:
            Updated credential
        """
        pass

    @abstractmethod
    async def delete(self, credential_id: uuid.UUID) -> bool:
        """Delete a credential.

        Args:
            credential_id: Credential ID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, user_id: uuid.UUID, provider: str) -> bool:
        """Check if a credential exists for user and provider.

        Args:
            user_id: User ID
            provider: Provider identifier

        Returns:
            True if credential exists
        """
        pass


class IProviderRepository(ABC):
    """Abstract repository interface for providers.

    This interface defines the contract for provider reference data operations.
    """

    @abstractmethod
    async def get_by_id(self, provider_id: str) -> Provider | None:
        """Get a provider by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            Provider if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(self, active_only: bool = True) -> list[Provider]:
        """List all providers.

        Args:
            active_only: If True, only return active providers

        Returns:
            List of providers
        """
        pass

    @abstractmethod
    async def list_by_type(self, provider_type: str) -> list[Provider]:
        """List providers by type.

        Args:
            provider_type: 'tts' or 'stt'

        Returns:
            List of providers supporting the type
        """
        pass
