"""DJ API Routes for Magic DJ Controller.

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

This module provides REST API endpoints for DJ preset and track management.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.dj_service import (
    AudioUploadError,
    DJService,
    PresetAccessDeniedError,
    PresetLimitExceededError,
    PresetNameExistsError,
    PresetNotFoundError,
    TrackLimitExceededError,
    TrackNotFoundError,
)
from src.domain.entities.dj import DJPreset, DJSettings, DJTrack
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.dj_repository_impl import DJRepositoryImpl
from src.infrastructure.storage.dj_audio_storage import DJAudioStorageService
from src.presentation.api.middleware.auth import CurrentUserDep
from src.presentation.api.schemas.dj import (
    AudioUploadResponse,
    CreatePresetRequest,
    CreateTrackRequest,
    ExportResponse,
    ImportRequest,
    PresetDetailResponse,
    PresetListResponse,
    PresetResponse,
    ReorderTracksRequest,
    TrackListResponse,
    TrackResponse,
    UpdatePresetRequest,
    UpdateTrackRequest,
)

router = APIRouter(prefix="/dj", tags=["DJ"])

# Global audio storage instance
_audio_storage: DJAudioStorageService | None = None


def _get_audio_storage() -> DJAudioStorageService:
    """Get or create the audio storage instance."""
    global _audio_storage
    if _audio_storage is None:
        # Use local storage for development, GCS for production
        _audio_storage = DJAudioStorageService(
            base_path="storage",
            gcs_bucket_name=None,  # Set via environment variable in production
        )
    return _audio_storage


def _get_dj_service(session: AsyncSession) -> DJService:
    """Create a DJService instance with the given session."""
    dj_repo = DJRepositoryImpl(session)
    audio_storage = _get_audio_storage()
    return DJService(dj_repo, audio_storage)


def _preset_to_response(preset: DJPreset) -> PresetResponse:
    """Convert DJPreset entity to response schema."""
    from src.presentation.api.schemas.dj import DJSettingsSchema

    return PresetResponse(
        id=preset.id,
        user_id=preset.user_id,
        name=preset.name,
        description=preset.description,
        is_default=preset.is_default,
        settings=DJSettingsSchema(
            master_volume=preset.settings.master_volume,
            time_warning_at=preset.settings.time_warning_at,
            session_time_limit=preset.settings.session_time_limit,
            ai_response_timeout=preset.settings.ai_response_timeout,
            auto_play_filler=preset.settings.auto_play_filler,
        ),
        created_at=preset.created_at,
        updated_at=preset.updated_at,
    )


def _track_to_response(track: DJTrack, audio_url: str | None = None) -> TrackResponse:
    """Convert DJTrack entity to response schema."""

    return TrackResponse(
        id=track.id,
        preset_id=track.preset_id,
        name=track.name,
        type=track.type,
        source=track.source,
        hotkey=track.hotkey,
        loop=track.loop,
        sort_order=track.sort_order,
        text_content=track.text_content,
        tts_provider=track.tts_provider,
        tts_voice_id=track.tts_voice_id,
        tts_speed=track.tts_speed,
        original_filename=track.original_filename,
        audio_url=audio_url,
        duration_ms=track.duration_ms,
        file_size_bytes=track.file_size_bytes,
        content_type=track.content_type,
        volume=track.volume,
        created_at=track.created_at,
        updated_at=track.updated_at,
    )


# =============================================================================
# Preset Endpoints
# =============================================================================


@router.get(
    "/presets",
    response_model=PresetListResponse,
    summary="列出所有預設組",
    description="取得目前使用者的所有 DJ 預設組。",
)
async def list_presets(
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PresetListResponse:
    """List all presets for the current user."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    presets = await dj_service.list_presets(user_id)

    return PresetListResponse(
        items=[_preset_to_response(p) for p in presets],
        total=len(presets),
    )


@router.post(
    "/presets",
    response_model=PresetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立預設組",
    description="建立新的 DJ 預設組。",
)
async def create_preset(
    request: CreatePresetRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PresetResponse:
    """Create a new preset."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    settings = DJSettings(
        master_volume=request.settings.master_volume,
        time_warning_at=request.settings.time_warning_at,
        session_time_limit=request.settings.session_time_limit,
        ai_response_timeout=request.settings.ai_response_timeout,
        auto_play_filler=request.settings.auto_play_filler,
    )

    try:
        preset = await dj_service.create_preset(
            user_id=user_id,
            name=request.name,
            description=request.description,
            is_default=request.is_default,
            settings=settings,
        )
        await session.commit()
        return _preset_to_response(preset)

    except PresetLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        ) from None
    except PresetNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None


@router.get(
    "/presets/{preset_id}",
    response_model=PresetDetailResponse,
    summary="取得預設組詳情",
    description="取得預設組詳情，包含所有音軌。",
)
async def get_preset(
    preset_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PresetDetailResponse:
    """Get preset details with tracks."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    try:
        preset = await dj_service.get_preset(preset_id, user_id)
        tracks = await dj_service.list_tracks(preset_id, user_id)

        # Generate audio URLs for tracks
        track_responses = []
        for track in tracks:
            audio_url = None
            if track.audio_storage_path:
                audio_url = audio_storage.get_signed_url(track.audio_storage_path)
            track_responses.append(_track_to_response(track, audio_url))

        response = _preset_to_response(preset)
        return PresetDetailResponse(
            **response.model_dump(),
            tracks=track_responses,
        )

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.put(
    "/presets/{preset_id}",
    response_model=PresetResponse,
    summary="更新預設組",
    description="更新預設組設定。",
)
async def update_preset(
    preset_id: uuid.UUID,
    request: UpdatePresetRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PresetResponse:
    """Update a preset."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    settings = None
    if request.settings is not None:
        settings = DJSettings(
            master_volume=request.settings.master_volume,
            time_warning_at=request.settings.time_warning_at,
            session_time_limit=request.settings.session_time_limit,
            ai_response_timeout=request.settings.ai_response_timeout,
            auto_play_filler=request.settings.auto_play_filler,
        )

    try:
        preset = await dj_service.update_preset(
            preset_id=preset_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
            is_default=request.is_default,
            settings=settings,
        )
        await session.commit()
        return _preset_to_response(preset)

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None
    except PresetNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None


@router.delete(
    "/presets/{preset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除預設組",
    description="刪除預設組及其所有音軌。",
)
async def delete_preset(
    preset_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a preset and all its tracks."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        await dj_service.delete_preset(preset_id, user_id)
        await session.commit()

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.post(
    "/presets/{preset_id}/clone",
    response_model=PresetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="複製預設組",
    description="複製現有預設組到新的預設組。",
)
async def clone_preset(
    preset_id: uuid.UUID,
    new_name: str,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PresetResponse:
    """Clone a preset with a new name."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        preset = await dj_service.clone_preset(preset_id, user_id, new_name)
        await session.commit()
        return _preset_to_response(preset)

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None
    except PresetLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        ) from None
    except PresetNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None


# =============================================================================
# Track Endpoints
# =============================================================================


@router.get(
    "/presets/{preset_id}/tracks",
    response_model=TrackListResponse,
    summary="列出音軌",
    description="取得預設組的所有音軌。",
)
async def list_tracks(
    preset_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackListResponse:
    """List all tracks for a preset."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    try:
        tracks = await dj_service.list_tracks(preset_id, user_id)

        track_responses = []
        for track in tracks:
            audio_url = None
            if track.audio_storage_path:
                audio_url = audio_storage.get_signed_url(track.audio_storage_path)
            track_responses.append(_track_to_response(track, audio_url))

        return TrackListResponse(
            items=track_responses,
            total=len(tracks),
        )

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.post(
    "/presets/{preset_id}/tracks",
    response_model=TrackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立音軌",
    description="在預設組中建立新音軌。",
)
async def create_track(
    preset_id: uuid.UUID,
    request: CreateTrackRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackResponse:
    """Create a new track."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        track = await dj_service.create_track(
            preset_id=preset_id,
            user_id=user_id,
            name=request.name,
            track_type=request.type,
            source=request.source,
            hotkey=request.hotkey,
            loop=request.loop,
            sort_order=request.sort_order,
            text_content=request.text_content,
            tts_provider=request.tts_provider,
            tts_voice_id=request.tts_voice_id,
            tts_speed=request.tts_speed,
            volume=request.volume,
        )
        await session.commit()
        return _track_to_response(track)

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None
    except TrackLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        ) from None


@router.get(
    "/presets/{preset_id}/tracks/{track_id}",
    response_model=TrackResponse,
    summary="取得音軌詳情",
    description="取得單一音軌詳情。",
)
async def get_track(
    preset_id: uuid.UUID,
    track_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackResponse:
    """Get track details."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    try:
        track = await dj_service.get_track(track_id, user_id)

        if track.preset_id != preset_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track {track_id} not found in preset {preset_id}",
            )

        audio_url = None
        if track.audio_storage_path:
            audio_url = audio_storage.get_signed_url(track.audio_storage_path)

        return _track_to_response(track, audio_url)

    except TrackNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.put(
    "/presets/{preset_id}/tracks/{track_id}",
    response_model=TrackResponse,
    summary="更新音軌",
    description="更新音軌設定。",
)
async def update_track(
    preset_id: uuid.UUID,
    track_id: uuid.UUID,
    request: UpdateTrackRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackResponse:
    """Update a track."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    try:
        # Verify track belongs to preset
        track = await dj_service.get_track(track_id, user_id)
        if track.preset_id != preset_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track {track_id} not found in preset {preset_id}",
            )

        track = await dj_service.update_track(
            track_id=track_id,
            user_id=user_id,
            name=request.name,
            track_type=request.type,
            hotkey=request.hotkey,
            loop=request.loop,
            sort_order=request.sort_order,
            text_content=request.text_content,
            tts_provider=request.tts_provider,
            tts_voice_id=request.tts_voice_id,
            tts_speed=request.tts_speed,
            volume=request.volume,
        )
        await session.commit()

        audio_url = None
        if track.audio_storage_path:
            audio_url = audio_storage.get_signed_url(track.audio_storage_path)

        return _track_to_response(track, audio_url)

    except TrackNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.delete(
    "/presets/{preset_id}/tracks/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除音軌",
    description="刪除音軌及其音檔。",
)
async def delete_track(
    preset_id: uuid.UUID,
    track_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a track."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        # Verify track belongs to preset
        track = await dj_service.get_track(track_id, user_id)
        if track.preset_id != preset_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track {track_id} not found in preset {preset_id}",
            )

        await dj_service.delete_track(track_id, user_id)
        await session.commit()

    except TrackNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.put(
    "/presets/{preset_id}/tracks/reorder",
    response_model=TrackListResponse,
    summary="重新排序音軌",
    description="根據提供的 ID 順序重新排序音軌。",
)
async def reorder_tracks(
    preset_id: uuid.UUID,
    request: ReorderTracksRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackListResponse:
    """Reorder tracks in a preset."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    try:
        tracks = await dj_service.reorder_tracks(preset_id, user_id, request.track_ids)
        await session.commit()

        track_responses = []
        for track in tracks:
            audio_url = None
            if track.audio_storage_path:
                audio_url = audio_storage.get_signed_url(track.audio_storage_path)
            track_responses.append(_track_to_response(track, audio_url))

        return TrackListResponse(
            items=track_responses,
            total=len(tracks),
        )

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


# =============================================================================
# Audio Endpoints
# =============================================================================


@router.post(
    "/audio/upload",
    response_model=AudioUploadResponse,
    summary="上傳音檔",
    description="上傳音檔到指定音軌。",
)
async def upload_audio(
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    file: UploadFile = File(...),
    track_id: uuid.UUID = Form(...),
) -> AudioUploadResponse:
    """Upload audio file for a track."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    # Validate file type
    allowed_types = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/ogg",
        "audio/webm",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(allowed_types)}",
        )

    try:
        # Read file content
        audio_data = await file.read()

        audio_info = await dj_service.upload_audio(
            track_id=track_id,
            user_id=user_id,
            audio_data=audio_data,
            content_type=file.content_type or "audio/mpeg",
            original_filename=file.filename,
        )
        await session.commit()

        # Generate signed URL
        audio_url = audio_storage.get_signed_url(audio_info.storage_path) or ""

        return AudioUploadResponse(
            track_id=track_id,
            storage_path=audio_info.storage_path,
            audio_url=audio_url,
            duration_ms=audio_info.duration_ms,
            file_size_bytes=audio_info.file_size_bytes,
            content_type=audio_info.content_type,
        )

    except TrackNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None
    except AudioUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None


@router.get(
    "/audio/{track_id}",
    summary="取得音檔",
    description="重導向到音檔的 signed URL。",
)
async def get_audio(
    track_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RedirectResponse:
    """Get audio file (redirect to signed URL)."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        audio_url = await dj_service.get_audio_url(track_id, user_id)

        if audio_url is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audio for track {track_id}",
            )

        return RedirectResponse(url=audio_url)

    except TrackNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


@router.delete(
    "/audio/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除音檔",
    description="刪除音軌的音檔（不刪除音軌本身）。",
)
async def delete_audio(
    track_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete audio file for a track."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        await dj_service.delete_audio(track_id, user_id)
        await session.commit()

    except TrackNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None


# =============================================================================
# Import/Export Endpoints
# =============================================================================


@router.post(
    "/import",
    response_model=PresetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="從 localStorage 匯入",
    description="從 localStorage 格式匯入預設組和音軌。",
)
async def import_from_local_storage(
    request: ImportRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PresetResponse:
    """Import preset from localStorage format."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)

    try:
        preset = await dj_service.import_from_local_storage(
            user_id=user_id,
            preset_name=request.preset_name,
            data=request.data.model_dump(),
        )
        await session.commit()
        return _preset_to_response(preset)

    except PresetLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        ) from None
    except PresetNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from None


@router.get(
    "/export/{preset_id}",
    response_model=ExportResponse,
    summary="匯出預設組",
    description="匯出預設組為 JSON 格式。",
)
async def export_preset(
    preset_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExportResponse:
    """Export preset to JSON format."""
    dj_service = _get_dj_service(session)
    user_id = uuid.UUID(current_user.id)
    audio_storage = _get_audio_storage()

    try:
        preset = await dj_service.get_preset(preset_id, user_id)
        tracks = await dj_service.list_tracks(preset_id, user_id)

        track_responses = []
        for track in tracks:
            audio_url = None
            if track.audio_storage_path:
                audio_url = audio_storage.get_signed_url(track.audio_storage_path)
            track_responses.append(_track_to_response(track, audio_url))

        return ExportResponse(
            preset=_preset_to_response(preset),
            tracks=track_responses,
        )

    except PresetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        ) from None
    except PresetAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from None
