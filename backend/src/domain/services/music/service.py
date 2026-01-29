"""Music Generation Service.

This module provides the core business logic for music generation using Mureka AI.
"""

import logging
import uuid
from dataclasses import dataclass

from src.config import get_settings
from src.domain.entities.music import (
    MusicGenerationJob,
    MusicGenerationStatus,
    MusicGenerationType,
    MusicModel,
)
from src.domain.repositories.music_job_repository import IMusicGenerationJobRepository
from src.infrastructure.adapters.mureka.client import MurekaAPIClient

logger = logging.getLogger(__name__)


@dataclass
class QuotaStatus:
    """User's music generation quota status."""

    daily_used: int
    daily_limit: int
    monthly_used: int
    monthly_limit: int
    concurrent_jobs: int
    max_concurrent_jobs: int

    @property
    def can_submit(self) -> bool:
        """Check if user can submit a new job."""
        return (
            self.daily_used < self.daily_limit
            and self.monthly_used < self.monthly_limit
            and self.concurrent_jobs < self.max_concurrent_jobs
        )


class QuotaExceededError(Exception):
    """Raised when user has exceeded their quota."""

    def __init__(self, message: str, quota_status: QuotaStatus):
        super().__init__(message)
        self.quota_status = quota_status


class MusicGenerationService:
    """Service for music generation operations.

    Handles submission, tracking, and management of music generation jobs.
    """

    def __init__(
        self,
        repository: IMusicGenerationJobRepository,
        mureka_client: MurekaAPIClient | None = None,
    ):
        """Initialize the service.

        Args:
            repository: Job repository for persistence
            mureka_client: Mureka API client (created if not provided)
        """
        self.repository = repository
        self.mureka_client = mureka_client or MurekaAPIClient()
        self._settings = get_settings()

    async def get_quota_status(self, user_id: uuid.UUID) -> QuotaStatus:
        """Get user's current quota status.

        Args:
            user_id: User ID

        Returns:
            QuotaStatus with current usage and limits
        """
        daily_used = await self.repository.count_daily_usage(user_id)
        monthly_used = await self.repository.count_monthly_usage(user_id)
        concurrent_jobs = await self.repository.count_active_jobs(user_id)

        return QuotaStatus(
            daily_used=daily_used,
            daily_limit=self._settings.music_daily_limit_per_user,
            monthly_used=monthly_used,
            monthly_limit=self._settings.music_monthly_limit_per_user,
            concurrent_jobs=concurrent_jobs,
            max_concurrent_jobs=self._settings.music_max_concurrent_jobs,
        )

    async def _check_quota(self, user_id: uuid.UUID) -> QuotaStatus:
        """Check if user can submit a new job.

        Args:
            user_id: User ID

        Returns:
            QuotaStatus

        Raises:
            QuotaExceededError: If quota is exceeded
        """
        quota = await self.get_quota_status(user_id)

        if not quota.can_submit:
            if quota.concurrent_jobs >= quota.max_concurrent_jobs:
                raise QuotaExceededError(
                    f"Maximum concurrent jobs reached ({quota.max_concurrent_jobs}). "
                    "Please wait for existing jobs to complete.",
                    quota,
                )
            elif quota.daily_used >= quota.daily_limit:
                raise QuotaExceededError(
                    f"Daily limit reached ({quota.daily_limit}). Please try again tomorrow.",
                    quota,
                )
            else:
                raise QuotaExceededError(
                    f"Monthly limit reached ({quota.monthly_limit}). Please contact administrator.",
                    quota,
                )

        return quota

    async def submit_instrumental(
        self,
        user_id: uuid.UUID,
        prompt: str,
        model: str = MusicModel.AUTO.value,
    ) -> MusicGenerationJob:
        """Submit an instrumental/BGM generation job.

        Args:
            user_id: User ID
            prompt: Scene/style description
            model: Mureka model selection

        Returns:
            Created MusicGenerationJob

        Raises:
            QuotaExceededError: If quota is exceeded
            MurekaAPIError: If Mureka API call fails
        """
        await self._check_quota(user_id)

        # Create job in pending status
        job = MusicGenerationJob(
            user_id=user_id,
            type=MusicGenerationType.INSTRUMENTAL,
            prompt=prompt,
            model=model,
        )

        # Save to database
        job = await self.repository.save(job)
        logger.info(f"Created instrumental job {job.id} for user {user_id}")

        return job

    async def submit_song(
        self,
        user_id: uuid.UUID,
        prompt: str | None = None,
        lyrics: str | None = None,
        model: str = MusicModel.AUTO.value,
    ) -> MusicGenerationJob:
        """Submit a song generation job.

        Args:
            user_id: User ID
            prompt: Style description
            lyrics: Song lyrics
            model: Mureka model selection

        Returns:
            Created MusicGenerationJob

        Raises:
            QuotaExceededError: If quota is exceeded
            ValueError: If neither prompt nor lyrics is provided
        """
        if not prompt and not lyrics:
            raise ValueError("Either prompt or lyrics must be provided")

        await self._check_quota(user_id)

        job = MusicGenerationJob(
            user_id=user_id,
            type=MusicGenerationType.SONG,
            prompt=prompt,
            lyrics=lyrics,
            model=model,
        )

        job = await self.repository.save(job)
        logger.info(f"Created song job {job.id} for user {user_id}")

        return job

    async def submit_lyrics(
        self,
        user_id: uuid.UUID,
        prompt: str,
    ) -> MusicGenerationJob:
        """Submit a lyrics generation job.

        Args:
            user_id: User ID
            prompt: Theme/topic description

        Returns:
            Created MusicGenerationJob

        Raises:
            QuotaExceededError: If quota is exceeded
        """
        await self._check_quota(user_id)

        job = MusicGenerationJob(
            user_id=user_id,
            type=MusicGenerationType.LYRICS,
            prompt=prompt,
        )

        job = await self.repository.save(job)
        logger.info(f"Created lyrics job {job.id} for user {user_id}")

        return job

    async def get_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> MusicGenerationJob | None:
        """Get a job by ID.

        Args:
            job_id: Job ID
            user_id: Optional user ID for ownership verification

        Returns:
            Job if found (and owned by user if user_id provided), None otherwise
        """
        job = await self.repository.get_by_id(job_id)

        if job and user_id and job.user_id != user_id:
            return None

        return job

    async def list_jobs(
        self,
        user_id: uuid.UUID,
        status: MusicGenerationStatus | None = None,
        job_type: MusicGenerationType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MusicGenerationJob], int]:
        """List jobs for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            job_type: Optional type filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            Tuple of (jobs list, total count)
        """
        jobs = await self.repository.get_by_user_id(
            user_id=user_id,
            status=status,
            job_type=job_type,
            limit=limit,
            offset=offset,
        )

        total = await self.repository.count_by_user_id(
            user_id=user_id,
            status=status,
            job_type=job_type,
        )

        return jobs, total

    async def retry_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MusicGenerationJob:
        """Retry a failed job.

        Args:
            job_id: Job ID to retry
            user_id: User ID for ownership verification

        Returns:
            Reset job ready for processing

        Raises:
            ValueError: If job not found or cannot be retried
        """
        job = await self.get_job(job_id, user_id)

        if not job:
            raise ValueError(f"Job {job_id} not found")

        if not job.can_retry():
            raise ValueError(
                f"Job {job_id} cannot be retried "
                f"(status={job.status}, retry_count={job.retry_count})"
            )

        job.retry()
        job = await self.repository.update(job)

        logger.info(f"Retried job {job_id}, retry_count={job.retry_count}")
        return job
