"""SQLAlchemy implementation of VoiceSyncJobRepository.

Feature: 008-voai-multi-role-voice-generation
T009: Implement VoiceSyncJobRepositoryImpl
"""

from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.voice_sync_job_repository import IVoiceSyncJobRepository
from src.domain.entities.voice_sync_job import VoiceSyncJob, VoiceSyncStatus
from src.infrastructure.persistence.models import VoiceSyncJobModel


class VoiceSyncJobRepositoryImpl(IVoiceSyncJobRepository):
    """SQLAlchemy-based implementation of IVoiceSyncJobRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: VoiceSyncJob) -> VoiceSyncJob:
        """Create a new sync job."""
        model = VoiceSyncJobModel(
            id=job.id,
            provider=job.provider,
            status=job.status.value,
            voices_added=job.voices_added,
            voices_updated=job.voices_updated,
            voices_deprecated=job.voices_deprecated,
            error_message=job.error_message,
            retry_count=job.retry_count,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return job

    async def get_by_id(self, job_id: UUID) -> VoiceSyncJob | None:
        """Get sync job by ID."""
        result = await self._session.execute(
            select(VoiceSyncJobModel).where(VoiceSyncJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update(self, job: VoiceSyncJob) -> VoiceSyncJob:
        """Update a sync job."""
        await self._session.execute(
            update(VoiceSyncJobModel)
            .where(VoiceSyncJobModel.id == job.id)
            .values(
                status=job.status.value,
                voices_added=job.voices_added,
                voices_updated=job.voices_updated,
                voices_deprecated=job.voices_deprecated,
                error_message=job.error_message,
                retry_count=job.retry_count,
                started_at=job.started_at,
                completed_at=job.completed_at,
            )
        )
        await self._session.flush()
        return job

    async def update_status(
        self,
        job_id: UUID,
        status: VoiceSyncStatus,
        *,
        voices_added: int | None = None,
        voices_updated: int | None = None,
        voices_deprecated: int | None = None,
        error_message: str | None = None,
    ) -> VoiceSyncJob | None:
        """Update sync job status and metrics."""
        values: dict = {"status": status.value}

        if status == VoiceSyncStatus.RUNNING:
            values["started_at"] = datetime.utcnow()
        elif status in (VoiceSyncStatus.COMPLETED, VoiceSyncStatus.FAILED):
            values["completed_at"] = datetime.utcnow()

        if voices_added is not None:
            values["voices_added"] = voices_added
        if voices_updated is not None:
            values["voices_updated"] = voices_updated
        if voices_deprecated is not None:
            values["voices_deprecated"] = voices_deprecated
        if error_message is not None:
            values["error_message"] = error_message

        await self._session.execute(
            update(VoiceSyncJobModel).where(VoiceSyncJobModel.id == job_id).values(**values)
        )
        await self._session.flush()

        return await self.get_by_id(job_id)

    async def get_latest_by_provider(
        self,
        provider: str | None,
    ) -> VoiceSyncJob | None:
        """Get the latest sync job for a provider."""
        query = select(VoiceSyncJobModel)

        if provider is None:
            query = query.where(VoiceSyncJobModel.provider.is_(None))
        else:
            query = query.where(VoiceSyncJobModel.provider == provider)

        query = query.order_by(VoiceSyncJobModel.created_at.desc()).limit(1)

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_latest_completed_by_provider(
        self,
        provider: str | None,
    ) -> VoiceSyncJob | None:
        """Get the latest completed sync job for a provider."""
        query = select(VoiceSyncJobModel).where(
            VoiceSyncJobModel.status == VoiceSyncStatus.COMPLETED.value
        )

        if provider is None:
            query = query.where(VoiceSyncJobModel.provider.is_(None))
        else:
            query = query.where(VoiceSyncJobModel.provider == provider)

        query = query.order_by(VoiceSyncJobModel.completed_at.desc()).limit(1)

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def list_recent(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> Sequence[VoiceSyncJob]:
        """List recent sync jobs."""
        query = (
            select(VoiceSyncJobModel)
            .order_by(VoiceSyncJobModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_by_status(
        self,
        status: VoiceSyncStatus,
        limit: int = 10,
    ) -> Sequence[VoiceSyncJob]:
        """List jobs by status."""
        query = (
            select(VoiceSyncJobModel)
            .where(VoiceSyncJobModel.status == status.value)
            .order_by(VoiceSyncJobModel.created_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def count_by_status(
        self,
        status: VoiceSyncStatus,
    ) -> int:
        """Count jobs by status."""
        result = await self._session.execute(
            select(func.count())
            .select_from(VoiceSyncJobModel)
            .where(VoiceSyncJobModel.status == status.value)
        )
        return result.scalar() or 0

    async def has_running_job(
        self,
        provider: str | None = None,
    ) -> bool:
        """Check if there's a running sync job."""
        query = (
            select(func.count())
            .select_from(VoiceSyncJobModel)
            .where(VoiceSyncJobModel.status == VoiceSyncStatus.RUNNING.value)
        )

        if provider is not None:
            query = query.where(VoiceSyncJobModel.provider == provider)

        result = await self._session.execute(query)
        return (result.scalar() or 0) > 0

    async def cleanup_old_jobs(
        self,
        days: int = 30,
    ) -> int:
        """Delete jobs older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self._session.execute(
            delete(VoiceSyncJobModel).where(VoiceSyncJobModel.created_at < cutoff)
        )
        await self._session.flush()
        return result.rowcount

    def _model_to_entity(self, model: VoiceSyncJobModel) -> VoiceSyncJob:
        """Convert SQLAlchemy model to domain entity."""
        return VoiceSyncJob(
            id=model.id,
            provider=model.provider,
            status=VoiceSyncStatus(model.status),
            voices_added=model.voices_added,
            voices_updated=model.voices_updated,
            voices_deprecated=model.voices_deprecated,
            error_message=model.error_message,
            retry_count=model.retry_count,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )
