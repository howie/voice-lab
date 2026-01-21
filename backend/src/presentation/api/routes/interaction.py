"""Interaction API Routes.

T020: REST endpoints for interaction session management.
"""

import base64
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
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
