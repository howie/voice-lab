"""STT API Routes.

Feature: 003-stt-testing-module
T027: Implement GET /stt/providers endpoint
T028: Implement POST /stt/transcribe endpoint
"""

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.application.interfaces.stt_provider import ISTTProvider
from src.application.use_cases.transcribe_audio import (
    TranscribeAudioInput,
    TranscribeAudioUseCase,
)
from src.domain.entities.audio import AudioData, AudioFormat
from src.infrastructure.providers.stt.factory import STTProviderFactory
from src.presentation.api.dependencies import (
    get_stt_providers,
    get_transcribe_audio_use_case,
)
from src.presentation.schemas.stt import (
    STTProviderResponse,
    STTProvidersListResponse,
    STTTranscribeResponse,
    WERAnalysisResponse,
    WordTimingResponse,
)

router = APIRouter()


# CJK languages for determining WER vs CER
CJK_LANGUAGES = {"zh-TW", "zh-CN", "ja-JP", "ko-KR"}


def _get_audio_format(content_type: str, filename: str) -> AudioFormat:
    """Determine audio format from content type or filename."""
    content_type_lower = content_type.lower() if content_type else ""
    filename_lower = filename.lower() if filename else ""

    if "wav" in content_type_lower or filename_lower.endswith(".wav"):
        return AudioFormat.WAV
    elif "ogg" in content_type_lower or filename_lower.endswith(".ogg"):
        return AudioFormat.OGG
    elif "webm" in content_type_lower or filename_lower.endswith(".webm"):
        return AudioFormat.WEBM
    elif "flac" in content_type_lower or filename_lower.endswith(".flac"):
        return AudioFormat.FLAC
    elif "m4a" in content_type_lower or filename_lower.endswith(".m4a"):
        return AudioFormat.M4A
    else:
        return AudioFormat.MP3


def _determine_error_type(language: str) -> str:
    """Determine whether to use WER or CER based on language."""
    return "CER" if language in CJK_LANGUAGES else "WER"


@router.get("/providers", response_model=STTProvidersListResponse)
async def list_providers(
    stt_providers: dict[str, ISTTProvider] = Depends(get_stt_providers),
):
    """List available STT providers with their capabilities.

    Returns full provider information including:
    - Supported formats and file size limits
    - Streaming and child mode support
    - Supported languages
    """
    # Get available provider names from initialized providers
    available_provider_names = set(stt_providers.keys())

    # Get full provider info from factory, filtered by available providers
    providers_info = []
    for provider_data in STTProviderFactory.list_providers():
        if provider_data["name"] in available_provider_names:
            providers_info.append(
                STTProviderResponse(
                    name=provider_data["name"],
                    display_name=provider_data["display_name"],
                    supports_streaming=provider_data["supports_streaming"],
                    supports_child_mode=provider_data["supports_child_mode"],
                    max_duration_sec=provider_data["max_duration_sec"],
                    max_file_size_mb=provider_data["max_file_size_mb"],
                    supported_formats=provider_data["supported_formats"],
                    supported_languages=provider_data["supported_languages"],
                )
            )

    return STTProvidersListResponse(providers=providers_info)


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
    """Transcribe audio to text.

    Returns transcription result with:
    - Transcript text and confidence score
    - Word-level timing information (if available)
    - WER/CER analysis (if ground truth provided)
    - Processing latency
    """
    try:
        # Validate provider exists
        provider_info = None
        try:
            provider_info = STTProviderFactory.get_provider_info(provider)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # Read and validate audio data
        audio_bytes = await audio.read()
        audio_format = _get_audio_format(audio.content_type or "", audio.filename or "")

        # Check file size limit
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        max_size = provider_info["max_file_size_mb"]
        if file_size_mb > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size_mb:.1f}MB) exceeds {provider} limit ({max_size}MB)",
            )

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

        # Convert word timings to response format
        words = None
        word_timings_legacy = None
        if output.result.words:
            words = [
                WordTimingResponse(
                    word=wt.word,
                    start_ms=wt.start_ms,
                    end_ms=wt.end_ms,
                    confidence=wt.confidence,
                )
                for wt in output.result.words
            ]
            # Also provide legacy format
            word_timings_legacy = words

        # Build WER analysis response if ground truth was provided
        wer_analysis = None
        if ground_truth and (output.wer is not None or output.cer is not None):
            error_type = _determine_error_type(language)
            error_rate = output.cer if error_type == "CER" else output.wer

            # Calculate detailed metrics
            from src.domain.services.wer_calculator import calculate_alignment

            if error_type == "CER":
                ref_tokens = list(ground_truth.replace(" ", ""))
                hyp_tokens = list(output.result.transcript.replace(" ", ""))
            else:
                ref_tokens = ground_truth.split()
                hyp_tokens = output.result.transcript.split()

            _, insertions, deletions, substitutions = calculate_alignment(ref_tokens, hyp_tokens)

            wer_analysis = WERAnalysisResponse(
                error_rate=error_rate or 0.0,
                error_type=error_type,
                insertions=insertions,
                deletions=deletions,
                substitutions=substitutions,
                total_reference=len(ref_tokens),
            )

        return STTTranscribeResponse(
            id=output.record_id,
            transcript=output.result.transcript,
            provider=output.result.provider,
            language=output.result.language,
            latency_ms=output.result.latency_ms,
            confidence=output.result.confidence or 0.0,
            words=words,
            audio_duration_ms=output.result.audio_duration_ms,
            wer_analysis=wer_analysis,
            created_at=datetime.utcnow().isoformat() + "Z",
            # Legacy fields
            word_timings=word_timings_legacy,
            wer=output.wer,
            cer=output.cer,
            record_id=output.record_id,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") from e
