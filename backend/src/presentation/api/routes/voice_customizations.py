"""Voice Customizations API routes.

Feature: 013-tts-role-mgmt
T015: Create voice_customizations API routes (GET, PUT, DELETE)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.get_voice_customization import (
    GetVoiceCustomizationUseCase,
)
from src.application.use_cases.update_voice_customization import (
    UpdateVoiceCustomizationInput,
    UpdateVoiceCustomizationUseCase,
)
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.presentation.api.dependencies import get_voice_customization_repository
from src.presentation.api.schemas.voice_customization import (
    BulkUpdateResultSchema,
    BulkUpdateVoiceCustomizationRequest,
    UpdateVoiceCustomizationRequest,
    VoiceCustomizationDefaultSchema,
    VoiceCustomizationSchema,
)

router = APIRouter(prefix="/voice-customizations", tags=["voice-customizations"])


def get_update_use_case(
    repo: Annotated[IVoiceCustomizationRepository, Depends(get_voice_customization_repository)],
) -> UpdateVoiceCustomizationUseCase:
    """Dependency for update use case."""
    return UpdateVoiceCustomizationUseCase(repo)


def get_get_use_case(
    repo: Annotated[IVoiceCustomizationRepository, Depends(get_voice_customization_repository)],
) -> GetVoiceCustomizationUseCase:
    """Dependency for get use case."""
    return GetVoiceCustomizationUseCase(repo)


@router.get("", response_model=list[VoiceCustomizationSchema])
async def list_voice_customizations(
    is_favorite: bool | None = Query(None, description="Filter by favorite status"),
    is_hidden: bool | None = Query(None, description="Filter by hidden status"),
    repo: IVoiceCustomizationRepository = Depends(get_voice_customization_repository),
) -> list[VoiceCustomizationSchema]:
    """List all voice customizations with optional filters.

    Returns customizations that have been modified from defaults.
    """
    if is_favorite is not None or is_hidden is not None:
        customizations = await repo.list_by_filter(is_favorite=is_favorite, is_hidden=is_hidden)
    else:
        customizations = await repo.list_all()

    return [
        VoiceCustomizationSchema(
            id=c.id,
            voice_cache_id=c.voice_cache_id,
            custom_name=c.custom_name,
            is_favorite=c.is_favorite,
            is_hidden=c.is_hidden,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in customizations
    ]


@router.get(
    "/{voice_cache_id}",
    response_model=VoiceCustomizationSchema | VoiceCustomizationDefaultSchema,
    responses={
        200: {"description": "Customization found"},
        404: {"description": "Customization not found, returns defaults"},
    },
)
async def get_voice_customization(
    voice_cache_id: str,
    use_case: GetVoiceCustomizationUseCase = Depends(get_get_use_case),
) -> VoiceCustomizationSchema | VoiceCustomizationDefaultSchema:
    """Get customization for a specific voice.

    Returns the customization if it exists, otherwise returns default values
    with a 404 status (but still returns a valid response body).
    """
    customization = await use_case.execute(voice_cache_id)

    if customization:
        return VoiceCustomizationSchema(
            id=customization.id,
            voice_cache_id=customization.voice_cache_id,
            custom_name=customization.custom_name,
            is_favorite=customization.is_favorite,
            is_hidden=customization.is_hidden,
            created_at=customization.created_at,
            updated_at=customization.updated_at,
        )

    # Return defaults with special flag that this is default
    return VoiceCustomizationDefaultSchema(
        voice_cache_id=voice_cache_id,
        custom_name=None,
        is_favorite=False,
        is_hidden=False,
    )


@router.put("/{voice_cache_id}", response_model=VoiceCustomizationSchema)
async def update_voice_customization(
    voice_cache_id: str,
    request: UpdateVoiceCustomizationRequest,
    use_case: UpdateVoiceCustomizationUseCase = Depends(get_update_use_case),
    session: AsyncSession = Depends(get_db_session),
) -> VoiceCustomizationSchema:
    """Update or create a voice customization.

    This endpoint implements upsert semantics - it will create a new
    customization if one doesn't exist, or update the existing one.
    """
    try:
        result = await use_case.execute(
            UpdateVoiceCustomizationInput(
                voice_cache_id=voice_cache_id,
                custom_name=request.custom_name,
                is_favorite=request.is_favorite,
                is_hidden=request.is_hidden,
            )
        )
        await session.commit()

        c = result.customization
        return VoiceCustomizationSchema(
            id=c.id,
            voice_cache_id=c.voice_cache_id,
            custom_name=c.custom_name,
            is_favorite=c.is_favorite,
            is_hidden=c.is_hidden,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{voice_cache_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_customization(
    voice_cache_id: str,
    repo: IVoiceCustomizationRepository = Depends(get_voice_customization_repository),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a voice customization (reset to defaults).

    After deletion, the voice will use its original name and have
    is_favorite=False, is_hidden=False.
    """
    deleted = await repo.delete(voice_cache_id)
    await session.commit()

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customization not found: {voice_cache_id}",
        )


@router.patch("/bulk", response_model=BulkUpdateResultSchema)
async def bulk_update_voice_customizations(
    request: BulkUpdateVoiceCustomizationRequest,
    repo: IVoiceCustomizationRepository = Depends(get_voice_customization_repository),
    session: AsyncSession = Depends(get_db_session),
) -> BulkUpdateResultSchema:
    """Bulk update multiple voice customizations.

    Processes up to 50 updates in a single request.
    Returns the count of successful updates and any failures.
    """
    from src.application.use_cases.bulk_update_voice_customization import (
        BulkUpdateInput,
        BulkUpdateItem,
        BulkUpdateVoiceCustomizationUseCase,
    )

    use_case = BulkUpdateVoiceCustomizationUseCase(repo)

    try:
        result = await use_case.execute(
            BulkUpdateInput(
                updates=[
                    BulkUpdateItem(
                        voice_cache_id=item.voice_cache_id,
                        custom_name=item.custom_name,
                        is_favorite=item.is_favorite,
                        is_hidden=item.is_hidden,
                    )
                    for item in request.updates
                ]
            )
        )
        await session.commit()

        return BulkUpdateResultSchema(
            updated_count=result.updated_count,
            failed=[
                {"voice_cache_id": f.voice_cache_id, "error": f.error} for f in result.failed
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
