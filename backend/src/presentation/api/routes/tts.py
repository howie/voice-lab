"""TTS API Routes.

T030: Update TTS API route POST /tts/synthesize (batch mode)
T031: Add TTS API route POST /tts/stream (streaming mode)
"""

import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

from src.application.use_cases.synthesize_speech import SynthesizeSpeech
from src.domain.config.provider_limits import validate_text_length
from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest
from src.domain.errors import (
    InvalidProviderError,
    ProviderError,
    SynthesisError,
)
from src.infrastructure.storage.local_storage import LocalStorage
from src.presentation.api.dependencies import get_container
from src.presentation.api.schemas.tts import (
    StreamRequest,
    SynthesizeRequest,
    SynthesizeResponse,
)

router = APIRouter(prefix="/tts", tags=["tts"])


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
async def synthesize(request: SynthesizeRequest):
    """Synthesize speech from text (batch mode).

    Returns complete audio data as base64 encoded string.
    """
    # Validate text length for provider (outside try-except to ensure proper HTTP status)
    is_valid, error_msg, exceeds_recommended = validate_text_length(request.provider, request.text)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": error_msg})

    # Log warning if exceeds recommended length
    if exceeds_recommended:
        print(
            f"Warning: Text length ({len(request.text)}) exceeds recommended limit for {request.provider}"
        )

    try:
        provider = get_provider(request.provider)
        storage = get_storage()
        use_case = SynthesizeSpeech(provider, storage=storage)

        # Map output format
        try:
            output_format = AudioFormat(request.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        domain_request = TTSRequest(
            text=request.text,
            voice_id=request.voice_id,
            provider=request.provider,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            output_format=output_format,
            output_mode=OutputMode.BATCH,
        )

        result = await use_case.execute(domain_request)

        # Return base64 encoded audio
        audio_b64 = base64.b64encode(result.audio.data).decode("utf-8")

        return SynthesizeResponse(
            audio_content=audio_b64,
            content_type=result.audio.format.mime_type,
            duration_ms=result.duration_ms,
            latency_ms=result.latency_ms,
            storage_path=result.storage_path,
        )

    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except (SynthesisError, ProviderError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/stream")
async def stream(request: StreamRequest):
    """Synthesize speech from text (streaming mode).

    Returns audio data as a streaming response.
    """
    # Validate text length for provider
    is_valid, error_msg, exceeds_recommended = validate_text_length(request.provider, request.text)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": error_msg})

    if exceeds_recommended:
        print(
            f"Warning: Text length ({len(request.text)}) exceeds recommended limit for {request.provider}"
        )

    try:
        provider = get_provider(request.provider)
        use_case = SynthesizeSpeech(provider)

        # Map output format
        try:
            output_format = AudioFormat(request.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        domain_request = TTSRequest(
            text=request.text,
            voice_id=request.voice_id,
            provider=request.provider,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            output_format=output_format,
            output_mode=OutputMode.STREAMING,
        )

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
                "X-Provider": request.provider,
                "X-Voice-ID": request.voice_id,
            },
        )

    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except (SynthesisError, ProviderError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/synthesize/binary")
async def synthesize_binary(request: SynthesizeRequest):
    """Synthesize speech and return raw binary audio data.

    Alternative endpoint that returns audio directly instead of base64.
    """
    # Validate text length for provider
    is_valid, error_msg, exceeds_recommended = validate_text_length(request.provider, request.text)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": error_msg})

    if exceeds_recommended:
        print(
            f"Warning: Text length ({len(request.text)}) exceeds recommended limit for {request.provider}"
        )

    try:
        provider = get_provider(request.provider)
        storage = get_storage()
        use_case = SynthesizeSpeech(provider, storage=storage)

        # Map output format
        try:
            output_format = AudioFormat(request.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        domain_request = TTSRequest(
            text=request.text,
            voice_id=request.voice_id,
            provider=request.provider,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            output_format=output_format,
            output_mode=OutputMode.BATCH,
        )

        result = await use_case.execute(domain_request)

        return Response(
            content=result.audio.data,
            media_type=result.audio.format.mime_type,
            headers={
                "X-Duration-Ms": str(result.duration_ms),
                "X-Latency-Ms": str(result.latency_ms),
                "X-Provider": request.provider,
                "X-Storage-Path": result.storage_path or "",
            },
        )

    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except (SynthesisError, ProviderError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
