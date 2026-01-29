"""Music generation entity and related enums.

This module defines the core domain entities for Mureka AI music generation jobs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class MusicGenerationType(str, Enum):
    """Type of music generation request.

    - SONG: Complete song with vocals
    - INSTRUMENTAL: Background music/BGM without vocals
    - LYRICS: AI-generated lyrics
    """

    SONG = "song"
    INSTRUMENTAL = "instrumental"
    LYRICS = "lyrics"


class MusicGenerationStatus(str, Enum):
    """Status of music generation job.

    State transitions:
    - PENDING -> PROCESSING: Worker picks up the job and submits to Mureka
    - PROCESSING -> COMPLETED: Mureka returns completed result
    - PROCESSING -> FAILED: Error or timeout occurs
    - FAILED -> PENDING: User retries the job (if retry_count < MAX_RETRY)
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MusicModel(str, Enum):
    """Mureka AI model selection.

    - AUTO: Automatically select the best model
    - MUREKA_01: Latest flagship model (O1)
    - V7_5: Balanced model
    - V6: Classic stable model
    """

    AUTO = "auto"
    MUREKA_01 = "mureka-01"
    V7_5 = "v7.5"
    V6 = "v6"


@dataclass
class MusicGenerationJob:
    """Domain entity representing a music generation job.

    Attributes:
        id: Unique identifier for the job
        user_id: ID of the user who submitted the job
        type: Type of generation (song, instrumental, lyrics)
        status: Current status of the job
        prompt: Style/scene description for generation
        lyrics: Input lyrics (for song generation)
        model: Mureka model selection
        mureka_task_id: Task ID returned by Mureka API
        result_url: Local storage URL for the result
        original_url: Original Mureka MP3 URL
        cover_url: Cover image URL (for songs)
        generated_lyrics: AI-generated lyrics
        duration_ms: Duration in milliseconds
        title: Generated title
        created_at: Timestamp when job was created
        started_at: Timestamp when processing started
        completed_at: Timestamp when job completed or failed
        error_message: Error description (only when failed)
        retry_count: Number of retry attempts (max 3)
    """

    user_id: UUID
    type: MusicGenerationType
    id: UUID = field(default_factory=uuid4)
    status: MusicGenerationStatus = MusicGenerationStatus.PENDING
    prompt: str | None = None
    lyrics: str | None = None
    model: str = MusicModel.AUTO.value
    mureka_task_id: str | None = None
    result_url: str | None = None
    original_url: str | None = None
    cover_url: str | None = None
    generated_lyrics: str | None = None
    duration_ms: int | None = None
    title: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0

    # Constants
    MAX_RETRY_COUNT: int = field(default=3, init=False, repr=False)
    TIMEOUT_MINUTES: int = field(default=5, init=False, repr=False)

    def can_retry(self) -> bool:
        """Check if the job can be retried.

        Jobs can be retried if status is FAILED and retry_count < MAX_RETRY_COUNT.
        """
        return (
            self.status == MusicGenerationStatus.FAILED and self.retry_count < self.MAX_RETRY_COUNT
        )

    def start_processing(self, mureka_task_id: str) -> None:
        """Mark the job as processing.

        Args:
            mureka_task_id: Task ID from Mureka API

        Raises:
            ValueError: If job is not in PENDING status
        """
        if self.status != MusicGenerationStatus.PENDING:
            raise ValueError(f"Cannot start job in {self.status} status")
        self.status = MusicGenerationStatus.PROCESSING
        self.mureka_task_id = mureka_task_id
        self.started_at = datetime.utcnow()

    def complete(
        self,
        result_url: str,
        original_url: str | None = None,
        cover_url: str | None = None,
        generated_lyrics: str | None = None,
        duration_ms: int | None = None,
        title: str | None = None,
    ) -> None:
        """Mark the job as completed.

        Args:
            result_url: Local storage URL for the result
            original_url: Original Mureka MP3 URL
            cover_url: Cover image URL
            generated_lyrics: AI-generated lyrics
            duration_ms: Duration in milliseconds
            title: Generated title

        Raises:
            ValueError: If job is not in PROCESSING status
        """
        if self.status != MusicGenerationStatus.PROCESSING:
            raise ValueError(f"Cannot complete job in {self.status} status")
        self.status = MusicGenerationStatus.COMPLETED
        self.result_url = result_url
        self.original_url = original_url
        self.cover_url = cover_url
        self.generated_lyrics = generated_lyrics
        self.duration_ms = duration_ms
        self.title = title
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """Mark the job as failed.

        Args:
            error_message: Description of the failure

        Raises:
            ValueError: If job is not in PENDING or PROCESSING status
        """
        if self.status not in (MusicGenerationStatus.PENDING, MusicGenerationStatus.PROCESSING):
            raise ValueError(f"Cannot fail job in {self.status} status")
        self.status = MusicGenerationStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def retry(self) -> None:
        """Reset the job for retry.

        Raises:
            ValueError: If job cannot be retried
        """
        if not self.can_retry():
            raise ValueError(
                f"Cannot retry job in {self.status} status "
                f"(retry_count={self.retry_count}, max={self.MAX_RETRY_COUNT})"
            )
        self.status = MusicGenerationStatus.PENDING
        self.retry_count += 1
        self.error_message = None
        self.mureka_task_id = None
        self.started_at = None
        self.completed_at = None

    def is_terminal(self) -> bool:
        """Check if the job is in a terminal state."""
        return self.status in (MusicGenerationStatus.COMPLETED, MusicGenerationStatus.FAILED)

    def is_active(self) -> bool:
        """Check if the job is actively being processed or waiting."""
        return self.status in (MusicGenerationStatus.PENDING, MusicGenerationStatus.PROCESSING)
