"""Interaction API Routes.

T020: REST endpoints for interaction session management.
"""

import base64
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.voice_interaction import (
    VoiceInteractionInput,
    VoiceInteractionUseCase,
)
from src.domain.entities import InteractionMode, SessionStatus
from src.domain.entities.audio import AudioData, AudioFormat
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.interaction_repository_impl import (
    SQLAlchemyInteractionRepository,
)
from src.infrastructure.persistence.scenario_template_repository_impl import (
    SQLAlchemyScenarioTemplateRepository,
)
from src.infrastructure.storage.audio_storage import AudioStorageService
from src.presentation.api.dependencies import get_voice_interaction_use_case
from src.presentation.schemas.interaction import (
    ConversationMessage,
    InteractionResponse,
    LatencyStatsResponse,
    ScenarioTemplateResponse,
    SessionListResponse,
    SessionResponse,
    TurnResponse,
)

router = APIRouter()


@router.post("/voice", response_model=InteractionResponse)
async def voice_interaction(
    audio: UploadFile = File(..., description="User audio input"),
    stt_provider: str = Form(..., description="STT provider"),
    llm_provider: str = Form(..., description="LLM provider"),
    tts_provider: str = Form(..., description="TTS provider"),
    voice_id: str = Form(..., description="TTS voice ID"),
    system_prompt: str = Form(default="", description="System prompt for LLM"),
    conversation_history: str = Form(default="[]", description="JSON array of previous messages"),
    language: str = Form(default="zh-TW", description="Language code"),
    max_response_tokens: int = Form(default=150, description="Max LLM response tokens"),
    use_case: VoiceInteractionUseCase = Depends(get_voice_interaction_use_case),
):
    """Process voice interaction: STT -> LLM -> TTS."""
    import json

    try:
        # Read audio data
        audio_bytes = await audio.read()
        audio_format = AudioFormat.WEBM  # Assume WebM from browser

        if audio.filename:
            if audio.filename.endswith(".wav"):
                audio_format = AudioFormat.WAV
            elif audio.filename.endswith(".mp3"):
                audio_format = AudioFormat.MP3

        audio_data = AudioData(
            data=audio_bytes,
            format=audio_format,
            sample_rate=16000,
        )

        # Parse conversation history
        try:
            history = json.loads(conversation_history)
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []

        input_data = VoiceInteractionInput(
            user_audio=audio_data,
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            tts_provider=tts_provider,
            voice_id=voice_id,
            system_prompt=system_prompt,
            conversation_history=history,
            language=language,
            max_response_tokens=max_response_tokens,
            user_id="anonymous",
        )

        output = await use_case.execute(input_data)

        return InteractionResponse(
            user_transcript=output.user_transcript,
            ai_response_text=output.ai_response_text,
            ai_response_audio_base64=base64.b64encode(output.ai_response_audio.data).decode(
                "utf-8"
            ),
            audio_format=output.ai_response_audio.format.value,
            stt_latency_ms=output.stt_latency_ms,
            llm_latency_ms=output.llm_latency_ms,
            tts_latency_ms=output.tts_latency_ms,
            total_latency_ms=output.total_latency_ms,
            updated_history=[
                ConversationMessage(role=m["role"], content=m["content"])
                for m in output.updated_history
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interaction failed: {str(e)}") from e


# =============================================================================
# Session Management Endpoints (Phase 4 - Interaction Module)
# =============================================================================


def _session_to_response(session) -> SessionResponse:
    """Convert domain entity to response schema."""
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        mode=session.mode.value,
        provider_config=session.provider_config,
        system_prompt=session.system_prompt,
        status=session.status.value,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _turn_to_response(turn) -> TurnResponse:
    """Convert domain entity to response schema."""
    return TurnResponse(
        id=turn.id,
        session_id=turn.session_id,
        turn_number=turn.turn_number,
        user_audio_path=turn.user_audio_path,
        user_transcript=turn.user_transcript,
        ai_response_text=turn.ai_response_text,
        ai_audio_path=turn.ai_audio_path,
        interrupted=turn.interrupted,
        started_at=turn.started_at,
        ended_at=turn.ended_at,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: UUID = Query(..., description="User ID to filter sessions"),
    mode: str | None = Query(None, description="Filter by mode: 'realtime' or 'cascade'"),
    status: str | None = Query(None, description="Filter by status"),
    start_date: datetime | None = Query(None, description="Filter sessions started after"),
    end_date: datetime | None = Query(None, description="Filter sessions started before"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db_session),
) -> SessionListResponse:
    """List interaction sessions for a user with optional filters."""
    repository = SQLAlchemyInteractionRepository(db)

    mode_enum = InteractionMode(mode) if mode else None
    status_enum = SessionStatus(status) if status else None

    sessions, total = await repository.list_sessions(
        user_id=user_id,
        mode=mode_enum,
        status=status_enum,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Get details of a specific interaction session."""
    repository = SQLAlchemyInteractionRepository(db)
    session = await repository.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _session_to_response(session)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Delete an interaction session and its associated audio files."""
    repository = SQLAlchemyInteractionRepository(db)
    audio_storage = AudioStorageService()

    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete audio files
    await audio_storage.delete_session_audio(session_id)

    # Delete from database
    await repository.delete_session(session_id)
    await db.commit()

    return {"status": "deleted", "session_id": str(session_id)}


@router.get("/sessions/{session_id}/turns", response_model=list[TurnResponse])
async def list_session_turns(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[TurnResponse]:
    """List all conversation turns for a session."""
    repository = SQLAlchemyInteractionRepository(db)

    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turns = await repository.list_turns(session_id)
    return [_turn_to_response(t) for t in turns]


@router.get("/sessions/{session_id}/turns/{turn_id}/audio")
async def get_turn_audio(
    session_id: UUID,
    turn_id: UUID,
    audio_type: str = Query("ai", description="Audio type: 'user' or 'ai'"),
    db: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    """Get audio file for a specific turn.

    T093 [US6]: GET /api/v1/interaction/sessions/{id}/turns/{turn_id}/audio

    Args:
        session_id: Session UUID
        turn_id: Turn UUID
        audio_type: 'user' for user's recording or 'ai' for AI's response

    Returns:
        Audio file as streaming response
    """
    repository = SQLAlchemyInteractionRepository(db)
    audio_storage = AudioStorageService()

    # Verify session exists
    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the turn
    turn = await repository.get_turn(turn_id)
    if not turn or turn.session_id != session_id:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Get the appropriate audio path
    if audio_type == "user":
        audio_path = turn.user_audio_path
    elif audio_type == "ai":
        audio_path = turn.ai_audio_path
    else:
        raise HTTPException(status_code=400, detail="audio_type must be 'user' or 'ai'")

    if not audio_path:
        raise HTTPException(
            status_code=404, detail=f"No {audio_type} audio available for this turn"
        )

    # Get the full file path
    full_path = await audio_storage.get_audio_path(audio_path)
    if not full_path or not full_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Determine media type based on file extension
    media_type = "audio/mpeg"  # Default for mp3
    if audio_path.endswith(".webm"):
        media_type = "audio/webm"
    elif audio_path.endswith(".wav"):
        media_type = "audio/wav"
    elif audio_path.endswith(".pcm"):
        media_type = "audio/pcm"

    return FileResponse(
        path=full_path,
        media_type=media_type,
        filename=full_path.name,
    )


@router.get("/sessions/{session_id}/latency", response_model=LatencyStatsResponse)
async def get_session_latency_stats(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> LatencyStatsResponse:
    """Get latency statistics for a session."""
    repository = SQLAlchemyInteractionRepository(db)

    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = await repository.get_session_latency_stats(session_id)

    return LatencyStatsResponse(
        total_turns=stats["total_turns"],
        avg_total_ms=stats["avg_total_ms"],
        min_total_ms=stats["min_total_ms"],
        max_total_ms=stats["max_total_ms"],
        p95_total_ms=stats["p95_total_ms"],
        avg_stt_ms=stats["avg_stt_ms"],
        avg_llm_ttft_ms=stats["avg_llm_ttft_ms"],
        avg_tts_ttfb_ms=stats["avg_tts_ttfb_ms"],
    )


# =============================================================================
# Scenario Templates Endpoints (US4 - Role/Scenario Configuration)
# =============================================================================


def _template_to_response(template) -> ScenarioTemplateResponse:
    """Convert domain entity to response schema."""
    return ScenarioTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        user_role=template.user_role,
        ai_role=template.ai_role,
        scenario_context=template.scenario_context,
        category=template.category,
        is_default=template.is_default,
    )


@router.get("/templates", response_model=list[ScenarioTemplateResponse])
async def list_scenario_templates(
    category: str | None = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScenarioTemplateResponse]:
    """List scenario templates with optional category filter.

    T071 [US4]: GET /api/v1/interaction/templates
    """
    repository = SQLAlchemyScenarioTemplateRepository(db)

    if category:
        templates = await repository.list_by_category(category)
    else:
        templates = await repository.list_all()

    return [_template_to_response(t) for t in templates]


@router.get("/templates/{template_id}", response_model=ScenarioTemplateResponse)
async def get_scenario_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ScenarioTemplateResponse:
    """Get a specific scenario template by ID.

    T072 [US4]: GET /api/v1/interaction/templates/{id}
    """
    repository = SQLAlchemyScenarioTemplateRepository(db)
    template = await repository.get_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return _template_to_response(template)


# =============================================================================
# Providers Endpoints (US2 - Mode Selection)
# =============================================================================


@router.get("/providers")
async def list_providers() -> dict:
    """List available providers for cascade mode.

    T051 [US2]: GET /api/v1/interaction/providers
    Returns available STT, LLM, and TTS providers with metadata.
    """
    from src.domain.services.interaction.cascade_mode_factory import CascadeModeFactory

    provider_info = CascadeModeFactory.get_provider_info()

    return {
        "stt_providers": provider_info["stt"],
        "llm_providers": provider_info["llm"],
        "tts_providers": provider_info["tts"],
    }


# =============================================================================
# Metrics Endpoint (T104-T105 - Observability)
# =============================================================================


@router.get("/metrics")
async def get_metrics() -> dict:
    """Get interaction module metrics.

    T104 [Phase 9]: API call counter metrics per provider.
    T105 [Phase 9]: Error rate tracking.

    Returns provider call counts, error rates, and latency statistics.
    """
    from src.infrastructure.logging import get_interaction_metrics

    metrics = get_interaction_metrics()
    return metrics.get_all_metrics()


# =============================================================================
# V2V Feature Flags Endpoint (Performance Optimization)
# =============================================================================


@router.get("/v2v/feature-flags")
async def get_v2v_feature_flags() -> dict:
    """Get V2V performance feature flags.

    Returns current state of all V2V optimization toggles for A/B testing.
    These can be overridden per-session via WebSocket config message.
    """
    from src.config import get_settings

    settings = get_settings()

    return {
        "feature_flags": {
            "lightweight_mode": {
                "enabled": settings.v2v_lightweight_mode,
                "description": "Skip sync audio storage for lower latency",
                "trade_off": "Audio not saved in real-time, need batch upload after session",
            },
            "ws_compression": {
                "enabled": settings.v2v_ws_compression,
                "description": "WebSocket permessage-deflate compression",
                "trade_off": "Lower bandwidth vs higher CPU usage",
            },
            "batch_audio_upload": {
                "enabled": settings.v2v_batch_audio_upload,
                "description": "Buffer audio and upload after session ends",
                "trade_off": "No real-time audio backup vs lower latency",
            },
            "skip_latency_tracking": {
                "enabled": settings.v2v_skip_latency_tracking,
                "description": "Disable detailed latency metrics collection",
                "trade_off": "No latency metrics vs lower overhead",
            },
        },
        "gemini_config": {
            "model": settings.gemini_live_model,
            "available_models": [
                "gemini-2.0-flash-exp",
                "gemini-2.5-flash-preview-native-audio-dialog",
            ],
        },
    }


# =============================================================================
# Batch Audio Upload Endpoint (V2V Performance Optimization)
# =============================================================================


@router.post("/sessions/{session_id}/audio/batch")
async def batch_upload_audio(
    session_id: UUID,
    audio: UploadFile = File(..., description="Audio file (WebM/PCM)"),
    turn_numbers: str = Form(..., description="Comma-separated turn numbers for this audio"),
    audio_type: str = Form("user", description="Audio type: 'user' or 'ai'"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Batch upload audio for a session after it ends.

    This endpoint is used when lightweight_mode is enabled and audio
    is buffered on the client side instead of being streamed in real-time.

    Args:
        session_id: Session UUID
        audio: Audio file (WebM or PCM format)
        turn_numbers: Comma-separated list of turn numbers this audio covers
        audio_type: 'user' for user's recording or 'ai' for AI's response

    Returns:
        Upload status and saved file path
    """
    repository = SQLAlchemyInteractionRepository(db)
    audio_storage = AudioStorageService()

    # Verify session exists
    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Parse turn numbers
    try:
        turns = [int(t.strip()) for t in turn_numbers.split(",") if t.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid turn_numbers format") from None

    if not turns:
        raise HTTPException(status_code=400, detail="At least one turn number required")

    # Read audio data
    audio_bytes = await audio.read()

    # Determine format from filename or content type
    audio_format = "webm"
    if audio.filename:
        if audio.filename.endswith(".pcm"):
            audio_format = "pcm"
        elif audio.filename.endswith(".wav"):
            audio_format = "wav"
        elif audio.filename.endswith(".mp3"):
            audio_format = "mp3"

    # Store the audio file
    saved_paths = []
    for turn_number in turns:
        if audio_type == "user":
            path = await audio_storage.save_user_audio_batch(
                session_id=session_id,
                turn_number=turn_number,
                audio_data=audio_bytes,
                format=audio_format,
            )
        else:
            path = await audio_storage.save_ai_audio_batch(
                session_id=session_id,
                turn_number=turn_number,
                audio_data=audio_bytes,
                format=audio_format,
            )
        saved_paths.append(str(path))

        # Update turn record with audio path
        turn = await repository.get_turn_by_session_and_number(session_id, turn_number)
        if turn:
            if audio_type == "user":
                turn.user_audio_path = str(path)
            else:
                turn.ai_audio_path = str(path)
            await repository.update_turn(turn)

    await db.commit()

    return {
        "status": "uploaded",
        "session_id": str(session_id),
        "turns": turns,
        "audio_type": audio_type,
        "paths": saved_paths,
        "size_bytes": len(audio_bytes),
    }
