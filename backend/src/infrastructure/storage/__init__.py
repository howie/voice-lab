"""Storage Layer - Storage service implementations."""

from src.infrastructure.storage.local_storage import LocalStorage

# Alias for backward compatibility
LocalStorageService = LocalStorage

# S3 is optional - only import if aioboto3 is available
try:
    from src.infrastructure.storage.s3_storage import S3StorageService
except ImportError:
    S3StorageService = None  # type: ignore

__all__ = [
    "LocalStorage",
    "LocalStorageService",
    "S3StorageService",
]
