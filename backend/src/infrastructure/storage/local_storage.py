"""Local file storage implementation.

T032: Complete local storage implementation (storage/{provider}/{uuid}.mp3)
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles

from src.application.interfaces.storage_service import IStorageService, StoredFile
from src.domain.entities.audio import AudioData
from src.domain.errors import StorageError


class LocalStorage(IStorageService):
    """Local file system storage for audio files.

    Stores audio files in a structured directory format:
    {base_path}/{provider}/{date}/{uuid}.{extension}
    """

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize local storage.

        Args:
            base_path: Base directory for storage. Defaults to ./storage
        """
        self.base_path = base_path or os.getenv("LOCAL_STORAGE_PATH", "./storage")
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        """Ensure base storage directory exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def _get_provider_path(self, provider: str) -> Path:
        """Get storage path for a provider.

        Uses date-based subdirectories for better organization.
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        provider_path = Path(self.base_path) / provider / date_str
        provider_path.mkdir(parents=True, exist_ok=True)
        return provider_path

    def _generate_filename(self, audio: AudioData) -> str:
        """Generate unique filename for audio file."""
        unique_id = str(uuid.uuid4())
        extension = audio.format.file_extension
        return f"{unique_id}{extension}"

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
        try:
            # Use the key as relative path
            file_path = Path(self.base_path) / key
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)

            # Generate URL without checking existence (file was just created)
            if key.startswith("storage/"):
                url = f"/files/{key.replace('storage/', '')}"
            else:
                url = f"/files/{key}"

            return StoredFile(
                key=key,
                url=url,
                size_bytes=len(data),
                content_type=content_type,
            )

        except OSError as e:
            raise StorageError(f"Failed to upload file: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error uploading file: {str(e)}") from e

    async def save(self, audio: AudioData, provider: str) -> str:
        """Save audio data to local storage.

        Args:
            audio: AudioData object containing the audio bytes
            provider: Name of the TTS provider

        Returns:
            Relative path to the saved file

        Raises:
            StorageError: If saving fails
        """
        try:
            provider_path = self._get_provider_path(provider)
            filename = self._generate_filename(audio)
            file_path = provider_path / filename

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(audio.data)

            # Return relative path from base_path
            return str(file_path.relative_to(Path(self.base_path).parent))

        except OSError as e:
            raise StorageError(f"Failed to save audio: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error saving audio: {str(e)}") from e

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
        try:
            # Construct full path
            if key.startswith("storage/"):
                full_path = Path(self.base_path).parent / key
            else:
                full_path = Path(self.base_path) / key

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {key}")

            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()

        except FileNotFoundError:
            raise
        except OSError as e:
            raise StorageError(f"Failed to download file: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error downloading file: {str(e)}") from e

    async def get(self, path: str) -> bytes:
        """Retrieve audio data from storage.

        Args:
            path: Relative path to the audio file

        Returns:
            Audio data as bytes

        Raises:
            StorageError: If retrieval fails
        """
        try:
            # Construct full path
            if path.startswith("storage/"):
                full_path = Path(self.base_path).parent / path
            else:
                full_path = Path(self.base_path) / path

            if not full_path.exists():
                raise StorageError(f"File not found: {path}")

            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()

        except StorageError:
            raise
        except OSError as e:
            raise StorageError(f"Failed to read audio: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error reading audio: {str(e)}") from e

    async def delete(self, path: str) -> bool:
        """Delete audio file from storage.

        Args:
            path: Relative path to the audio file

        Returns:
            True if deleted, False if file didn't exist

        Raises:
            StorageError: If deletion fails
        """
        try:
            # Construct full path
            if path.startswith("storage/"):
                full_path = Path(self.base_path).parent / path
            else:
                full_path = Path(self.base_path) / path

            if not full_path.exists():
                return False

            os.remove(full_path)
            return True

        except OSError as e:
            raise StorageError(f"Failed to delete audio: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error deleting audio: {str(e)}") from e

    async def exists(self, path: str) -> bool:
        """Check if audio file exists in storage.

        Args:
            path: Relative path to the audio file

        Returns:
            True if file exists, False otherwise
        """
        try:
            if path.startswith("storage/"):
                full_path = Path(self.base_path).parent / path
            else:
                full_path = Path(self.base_path) / path

            return full_path.exists()

        except Exception:
            return False

    async def get_url(self, key: str, _expires_in: int = 3600) -> str:
        """Get a URL to access the file.

        Args:
            key: Storage key/path of the file
            _expires_in: URL expiration time in seconds (ignored for local storage)

        Returns:
            URL to access the file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Construct full path to check existence
        if key.startswith("storage/"):
            full_path = Path(self.base_path).parent / key
        else:
            full_path = Path(self.base_path) / key

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        # For local storage, return the file path relative to static mount
        # expires_in is ignored as local files don't have expiring URLs
        if key.startswith("storage/"):
            return f"/files/{key.replace('storage/', '')}"
        return f"/files/{key}"

    async def list_files(
        self,
        provider: str | None = None,
        date: str | None = None,
    ) -> list[str]:
        """List stored audio files.

        Args:
            provider: Optional filter by provider
            date: Optional filter by date (YYYY-MM-DD format)

        Returns:
            List of file paths
        """
        try:
            base = Path(self.base_path)
            files = []

            if provider:
                search_path = base / provider
                if date:
                    search_path = search_path / date
            else:
                search_path = base

            if not search_path.exists():
                return []

            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(base)))

            return sorted(files)

        except Exception:
            return []

    async def get_storage_stats(self) -> dict:
        """Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        try:
            base = Path(self.base_path)
            total_files = 0
            total_size = 0
            providers: dict[str, dict] = {}

            if not base.exists():
                return {
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "providers": {},
                }

            for provider_dir in base.iterdir():
                if provider_dir.is_dir():
                    provider_name = provider_dir.name
                    provider_files = 0
                    provider_size = 0

                    for file_path in provider_dir.rglob("*"):
                        if file_path.is_file():
                            provider_files += 1
                            provider_size += file_path.stat().st_size

                    providers[provider_name] = {
                        "files": provider_files,
                        "size_bytes": provider_size,
                    }
                    total_files += provider_files
                    total_size += provider_size

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "providers": providers,
            }

        except Exception:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "providers": {},
            }
