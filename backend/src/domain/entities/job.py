"""Job entity and related enums for async job management.

This module defines the core domain entities for background TTS synthesis jobs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class JobStatus(str, Enum):
    """Job status enum representing the lifecycle states of a job.

    State transitions:
    - PENDING -> PROCESSING: Worker picks up the job
    - PENDING -> CANCELLED: User cancels the job
    - PROCESSING -> COMPLETED: TTS synthesis succeeds
    - PROCESSING -> FAILED: Error or timeout occurs
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enum for different synthesis operations.

    Currently supports multi-role TTS. Future extensions may include:
    - SINGLE_TTS: Single voice synthesis
    - STT_TRANSCRIPTION: Speech-to-text transcription
    """

    MULTI_ROLE_TTS = "multi_role_tts"


@dataclass
class Job:
    """Domain entity representing a TTS synthesis job.

    Attributes:
        id: Unique identifier for the job
        user_id: ID of the user who submitted the job
        job_type: Type of synthesis operation
        status: Current status of the job
        provider: TTS provider name (e.g., "azure", "google")
        input_params: Synthesis parameters as a dictionary
        audio_file_id: ID of the generated audio file (only when completed)
        result_metadata: Execution result metadata (only when completed)
        error_message: Error description (only when failed)
        retry_count: Number of retry attempts (max 3)
        created_at: Timestamp when job was created
        started_at: Timestamp when processing started
        completed_at: Timestamp when job completed or failed
    """

    user_id: UUID
    job_type: JobType
    provider: str
    input_params: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    audio_file_id: UUID | None = None
    result_metadata: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Constants
    MAX_RETRY_COUNT: int = field(default=3, init=False, repr=False)
    TIMEOUT_MINUTES: int = field(default=10, init=False, repr=False)

    def can_cancel(self) -> bool:
        """Check if the job can be cancelled.

        Only jobs in PENDING status can be cancelled.
        """
        return self.status == JobStatus.PENDING

    def can_retry(self) -> bool:
        """Check if the job can be retried.

        Jobs can be retried if retry_count < MAX_RETRY_COUNT.
        """
        return self.retry_count < self.MAX_RETRY_COUNT

    def start_processing(self) -> None:
        """Mark the job as processing.

        Raises:
            ValueError: If job is not in PENDING status
        """
        if self.status != JobStatus.PENDING:
            raise ValueError(f"Cannot start job in {self.status} status")
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete(
        self,
        audio_file_id: UUID,
        result_metadata: dict[str, Any],
    ) -> None:
        """Mark the job as completed.

        Args:
            audio_file_id: ID of the generated audio file
            result_metadata: Execution result metadata

        Raises:
            ValueError: If job is not in PROCESSING status
        """
        if self.status != JobStatus.PROCESSING:
            raise ValueError(f"Cannot complete job in {self.status} status")
        self.status = JobStatus.COMPLETED
        self.audio_file_id = audio_file_id
        self.result_metadata = result_metadata
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """Mark the job as failed.

        Args:
            error_message: Description of the failure

        Raises:
            ValueError: If job is not in PENDING or PROCESSING status
        """
        if self.status not in (JobStatus.PENDING, JobStatus.PROCESSING):
            raise ValueError(f"Cannot fail job in {self.status} status")
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the job.

        Raises:
            ValueError: If job is not in PENDING status
        """
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel job in {self.status} status")
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def increment_retry(self) -> None:
        """Increment the retry count.

        Raises:
            ValueError: If max retries exceeded
        """
        if not self.can_retry():
            raise ValueError(f"Max retries ({self.MAX_RETRY_COUNT}) exceeded")
        self.retry_count += 1

    def is_terminal(self) -> bool:
        """Check if the job is in a terminal state."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    def is_active(self) -> bool:
        """Check if the job is actively being processed or waiting."""
        return self.status in (JobStatus.PENDING, JobStatus.PROCESSING)
