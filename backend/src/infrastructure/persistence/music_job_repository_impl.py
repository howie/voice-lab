"""Music Generation Job Repository Implementation.

This module provides the SQLAlchemy implementation of the music job repository.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.music import (
    MusicGenerationJob,
    MusicGenerationStatus,
    MusicGenerationType,
)
from src.domain.repositories.music_job_repository import IMusicGenerationJobRepository
from src.infrastructure.persistence.models import MusicGenerationJobModel


class MusicGenerationJobRepository(IMusicGenerationJobRepository):
    """SQLAlchemy implementation of the music job repository."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    def _to_entity(self, model: MusicGenerationJobModel) -> MusicGenerationJob:
        """Convert SQLAlchemy model to domain entity."""
        return MusicGenerationJob(
            id=model.id,
            user_id=model.user_id,
            type=MusicGenerationType(model.type),
            status=MusicGenerationStatus(model.status),
            provider=model.provider,
            prompt=model.prompt,
            lyrics=model.lyrics,
            model=model.model,
            provider_task_id=model.mureka_task_id,
            result_url=model.result_url,
            original_url=model.original_url,
            cover_url=model.cover_url,
            generated_lyrics=model.generated_lyrics,
            duration_ms=model.duration_ms,
            title=model.title,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
            retry_count=model.retry_count,
        )

    def _to_model(self, entity: MusicGenerationJob) -> MusicGenerationJobModel:
        """Convert domain entity to SQLAlchemy model."""
        return MusicGenerationJobModel(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type.value,
            status=entity.status.value,
            provider=entity.provider,
            prompt=entity.prompt,
            lyrics=entity.lyrics,
            model=entity.model,
            mureka_task_id=entity.provider_task_id,
            result_url=entity.result_url,
            original_url=entity.original_url,
            cover_url=entity.cover_url,
            generated_lyrics=entity.generated_lyrics,
            duration_ms=entity.duration_ms,
            title=entity.title,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            error_message=entity.error_message,
            retry_count=entity.retry_count,
        )

    async def save(self, job: MusicGenerationJob) -> MusicGenerationJob:
        """Save a new music generation job."""
        model = self._to_model(job)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, job_id: uuid.UUID) -> MusicGenerationJob | None:
        """Get a job by ID."""
        result = await self.session.execute(
            select(MusicGenerationJobModel).where(MusicGenerationJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: MusicGenerationStatus | None = None,
        job_type: MusicGenerationType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MusicGenerationJob]:
        """List jobs for a user with optional filters."""
        query = select(MusicGenerationJobModel).where(MusicGenerationJobModel.user_id == user_id)

        if status:
            query = query.where(MusicGenerationJobModel.status == status.value)
        if job_type:
            query = query.where(MusicGenerationJobModel.type == job_type.value)

        query = query.order_by(MusicGenerationJobModel.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_user_id(
        self,
        user_id: uuid.UUID,
        status: MusicGenerationStatus | None = None,
        job_type: MusicGenerationType | None = None,
    ) -> int:
        """Count jobs for a user with optional filters."""
        query = (
            select(func.count())
            .select_from(MusicGenerationJobModel)
            .where(MusicGenerationJobModel.user_id == user_id)
        )

        if status:
            query = query.where(MusicGenerationJobModel.status == status.value)
        if job_type:
            query = query.where(MusicGenerationJobModel.type == job_type.value)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, job: MusicGenerationJob) -> MusicGenerationJob:
        """Update an existing job."""
        result = await self.session.execute(
            select(MusicGenerationJobModel).where(MusicGenerationJobModel.id == job.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Job {job.id} not found")

        # Update fields
        model.status = job.status.value
        model.provider = job.provider
        model.mureka_task_id = job.provider_task_id
        model.result_url = job.result_url
        model.original_url = job.original_url
        model.cover_url = job.cover_url
        model.generated_lyrics = job.generated_lyrics
        model.duration_ms = job.duration_ms
        model.title = job.title
        model.started_at = job.started_at
        model.completed_at = job.completed_at
        model.error_message = job.error_message
        model.retry_count = job.retry_count

        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def count_active_jobs(self, user_id: uuid.UUID) -> int:
        """Count active (pending or processing) jobs for a user."""
        active_statuses = [
            MusicGenerationStatus.PENDING.value,
            MusicGenerationStatus.PROCESSING.value,
        ]
        query = (
            select(func.count())
            .select_from(MusicGenerationJobModel)
            .where(
                and_(
                    MusicGenerationJobModel.user_id == user_id,
                    MusicGenerationJobModel.status.in_(active_statuses),
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def acquire_pending_job(self) -> MusicGenerationJob | None:
        """Acquire a pending job for processing using FOR UPDATE SKIP LOCKED."""
        query = (
            select(MusicGenerationJobModel)
            .where(MusicGenerationJobModel.status == MusicGenerationStatus.PENDING.value)
            .order_by(MusicGenerationJobModel.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_timed_out_jobs(self, timeout: timedelta) -> list[MusicGenerationJob]:
        """Get jobs that have been processing for longer than the timeout."""
        cutoff = datetime.utcnow() - timeout
        query = select(MusicGenerationJobModel).where(
            and_(
                MusicGenerationJobModel.status == MusicGenerationStatus.PROCESSING.value,
                MusicGenerationJobModel.started_at < cutoff,
            )
        )

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_daily_usage(self, user_id: uuid.UUID) -> int:
        """Count jobs created by user today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = (
            select(func.count())
            .select_from(MusicGenerationJobModel)
            .where(
                and_(
                    MusicGenerationJobModel.user_id == user_id,
                    MusicGenerationJobModel.created_at >= today_start,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_monthly_usage(self, user_id: uuid.UUID) -> int:
        """Count jobs created by user this month."""
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = (
            select(func.count())
            .select_from(MusicGenerationJobModel)
            .where(
                and_(
                    MusicGenerationJobModel.user_id == user_id,
                    MusicGenerationJobModel.created_at >= month_start,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
