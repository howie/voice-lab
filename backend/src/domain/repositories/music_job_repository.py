"""Music Generation Job Repository Interface.

This module defines the abstract repository interface for music generation job storage.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import timedelta

from src.domain.entities.music import MusicGenerationJob, MusicGenerationStatus, MusicGenerationType


class IMusicGenerationJobRepository(ABC):
    """Abstract repository interface for music generation jobs.

    This interface defines the contract for music job storage operations,
    including support for background worker queries using SELECT ... FOR UPDATE SKIP LOCKED.
    """

    @abstractmethod
    async def save(self, job: MusicGenerationJob) -> MusicGenerationJob:
        """Save a new music generation job.

        Args:
            job: Job to save

        Returns:
            Saved job with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, job_id: uuid.UUID) -> MusicGenerationJob | None:
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
        status: MusicGenerationStatus | None = None,
        job_type: MusicGenerationType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MusicGenerationJob]:
        """List jobs for a user with optional filters.

        Args:
            user_id: User ID
            status: Optional status filter
            job_type: Optional type filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs ordered by created_at descending
        """
        pass

    @abstractmethod
    async def count_by_user_id(
        self,
        user_id: uuid.UUID,
        status: MusicGenerationStatus | None = None,
        job_type: MusicGenerationType | None = None,
    ) -> int:
        """Count jobs for a user with optional filters.

        Args:
            user_id: User ID
            status: Optional status filter
            job_type: Optional type filter

        Returns:
            Number of matching jobs
        """
        pass

    @abstractmethod
    async def update(self, job: MusicGenerationJob) -> MusicGenerationJob:
        """Update an existing job.

        Args:
            job: Job to update

        Returns:
            Updated job
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
    async def acquire_pending_job(self) -> MusicGenerationJob | None:
        """Acquire a pending job for processing using FOR UPDATE SKIP LOCKED.

        This method atomically finds and locks a pending job for processing.

        Returns:
            Job if one was acquired, None if no pending jobs available
        """
        pass

    @abstractmethod
    async def get_timed_out_jobs(self, timeout: timedelta) -> list[MusicGenerationJob]:
        """Get jobs that have been processing for longer than the timeout.

        Args:
            timeout: Maximum allowed processing time

        Returns:
            List of timed out jobs
        """
        pass

    @abstractmethod
    async def count_daily_usage(self, user_id: uuid.UUID) -> int:
        """Count jobs created by user today.

        Args:
            user_id: User ID

        Returns:
            Number of jobs created today
        """
        pass

    @abstractmethod
    async def count_monthly_usage(self, user_id: uuid.UUID) -> int:
        """Count jobs created by user this month.

        Args:
            user_id: User ID

        Returns:
            Number of jobs created this month
        """
        pass
