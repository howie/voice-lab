"""Voices API routes.

T055: Add GET /voices endpoint (list all voices with filters)
T056: Add GET /voices/{provider}/{voice_id} endpoint
"""

from fastapi import APIRouter, HTTPException, Query

from src.application.use_cases.list_voices import (
    VoiceFilter,
    VoiceProfile,
    list_voices_use_case,
)

router = APIRouter(prefix="/voices", tags=["voices"])


# Valid providers
VALID_PROVIDERS = {"azure", "gemini", "elevenlabs", "voai"}


# Valid age groups
VALID_AGE_GROUPS = {"child", "young", "adult", "senior"}


@router.get("", response_model=list[dict])
async def list_voices(
    provider: str | None = Query(None, description="Filter by provider"),
    language: str | None = Query(None, description="Filter by language code"),
    gender: str | None = Query(None, description="Filter by gender"),
    age_group: str | None = Query(
        None, description="Filter by age group (child, young, adult, senior)"
    ),
    style: str | None = Query(
        None, description="Filter by style (e.g., news, conversation, cheerful)"
    ),
    search: str | None = Query(None, description="Search by name or description"),
    limit: int | None = Query(None, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Results offset"),
) -> list[dict]:
    """List all available voices with optional filters.

    Returns a list of voice profiles from all configured TTS providers.
    """
    # Validate provider if specified
    if provider and provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {', '.join(VALID_PROVIDERS)}",
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
        search=search,
    )

    voices = await list_voices_use_case.execute(
        filter=filter,
        limit=limit,
        offset=offset,
    )

    return [_voice_to_dict(v) for v in voices]


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
