"""Music Provider Interface (Port).

Defines the abstract contract for music generation providers.
Infrastructure layer provides concrete implementations (Mureka, Suno, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class MusicTaskStatus(str, Enum):
    """Unified task status across all music providers."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MusicSubmitResult:
    """Unified result from submitting a generation task."""

    task_id: str
    provider: str
    status: MusicTaskStatus


@dataclass
class MusicTaskResult:
    """Unified result from querying a generation task."""

    task_id: str
    provider: str
    status: MusicTaskStatus
    audio_url: str | None = None
    cover_url: str | None = None
    lyrics: str | None = None
    duration_ms: int | None = None
    title: str | None = None
    error_message: str | None = None


class IMusicProvider(ABC):
    """Abstract interface for music generation providers.

    This interface defines the contract that all music provider
    implementations must follow. Infrastructure layer provides
    concrete implementations (Mureka, Suno, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider identifier (e.g., 'mureka', 'suno')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get human-readable provider name."""
        ...

    @abstractmethod
    async def generate_song(
        self,
        *,
        lyrics: str | None = None,
        prompt: str | None = None,
        model: str | None = None,
    ) -> MusicSubmitResult:
        """Submit a song generation task (vocals + music).

        Args:
            lyrics: Song lyrics with optional section markers
            prompt: Style description
            model: Provider-specific model selection

        Returns:
            MusicSubmitResult with task_id and initial status
        """
        ...

    @abstractmethod
    async def generate_instrumental(
        self,
        *,
        prompt: str,
        model: str | None = None,
    ) -> MusicSubmitResult:
        """Submit an instrumental/BGM generation task.

        Args:
            prompt: Scene/style description
            model: Provider-specific model selection

        Returns:
            MusicSubmitResult with task_id and initial status
        """
        ...

    @abstractmethod
    async def generate_lyrics(
        self,
        *,
        prompt: str | None = None,
    ) -> MusicSubmitResult:
        """Submit a lyrics generation task.

        Args:
            prompt: Theme/topic description

        Returns:
            MusicSubmitResult with task_id and initial status
        """
        ...

    @abstractmethod
    async def query_task(
        self,
        task_id: str,
        task_type: str,
    ) -> MusicTaskResult:
        """Query the status of a generation task.

        Args:
            task_id: Provider-specific task identifier
            task_type: Type of task ('song', 'instrumental', 'lyrics')

        Returns:
            MusicTaskResult with current status and results
        """
        ...

    async def health_check(self) -> bool:
        """Check if provider is available and configured.

        Returns:
            True if provider is healthy
        """
        return True
