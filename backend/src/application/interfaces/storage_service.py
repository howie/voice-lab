"""Storage Service Interface (Port)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredFile:
    """Information about a stored file."""

    key: str
    url: str
    size_bytes: int
    content_type: str


class IStorageService(ABC):
    """Abstract interface for file storage.

    This interface defines the contract for file storage services.
    Implementations can be local filesystem, S3, GCS, etc.
    """

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> StoredFile:
        """Upload a file to storage.

        Args:
            key: Storage key/path for the file
            data: File content as bytes
            content_type: MIME type of the file

        Returns:
            Information about the stored file

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download a file from storage.

        Args:
            key: Storage key/path of the file

        Returns:
            File content as bytes

        Raises:
            StorageError: If download fails
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file from storage.

        Args:
            key: Storage key/path of the file

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a URL to access the file.

        Args:
            key: Storage key/path of the file
            expires_in: URL expiration time in seconds (for signed URLs)

        Returns:
            URL to access the file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists.

        Args:
            key: Storage key/path of the file

        Returns:
            True if file exists, False otherwise
        """
        pass
