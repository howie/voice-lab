"""STT API Routes."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.application.interfaces.stt_provider import ISTTProvider
from src.application.use_cases.transcribe_audio import (
    TranscribeAudioInput,
    TranscribeAudioUseCase,
)
from src.domain.entities.audio import AudioData, AudioFormat
from src.presentation.api.dependencies import (
    get_stt_providers,
    get_transcribe_audio_use_case,
)
from src.presentation.schemas.stt import (
    STTTranscribeResponse,
    WordTimingResponse,
)

router = APIRouter()


def _get_audio_format(content_type: str, filename: str) -> AudioFormat:
    """Determine audio format from content type or filename."""
    if "wav" in content_type or filename.endswith(".wav"):
        return AudioFormat.WAV
    elif "ogg" in content_type or filename.endswith(".ogg"):
        return AudioFormat.OGG
    elif "webm" in content_type or filename.endswith(".webm"):
        return AudioFormat.WEBM
    elif "flac" in content_type or filename.endswith(".flac"):
        return AudioFormat.FLAC
    else:
        return AudioFormat.MP3


@router.post("/transcribe", response_model=STTTranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    provider: str = Form(..., description="STT provider name"),
    language: str = Form(default="zh-TW", description="Language code"),
    child_mode: bool = Form(default=False, description="Enable child speech mode"),
    ground_truth: str | None = Form(default=None, description="Ground truth text"),
    save_to_history: bool = Form(default=True, description="Save to history"),
    use_case: TranscribeAudioUseCase = Depends(get_transcribe_audio_use_case),
):
    """Transcribe audio to text."""
    try:
        # Read audio data
        audio_bytes = await audio.read()
        audio_format = _get_audio_format(audio.content_type or "", audio.filename or "")

        audio_data = AudioData(
            data=audio_bytes,
            format=audio_format,
            sample_rate=16000,  # Default, actual rate may vary
        )

        input_data = TranscribeAudioInput(
            provider_name=provider,
            audio=audio_data,
            language=language,
            child_mode=child_mode,
            ground_truth=ground_truth,
            user_id="anonymous",  # TODO: Get from auth
            save_to_history=save_to_history,
        )

        output = await use_case.execute(input_data)

        word_timings = None
        if output.result.word_timings:
            word_timings = [
                WordTimingResponse(
                    word=wt.word,
                    start_time=wt.start_time,
                    end_time=wt.end_time,
                    confidence=wt.confidence,
                )
                for wt in output.result.word_timings
            ]

        return STTTranscribeResponse(
            transcript=output.result.transcript,
            provider=output.result.provider,
            language=output.result.language,
            latency_ms=output.result.latency_ms,
            confidence=output.result.confidence,
            word_timings=word_timings,
            audio_duration_ms=output.result.audio_duration_ms,
            wer=output.wer,
            cer=output.cer,
            record_id=output.record_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") from e


@router.get("/providers")
async def list_providers(
    stt_providers: dict[str, ISTTProvider] = Depends(get_stt_providers),
):
    """List available STT providers."""
    providers_info = []
    for name, provider in stt_providers.items():
        providers_info.append(
            {
                "name": name,
                "supports_streaming": provider.supports_streaming,
            }
        )

    return {
        "providers": providers_info,
        "total": len(stt_providers),
    }
