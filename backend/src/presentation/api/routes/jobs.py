"""Jobs API Routes for async job management.

Feature: 007-async-job-mgmt
This module provides REST API endpoints for async TTS synthesis job management.
"""

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.job_service import (
    JobCancelError,
    JobLimitExceededError,
    JobNotFoundError,
    JobService,
)
from src.domain.entities.job import JobStatus, JobType
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.job_repository_impl import JobRepositoryImpl
from src.infrastructure.persistence.models import AudioFileModel
from src.infrastructure.storage.local_storage import LocalStorage
from src.presentation.api.middleware.auth import CurrentUserDep
from src.presentation.api.schemas.job_schemas import (
    CreateJobRequest,
    JobDetailResponse,
    JobListResponse,
    JobResponse,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _get_job_service(session: AsyncSession) -> JobService:
    """Create a JobService instance with the given session."""
    job_repo = JobRepositoryImpl(session)
    return JobService(job_repo)


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交 TTS 合成工作",
    description="建立一個新的背景 TTS 合成工作。",
)
async def create_job(
    request: CreateJobRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobResponse:
    """Create a new TTS synthesis job.

    Args:
        request: Job creation request
        user_id: Current user ID
        session: Database session

    Returns:
        Created job response

    Raises:
        HTTPException: 429 if concurrent job limit exceeded
    """
    job_service = _get_job_service(session)

    # Build input params from request
    input_params = {
        "provider": request.provider,
        "turns": [turn.model_dump() for turn in request.turns],
        "voice_assignments": [va.model_dump() for va in request.voice_assignments],
        "language": request.language,
        "output_format": request.output_format,
        "gap_ms": request.gap_ms,
        "crossfade_ms": request.crossfade_ms,
    }

    user_id = uuid.UUID(current_user.id)

    try:
        job = await job_service.create_job(
            user_id=user_id,
            provider=request.provider,
            input_params=input_params,
            job_type=JobType.MULTI_ROLE_TTS,
        )
        await session.commit()

        return JobResponse(
            id=job.id,
            status=job.status,
            job_type=job.job_type,
            provider=job.provider,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    except JobLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "JOB_LIMIT_EXCEEDED",
                "message": f"已達並發上限，請等待現有工作完成 ({e.current_count}/{e.max_count})",
            },
        ) from e


@router.get(
    "",
    response_model=JobListResponse,
    summary="列出所有工作",
    description="取得使用者的所有工作列表，支援依狀態篩選和分頁。",
)
async def list_jobs(
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[
        JobStatus | None,
        Query(alias="status", description="依狀態篩選"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="每頁筆數"),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0, description="跳過筆數"),
    ] = 0,
) -> JobListResponse:
    """List jobs for the current user.

    Args:
        current_user: Current authenticated user
        session: Database session
        status_filter: Optional status filter
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip

    Returns:
        Paginated job list response
    """
    job_service = _get_job_service(session)
    user_id = uuid.UUID(current_user.id)

    jobs, total = await job_service.list_jobs(
        user_id=user_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return JobListResponse(
        items=[
            JobResponse(
                id=job.id,
                status=job.status,
                job_type=job.job_type,
                provider=job.provider,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
            )
            for job in jobs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="取得工作詳情",
    description="取得單一工作的詳細狀態和結果。",
)
async def get_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobDetailResponse:
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
    job_service = _get_job_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await job_service.get_job(job_id, user_id)

        return JobDetailResponse(
            id=job.id,
            status=job.status,
            job_type=job.job_type,
            provider=job.provider,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            input_params=job.input_params,
            result_metadata=job.result_metadata,
            audio_file_id=job.audio_file_id,
            error_message=job.error_message,
            retry_count=job.retry_count,
        )

    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        ) from e


@router.delete(
    "/{job_id}",
    response_model=JobResponse,
    summary="取消工作",
    description="取消狀態為 pending 的工作。",
)
async def cancel_job(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobResponse:
    """Cancel a pending job.

    Args:
        job_id: Job ID to cancel
        current_user: Current authenticated user
        session: Database session

    Returns:
        Cancelled job response

    Raises:
        HTTPException: 404 if job not found, 409 if cannot cancel
    """
    job_service = _get_job_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await job_service.cancel_job(job_id, user_id)
        await session.commit()

        return JobResponse(
            id=job.id,
            status=job.status,
            job_type=job.job_type,
            provider=job.provider,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        ) from e

    except JobCancelError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job in {e.status.value} status",
        ) from e


# =============================================================================
# T049-T050: Download endpoint for completed job audio
# =============================================================================


async def get_audio_file_content(
    audio_file_id: uuid.UUID,
    session: AsyncSession,
) -> tuple[bytes, str, str]:
    """Get audio file content from storage.

    Args:
        audio_file_id: ID of the audio file
        session: Database session

    Returns:
        Tuple of (content, content_type, filename)

    Raises:
        HTTPException: 404 if audio file not found
    """
    # Get audio file record
    result = await session.execute(select(AudioFileModel).where(AudioFileModel.id == audio_file_id))
    audio_file = result.scalar_one_or_none()

    if audio_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found",
        )

    # Get storage and read file
    storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
    storage = LocalStorage(base_path=storage_path)

    try:
        content = await storage.download(audio_file.storage_path)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found in storage",
        ) from e

    # Determine content type from format
    content_type_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
    }
    content_type = content_type_map.get(audio_file.format, "application/octet-stream")

    return content, content_type, audio_file.filename


@router.get(
    "/{job_id}/download",
    summary="下載完成的音檔",
    description="下載已完成工作的合成音檔。",
    responses={
        200: {
            "content": {"audio/mpeg": {}, "audio/wav": {}},
            "description": "Audio file stream",
        },
        404: {"description": "Job not found or not completed"},
    },
)
async def download_job_audio(
    job_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """Download audio file for a completed job.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Audio file as streaming response

    Raises:
        HTTPException: 404 if job not found, not owned by user,
                       not completed, or has no audio file
    """
    job_service = _get_job_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        job = await job_service.get_job(job_id, user_id)
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        ) from e

    # Check if job is completed
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} is not completed (status: {job.status.value})",
        )

    # Check if job has audio file
    if job.audio_file_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} has no audio file",
        )

    # Get audio file content
    content, content_type, filename = await get_audio_file_content(job.audio_file_id, session)

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )
