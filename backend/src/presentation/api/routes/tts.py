"""TTS API Routes."""

import base64
from fastapi import APIRouter, Depends, HTTPException

from src.presentation.schemas.tts import (
    TTSSynthesizeRequest,
    TTSSynthesizeResponse,
    VoiceListResponse,
    VoiceResponse,
)
from src.presentation.api.dependencies import (
    get_synthesize_speech_use_case,
    get_tts_providers,
)
from src.application.use_cases.synthesize_speech import (
    SynthesizeSpeechUseCase,
    SynthesizeSpeechInput,
)
from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioFormat

router = APIRouter()


@router.post("/synthesize", response_model=TTSSynthesizeResponse)
async def synthesize_speech(
    request: TTSSynthesizeRequest,
    use_case: SynthesizeSpeechUseCase = Depends(get_synthesize_speech_use_case),
):
    """Synthesize speech from text."""
    try:
        # Map output format
        try:
            output_format = AudioFormat(request.output_format)
        except ValueError:
            output_format = AudioFormat.MP3

        input_data = SynthesizeSpeechInput(
            text=request.text,
            provider_name=request.provider,
            voice_id=request.voice_id,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            output_format=output_format,
            user_id="anonymous",  # TODO: Get from auth
            save_to_storage=True,
            save_to_history=request.save_to_history,
        )

        output = await use_case.execute(input_data)

        return TTSSynthesizeResponse(
            audio_base64=base64.b64encode(output.result.audio.data).decode("utf-8"),
            audio_format=output.result.audio.format.value,
            provider=output.result.provider,
            voice_id=output.result.voice_id,
            latency_ms=output.result.latency_ms,
            text_length=output.result.text_length,
            audio_url=output.audio_url,
            record_id=output.record_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(
    provider: str | None = None,
    language: str | None = None,
    tts_providers: dict[str, ITTSProvider] = Depends(get_tts_providers),
):
    """List available voices."""
    voices = []

    providers_to_query = (
        {provider: tts_providers[provider]}
        if provider and provider in tts_providers
        else tts_providers
    )

    for name, p in providers_to_query.items():
        try:
            provider_voices = await p.list_voices(language=language)
            for v in provider_voices:
                voices.append(
                    VoiceResponse(
                        voice_id=v.voice_id,
                        name=v.name,
                        provider=v.provider,
                        language=v.language,
                        gender=v.gender.value,
                        sample_audio_url=v.sample_audio_url,
                        description=v.description,
                    )
                )
        except Exception:
            # Skip providers that fail
            continue

    return VoiceListResponse(
        voices=voices,
        total=len(voices),
        provider=provider,
        language=language,
    )


@router.get("/providers")
async def list_providers(
    tts_providers: dict[str, ITTSProvider] = Depends(get_tts_providers),
):
    """List available TTS providers."""
    return {
        "providers": list(tts_providers.keys()),
        "total": len(tts_providers),
    }
