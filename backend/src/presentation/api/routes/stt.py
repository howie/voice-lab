"""STT API Routes.

Feature: 003-stt-testing-module
T027: Implement GET /stt/providers endpoint
T028: Implement POST /stt/transcribe endpoint
T051: Implement POST /stt/analysis/wer endpoint
T064-T067: History and Comparison endpoints
"""

import asyncio
import io
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydub import AudioSegment

from src.application.interfaces.storage_service import IStorageService
from src.application.services.stt_service import STTService
from src.domain.entities.audio_file import AudioFile, AudioFileFormat, AudioSource
from src.domain.repositories.transcription_repository import ITranscriptionRepository
from src.infrastructure.providers.stt.factory import STTProviderFactory
from src.presentation.api.dependencies import (
    get_storage_service,
    get_stt_service,
    get_transcription_repository,
)
from src.presentation.api.middleware.auth import CurrentUserDep
from src.presentation.schemas.stt import (
    ComparisonResponse,
    STTProviderResponse,
    STTProvidersListResponse,
    STTTranscribeResponse,
    TranscriptionDetail,
    TranscriptionHistoryPage,
    TranscriptionSummary,
    WERAnalysisRequest,
    WERAnalysisResponse,
    WordTimingResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# CJK languages for determining WER vs CER
CJK_LANGUAGES = {"zh-TW", "zh-CN", "ja-JP", "ko-KR"}


def _get_audio_format(content_type: str, filename: str) -> AudioFileFormat:
    """Determine audio format from content type or filename."""
    content_type_lower = content_type.lower() if content_type else ""
    filename_lower = filename.lower() if filename else ""

    if "wav" in content_type_lower or filename_lower.endswith(".wav"):
        return AudioFileFormat.WAV
    elif "ogg" in content_type_lower or filename_lower.endswith(".ogg"):
        return AudioFileFormat.OGG
    elif "webm" in content_type_lower or filename_lower.endswith(".webm"):
        return AudioFileFormat.WEBM
    elif "flac" in content_type_lower or filename_lower.endswith(".flac"):
        return AudioFileFormat.FLAC
    elif "m4a" in content_type_lower or filename_lower.endswith(".m4a"):
        return AudioFileFormat.M4A
    else:
        return AudioFileFormat.MP3


def _determine_error_type(language: str) -> str:
    """Determine whether to use WER or CER based on language."""
    return "CER" if language in CJK_LANGUAGES else "WER"


def _calculate_audio_metadata(audio_bytes: bytes) -> tuple[int, int]:
    """Calculate duration and sample rate from audio bytes."""
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        duration_ms = len(audio)
        sample_rate = audio.frame_rate
        return duration_ms, sample_rate
    except Exception:
        # Fallback if pydub fails
        return 0, 16000


@router.get("/providers", response_model=STTProvidersListResponse)
async def list_providers():
    """List available STT providers with their capabilities."""
    providers_info = []
    for provider_data in STTProviderFactory.list_providers():
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
    current_user: CurrentUserDep,
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    provider: str = Form(..., description="STT provider name"),
    language: str = Form(default="zh-TW", description="Language code"),
    child_mode: bool = Form(default=False, description="Enable child speech mode"),
    ground_truth: str | None = Form(default=None, description="Ground truth text"),
    save_to_history: bool = Form(  # noqa: ARG001
        default=True, description="Save to history"
    ),  # Reserved for future use
    stt_service: STTService = Depends(get_stt_service),
    storage_service: IStorageService = Depends(get_storage_service),
    transcription_repo: ITranscriptionRepository = Depends(get_transcription_repository),
):
    """Transcribe audio to text."""
    try:
        user_id = uuid.UUID(current_user.id)
        logger.info(
            f"Starting transcription: user_id={user_id}, provider={provider}, "
            f"language={language}, child_mode={child_mode}"
        )

        # 1. Validate Provider
        try:
            provider_info = STTProviderFactory.get_provider_info(provider)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # 2. Read and validate audio data
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

        # Calculate metadata
        duration_ms, sample_rate = _calculate_audio_metadata(audio_bytes)

        # 3. Save Audio File (upload to storage and create entity)
        storage_path = await storage_service.save(
            audio_bytes, f"stt/uploads/{user_id}/{uuid.uuid4()}.{audio_format.value}"
        )

        audio_file = AudioFile(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=audio.filename or "unknown",
            format=audio_format,
            duration_ms=duration_ms,
            sample_rate=sample_rate,
            file_size_bytes=len(audio_bytes),
            storage_path=storage_path,
            source=AudioSource.UPLOAD,
        )

        await transcription_repo.save_audio_file(audio_file)

        # 4. Save Ground Truth if provided
        gt_entity = None
        if ground_truth:
            from src.domain.entities.ground_truth import GroundTruth

            gt_entity = GroundTruth(
                id=uuid.uuid4(), audio_file_id=audio_file.id, text=ground_truth, language=language
            )
            await transcription_repo.save_ground_truth(gt_entity)

        # 5. Call STT Service
        result, record_id, result_id = await stt_service.transcribe_audio(
            user_id=user_id,
            audio_file_id=audio_file.id,
            provider_name=provider,
            language=language,
            child_mode=child_mode,
        )

        # 6. Convert response
        words = None
        if result.words:
            words = [
                WordTimingResponse(
                    word=wt.word,
                    start_ms=wt.start_ms,
                    end_ms=wt.end_ms,
                    confidence=wt.confidence,
                )
                for wt in result.words
            ]

        # 7. WER Analysis Calculation (if ground truth provided)
        wer_analysis = None
        wer_val = None
        cer_val = None

        if ground_truth and gt_entity:
            from src.domain.services.wer_calculator import (
                calculate_alignment,
                calculate_cer,
                calculate_wer,
            )

            error_type = _determine_error_type(language)

            if error_type == "CER":
                cer_val = calculate_cer(ground_truth, result.transcript)
                error_rate = cer_val
                ref_tokens = list(ground_truth.replace(" ", ""))
                hyp_tokens = list(result.transcript.replace(" ", ""))
            else:
                wer_val = calculate_wer(ground_truth, result.transcript)
                error_rate = wer_val
                ref_tokens = ground_truth.split()
                hyp_tokens = result.transcript.split()

            _, insertions, deletions, substitutions = calculate_alignment(ref_tokens, hyp_tokens)

            wer_analysis = WERAnalysisResponse(
                error_rate=error_rate,
                error_type=error_type,
                insertions=insertions,
                deletions=deletions,
                substitutions=substitutions,
                total_reference=len(ref_tokens),
            )

            # Save WER Analysis
            from src.domain.entities.wer_analysis import WERAnalysis

            wer_entity = WERAnalysis(
                id=uuid.uuid4(),
                result_id=result_id,
                ground_truth_id=gt_entity.id,
                error_rate=error_rate or 0.0,
                error_type=error_type,
                insertions=insertions,
                deletions=deletions,
                substitutions=substitutions,
                alignment=None,
            )
            await transcription_repo.save_wer_analysis(wer_entity)

        logger.info(
            f"Transcription completed: record_id={record_id}, provider={provider}, "
            f"latency_ms={result.latency_ms}, confidence={result.confidence}"
        )

        return STTTranscribeResponse(
            id=str(record_id),
            transcript=result.transcript,
            provider=result.provider,
            language=result.language,
            latency_ms=result.latency_ms,
            confidence=result.confidence or 0.0,
            words=words,
            audio_duration_ms=result.audio_duration_ms,
            wer_analysis=wer_analysis,
            created_at=datetime.utcnow().isoformat() + "Z",
            wer=wer_val,
            cer=cer_val,
            record_id=str(record_id),
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Transcription validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") from e


@router.post("/analysis/wer", response_model=WERAnalysisResponse)
async def calculate_error_rate_endpoint(
    data: WERAnalysisRequest,
    transcription_repo: ITranscriptionRepository = Depends(get_transcription_repository),
):
    """Calculate WER/CER for a transcription result."""
    try:
        result_id = uuid.UUID(data.result_id)
        logger.info(f"Calculating error rate for result_id={result_id}")
        stt_result = await transcription_repo.get_transcription(result_id)
        if not stt_result:
            raise HTTPException(status_code=404, detail="Transcription not found")

        from src.domain.services.wer_calculator import (
            calculate_alignment,
            calculate_cer,
            calculate_wer,
        )

        language = stt_result.language
        error_type = _determine_error_type(language)

        if error_type == "CER":
            error_rate = calculate_cer(data.ground_truth, stt_result.transcript)
            ref_tokens = list(data.ground_truth.replace(" ", ""))
            hyp_tokens = list(stt_result.transcript.replace(" ", ""))
        else:
            error_rate = calculate_wer(data.ground_truth, stt_result.transcript)
            ref_tokens = data.ground_truth.split()
            hyp_tokens = stt_result.transcript.split()

        _, insertions, deletions, substitutions = calculate_alignment(ref_tokens, hyp_tokens)

        logger.info(
            f"Error rate calculated: result_id={result_id}, "
            f"error_type={error_type}, error_rate={error_rate:.4f}"
        )

        return WERAnalysisResponse(
            error_rate=error_rate,
            error_type=error_type,
            insertions=insertions,
            deletions=deletions,
            substitutions=substitutions,
            total_reference=len(ref_tokens),
        )
    except ValueError as e:
        logger.error(f"Error rate calculation validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error rate calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/history", response_model=TranscriptionHistoryPage)
async def list_history(
    current_user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    provider: str | None = None,
    language: str | None = None,
    transcription_repo: ITranscriptionRepository = Depends(get_transcription_repository),
):
    """List transcription history."""
    try:
        user_id = uuid.UUID(current_user.id)
        logger.info(
            f"Fetching transcription history: user_id={user_id}, page={page}, "
            f"page_size={page_size}, provider={provider}, language={language}"
        )
        items, total = await transcription_repo.list_transcriptions(
            user_id=user_id, provider=provider, language=language, page=page, page_size=page_size
        )

        total_pages = (total + page_size - 1) // page_size

        summary_items = [TranscriptionSummary(**item) for item in items]

        logger.info(f"Retrieved {len(items)} transcriptions (total={total}) for user_id={user_id}")

        return TranscriptionHistoryPage(
            items=summary_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error(f"Failed to fetch transcription history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/history/{id}", response_model=TranscriptionDetail)
async def get_history_detail(
    id: str,
    _current_user: CurrentUserDep,  # noqa: ARG001 - Auth required but ID unused
    transcription_repo: ITranscriptionRepository = Depends(get_transcription_repository),
):
    """Get detailed transcription record."""
    try:
        logger.info(f"Fetching transcription detail: id={id}")
        detail = await transcription_repo.get_transcription_detail(uuid.UUID(id))
        if not detail:
            logger.warning(f"Transcription detail not found: id={id}")
            raise HTTPException(status_code=404, detail="Transcription not found")

        logger.info(f"Retrieved transcription detail: id={id}")
        return TranscriptionDetail(**detail)
    except ValueError as e:
        logger.error(f"Invalid transcription ID: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/history/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
    id: str,
    _current_user: CurrentUserDep,  # noqa: ARG001 - Auth required but ID unused
    transcription_repo: ITranscriptionRepository = Depends(get_transcription_repository),
):
    """Delete a transcription record."""
    try:
        logger.info(f"Deleting transcription: id={id}")
        success = await transcription_repo.delete_transcription(uuid.UUID(id))
        if not success:
            logger.warning(f"Transcription not found for deletion: id={id}")
            raise HTTPException(status_code=404, detail="Transcription not found")
        logger.info(f"Successfully deleted transcription: id={id}")
    except ValueError as e:
        logger.error(f"Invalid transcription ID for deletion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/compare", response_model=ComparisonResponse)
async def compare_providers(
    current_user: CurrentUserDep,
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    providers: list[str] = Form(..., description="List of providers to compare"),
    language: str = Form(default="zh-TW"),
    ground_truth: str | None = Form(default=None),
    stt_service: STTService = Depends(get_stt_service),
    storage_service: IStorageService = Depends(get_storage_service),
    transcription_repo: ITranscriptionRepository = Depends(get_transcription_repository),
):
    """Compare multiple providers."""
    try:
        user_id = uuid.UUID(current_user.id)
        logger.info(
            f"Starting provider comparison: user_id={user_id}, providers={providers}, "
            f"language={language}"
        )

        # 1. Save Audio (Once)
        audio_bytes = await audio.read()
        audio_format = _get_audio_format(audio.content_type or "", audio.filename or "")
        duration_ms, sample_rate = _calculate_audio_metadata(audio_bytes)

        storage_path = await storage_service.save(
            audio_bytes, f"stt/uploads/{user_id}/{uuid.uuid4()}.{audio_format.value}"
        )

        audio_file = AudioFile(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=audio.filename or "unknown",
            format=audio_format,
            duration_ms=duration_ms,
            sample_rate=sample_rate,
            file_size_bytes=len(audio_bytes),
            storage_path=storage_path,
            source=AudioSource.UPLOAD,
        )
        await transcription_repo.save_audio_file(audio_file)

        # Save Ground Truth
        if ground_truth:
            from src.domain.entities.ground_truth import GroundTruth

            gt = GroundTruth(
                id=uuid.uuid4(), audio_file_id=audio_file.id, text=ground_truth, language=language
            )
            await transcription_repo.save_ground_truth(gt)

        # 2. Process Providers in Parallel (T077 Performance Optimization)
        async def _transcribe_one_provider(provider_name: str) -> tuple | None:
            """Transcribe audio with one provider, returning (response, table_entry) or None on error."""
            try:
                logger.info(f"Comparing provider: {provider_name}")
                result, record_id, result_id = await stt_service.transcribe_audio(
                    user_id=user_id,
                    audio_file_id=audio_file.id,
                    provider_name=provider_name,
                    language=language,
                )

                # Calculate WER
                error_rate = None
                if ground_truth:
                    from src.domain.services.wer_calculator import calculate_cer, calculate_wer

                    error_type = _determine_error_type(language)
                    if error_type == "CER":
                        error_rate = calculate_cer(ground_truth, result.transcript)
                    else:
                        error_rate = calculate_wer(ground_truth, result.transcript)

                # Convert to response
                words = (
                    [
                        WordTimingResponse(
                            word=w.word,
                            start_ms=w.start_ms,
                            end_ms=w.end_ms,
                            confidence=w.confidence,
                        )
                        for w in result.words
                    ]
                    if result.words
                    else None
                )

                transcribe_response = STTTranscribeResponse(
                    id=str(record_id),
                    transcript=result.transcript,
                    provider=result.provider,
                    language=result.language,
                    latency_ms=result.latency_ms,
                    confidence=result.confidence or 0.0,
                    words=words,
                    created_at=datetime.utcnow().isoformat() + "Z",
                    record_id=str(record_id),
                )

                logger.info(
                    f"Provider comparison result: provider={provider_name}, "
                    f"latency_ms={result.latency_ms}, confidence={result.confidence}"
                )

                table_entry = {
                    "provider": provider_name,
                    "transcript": result.transcript,
                    "confidence": result.confidence,
                    "latency_ms": result.latency_ms,
                    "error_rate": error_rate,
                    "error_type": _determine_error_type(language)
                    if error_rate is not None
                    else None,
                }

                return (transcribe_response, table_entry)

            except Exception as e:
                # Log error but continue with other providers
                logger.warning(
                    f"Comparison failed for provider {provider_name}: {str(e)}", exc_info=True
                )
                return None

        # Execute all providers in parallel
        provider_tasks = [_transcribe_one_provider(provider_name) for provider_name in providers]
        provider_results = await asyncio.gather(*provider_tasks)

        # Collect successful results
        results = []
        comparison_table = []
        for provider_result in provider_results:
            if provider_result is not None:
                response, table_entry = provider_result
                results.append(response)
                comparison_table.append(table_entry)

        logger.info(
            f"Provider comparison completed: {len(results)}/{len(providers)} providers succeeded"
        )

        return ComparisonResponse(
            audio_file_id=str(audio_file.id),
            results=results,
            ground_truth=ground_truth,
            comparison_table=comparison_table,
        )

    except Exception as e:
        logger.error(f"Provider comparison failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
