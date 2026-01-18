"""Comparison API Routes."""

import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.application.use_cases.compare_providers import (
    CompareProvidersUseCase,
    STTComparisonInput,
    TTSComparisonInput,
)
from src.domain.entities.audio import AudioData, AudioFormat
from src.presentation.api.dependencies import get_compare_providers_use_case
from src.presentation.schemas.compare import (
    STTCompareResponse,
    STTProviderResult,
    TTSCompareRequest,
    TTSCompareResponse,
    TTSProviderResult,
)

router = APIRouter()


@router.post("/tts", response_model=TTSCompareResponse)
async def compare_tts(
    request: TTSCompareRequest,
    use_case: CompareProvidersUseCase = Depends(get_compare_providers_use_case),
):
    """Compare TTS providers side-by-side."""
    try:
        input_data = TTSComparisonInput(
            text=request.text,
            voice_ids=request.voice_ids,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
        )

        output = await use_case.compare_tts(input_data)

        results = []
        for r in output.results:
            result = TTSProviderResult(
                provider=r.provider,
                success=r.success,
                error=r.error,
            )
            if r.success and r.result:
                result.audio_base64 = base64.b64encode(r.result.audio.data).decode("utf-8")
                result.audio_format = r.result.audio.format.value
                result.latency_ms = r.result.latency_ms

            results.append(result)

        return TTSCompareResponse(
            results=results,
            fastest_provider=output.fastest_provider,
            summary=output.summary,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}") from e


@router.post("/stt", response_model=STTCompareResponse)
async def compare_stt(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    providers: str = Form(..., description="Comma-separated list of providers"),
    language: str = Form(default="zh-TW", description="Language code"),
    child_mode: bool = Form(default=False, description="Enable child speech mode"),
    ground_truth: str | None = Form(default=None, description="Ground truth text"),
    use_case: CompareProvidersUseCase = Depends(get_compare_providers_use_case),
):
    """Compare STT providers side-by-side."""
    try:
        # Read audio
        audio_bytes = await audio.read()
        audio_format = AudioFormat.WAV  # Default

        if audio.filename:
            if audio.filename.endswith(".mp3"):
                audio_format = AudioFormat.MP3
            elif audio.filename.endswith(".webm"):
                audio_format = AudioFormat.WEBM

        audio_data = AudioData(
            data=audio_bytes,
            format=audio_format,
            sample_rate=16000,
        )

        provider_list = [p.strip() for p in providers.split(",")]

        input_data = STTComparisonInput(
            audio=audio_data,
            providers=provider_list,
            language=language,
            child_mode=child_mode,
            ground_truth=ground_truth,
        )

        output = await use_case.compare_stt(input_data)

        results = []
        for r in output.results:
            result = STTProviderResult(
                provider=r.provider,
                success=r.success,
                error=r.error,
                wer=r.wer,
                cer=r.cer,
            )
            if r.success and r.result:
                result.transcript = r.result.transcript
                result.latency_ms = r.result.latency_ms
                result.confidence = r.result.confidence

            results.append(result)

        return STTCompareResponse(
            results=results,
            most_accurate_provider=output.most_accurate_provider,
            fastest_provider=output.fastest_provider,
            summary=output.summary,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}") from e
