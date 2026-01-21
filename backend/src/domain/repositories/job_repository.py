"""Job Repository Interface for async job management.

This module defines the abstract repository interface for job storage operations.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import timedelta

from src.domain.entities.job import Job, JobStatus


class IJobRepository(ABC):
    """Abstract repository interface for jobs.

    This interface defines the contract for job storage operations,
    including support for background worker queries using SELECT ... FOR UPDATE SKIP LOCKED.
    """

    @abstractmethod
    async def save(self, job: Job) -> Job:
        """Save a new job.

        Args:
            job: Job to save

        Returns:
            Saved job with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs for a user with optional status filter.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs ordered by created_at descending
        """
        pass

    @abstractmethod
    async def update(self, job: Job) -> Job:
        """Update an existing job.

        Args:
            job: Job to update

        Returns:
            Updated job
        """
        pass

    @abstractmethod
    async def delete(self, job_id: uuid.UUID) -> bool:
        """Delete a job.

        Args:
            job_id: Job ID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_active_jobs(self, user_id: uuid.UUID) -> int:
        """Count active (pending or processing) jobs for a user.

        Used for concurrent job limit enforcement.

        Args:
            user_id: User ID

        Returns:
            Number of active jobs
        """
        pass

    @abstractmethod
    async def acquire_pending_job(self) -> Job | None:
        """Acquire a pending job for processing using FOR UPDATE SKIP LOCKED.

        This method atomically finds and locks a pending job for processing.
        The job status is updated to PROCESSING before returning.

        Returns:
            Job if one was acquired, None if no pending jobs available
        """
        pass

    @abstractmethod
    async def get_timed_out_jobs(self, timeout: timedelta) -> list[Job]:
        """Get jobs that have been processing for longer than the timeout.

        Args:
            timeout: Maximum allowed processing time

        Returns:
            List of timed out jobs
        """
        pass

    @abstractmethod
    async def get_stale_processing_jobs(self) -> list[Job]:
        """Get jobs stuck in processing status (for recovery on startup).

        Used to recover jobs that were processing when the system shut down.

        Returns:
            List of jobs in processing status
        """
        pass

    @abstractmethod
    async def count_by_user_and_status(
        self, user_id: uuid.UUID, status: JobStatus | None = None
    ) -> int:
        """Count jobs for a user with optional status filter.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Number of matching jobs
        """
        pass

    @abstractmethod
    async def get_jobs_for_cleanup(self, retention_days: int, limit: int = 100) -> list[Job]:
        """Get completed/failed/cancelled jobs older than retention period.

        Args:
            retention_days: Number of days to retain jobs
            limit: Maximum number of jobs to return

        Returns:
            List of jobs eligible for cleanup
        """
        pass
