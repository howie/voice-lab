"""StoryPal REST API routes.

Feature: StoryPal — AI Interactive Story Companion

Endpoints for managing story templates and sessions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.story import (
    StorySessionStatus,
)
from src.domain.services.story.templates import get_default_templates
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.models import (
    StorySessionModel,
    StoryTemplateModel,
)
from src.presentation.api.middleware.auth import CurrentUserDep
from src.presentation.api.schemas.story_schemas import (
    CreateStorySessionRequest,
    SceneInfoSchema,
    StoryCharacterSchema,
    StorySessionListResponse,
    StorySessionResponse,
    StoryTemplateListResponse,
    StoryTemplateResponse,
    StoryTurnResponse,
)

router = APIRouter(prefix="/story", tags=["StoryPal"])


# =============================================================================
# Helpers
# =============================================================================


def _template_entity_to_response(t: Any) -> StoryTemplateResponse:
    """Convert a StoryTemplate entity to response schema."""
    return StoryTemplateResponse(
        id=str(t.id),
        name=t.name,
        description=t.description,
        category=t.category if isinstance(t.category, str) else t.category.value,
        target_age_min=t.target_age_min,
        target_age_max=t.target_age_max,
        language=t.language,
        characters=[
            StoryCharacterSchema(
                name=c.name,
                description=c.description,
                voice_provider=c.voice_provider,
                voice_id=c.voice_id,
                voice_settings=c.voice_settings,
                emotion=c.emotion,
            )
            for c in t.characters
        ],
        scenes=[
            SceneInfoSchema(
                name=s.name,
                description=s.description,
                bgm_prompt=s.bgm_prompt,
                mood=s.mood,
            )
            for s in t.scenes
        ],
        opening_prompt=t.opening_prompt,
        system_prompt=t.system_prompt,
        is_default=t.is_default,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _db_template_to_response(m: StoryTemplateModel) -> StoryTemplateResponse:
    """Convert DB model to response."""
    characters = [StoryCharacterSchema(**c) for c in (m.characters or [])]
    scenes = [SceneInfoSchema(**s) for s in (m.scenes or [])]
    return StoryTemplateResponse(
        id=str(m.id),
        name=m.name,
        description=m.description,
        category=m.category,
        target_age_min=m.target_age_min,
        target_age_max=m.target_age_max,
        language=m.language,
        characters=characters,
        scenes=scenes,
        opening_prompt=m.opening_prompt,
        system_prompt=m.system_prompt,
        is_default=m.is_default,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _session_to_response(
    m: StorySessionModel,
    include_turns: bool = False,
) -> StorySessionResponse:
    """Convert DB session model to response."""
    turns = None
    if include_turns and m.turns:
        turns = [
            StoryTurnResponse(
                id=str(t.id),
                session_id=str(t.session_id),
                turn_number=t.turn_number,
                turn_type=t.turn_type,
                character_name=t.character_name,
                content=t.content,
                audio_path=t.audio_path,
                choice_options=t.choice_options,
                child_choice=t.child_choice,
                bgm_scene=t.bgm_scene,
                created_at=t.created_at,
            )
            for t in sorted(m.turns, key=lambda x: x.turn_number)
        ]

    return StorySessionResponse(
        id=str(m.id),
        user_id=str(m.user_id),
        template_id=str(m.template_id) if m.template_id else None,
        title=m.title,
        language=m.language,
        status=m.status,
        story_state=m.story_state or {},
        characters_config=[StoryCharacterSchema(**c) for c in (m.characters_config or [])],
        interaction_session_id=str(m.interaction_session_id) if m.interaction_session_id else None,
        current_scene=None,
        started_at=m.started_at,
        ended_at=m.ended_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        turns=turns,
    )


# =============================================================================
# Template Endpoints
# =============================================================================


@router.get(
    "/templates",
    response_model=StoryTemplateListResponse,
    summary="取得故事範本列表",
)
async def list_templates(
    _current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None, description="Filter by category"),
    language: str | None = Query(None, description="Filter by language"),
) -> StoryTemplateListResponse:
    """List available story templates (defaults + user-created)."""
    # Start with hardcoded defaults
    defaults = get_default_templates()
    templates = [_template_entity_to_response(t) for t in defaults]

    # Add DB-stored templates
    stmt = select(StoryTemplateModel)
    if category:
        stmt = stmt.where(StoryTemplateModel.category == category)
    if language:
        stmt = stmt.where(StoryTemplateModel.language == language)
    result = await session.execute(stmt)
    db_templates = result.scalars().all()
    templates.extend(_db_template_to_response(m) for m in db_templates)

    # Apply category filter to defaults too
    if category:
        templates = [t for t in templates if t.category == category]
    if language:
        templates = [t for t in templates if t.language == language]

    return StoryTemplateListResponse(templates=templates, total=len(templates))


@router.get(
    "/templates/{template_id}",
    response_model=StoryTemplateResponse,
    summary="取得故事範本詳情",
)
async def get_template(
    template_id: str,
    _current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StoryTemplateResponse:
    """Get a specific story template by ID."""
    # Check defaults first
    for t in get_default_templates():
        if str(t.id) == template_id:
            return _template_entity_to_response(t)

    # Check DB
    result = await session.execute(
        select(StoryTemplateModel).where(StoryTemplateModel.id == uuid.UUID(template_id))
    )
    db_template = result.scalar_one_or_none()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return _db_template_to_response(db_template)


# =============================================================================
# Session Endpoints
# =============================================================================


@router.post(
    "/sessions",
    response_model=StorySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立新故事",
)
async def create_session(
    request: CreateStorySessionRequest,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StorySessionResponse:
    """Start a new interactive story session."""
    user_id = uuid.UUID(current_user.id)

    # Resolve template
    template_id = None
    title = request.title or "新故事"
    characters_config: list[dict[str, Any]] = []

    if request.template_id:
        template_id = uuid.UUID(request.template_id)
        # Find template for title and characters
        for t in get_default_templates():
            if str(t.id) == request.template_id:
                title = request.title or t.name
                characters_config = [
                    StoryCharacterSchema(
                        name=c.name,
                        description=c.description,
                        voice_provider=c.voice_provider,
                        voice_id=c.voice_id,
                        voice_settings=c.voice_settings,
                        emotion=c.emotion,
                    ).model_dump()
                    for c in t.characters
                ]
                break

    # Override with request characters if provided
    if request.characters_config:
        characters_config = [c.model_dump() for c in request.characters_config]

    now = datetime.now(UTC)
    db_session = StorySessionModel(
        id=uuid.uuid4(),
        user_id=user_id,
        template_id=template_id,
        title=title,
        language=request.language,
        status=StorySessionStatus.ACTIVE.value,
        story_state={},
        characters_config=characters_config,
        started_at=now,
    )
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)

    return _session_to_response(db_session)


@router.get(
    "/sessions",
    response_model=StorySessionListResponse,
    summary="取得故事列表",
)
async def list_sessions(
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    session_status: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> StorySessionListResponse:
    """List story sessions for the current user."""
    user_id = uuid.UUID(current_user.id)

    stmt = select(StorySessionModel).where(StorySessionModel.user_id == user_id)
    if session_status:
        stmt = stmt.where(StorySessionModel.status == session_status)
    stmt = stmt.order_by(StorySessionModel.updated_at.desc())

    # Count total
    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    sessions_list = result.scalars().all()

    return StorySessionListResponse(
        sessions=[_session_to_response(s) for s in sessions_list],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=StorySessionResponse,
    summary="取得故事詳情",
)
async def get_session(
    session_id: str,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StorySessionResponse:
    """Get story session details with all turns."""
    user_id = uuid.UUID(current_user.id)
    result = await session.execute(
        select(StorySessionModel)
        .where(
            StorySessionModel.id == uuid.UUID(session_id),
            StorySessionModel.user_id == user_id,
        )
        .options(selectinload(StorySessionModel.turns))
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _session_to_response(db_session, include_turns=True)


@router.post(
    "/sessions/{session_id}/resume",
    response_model=StorySessionResponse,
    summary="繼續故事",
)
async def resume_session(
    session_id: str,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StorySessionResponse:
    """Resume a paused story session."""
    user_id = uuid.UUID(current_user.id)
    result = await session.execute(
        select(StorySessionModel)
        .where(
            StorySessionModel.id == uuid.UUID(session_id),
            StorySessionModel.user_id == user_id,
        )
        .options(selectinload(StorySessionModel.turns))
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if db_session.status == StorySessionStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Session already completed"
        )

    db_session.status = StorySessionStatus.ACTIVE.value
    await session.commit()
    await session.refresh(db_session)
    return _session_to_response(db_session, include_turns=True)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除故事",
)
async def delete_session(
    session_id: str,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a story session and its turns."""
    user_id = uuid.UUID(current_user.id)
    result = await session.execute(
        select(StorySessionModel).where(
            StorySessionModel.id == uuid.UUID(session_id),
            StorySessionModel.user_id == user_id,
        )
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await session.delete(db_session)
    await session.commit()
