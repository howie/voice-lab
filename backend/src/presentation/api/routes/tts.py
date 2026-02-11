"""TTS API Routes.

T030: Update TTS API route POST /tts/synthesize (batch mode)
T031: Add TTS API route POST /tts/stream (streaming mode)
T074: Add audit logging for credential.used events
"""

import base64
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.audit_service import AuditService
from src.application.use_cases.synthesize_long_text import SynthesizeLongText
from src.application.use_cases.synthesize_speech import SynthesizeSpeech
from src.config import get_settings
from src.domain.config.provider_limits import (
    get_provider_limits,
    get_split_config,
    validate_text_length,
)
from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest
from src.domain.errors import (
    InvalidProviderError,
    ProviderError,
    QuotaExceededError,
    SynthesisError,
)
from src.domain.services.text_splitter import TextSplitter
from src.domain.services.usage_tracker import provider_usage_tracker
from src.infrastructure.persistence.audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)
from src.infrastructure.persistence.credential_repository import (
    SQLAlchemyProviderCredentialRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.providers.tts.factory import TTSProviderFactory
from src.infrastructure.storage.local_storage import LocalStorage
from src.presentation.api.dependencies import get_container
from src.presentation.api.schemas.tts import (
    ProviderLimitInfo,
    SegmentPreviewItem,
    SegmentPreviewRequest,
    SegmentPreviewResponse,
    SegmentTiming,
    StreamRequest,
    SynthesisMetadata,
    SynthesizeRequest,
    SynthesizeResponse,
)

router = APIRouter(prefix="/tts", tags=["tts"])
logger = logging.getLogger(__name__)

# Development user ID for DISABLE_AUTH mode
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def get_optional_user_id(request: Request) -> uuid.UUID | None:
    """Get the current user ID from the request if available.

    This is optional - TTS can work without authentication using system credentials.
    """
    settings = get_settings()

    # Development mode: return dev user ID
    if settings.disable_auth:
        return DEV_USER_ID

    # Check if there's a user_id in request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return user_id

    # Allow a header-based user ID for BYOL mode
    user_id_header = request.headers.get("X-User-Id")
    if user_id_header:
        try:
            return uuid.UUID(user_id_header)
        except ValueError:
            return None

    return None


def get_provider(provider_name: str, container=None):
    """Get TTS provider instance by name from Container."""
    if container is None:
        container = get_container()

    tts_providers = container.get_tts_providers()
    provider = tts_providers.get(provider_name)

    if not provider:
        available = list(tts_providers.keys())
        raise InvalidProviderError(provider_name, available)

    return provider


def get_storage() -> LocalStorage:
    """Get storage service."""
    return LocalStorage()


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(
    request_data: SynthesizeRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Synthesize speech from text (batch mode).

    Returns complete audio data as base64 encoded string.

    If authenticated, uses user's stored API key (BYOL mode).
    Falls back to system credentials if no user credential is available.
    """
    # Check if text needs segmentation for this provider
    split_config = get_split_config(request_data.provider)
    splitter = TextSplitter(split_config)
    needs_segmentation = splitter.needs_splitting(request_data.text)

    try:
        # Get optional user ID for BYOL mode
        user_id = await get_optional_user_id(request)

        # Try to use user credential if available
        credential_repo = SQLAlchemyProviderCredentialRepository(session)
        provider_result = await TTSProviderFactory.create_with_metadata(
            provider_name=request_data.provider,
            user_id=user_id,
            credential_repo=credential_repo,
        )

        # Log credential usage if user credential was used
        if provider_result.used_user_credential and user_id and provider_result.credential_id:
            audit_repo = SQLAlchemyAuditLogRepository(session)
            audit_service = AuditService(audit_repo)
            await audit_service.log_credential_used(
                user_id=user_id,
                credential_id=provider_result.credential_id,
                provider=provider_result.provider_name,
                operation="tts.synthesize",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
            await session.commit()

        storage = get_storage()

        # Map output format
        try:
            output_format = AudioFormat(request_data.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        if needs_segmentation:
            # Long text path: auto-segment and merge
            long_text_use_case = SynthesizeLongText(
                provider=provider_result.provider, storage=storage
            )
            long_result = await long_text_use_case.execute(
                text=request_data.text,
                voice_id=request_data.voice_id,
                provider_name=request_data.provider,
                language=request_data.language,
                output_format=output_format,
                gap_ms=request_data.segment_gap_ms,
                crossfade_ms=request_data.segment_crossfade_ms,
            )

            # Track successful request
            _track_success(user_id, request_data.provider)
            _capture_rate_limit_headers(user_id, request_data.provider, provider_result.provider)

            audio_b64 = base64.b64encode(long_result.audio_content).decode("utf-8")

            # Build segment timing metadata
            timings = []
            if long_result.segment_timings:
                timings = [
                    SegmentTiming(index=t.turn_index, start_ms=t.start_ms, end_ms=t.end_ms)
                    for t in long_result.segment_timings
                ]

            return SynthesizeResponse(
                audio_content=audio_b64,
                content_type=long_result.content_type,
                duration_ms=long_result.duration_ms,
                latency_ms=long_result.latency_ms,
                storage_path=long_result.storage_path,
                metadata=SynthesisMetadata(
                    segmented=True,
                    segment_count=long_result.segment_count,
                    total_text_chars=long_result.total_text_length,
                    total_text_bytes=long_result.total_byte_length,
                    segment_timings=timings,
                ),
            )
        else:
            # Short text path: existing single-request synthesis
            use_case = SynthesizeSpeech(provider_result.provider, storage=storage)

            domain_request = TTSRequest(
                text=request_data.text,
                voice_id=request_data.voice_id,
                provider=request_data.provider,
                language=request_data.language,
                speed=request_data.speed,
                pitch=request_data.pitch,
                volume=request_data.volume,
                output_format=output_format,
                output_mode=OutputMode.BATCH,
            )

            result = await use_case.execute(domain_request)

            # Track successful request
            _track_success(user_id, request_data.provider)
            _capture_rate_limit_headers(user_id, request_data.provider, provider_result.provider)

            audio_b64 = base64.b64encode(result.audio.data).decode("utf-8")

            return SynthesizeResponse(
                audio_content=audio_b64,
                content_type=result.audio.format.mime_type,
                duration_ms=result.duration_ms,
                latency_ms=result.latency_ms,
                storage_path=result.storage_path,
            )

    except QuotaExceededError as e:
        _track_quota_error(user_id, request_data.provider, e)
        raise
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except (SynthesisError, ProviderError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/stream")
async def stream(
    request_data: StreamRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Synthesize speech from text (streaming mode).

    Returns audio data as a streaming response.

    If authenticated, uses user's stored API key (BYOL mode).
    Falls back to system credentials if no user credential is available.
    """
    # Validate text length for provider
    is_valid, error_msg, exceeds_recommended = validate_text_length(
        request_data.provider, request_data.text
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": error_msg})

    if exceeds_recommended:
        logger.warning(
            "Text length (%d) exceeds recommended limit for %s",
            len(request_data.text),
            request_data.provider,
        )

    try:
        # Get optional user ID for BYOL mode
        user_id = await get_optional_user_id(request)

        # Try to use user credential if available
        credential_repo = SQLAlchemyProviderCredentialRepository(session)
        provider_result = await TTSProviderFactory.create_with_metadata(
            provider_name=request_data.provider,
            user_id=user_id,
            credential_repo=credential_repo,
        )

        # Log credential usage if user credential was used
        if provider_result.used_user_credential and user_id and provider_result.credential_id:
            audit_repo = SQLAlchemyAuditLogRepository(session)
            audit_service = AuditService(audit_repo)
            await audit_service.log_credential_used(
                user_id=user_id,
                credential_id=provider_result.credential_id,
                provider=provider_result.provider_name,
                operation="tts.stream",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
            await session.commit()

        use_case = SynthesizeSpeech(provider_result.provider)

        # Map output format
        try:
            output_format = AudioFormat(request_data.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        domain_request = TTSRequest(
            text=request_data.text,
            voice_id=request_data.voice_id,
            provider=request_data.provider,
            language=request_data.language,
            speed=request_data.speed,
            pitch=request_data.pitch,
            volume=request_data.volume,
            output_format=output_format,
            output_mode=OutputMode.STREAMING,
        )

        _track_success(user_id, request_data.provider)

        # Capture rate limit headers from the provider
        _capture_rate_limit_headers(user_id, request_data.provider, provider_result.provider)

        async def audio_stream():
            """Generate audio chunks for streaming response."""
            async for chunk in use_case.execute_stream(domain_request):
                yield chunk

        # Determine content type based on format
        content_type = output_format.mime_type

        return StreamingResponse(
            audio_stream(),
            media_type=content_type,
            headers={
                "X-Provider": request_data.provider,
                "X-Voice-ID": request_data.voice_id,
            },
        )

    except QuotaExceededError as e:
        _track_quota_error(user_id, request_data.provider, e)
        raise
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except (SynthesisError, ProviderError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/synthesize/binary")
async def synthesize_binary(
    request_data: SynthesizeRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Synthesize speech and return raw binary audio data.

    Alternative endpoint that returns audio directly instead of base64.

    If authenticated, uses user's stored API key (BYOL mode).
    Falls back to system credentials if no user credential is available.
    """
    # Validate text length for provider
    is_valid, error_msg, exceeds_recommended = validate_text_length(
        request_data.provider, request_data.text
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": error_msg})

    if exceeds_recommended:
        logger.warning(
            "Text length (%d) exceeds recommended limit for %s",
            len(request_data.text),
            request_data.provider,
        )

    try:
        # Get optional user ID for BYOL mode
        user_id = await get_optional_user_id(request)

        # Try to use user credential if available
        credential_repo = SQLAlchemyProviderCredentialRepository(session)
        provider_result = await TTSProviderFactory.create_with_metadata(
            provider_name=request_data.provider,
            user_id=user_id,
            credential_repo=credential_repo,
        )

        # Log credential usage if user credential was used
        if provider_result.used_user_credential and user_id and provider_result.credential_id:
            audit_repo = SQLAlchemyAuditLogRepository(session)
            audit_service = AuditService(audit_repo)
            await audit_service.log_credential_used(
                user_id=user_id,
                credential_id=provider_result.credential_id,
                provider=provider_result.provider_name,
                operation="tts.synthesize_binary",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
            await session.commit()

        storage = get_storage()
        use_case = SynthesizeSpeech(provider_result.provider, storage=storage)

        # Map output format
        try:
            output_format = AudioFormat(request_data.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        domain_request = TTSRequest(
            text=request_data.text,
            voice_id=request_data.voice_id,
            provider=request_data.provider,
            language=request_data.language,
            speed=request_data.speed,
            pitch=request_data.pitch,
            volume=request_data.volume,
            output_format=output_format,
            output_mode=OutputMode.BATCH,
        )

        result = await use_case.execute(domain_request)

        # Track successful request
        _track_success(user_id, request_data.provider)

        # Capture rate limit headers from the provider
        _capture_rate_limit_headers(user_id, request_data.provider, provider_result.provider)

        return Response(
            content=result.audio.data,
            media_type=result.audio.format.mime_type,
            headers={
                "X-Duration-Ms": str(result.duration_ms),
                "X-Latency-Ms": str(result.latency_ms),
                "X-Provider": request_data.provider,
                "X-Storage-Path": result.storage_path or "",
            },
        )

    except QuotaExceededError as e:
        _track_quota_error(user_id, request_data.provider, e)
        raise
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except (SynthesisError, ProviderError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/synthesize/preview", response_model=SegmentPreviewResponse)
async def synthesize_preview(
    request_data: SegmentPreviewRequest,
):
    """Preview how text will be segmented for a given provider.

    Returns segmentation plan without calling the TTS API.
    No credentials or authentication required.
    """
    split_config = get_split_config(request_data.provider)
    splitter = TextSplitter(split_config)
    limits = get_provider_limits(request_data.provider)

    needs_seg = splitter.needs_splitting(request_data.text)

    segments_info: list[SegmentPreviewItem] = []
    if needs_seg:
        segments = splitter.split(request_data.text)
        for seg in segments:
            segments_info.append(
                SegmentPreviewItem(
                    index=seg.index,
                    text_preview=seg.text[:50],
                    char_length=seg.char_length,
                    byte_length=seg.byte_length,
                    boundary_type=seg.boundary_type,
                )
            )
    else:
        text = request_data.text
        segments_info.append(
            SegmentPreviewItem(
                index=0,
                text_preview=text[:50],
                char_length=len(text),
                byte_length=len(text.encode("utf-8")),
                boundary_type="none",
            )
        )

    # Rough estimate: ~5 seconds per segment for synthesis + merge overhead
    estimated_seconds = len(segments_info) * 5.0

    return SegmentPreviewResponse(
        needs_segmentation=needs_seg,
        segment_count=len(segments_info),
        segments=segments_info,
        provider_limit=ProviderLimitInfo(
            max_value=limits.max_text_length,
            limit_type=limits.limit_type,
        ),
        estimated_duration_seconds=estimated_seconds,
    )


# ============== Usage Tracking Helpers ==============


def _track_success(user_id: uuid.UUID | None, provider: str) -> None:
    """Record a successful provider request in the usage tracker."""
    uid = str(user_id) if user_id else "anonymous"
    provider_usage_tracker.record_request(uid, provider)


def _capture_rate_limit_headers(
    user_id: uuid.UUID | None,
    provider: str,
    provider_instance: object,
) -> None:
    """Capture rate limit headers from the provider and record in tracker."""
    rl_headers = getattr(provider_instance, "_last_rate_limit_headers", None)
    if rl_headers is not None:
        uid = str(user_id) if user_id else "anonymous"
        provider_usage_tracker.record_rate_limit_headers(uid, provider, rl_headers)


def _track_quota_error(
    user_id: uuid.UUID | None,
    provider: str,
    exc: QuotaExceededError,
) -> None:
    """Record a quota error and enrich the exception with usage context."""
    uid = str(user_id) if user_id else "anonymous"
    retry_after = exc.details.get("retry_after") if exc.details else None

    provider_usage_tracker.record_error(uid, provider, is_quota_error=True, retry_after=retry_after)

    # Enrich error details with usage context
    usage = provider_usage_tracker.get_usage(uid, provider)
    if exc.details is not None:
        exc.details["usage_context"] = {
            "minute_requests": usage.minute_requests,
            "hour_requests": usage.hour_requests,
            "day_requests": usage.day_requests,
            "quota_hits_today": usage.quota_hits_today,
            "estimated_rpm_limit": usage.estimated_rpm_limit,
            "usage_warning": usage.usage_warning,
        }
