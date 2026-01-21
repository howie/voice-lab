"""SQLAlchemy implementation of JobRepository.

This module provides the PostgreSQL-based implementation of the job repository,
including support for SELECT ... FOR UPDATE SKIP LOCKED for worker job acquisition.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.job import Job, JobStatus, JobType
from src.domain.repositories.job_repository import IJobRepository
from src.infrastructure.persistence.models import JobModel


class JobRepositoryImpl(IJobRepository):
    """SQLAlchemy-based implementation of IJobRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: Job) -> Job:
        """Save a new job."""
        model = JobModel(
            id=job.id,
            user_id=job.user_id,
            job_type=job.job_type.value,
            status=job.status.value,
            provider=job.provider,
            input_params=job.input_params,
            audio_file_id=job.audio_file_id,
            result_metadata=job.result_metadata,
            error_message=job.error_message,
            retry_count=job.retry_count,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        """Get a job by ID."""
        result = await self._session.execute(select(JobModel).where(JobModel.id == job_id))
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs for a user with optional status filter."""
        query = select(JobModel).where(JobModel.user_id == user_id)

        if status is not None:
            query = query.where(JobModel.status == status.value)

        query = query.order_by(JobModel.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def update(self, job: Job) -> Job:
        """Update an existing job."""
        await self._session.execute(
            update(JobModel)
            .where(JobModel.id == job.id)
            .values(
                status=job.status.value,
                audio_file_id=job.audio_file_id,
                result_metadata=job.result_metadata,
                error_message=job.error_message,
                retry_count=job.retry_count,
                started_at=job.started_at,
                completed_at=job.completed_at,
            )
        )
        await self._session.flush()
        return job

    async def delete(self, job_id: uuid.UUID) -> bool:
        """Delete a job."""
        result = await self._session.execute(delete(JobModel).where(JobModel.id == job_id))
        await self._session.flush()
        return result.rowcount > 0

    async def count_active_jobs(self, user_id: uuid.UUID) -> int:
        """Count active (pending or processing) jobs for a user."""
        result = await self._session.execute(
            select(func.count())
            .select_from(JobModel)
            .where(JobModel.user_id == user_id)
            .where(JobModel.status.in_([JobStatus.PENDING.value, JobStatus.PROCESSING.value]))
        )
        return result.scalar() or 0

    async def acquire_pending_job(self) -> Job | None:
        """Acquire a pending job for processing using FOR UPDATE SKIP LOCKED.

        This method atomically finds and locks a pending job for processing.
        The job status is updated to PROCESSING before returning.
        """
        # Use FOR UPDATE SKIP LOCKED to avoid blocking on locked rows
        query = (
            select(JobModel)
            .where(JobModel.status == JobStatus.PENDING.value)
            .order_by(JobModel.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        # Update to processing
        now = datetime.utcnow()
        model.status = JobStatus.PROCESSING.value
        model.started_at = now
        await self._session.flush()

        return self._model_to_entity(model)

    async def get_timed_out_jobs(self, timeout: timedelta) -> list[Job]:
        """Get jobs that have been processing for longer than the timeout."""
        cutoff = datetime.utcnow() - timeout
        result = await self._session.execute(
            select(JobModel)
            .where(JobModel.status == JobStatus.PROCESSING.value)
            .where(JobModel.started_at < cutoff)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def get_stale_processing_jobs(self) -> list[Job]:
        """Get jobs stuck in processing status (for recovery on startup)."""
        result = await self._session.execute(
            select(JobModel).where(JobModel.status == JobStatus.PROCESSING.value)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def count_by_user_and_status(
        self, user_id: uuid.UUID, status: JobStatus | None = None
    ) -> int:
        """Count jobs for a user with optional status filter."""
        query = select(func.count()).select_from(JobModel).where(JobModel.user_id == user_id)

        if status is not None:
            query = query.where(JobModel.status == status.value)

        result = await self._session.execute(query)
        return result.scalar() or 0

    async def get_jobs_for_cleanup(self, retention_days: int, limit: int = 100) -> list[Job]:
        """Get completed/failed/cancelled jobs older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        terminal_statuses = [
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        ]

        result = await self._session.execute(
            select(JobModel)
            .where(JobModel.status.in_(terminal_statuses))
            .where(JobModel.completed_at < cutoff)
            .order_by(JobModel.completed_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    def _model_to_entity(self, model: JobModel) -> Job:
        """Convert SQLAlchemy model to domain entity."""
        return Job(
            id=model.id,
            user_id=model.user_id,
            job_type=JobType(model.job_type),
            status=JobStatus(model.status),
            provider=model.provider,
            input_params=model.input_params,
            audio_file_id=model.audio_file_id,
            result_metadata=model.result_metadata,
            error_message=model.error_message,
            retry_count=model.retry_count,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )
