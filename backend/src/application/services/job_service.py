"""Job Service for async job management.

Feature: 007-async-job-mgmt
This service orchestrates async TTS synthesis job operations.
"""

import logging
from typing import Any
from uuid import UUID

from src.domain.entities.job import Job, JobStatus, JobType
from src.domain.repositories.job_repository import IJobRepository

logger = logging.getLogger(__name__)

# Maximum concurrent jobs per user
MAX_CONCURRENT_JOBS = 3


class JobLimitExceededError(Exception):
    """Raised when user exceeds concurrent job limit."""

    def __init__(self, current_count: int, max_count: int = MAX_CONCURRENT_JOBS):
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(f"Concurrent job limit exceeded: {current_count}/{max_count} active jobs")


class JobNotFoundError(Exception):
    """Raised when job is not found."""

    def __init__(self, job_id: UUID):
        self.job_id = job_id
        super().__init__(f"Job {job_id} not found")


class JobAccessDeniedError(Exception):
    """Raised when user doesn't have access to the job."""

    def __init__(self, job_id: UUID, user_id: UUID):
        self.job_id = job_id
        self.user_id = user_id
        super().__init__(f"Access denied to job {job_id}")


class JobCancelError(Exception):
    """Raised when job cannot be cancelled."""

    def __init__(self, job_id: UUID, status: JobStatus):
        self.job_id = job_id
        self.status = status
        super().__init__(f"Cannot cancel job {job_id} in {status.value} status")


class JobService:
    """Service for orchestrating async job operations."""

    def __init__(self, job_repository: IJobRepository):
        self._job_repo = job_repository

    async def create_job(
        self,
        user_id: UUID,
        provider: str,
        input_params: dict[str, Any],
        job_type: JobType = JobType.MULTI_ROLE_TTS,
    ) -> Job:
        """Create a new job.

        Args:
            user_id: ID of the user creating the job
            provider: TTS provider name
            input_params: Job input parameters
            job_type: Type of job (default: MULTI_ROLE_TTS)

        Returns:
            Created Job entity

        Raises:
            JobLimitExceededError: If user has reached concurrent job limit
        """
        logger.info(f"Creating job: user_id={user_id}, provider={provider}, type={job_type}")

        # Check concurrent job limit
        active_count = await self._job_repo.count_active_jobs(user_id)
        if active_count >= MAX_CONCURRENT_JOBS:
            logger.warning(
                f"Job limit exceeded for user {user_id}: "
                f"{active_count}/{MAX_CONCURRENT_JOBS} active jobs"
            )
            raise JobLimitExceededError(active_count)

        # Create job entity
        job = Job(
            user_id=user_id,
            job_type=job_type,
            provider=provider,
            input_params=input_params,
        )

        # Save to repository
        saved_job = await self._job_repo.save(job)
        logger.info(f"Job created: id={saved_job.id}, status={saved_job.status}")

        return saved_job

    async def get_job(self, job_id: UUID, user_id: UUID) -> Job:
        """Get a job by ID.

        Args:
            job_id: Job ID
            user_id: ID of the requesting user

        Returns:
            Job entity

        Raises:
            JobNotFoundError: If job doesn't exist or user doesn't have access
        """
        job = await self._job_repo.get_by_id(job_id)

        if job is None:
            logger.warning(f"Job not found: {job_id}")
            raise JobNotFoundError(job_id)

        # Check ownership
        if job.user_id != user_id:
            logger.warning(f"Access denied to job {job_id} for user {user_id}")
            raise JobNotFoundError(job_id)  # Return 404 to avoid leaking info

        return job

    async def list_jobs(
        self,
        user_id: UUID,
        status: JobStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        """List jobs for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            Tuple of (list of jobs, total count)
        """
        logger.debug(
            f"Listing jobs: user_id={user_id}, status={status}, limit={limit}, offset={offset}"
        )

        jobs = await self._job_repo.get_by_user_id(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        total = await self._job_repo.count_by_user_and_status(user_id, status)

        return jobs, total

    async def cancel_job(self, job_id: UUID, user_id: UUID) -> Job:
        """Cancel a pending job.

        Args:
            job_id: Job ID to cancel
            user_id: ID of the requesting user

        Returns:
            Cancelled Job entity

        Raises:
            JobNotFoundError: If job doesn't exist or user doesn't have access
            JobCancelError: If job cannot be cancelled
        """
        job = await self.get_job(job_id, user_id)

        if not job.can_cancel():
            logger.warning(f"Cannot cancel job {job_id}: status={job.status}")
            raise JobCancelError(job_id, job.status)

        job.cancel()
        updated_job = await self._job_repo.update(job)
        logger.info(f"Job cancelled: id={job_id}")

        return updated_job
