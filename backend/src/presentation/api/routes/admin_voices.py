"""Admin Voices API Routes.

Feature: 008-voai-multi-role-voice-generation
T028-T031: Admin endpoints for voice sync management
"""

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.voice_cache_repository import IVoiceCacheRepository
from src.application.interfaces.voice_sync_job_repository import IVoiceSyncJobRepository
from src.application.use_cases.sync_voices import (
    SyncVoicesInput,
    SyncVoicesUseCase,
)
from src.config import get_settings
from src.domain.entities.voice_sync_job import VoiceSyncJob, VoiceSyncStatus
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.voice_cache_repository_impl import (
    VoiceCacheRepositoryImpl,
)
from src.infrastructure.persistence.voice_sync_job_repository_impl import (
    VoiceSyncJobRepositoryImpl,
)
from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider
from src.infrastructure.providers.tts.voai_tts import VoAITTSProvider

router = APIRouter(prefix="/admin/voices", tags=["admin-voices"])


# Pydantic models for API
class SyncVoicesRequest(BaseModel):
    """Request to trigger voice sync."""

    providers: list[str] | None = None  # None = sync all supported providers
    language: str | None = None  # Optional language filter
    force: bool = False  # Force sync even if recently synced


class SyncVoicesResponse(BaseModel):
    """Response from voice sync trigger."""

    job_id: str
    message: str
    providers: list[str]


class SyncStatusResponse(BaseModel):
    """Response with sync status."""

    has_running_job: bool
    running_jobs: int
    pending_jobs: int
    completed_jobs: int
    failed_jobs: int


class SyncJobResponse(BaseModel):
    """Response with sync job details."""

    id: str
    providers: list[str]
    status: str
    voices_synced: int
    voices_deprecated: int
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str


class SyncJobListResponse(BaseModel):
    """Response with list of sync jobs."""

    jobs: list[SyncJobResponse]
    total: int


# Dependency injection helpers
def get_voice_cache_repo(
    session: AsyncSession = Depends(get_db_session),
) -> IVoiceCacheRepository:
    """Get voice cache repository instance."""
    return VoiceCacheRepositoryImpl(session)


def get_voice_sync_job_repo(
    session: AsyncSession = Depends(get_db_session),
) -> IVoiceSyncJobRepository:
    """Get voice sync job repository instance."""
    return VoiceSyncJobRepositoryImpl(session)


def get_sync_voices_use_case(
    voice_cache_repo: IVoiceCacheRepository = Depends(get_voice_cache_repo),
    sync_job_repo: IVoiceSyncJobRepository = Depends(get_voice_sync_job_repo),
) -> SyncVoicesUseCase:
    """Get sync voices use case instance."""
    settings = get_settings()

    # Initialize VoAI provider if API key is configured
    voai_provider = None
    if settings.voai_api_key:
        voai_provider = VoAITTSProvider(
            api_key=settings.voai_api_key,
            api_endpoint=settings.voai_api_endpoint or None,
        )

    # Initialize Gemini provider if API key is configured
    # Try google_ai_api_key first, then fallback to GEMINI_API_KEY env var
    gemini_provider = None
    gemini_api_key = settings.google_ai_api_key or os.getenv("GEMINI_API_KEY", "")
    if gemini_api_key:
        gemini_provider = GeminiTTSProvider(
            api_key=gemini_api_key,
            model=settings.gemini_tts_model,
        )

    return SyncVoicesUseCase(
        voice_cache_repo=voice_cache_repo,
        sync_job_repo=sync_job_repo,
        voai_provider=voai_provider,
        gemini_provider=gemini_provider,
    )


def _job_to_response(job: VoiceSyncJob) -> SyncJobResponse:
    """Convert VoiceSyncJob to API response."""
    return SyncJobResponse(
        id=job.id,
        providers=job.providers,
        status=job.status.value,
        voices_synced=job.voices_synced,
        voices_deprecated=job.voices_deprecated,
        error_message=job.error_message,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        created_at=job.created_at.isoformat(),
    )


@router.post("/sync", response_model=SyncVoicesResponse)
async def trigger_voice_sync(
    request: SyncVoicesRequest,
    use_case: SyncVoicesUseCase = Depends(get_sync_voices_use_case),
    session: AsyncSession = Depends(get_db_session),
) -> SyncVoicesResponse:
    """Trigger a voice sync operation.

    T028: POST /api/v1/admin/voices/sync endpoint for manual trigger

    This starts a sync job to sync voice data from the specified providers.
    If no providers are specified, all supported providers are synced.

    Args:
        request: Sync request with optional provider filter
        use_case: Sync voices use case instance
        session: Database session

    Returns:
        SyncVoicesResponse with job ID and status
    """
    input_data = SyncVoicesInput(
        providers=request.providers,
        language=request.language,
        force=request.force,
    )

    try:
        result = await use_case.execute(input_data)
        await session.commit()

        return SyncVoicesResponse(
            job_id=result.job_id,
            message=f"Voice sync started for {len(result.providers_synced)} providers",
            providers=result.providers_synced,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}") from e


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    sync_job_repo: IVoiceSyncJobRepository = Depends(get_voice_sync_job_repo),
) -> SyncStatusResponse:
    """Get voice sync status overview.

    T029: GET /api/v1/admin/voices/sync/status endpoint

    Returns counts of jobs by status.

    Returns:
        SyncStatusResponse with job counts
    """
    has_running = await sync_job_repo.has_running_job()
    running = await sync_job_repo.count_by_status(VoiceSyncStatus.RUNNING)
    pending = await sync_job_repo.count_by_status(VoiceSyncStatus.PENDING)
    completed = await sync_job_repo.count_by_status(VoiceSyncStatus.COMPLETED)
    failed = await sync_job_repo.count_by_status(VoiceSyncStatus.FAILED)

    return SyncStatusResponse(
        has_running_job=has_running,
        running_jobs=running,
        pending_jobs=pending,
        completed_jobs=completed,
        failed_jobs=failed,
    )


@router.get("/sync/jobs", response_model=SyncJobListResponse)
async def list_sync_jobs(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    sync_job_repo: IVoiceSyncJobRepository = Depends(get_voice_sync_job_repo),
) -> SyncJobListResponse:
    """List voice sync jobs.

    T030: GET /api/v1/admin/voices/sync/jobs endpoint

    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        status: Optional status filter (pending, running, completed, failed)

    Returns:
        SyncJobListResponse with list of jobs
    """
    if status:
        try:
            status_enum = VoiceSyncStatus(status)
            jobs = await sync_job_repo.list_by_status(status_enum, limit=limit)
            total = await sync_job_repo.count_by_status(status_enum)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Must be one of: pending, running, completed, failed",
            ) from e
    else:
        jobs = await sync_job_repo.list_recent(limit=limit, offset=offset)
        # Count total jobs (approximate)
        total = len(jobs) + offset

    return SyncJobListResponse(
        jobs=[_job_to_response(job) for job in jobs],
        total=total,
    )


@router.get("/sync/jobs/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: str,
    sync_job_repo: IVoiceSyncJobRepository = Depends(get_voice_sync_job_repo),
) -> SyncJobResponse:
    """Get voice sync job details.

    T031: GET /api/v1/admin/voices/sync/jobs/{job_id} endpoint

    Args:
        job_id: Job UUID

    Returns:
        SyncJobResponse with job details

    Raises:
        HTTPException: If job not found
    """
    job = await sync_job_repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Sync job {job_id} not found")

    return _job_to_response(job)
