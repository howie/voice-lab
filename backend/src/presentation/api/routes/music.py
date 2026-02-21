"""Music Generation API Routes.

Feature: 012-music-generation
REST API endpoints for music generation (multi-provider).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.music import (
    MusicGenerationStatus as DomainStatus,
)
from src.domain.entities.music import (
    MusicGenerationType as DomainType,
)
from src.domain.services.music.service import (
    MusicGenerationService,
    MusicJobCancelError,
    QuotaExceededError,
)
from src.infrastructure.adapters.mureka.client import MurekaAPIError
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.music_job_repository_impl import MusicGenerationJobRepository
from src.infrastructure.providers.music.factory import MusicProviderFactory
from src.presentation.api.middleware.auth import CurrentUserDep
from src.presentation.api.schemas.music_schemas import (
    ExtendLyricsRequest,
    InstrumentalRequest,
    LyricsRequest,
    MusicGenerationStatus,
    MusicGenerationType,
    MusicJobListResponse,
    MusicJobResponse,
    MusicModel,
    MusicProviderEnum,
    QuotaStatusResponse,
    SongRequest,
)

router = APIRouter(prefix="/music", tags=["Music"])


def _get_music_service(
    session: AsyncSession,
    provider_name: str = "mureka",
) -> MusicGenerationService:
    """Create a MusicGenerationService instance with the given session and provider."""
    repo = MusicGenerationJobRepository(session)
    music_provider = MusicProviderFactory.create(provider_name)
    return MusicGenerationService(repository=repo, music_provider=music_provider)


def _to_response(job) -> MusicJobResponse:
    """Convert domain entity to response model."""
    return MusicJobResponse(
        id=job.id,
        type=MusicGenerationType(job.type.value),
        status=MusicGenerationStatus(job.status.value),
        provider=MusicProviderEnum(job.provider),
        prompt=job.prompt,
        lyrics=job.lyrics,
        model=MusicModel(job.model),
        result_url=job.result_url,
        cover_url=job.cover_url,
        generated_lyrics=job.generated_lyrics,
        duration_ms=job.duration_ms,
        title=job.title,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )


# =============================================================================
# Instrumental/BGM Generation
# =============================================================================


@router.post(
    "/instrumental",
    response_model=MusicJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交純音樂生成任務",
    description="根據情境描述生成純音樂/背景音樂（BGM）",
)
async def submit_instrumental(
    request: InstrumentalRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Submit an instrumental/BGM generation job.

    Args:
        request: Instrumental generation request
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created job response

    Raises:
        HTTPException: 429 if quota exceeded
    """
    service = _get_music_service(session, provider_name=request.provider.value)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await service.submit_instrumental(
            user_id=user_id,
            prompt=request.prompt,
            model=request.model.value,
            provider=request.provider.value,
        )
        await session.commit()
        return _to_response(job)

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": str(e),
                "details": {
                    "daily_used": e.quota_status.daily_used,
                    "daily_limit": e.quota_status.daily_limit,
                    "concurrent_jobs": e.quota_status.concurrent_jobs,
                    "max_concurrent_jobs": e.quota_status.max_concurrent_jobs,
                },
            },
        ) from e

    except MurekaAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "MUSIC_PROVIDER_ERROR",
                "message": str(e),
            },
        ) from e


# =============================================================================
# Song Generation
# =============================================================================


@router.post(
    "/song",
    response_model=MusicJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交歌曲生成任務",
    description="根據歌詞和風格描述生成完整歌曲（含人聲）",
)
async def submit_song(
    request: SongRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Submit a song generation job.

    Args:
        request: Song generation request
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created job response

    Raises:
        HTTPException: 400 if neither prompt nor lyrics provided
        HTTPException: 429 if quota exceeded
    """
    if not request.prompt and not request.lyrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": "Either prompt or lyrics must be provided",
            },
        )

    service = _get_music_service(session, provider_name=request.provider.value)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await service.submit_song(
            user_id=user_id,
            prompt=request.prompt,
            lyrics=request.lyrics,
            model=request.model.value,
            provider=request.provider.value,
        )
        await session.commit()
        return _to_response(job)

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": str(e),
            },
        ) from e


# =============================================================================
# Lyrics Generation
# =============================================================================


@router.post(
    "/lyrics",
    response_model=MusicJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交歌詞生成任務",
    description="根據主題描述生成結構化歌詞",
)
async def submit_lyrics(
    request: LyricsRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Submit a lyrics generation job.

    Args:
        request: Lyrics generation request
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created job response
    """
    service = _get_music_service(session, provider_name=request.provider.value)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await service.submit_lyrics(
            user_id=user_id,
            prompt=request.prompt,
            provider=request.provider.value,
        )
        await session.commit()
        return _to_response(job)

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": str(e),
            },
        ) from e


@router.post(
    "/lyrics/extend",
    response_model=MusicJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="延伸歌詞",
    description="延伸現有歌詞，增加新的段落",
)
async def extend_lyrics(
    request: ExtendLyricsRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Extend existing lyrics.

    Args:
        request: Extend lyrics request
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created job response
    """
    # For now, treat extend as a new lyrics job with the existing lyrics as context
    service = _get_music_service(session, provider_name=request.provider.value)
    user_id = uuid.UUID(current_user.id)

    prompt = f"延伸以下歌詞：\n{request.lyrics}"
    if request.prompt:
        prompt += f"\n\n延伸方向：{request.prompt}"

    try:
        job = await service.submit_lyrics(
            user_id=user_id,
            prompt=prompt,
            provider=request.provider.value,
        )
        await session.commit()
        return _to_response(job)

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": str(e),
            },
        ) from e


# =============================================================================
# Job Management
# =============================================================================


@router.get(
    "/jobs",
    response_model=MusicJobListResponse,
    summary="列出音樂生成任務",
    description="取得當前用戶的音樂生成任務列表",
)
async def list_jobs(
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[
        MusicGenerationStatus | None,
        Query(alias="status", description="篩選特定狀態的任務"),
    ] = None,
    type_filter: Annotated[
        MusicGenerationType | None,
        Query(alias="type", description="篩選特定類型的任務"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="每頁數量"),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0, description="分頁偏移"),
    ] = 0,
) -> MusicJobListResponse:
    """List music generation jobs for the current user.

    Args:
        current_user: Current authenticated user
        session: Database session
        status_filter: Optional status filter
        type_filter: Optional type filter
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip

    Returns:
        Paginated job list response
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    # Convert schema enums to domain enums
    domain_status = DomainStatus(status_filter.value) if status_filter else None
    domain_type = DomainType(type_filter.value) if type_filter else None

    jobs, total = await service.list_jobs(
        user_id=user_id,
        status=domain_status,
        job_type=domain_type,
        limit=limit,
        offset=offset,
    )

    return MusicJobListResponse(
        items=[_to_response(job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=MusicJobResponse,
    summary="查詢單一任務狀態",
    description="取得特定音樂生成任務的詳細資訊",
)
async def get_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Get job details by ID.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Job detail response

    Raises:
        HTTPException: 404 if job not found
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    job = await service.get_job(job_id, user_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return _to_response(job)


@router.get(
    "/jobs/{job_id}/download",
    summary="下載生成結果",
    description="下載已完成任務的音檔",
    responses={
        302: {"description": "Redirect to audio file URL"},
        400: {"description": "任務未完成"},
        404: {"description": "任務不存在"},
    },
)
async def download_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RedirectResponse:
    """Download audio file for a completed job.

    Redirects to the result URL.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Redirect to audio file URL

    Raises:
        HTTPException: 404 if job not found, 400 if not completed
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    job = await service.get_job(job_id, user_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job.status != DomainStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is not completed (status: {job.status.value})",
        )

    if not job.result_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} has no result URL",
        )

    return RedirectResponse(url=job.result_url, status_code=302)


@router.post(
    "/jobs/{job_id}/retry",
    response_model=MusicJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="重新提交失敗任務",
    description="以相同參數重新提交失敗的任務",
)
async def retry_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Retry a failed job.

    Args:
        job_id: Job ID to retry
        current_user: Current authenticated user
        session: Database session

    Returns:
        Reset job response

    Raises:
        HTTPException: 404 if job not found, 400 if cannot retry
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await service.retry_job(job_id, user_id)
        await session.commit()
        return _to_response(job)

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete(
    "/jobs/{job_id}",
    response_model=MusicJobResponse,
    summary="取消音樂生成任務",
    description="取消等待中或處理中的音樂生成任務",
)
async def cancel_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Cancel a pending or processing job.

    Args:
        job_id: Job ID to cancel
        current_user: Current authenticated user
        session: Database session

    Returns:
        Cancelled job response

    Raises:
        HTTPException: 404 if job not found, 409 if cannot cancel
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await service.cancel_job(job_id, user_id)
        await session.commit()
        return _to_response(job)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except MusicJobCancelError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CANNOT_CANCEL",
                "message": str(e),
                "status": e.status,
            },
        ) from e


@router.post(
    "/jobs/{job_id}/restart",
    response_model=MusicJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="重新建立音樂生成任務",
    description="以相同參數建立全新的音樂生成任務（原始任務保留不變）",
)
async def restart_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MusicJobResponse:
    """Restart a cancelled or exhausted-retry job by creating a new job.

    Args:
        job_id: Original job ID to restart from
        current_user: Current authenticated user
        session: Database session

    Returns:
        Newly created job response

    Raises:
        HTTPException: 404 if not found, 400 if cannot restart, 429 if quota exceeded
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await service.restart_job(job_id, user_id)
        await session.commit()
        return _to_response(job)

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": str(e),
            },
        ) from e


# =============================================================================
# Quota Management
# =============================================================================


@router.get(
    "/quota",
    response_model=QuotaStatusResponse,
    summary="查詢配額使用狀況",
    description="取得當前用戶的配額使用統計",
)
async def get_quota(
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> QuotaStatusResponse:
    """Get user's quota status.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        Quota status response
    """
    service = _get_music_service(session)
    user_id = uuid.UUID(current_user.id)

    quota = await service.get_quota_status(user_id)

    return QuotaStatusResponse(
        daily_used=quota.daily_used,
        daily_limit=quota.daily_limit,
        monthly_used=quota.monthly_used,
        monthly_limit=quota.monthly_limit,
        concurrent_jobs=quota.concurrent_jobs,
        max_concurrent_jobs=quota.max_concurrent_jobs,
        can_submit=quota.can_submit,
    )
