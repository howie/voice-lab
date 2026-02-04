"""Voices API routes.

T055: Add GET /voices endpoint (list all voices with filters)
T056: Add GET /voices/{provider}/{voice_id} endpoint
T059: Add POST /{voice_cache_id}/preview endpoint (voice preview)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.storage_service import IStorageService
from src.application.interfaces.tts_provider import ITTSProvider
from src.application.interfaces.voice_cache_repository import IVoiceCacheRepository
from src.application.use_cases.generate_voice_preview import GenerateVoicePreview
from src.application.use_cases.list_voices import (
    VoiceFilter,
    VoiceProfile,
    list_voices_use_case,
)
from src.application.use_cases.list_voices_with_customization import (
    ListVoicesWithCustomizationUseCase,
    VoiceListFilters,
)
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.presentation.api.dependencies import (
    get_storage_service,
    get_tts_providers,
    get_voice_cache_repository,
    get_voice_customization_repository,
)

router = APIRouter(prefix="/voices", tags=["voices"])


# Valid providers
VALID_PROVIDERS = {"azure", "gemini", "elevenlabs", "voai"}


# Valid age groups
VALID_AGE_GROUPS = {"child", "young", "adult", "senior"}


@router.get("")
async def list_voices(
    provider: str | None = Query(None, description="Filter by provider"),
    language: str | None = Query(None, description="Filter by language code"),
    gender: str | None = Query(None, description="Filter by gender"),
    age_group: str | None = Query(
        None, description="Filter by age group (child, young, adult, senior)"
    ),
    search: str | None = Query(None, description="Search by name or description"),
    exclude_hidden: bool = Query(True, description="Exclude hidden voices"),
    favorites_only: bool = Query(False, description="Only show favorites"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    voice_cache_repo: IVoiceCacheRepository = Depends(get_voice_cache_repository),
    customization_repo: IVoiceCustomizationRepository = Depends(get_voice_customization_repository),
) -> dict:
    """List all available voices with optional filters and customization data.

    Returns a paginated list of voice profiles with customization info.
    When voice cache is empty for a provider, falls back to the provider's
    built-in voice list to ensure voices are always available.
    """
    filters = VoiceListFilters(
        provider=provider,
        language=language,
        gender=gender,
        age_group=age_group,
        search=search,
        exclude_hidden=exclude_hidden,
        favorites_only=favorites_only,
        limit=limit,
        offset=offset,
    )

    use_case = ListVoicesWithCustomizationUseCase(voice_cache_repo, customization_repo)
    result = await use_case.execute(filters)

    # Fallback: when voice cache is empty, use provider's built-in voice list
    if not result.items and provider:
        voice_filter = VoiceFilter(
            provider=provider,
            language=language,
            gender=gender,
            age_group=age_group,
        )
        fallback_voices = await list_voices_use_case.execute(
            filter=voice_filter, limit=limit, offset=offset
        )

        items = []
        for v in fallback_voices:
            items.append(
                {
                    "id": f"{v.provider}:{v.id}",
                    "provider": v.provider,
                    "voice_id": v.id,
                    "name": v.name,
                    "display_name": v.name,
                    "language": v.language,
                    "gender": v.gender,
                    "age_group": v.age_group,
                    "styles": v.supported_styles or [],
                    "use_cases": [],
                    "sample_audio_url": v.sample_url,
                    "is_deprecated": False,
                    "is_favorite": False,
                    "is_hidden": False,
                    "customization": None,
                }
            )

        return {
            "items": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
        }

    # Get customization map to include in response
    voice_ids = [v.id for v in result.items]
    customization_map = await customization_repo.get_customization_map(voice_ids)

    items = []
    for v in result.items:
        item: dict = {
            "id": v.id,
            "provider": v.provider,
            "voice_id": v.voice_id,
            "name": v.name,
            "display_name": v.display_name,
            "language": v.language,
            "gender": v.gender,
            "age_group": v.age_group,
            "styles": v.styles,
            "use_cases": v.use_cases,
            "sample_audio_url": v.sample_audio_url,
            "is_deprecated": v.is_deprecated,
            "is_favorite": v.is_favorite,
            "is_hidden": v.is_hidden,
            "customization": None,
        }
        c = customization_map.get(v.id)
        if c:
            item["customization"] = {
                "id": c.id,
                "voice_cache_id": c.voice_cache_id,
                "custom_name": c.custom_name,
                "is_favorite": c.is_favorite,
                "is_hidden": c.is_hidden,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
        items.append(item)

    return {
        "items": items,
        "total": result.total,
        "limit": result.limit,
        "offset": result.offset,
    }


@router.post("/{voice_cache_id}/preview")
async def generate_voice_preview(
    voice_cache_id: str,
    voice_cache_repo: IVoiceCacheRepository = Depends(get_voice_cache_repository),
    providers: dict[str, ITTSProvider] = Depends(get_tts_providers),
    storage: IStorageService = Depends(get_storage_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Generate or retrieve a preview audio URL for a voice.

    If the voice already has a cached preview URL, returns it immediately.
    Otherwise, synthesizes a short preview clip and stores it.

    Args:
        voice_cache_id: Voice cache ID (format: provider:voice_id)

    Returns:
        Dictionary with preview_url
    """
    use_case = GenerateVoicePreview(providers, storage, voice_cache_repo)
    preview_url = await use_case.execute(voice_cache_id)
    await session.commit()
    return {"preview_url": preview_url}


@router.get("/{provider}", response_model=list[dict])
async def list_voices_by_provider(
    provider: str,
    language: str | None = Query(None, description="Filter by language code"),
    gender: str | None = Query(None, description="Filter by gender"),
    age_group: str | None = Query(
        None, description="Filter by age group (child, young, adult, senior)"
    ),
    style: str | None = Query(
        None, description="Filter by style (e.g., news, conversation, cheerful)"
    ),
) -> list[dict]:
    """List voices for a specific provider.

    Args:
        provider: TTS provider name (azure, gcp, elevenlabs, voai)
        language: Optional language filter
        gender: Optional gender filter
        age_group: Optional age group filter (child, young, adult, senior)
        style: Optional style filter (e.g., news, conversation, cheerful)

    Returns:
        List of voice profiles for the provider
    """
    if provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found. Valid providers: {', '.join(VALID_PROVIDERS)}",
        )

    # Validate age_group if specified
    if age_group and age_group not in VALID_AGE_GROUPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid age_group. Must be one of: {', '.join(VALID_AGE_GROUPS)}",
        )

    filter = VoiceFilter(
        provider=provider,
        language=language,
        gender=gender,
        age_group=age_group,
        style=style,
    )

    voices = await list_voices_use_case.execute(filter=filter)

    return [_voice_to_dict(v) for v in voices]


@router.get("/{provider}/{voice_id}", response_model=dict)
async def get_voice_detail(
    provider: str,
    voice_id: str,
) -> dict:
    """Get details for a specific voice.

    Args:
        provider: TTS provider name
        voice_id: Voice identifier

    Returns:
        Detailed voice profile
    """
    if provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found",
        )

    voice = await list_voices_use_case.get_voice_by_id(provider, voice_id)

    if not voice:
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{voice_id}' not found for provider '{provider}'",
        )

    return _voice_to_dict(voice)


def _voice_to_dict(voice: VoiceProfile) -> dict:
    """Convert VoiceProfile to dictionary response.

    Args:
        voice: VoiceProfile instance

    Returns:
        Dictionary representation
    """
    result = {
        "id": voice.id,
        "name": voice.name,
        "provider": voice.provider,
        "language": voice.language,
    }

    if voice.gender:
        result["gender"] = voice.gender

    if voice.age_group:
        result["age_group"] = voice.age_group

    if voice.description:
        result["description"] = voice.description

    if voice.sample_url:
        result["sample_url"] = voice.sample_url

    if voice.supported_styles:
        result["supported_styles"] = voice.supported_styles

    return result
