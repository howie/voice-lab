"""Multi-Role TTS API Routes.

Provides endpoints for multi-role dialogue text-to-speech synthesis.
"""

import base64
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.application.use_cases.synthesize_multi_role import (
    SynthesizeMultiRoleInput,
    SynthesizeMultiRoleUseCase,
)
from src.domain.entities.multi_role_tts import DialogueTurn, VoiceAssignment
from src.domain.errors import QuotaExceededError, RateLimitError
from src.domain.services.dialogue_parser import parse_dialogue
from src.infrastructure.providers.tts.multi_role import (
    get_provider_capability,
)
from src.infrastructure.providers.tts.multi_role.capability_registry import (
    get_all_capabilities,
)

router = APIRouter(prefix="/tts/multi-role", tags=["multi-role-tts"])
logger = logging.getLogger(__name__)


# Request/Response Schemas


class ParseDialogueRequest(BaseModel):
    """Request to parse dialogue text."""

    text: str = Field(..., min_length=1, description="Dialogue text to parse")


class DialogueTurnResponse(BaseModel):
    """A single dialogue turn in response."""

    speaker: str
    text: str
    index: int


class ParseDialogueResponse(BaseModel):
    """Response from dialogue parsing."""

    turns: list[DialogueTurnResponse]
    speakers: list[str]
    total_characters: int


class ProviderCapabilityResponse(BaseModel):
    """Provider capability information."""

    provider_name: str
    support_type: str
    max_speakers: int
    character_limit: int
    advanced_features: list[str]
    notes: str | None


class CapabilitiesResponse(BaseModel):
    """Response containing all provider capabilities."""

    providers: list[ProviderCapabilityResponse]


class VoiceAssignmentRequest(BaseModel):
    """Voice assignment in request."""

    speaker: str
    voice_id: str
    voice_name: str | None = None
    style_prompt: str | None = None


class DialogueTurnRequest(BaseModel):
    """Dialogue turn in request."""

    speaker: str
    text: str
    index: int


class SynthesizeRequest(BaseModel):
    """Request for multi-role TTS synthesis."""

    provider: str
    turns: list[DialogueTurnRequest]
    voice_assignments: list[VoiceAssignmentRequest]
    language: str = "zh-TW"
    output_format: str = "mp3"
    gap_ms: int = Field(default=300, ge=0, le=2000)
    crossfade_ms: int = Field(default=50, ge=0, le=500)
    style_prompt: str | None = None


class TurnTimingResponse(BaseModel):
    """Timing information for a turn."""

    turn_index: int
    start_ms: int
    end_ms: int


class SynthesizeResponse(BaseModel):
    """Response from synthesis endpoint."""

    audio_url: str | None = None
    audio_content: str | None = None  # base64 encoded
    content_type: str
    duration_ms: int
    latency_ms: int
    provider: str
    synthesis_mode: str
    turn_timings: list[TurnTimingResponse] | None = None


# Endpoints


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities() -> CapabilitiesResponse:
    """Get multi-role TTS capabilities for all providers.

    Returns information about each provider's support for multi-role
    dialogue synthesis, including support type, speaker limits, and
    advanced features.
    """
    capabilities = get_all_capabilities()

    return CapabilitiesResponse(
        providers=[
            ProviderCapabilityResponse(
                provider_name=cap.provider_name,
                support_type=cap.support_type.value,
                max_speakers=cap.max_speakers,
                character_limit=cap.character_limit,
                advanced_features=cap.advanced_features,
                notes=cap.notes,
            )
            for cap in capabilities
        ]
    )


@router.post("/parse", response_model=ParseDialogueResponse)
async def parse_dialogue_text(request: ParseDialogueRequest) -> ParseDialogueResponse:
    """Parse dialogue text into structured turns.

    Supports formats:
    - Letter format: A: text, B: text
    - Bracket format: [Host]: text, [Guest]: text
    - Both English (:) and Chinese (：) colons
    """
    try:
        turns, speakers = parse_dialogue(request.text)

        total_chars = sum(len(turn.text) for turn in turns)

        return ParseDialogueResponse(
            turns=[
                DialogueTurnResponse(
                    speaker=turn.speaker,
                    text=turn.text,
                    index=turn.index,
                )
                for turn in turns
            ],
            speakers=speakers,
            total_characters=total_chars,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize multi-role dialogue into audio.

    Automatically selects native or segmented synthesis mode based
    on provider capability.

    For native providers (ElevenLabs, Azure, GCP), uses provider's
    built-in multi-speaker support.

    For segmented providers (OpenAI, Cartesia, Deepgram), synthesizes
    each turn separately and merges the audio.
    """
    # Validate provider exists
    capability = get_provider_capability(request.provider)
    if not capability:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {request.provider}",
        )

    # Validate turns not empty
    if not request.turns:
        raise HTTPException(
            status_code=400,
            detail="Turns cannot be empty",
        )

    # Validate voice assignments cover all speakers
    speakers = {turn.speaker for turn in request.turns}
    assigned = {va.speaker for va in request.voice_assignments}
    missing = speakers - assigned
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing voice assignments for speakers: {missing}",
        )

    try:
        # Convert request to domain objects
        domain_turns = [
            DialogueTurn(
                speaker=turn.speaker,
                text=turn.text,
                index=turn.index,
            )
            for turn in request.turns
        ]

        domain_assignments = [
            VoiceAssignment(
                speaker=va.speaker,
                voice_id=va.voice_id,
                voice_name=va.voice_name,
                style_prompt=va.style_prompt,
            )
            for va in request.voice_assignments
        ]

        # Execute use case
        use_case = SynthesizeMultiRoleUseCase()
        input_data = SynthesizeMultiRoleInput(
            provider=request.provider,
            turns=domain_turns,
            voice_assignments=domain_assignments,
            language=request.language,
            output_format=request.output_format,
            gap_ms=request.gap_ms,
            crossfade_ms=request.crossfade_ms,
            style_prompt=request.style_prompt,
        )

        result = await use_case.execute(input_data)

        # Encode audio as base64
        audio_b64 = base64.b64encode(result.audio_content).decode("utf-8")

        return SynthesizeResponse(
            audio_content=audio_b64,
            content_type=result.content_type,
            duration_ms=result.duration_ms,
            latency_ms=result.latency_ms,
            provider=result.provider,
            synthesis_mode=result.synthesis_mode.value,
            turn_timings=[
                TurnTimingResponse(
                    turn_index=tt.turn_index,
                    start_ms=tt.start_ms,
                    end_ms=tt.end_ms,
                )
                for tt in (result.turn_timings or [])
            ],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (QuotaExceededError, RateLimitError):
        raise
    except Exception as e:
        logger.exception("Multi-role TTS synthesis failed")
        raise HTTPException(
            status_code=503,
            detail=f"Synthesis failed: {e!s}",
        ) from e


@router.post("/synthesize/binary")
async def synthesize_binary(request: SynthesizeRequest) -> Response:
    """Synthesize multi-role dialogue and return raw binary audio.

    Alternative endpoint that returns audio directly instead of base64.
    """
    # Validate provider exists
    capability = get_provider_capability(request.provider)
    if not capability:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {request.provider}",
        )

    # Validate turns not empty
    if not request.turns:
        raise HTTPException(
            status_code=400,
            detail="Turns cannot be empty",
        )

    # Validate voice assignments
    speakers = {turn.speaker for turn in request.turns}
    assigned = {va.speaker for va in request.voice_assignments}
    missing = speakers - assigned
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing voice assignments for speakers: {missing}",
        )

    try:
        # Convert request to domain objects
        domain_turns = [
            DialogueTurn(
                speaker=turn.speaker,
                text=turn.text,
                index=turn.index,
            )
            for turn in request.turns
        ]

        domain_assignments = [
            VoiceAssignment(
                speaker=va.speaker,
                voice_id=va.voice_id,
                voice_name=va.voice_name,
                style_prompt=va.style_prompt,
            )
            for va in request.voice_assignments
        ]

        # Execute use case
        use_case = SynthesizeMultiRoleUseCase()
        input_data = SynthesizeMultiRoleInput(
            provider=request.provider,
            turns=domain_turns,
            voice_assignments=domain_assignments,
            language=request.language,
            output_format=request.output_format,
            gap_ms=request.gap_ms,
            crossfade_ms=request.crossfade_ms,
            style_prompt=request.style_prompt,
        )

        result = await use_case.execute(input_data)

        return Response(
            content=result.audio_content,
            media_type=result.content_type,
            headers={
                "X-Duration-Ms": str(result.duration_ms),
                "X-Latency-Ms": str(result.latency_ms),
                "X-Provider": result.provider,
                "X-Synthesis-Mode": result.synthesis_mode.value,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (QuotaExceededError, RateLimitError):
        raise
    except Exception as e:
        logger.exception("Multi-role TTS binary synthesis failed")
        raise HTTPException(
            status_code=503,
            detail=f"Synthesis failed: {e!s}",
        ) from e
