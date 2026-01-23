"""Voice sync job domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class VoiceSyncStatus(Enum):
    """Voice sync job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VoiceSyncJob:
    """Voice synchronization job entity.

    Tracks background sync operations that fetch voice metadata from providers.

    State Transitions:
        [PENDING] --start--> [RUNNING] --success--> [COMPLETED]
                                |
                                +--failure--> [FAILED]
                                                |
                                                +--retry (if retry_count < 3)--> [PENDING]
    """

    id: str  # UUID as string
    providers: list[str]  # List of providers to sync, empty = all
    status: VoiceSyncStatus
    voices_synced: int = 0
    voices_deprecated: int = 0
    error_message: str | None = None
    retry_count: int = 0  # Max: 3
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Constants
    MAX_RETRIES: int = field(default=3, init=False, repr=False)
    RETRY_DELAYS: tuple[float, ...] = field(default=(1.0, 2.0, 4.0), init=False, repr=False)

    @classmethod
    def create(cls, providers: list[str] | None = None) -> "VoiceSyncJob":
        """Create a new sync job."""
        return cls(
            id=str(uuid4()),
            providers=providers or [],
            status=VoiceSyncStatus.PENDING,
        )

    def start(self) -> "VoiceSyncJob":
        """Start processing the job. Returns self for chaining."""
        if self.status != VoiceSyncStatus.PENDING:
            raise ValueError(f"Cannot start job in {self.status} status")
        self.status = VoiceSyncStatus.RUNNING
        self.started_at = datetime.utcnow()
        return self

    def complete(
        self,
        voices_synced: int = 0,
        voices_deprecated: int = 0,
    ) -> "VoiceSyncJob":
        """Mark job as completed. Returns self for chaining."""
        if self.status != VoiceSyncStatus.RUNNING:
            raise ValueError(f"Cannot complete job in {self.status} status")
        self.status = VoiceSyncStatus.COMPLETED
        self.voices_synced = voices_synced
        self.voices_deprecated = voices_deprecated
        self.completed_at = datetime.utcnow()
        return self

    def fail(self, error: str) -> "VoiceSyncJob":
        """Mark job as failed. Returns self for chaining."""
        if self.status != VoiceSyncStatus.RUNNING:
            raise ValueError(f"Cannot fail job in {self.status} status")
        self.status = VoiceSyncStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
        return self

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.status == VoiceSyncStatus.FAILED and self.retry_count < self.MAX_RETRIES

    def retry(self) -> None:
        """Reset job for retry."""
        if not self.can_retry():
            raise ValueError("Job cannot be retried")
        self.retry_count += 1
        self.status = VoiceSyncStatus.PENDING
        self.error_message = None
        self.started_at = None
        self.completed_at = None

    def get_retry_delay(self) -> float:
        """Get delay before next retry in seconds."""
        if self.retry_count < len(self.RETRY_DELAYS):
            return self.RETRY_DELAYS[self.retry_count]
        return self.RETRY_DELAYS[-1]

    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state."""
        return self.status in (VoiceSyncStatus.COMPLETED, VoiceSyncStatus.FAILED)

    @property
    def total_voices_processed(self) -> int:
        """Get total number of voices processed."""
        return self.voices_synced + self.voices_deprecated
