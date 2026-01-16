"""Local File Storage Service Implementation."""

import os
from pathlib import Path

from src.application.interfaces.storage_service import IStorageService, StoredFile


class LocalStorageService(IStorageService):
    """Local filesystem storage implementation.

    Useful for development and testing.
    """

    def __init__(self, base_path: str, base_url: str = "http://localhost:8000/files"):
        """Initialize local storage service.

        Args:
            base_path: Base directory for file storage
            base_url: Base URL for serving files
        """
        self._base_path = Path(base_path)
        self._base_url = base_url.rstrip("/")

        # Ensure base directory exists
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredFile:
        """Upload data to local storage."""
        file_path = self._base_path / key

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_bytes(data)

        url = f"{self._base_url}/{key}"

        return StoredFile(
            key=key,
            url=url,
            size_bytes=len(data),
            content_type=content_type or "application/octet-stream",
        )

    async def download(self, key: str) -> bytes | None:
        """Download data from local storage."""
        file_path = self._base_path / key

        if not file_path.exists():
            return None

        return file_path.read_bytes()

    async def delete(self, key: str) -> bool:
        """Delete data from local storage."""
        file_path = self._base_path / key

        if not file_path.exists():
            return False

        file_path.unlink()
        return True

    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Get URL for accessing the file."""
        file_path = self._base_path / key

        if not file_path.exists():
            return None

        # Local storage doesn't support expiring URLs
        return f"{self._base_url}/{key}"

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        file_path = self._base_path / key
        return file_path.exists()
