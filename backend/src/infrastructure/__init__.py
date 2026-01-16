"""Infrastructure Layer - External service adapters and implementations.

This layer contains concrete implementations of interfaces defined in
the Application layer. It includes:
- Provider adapters (TTS, STT, LLM)
- Repository implementations (persistence)
- Storage service implementations

Note: Provider classes are imported lazily in the DI container
to avoid import errors when dependencies are not installed.
"""

from src.infrastructure.persistence import (
    InMemoryTestRecordRepository,
    InMemoryVoiceRepository,
)
from src.infrastructure.storage import (
    LocalStorageService,
    S3StorageService,
)

__all__ = [
    # Repositories
    "InMemoryTestRecordRepository",
    "InMemoryVoiceRepository",
    # Storage
    "LocalStorageService",
    "S3StorageService",
]
