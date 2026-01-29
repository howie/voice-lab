"""DJ Audio storage service for Magic DJ Controller.

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

Manages audio file storage for DJ tracks.
Supports local filesystem with option for GCS in production.
"""

import shutil
from datetime import timedelta
from pathlib import Path
from uuid import UUID

import aiofiles
import aiofiles.os

# GCS support - optional
try:
    from google.cloud import storage

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class DJAudioStorageService:
    """Service for managing DJ track audio files.

    Storage structure (local):
    storage/dj-audio/{user_id}/{track_id}.mp3

    Storage structure (GCS):
    gs://voice-lab-audio/dj-audio/{user_id}/{track_id}.mp3
    """

    # Class constants
    PATH_PREFIX = "dj-audio"
    DEFAULT_CONTENT_TYPE = "audio/mpeg"
    DEFAULT_SIGNED_URL_EXPIRATION = 3600  # 1 hour

    def __init__(
        self,
        base_path: str = "storage",
        gcs_bucket_name: str | None = None,
    ) -> None:
        """Initialize DJ audio storage.

        Args:
            base_path: Base path for local storage
            gcs_bucket_name: GCS bucket name (if using GCS)
        """
        self._base_path = Path(base_path) / self.PATH_PREFIX
        self._base_path.mkdir(parents=True, exist_ok=True)

        self._gcs_bucket_name = gcs_bucket_name
        self._gcs_client = None
        self._gcs_bucket = None

        if gcs_bucket_name and GCS_AVAILABLE:
            self._init_gcs()

    def _init_gcs(self) -> None:
        """Initialize GCS client and bucket."""
        try:
            self._gcs_client = storage.Client()
            self._gcs_bucket = self._gcs_client.bucket(self._gcs_bucket_name)
        except Exception:
            # Fall back to local storage if GCS init fails
            self._gcs_client = None
            self._gcs_bucket = None

    @property
    def is_using_gcs(self) -> bool:
        """Check if using GCS storage."""
        return self._gcs_bucket is not None

    def _user_dir(self, user_id: UUID) -> Path:
        """Get directory path for a user."""
        return self._base_path / str(user_id)

    def _track_path(self, user_id: UUID, track_id: UUID, extension: str = "mp3") -> Path:
        """Get local path for track audio file."""
        return self._user_dir(user_id) / f"{track_id}.{extension}"

    def _gcs_path(self, user_id: UUID, track_id: UUID, extension: str = "mp3") -> str:
        """Get GCS path for track audio file."""
        return f"{self.PATH_PREFIX}/{user_id}/{track_id}.{extension}"

    def get_storage_path(self, user_id: UUID, track_id: UUID, extension: str = "mp3") -> str:
        """Get storage path (GCS gs:// URL or local path)."""
        if self.is_using_gcs:
            return f"gs://{self._gcs_bucket_name}/{self._gcs_path(user_id, track_id, extension)}"
        return str(self._track_path(user_id, track_id, extension))

    async def ensure_user_dir(self, user_id: UUID) -> Path:
        """Create user directory if it doesn't exist (local only)."""
        dir_path = self._user_dir(user_id)
        await aiofiles.os.makedirs(dir_path, exist_ok=True)
        return dir_path

    # =========================================================================
    # Upload Methods
    # =========================================================================

    async def upload(
        self,
        user_id: UUID,
        track_id: UUID,
        audio_data: bytes,
        content_type: str = DEFAULT_CONTENT_TYPE,
        extension: str = "mp3",
    ) -> str:
        """Upload audio data and return storage path.

        Args:
            user_id: User ID
            track_id: Track ID
            audio_data: Audio bytes
            content_type: MIME type
            extension: File extension

        Returns:
            Storage path (gs:// URL or local path)
        """
        if self.is_using_gcs:
            return await self._upload_to_gcs(user_id, track_id, audio_data, content_type, extension)
        return await self._upload_to_local(user_id, track_id, audio_data, extension)

    async def _upload_to_local(
        self,
        user_id: UUID,
        track_id: UUID,
        audio_data: bytes,
        extension: str = "mp3",
    ) -> str:
        """Upload to local filesystem."""
        await self.ensure_user_dir(user_id)
        path = self._track_path(user_id, track_id, extension)

        async with aiofiles.open(path, "wb") as f:
            await f.write(audio_data)

        return str(path)

    async def _upload_to_gcs(
        self,
        user_id: UUID,
        track_id: UUID,
        audio_data: bytes,
        content_type: str,
        extension: str = "mp3",
    ) -> str:
        """Upload to Google Cloud Storage."""
        gcs_path = self._gcs_path(user_id, track_id, extension)
        blob = self._gcs_bucket.blob(gcs_path)
        blob.upload_from_string(audio_data, content_type=content_type)
        return f"gs://{self._gcs_bucket_name}/{gcs_path}"

    # =========================================================================
    # Download Methods
    # =========================================================================

    async def download(self, storage_path: str) -> bytes | None:
        """Download audio data from storage path.

        Args:
            storage_path: Storage path (gs:// URL or local path)

        Returns:
            Audio bytes or None if not found
        """
        if storage_path.startswith("gs://"):
            return await self._download_from_gcs(storage_path)
        return await self._download_from_local(storage_path)

    async def _download_from_local(self, path: str) -> bytes | None:
        """Download from local filesystem."""
        full_path = Path(path)
        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def _download_from_gcs(self, storage_path: str) -> bytes | None:
        """Download from Google Cloud Storage."""
        if not self.is_using_gcs:
            return None

        # Parse gs:// URL
        gcs_path = storage_path.replace(f"gs://{self._gcs_bucket_name}/", "")
        blob = self._gcs_bucket.blob(gcs_path)

        if not blob.exists():
            return None

        return blob.download_as_bytes()

    # =========================================================================
    # URL Generation Methods
    # =========================================================================

    def get_signed_url(
        self,
        storage_path: str,
        expiration: int = DEFAULT_SIGNED_URL_EXPIRATION,
    ) -> str | None:
        """Generate a signed URL for audio playback.

        Args:
            storage_path: Storage path (gs:// URL or local path)
            expiration: URL expiration in seconds

        Returns:
            Signed URL (GCS) or local file URL, or None if not found
        """
        if storage_path.startswith("gs://"):
            return self._get_gcs_signed_url(storage_path, expiration)
        return self._get_local_url(storage_path)

    def _get_local_url(self, path: str) -> str | None:
        """Get local file URL (for development)."""
        full_path = Path(path)
        if not full_path.exists():
            return None
        # Return relative path that can be served by the API
        return f"/api/v1/dj/audio/file/{full_path.relative_to(self._base_path)}"

    def _get_gcs_signed_url(self, storage_path: str, expiration: int) -> str | None:
        """Get GCS signed URL."""
        if not self.is_using_gcs:
            return None

        gcs_path = storage_path.replace(f"gs://{self._gcs_bucket_name}/", "")
        blob = self._gcs_bucket.blob(gcs_path)

        if not blob.exists():
            return None

        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET",
        )

    # =========================================================================
    # Delete Methods
    # =========================================================================

    async def delete(self, storage_path: str) -> bool:
        """Delete audio file from storage.

        Args:
            storage_path: Storage path (gs:// URL or local path)

        Returns:
            True if deleted, False otherwise
        """
        if storage_path.startswith("gs://"):
            return await self._delete_from_gcs(storage_path)
        return await self._delete_from_local(storage_path)

    async def _delete_from_local(self, path: str) -> bool:
        """Delete from local filesystem."""
        full_path = Path(path)
        if full_path.exists():
            await aiofiles.os.remove(full_path)
            return True
        return False

    async def _delete_from_gcs(self, storage_path: str) -> bool:
        """Delete from Google Cloud Storage."""
        if not self.is_using_gcs:
            return False

        gcs_path = storage_path.replace(f"gs://{self._gcs_bucket_name}/", "")
        blob = self._gcs_bucket.blob(gcs_path)

        if blob.exists():
            blob.delete()
            return True
        return False

    async def delete_user_audio(self, user_id: UUID) -> bool:
        """Delete all audio files for a user.

        Args:
            user_id: User ID

        Returns:
            True if any files deleted, False otherwise
        """
        if self.is_using_gcs:
            return await self._delete_user_audio_gcs(user_id)
        return await self._delete_user_audio_local(user_id)

    async def _delete_user_audio_local(self, user_id: UUID) -> bool:
        """Delete all local audio files for a user."""
        dir_path = self._user_dir(user_id)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            return True
        return False

    async def _delete_user_audio_gcs(self, user_id: UUID) -> bool:
        """Delete all GCS audio files for a user."""
        if not self.is_using_gcs:
            return False

        prefix = f"{self.PATH_PREFIX}/{user_id}/"
        blobs = list(self._gcs_bucket.list_blobs(prefix=prefix))

        if not blobs:
            return False

        for blob in blobs:
            blob.delete()

        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_file_size(self, storage_path: str) -> int | None:
        """Get file size in bytes.

        Args:
            storage_path: Storage path

        Returns:
            File size in bytes or None if not found
        """
        if storage_path.startswith("gs://"):
            return self._get_gcs_file_size(storage_path)
        return await self._get_local_file_size(storage_path)

    async def _get_local_file_size(self, path: str) -> int | None:
        """Get local file size."""
        full_path = Path(path)
        if full_path.exists():
            return full_path.stat().st_size
        return None

    def _get_gcs_file_size(self, storage_path: str) -> int | None:
        """Get GCS file size."""
        if not self.is_using_gcs:
            return None

        gcs_path = storage_path.replace(f"gs://{self._gcs_bucket_name}/", "")
        blob = self._gcs_bucket.blob(gcs_path)
        blob.reload()

        return blob.size if blob.exists() else None

    def exists(self, storage_path: str) -> bool:
        """Check if audio file exists.

        Args:
            storage_path: Storage path

        Returns:
            True if exists, False otherwise
        """
        if storage_path.startswith("gs://"):
            return self._exists_in_gcs(storage_path)
        return self._exists_in_local(storage_path)

    def _exists_in_local(self, path: str) -> bool:
        """Check if local file exists."""
        return Path(path).exists()

    def _exists_in_gcs(self, storage_path: str) -> bool:
        """Check if GCS file exists."""
        if not self.is_using_gcs:
            return False

        gcs_path = storage_path.replace(f"gs://{self._gcs_bucket_name}/", "")
        blob = self._gcs_bucket.blob(gcs_path)
        return blob.exists()
