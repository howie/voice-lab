"""Voice Sync Job Repository Interface (Port).

Feature: 008-voai-multi-role-voice-generation
T007: Define VoiceSyncJobRepository protocol
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.domain.entities.voice_sync_job import VoiceSyncJob, VoiceSyncStatus


class IVoiceSyncJobRepository(ABC):
    """Abstract interface for voice sync job repository.

    This interface defines the contract for voice sync job operations.
    Implementations provide database-backed tracking of voice synchronization jobs.
    """

    @abstractmethod
    async def create(self, job: VoiceSyncJob) -> VoiceSyncJob:
        """Create a new sync job.

        Args:
            job: Voice sync job to create

        Returns:
            Created job with database-assigned values
        """
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> VoiceSyncJob | None:
        """Get sync job by ID.

        Args:
            job_id: Job UUID as string

        Returns:
            VoiceSyncJob if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, job: VoiceSyncJob) -> VoiceSyncJob:
        """Update a sync job.

        Args:
            job: Job with updated fields

        Returns:
            Updated job

        Raises:
            ValueError: If job not found
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        job_id: str,
        status: VoiceSyncStatus,
        *,
        voices_synced: int | None = None,
        voices_deprecated: int | None = None,
        error_message: str | None = None,
    ) -> VoiceSyncJob | None:
        """Update sync job status and metrics.

        Args:
            job_id: Job UUID as string
            status: New status
            voices_synced: Number of voices synced (optional)
            voices_deprecated: Number of voices deprecated (optional)
            error_message: Error message if failed (optional)

        Returns:
            Updated job, or None if not found
        """
        pass

    @abstractmethod
    async def list_recent(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> Sequence[VoiceSyncJob]:
        """List recent sync jobs.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Sequence of recent jobs, ordered by created_at DESC
        """
        pass

    @abstractmethod
    async def list_by_status(
        self,
        status: VoiceSyncStatus,
        limit: int = 10,
    ) -> Sequence[VoiceSyncJob]:
        """List jobs by status.

        Args:
            status: Job status to filter by
            limit: Maximum number of results

        Returns:
            Sequence of jobs with the given status
        """
        pass

    @abstractmethod
    async def count_by_status(
        self,
        status: VoiceSyncStatus,
    ) -> int:
        """Count jobs by status.

        Args:
            status: Job status to count

        Returns:
            Number of jobs with the given status
        """
        pass

    @abstractmethod
    async def has_running_job(self) -> bool:
        """Check if there's a running sync job.

        Returns:
            True if there's a running job, False otherwise
        """
        pass

    @abstractmethod
    async def cleanup_old_jobs(
        self,
        days: int = 30,
    ) -> int:
        """Delete jobs older than specified days.

        Args:
            days: Number of days to keep jobs

        Returns:
            Number of deleted jobs
        """
        pass
