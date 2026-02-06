"""Transcription Repository Implementation.

Feature: 003-stt-testing-module
SQLAlchemy implementation for STT transcription persistence.
"""

from uuid import UUID

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.audio_file import AudioFile
from src.domain.entities.ground_truth import GroundTruth
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.domain.entities.wer_analysis import WERAnalysis
from src.domain.repositories.transcription_repository import ITranscriptionRepository
from src.infrastructure.persistence.models import (
    AudioFileModel,
    GroundTruthModel,
    TranscriptionRequestModel,
    TranscriptionResultModel,
    WERAnalysisModel,
    WordTimingModel,
)


class TranscriptionRepositoryImpl(ITranscriptionRepository):
    """SQLAlchemy implementation of TranscriptionRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # --- AudioFile Operations ---

    async def save_audio_file(self, audio_file: AudioFile) -> AudioFile:
        model = AudioFileModel(
            id=audio_file.id,
            user_id=audio_file.user_id,
            filename=audio_file.filename,
            format=audio_file.format,
            duration_ms=audio_file.duration_ms,
            sample_rate=audio_file.sample_rate,
            file_size_bytes=audio_file.file_size_bytes,
            storage_path=audio_file.storage_path,
            source=audio_file.source,
            created_at=audio_file.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return audio_file

    async def get_audio_file(self, audio_file_id: UUID) -> AudioFile | None:
        stmt = select(AudioFileModel).where(AudioFileModel.id == audio_file_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return AudioFile(
            id=model.id,
            user_id=model.user_id,
            filename=model.filename,
            format=model.format,
            duration_ms=model.duration_ms,
            sample_rate=model.sample_rate,
            file_size_bytes=model.file_size_bytes,
            storage_path=model.storage_path,
            source=model.source,
            created_at=model.created_at,
        )

    async def delete_audio_file(self, audio_file_id: UUID) -> bool:
        stmt = delete(AudioFileModel).where(AudioFileModel.id == audio_file_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    # --- Transcription Result Operations ---

    async def save_transcription(
        self,
        result: STTResult,
        audio_file_id: UUID,
        _user_id: UUID,  # noqa: ARG002 - Required by interface but unused
    ) -> tuple[UUID, UUID]:
        # 1. Create Request
        request_model = TranscriptionRequestModel(
            audio_file_id=audio_file_id,
            provider=result.provider,
            language=result.language,
            child_mode=result.request.child_mode,
            status="completed",
        )
        self._session.add(request_model)
        await self._session.flush()  # Get ID

        # 2. Create Result
        result_model = TranscriptionResultModel(
            request_id=request_model.id,
            transcript=result.transcript,
            confidence=result.confidence,
            latency_ms=result.latency_ms,
            metadata_=result.metadata,
            created_at=result.created_at,
        )
        self._session.add(result_model)
        await self._session.flush()

        # 3. Create Words
        if result.words:
            words_models = [
                WordTimingModel(
                    result_id=result_model.id,
                    word=w.word,
                    start_ms=w.start_ms,
                    end_ms=w.end_ms,
                    confidence=w.confidence,
                    speaker_id=w.speaker_id,
                )
                for w in result.words
            ]
            self._session.add_all(words_models)

        await self._session.commit()
        return request_model.id, result_model.id

    async def get_transcription(self, transcription_id: UUID) -> STTResult | None:
        # transcription_id is request_id
        stmt = (
            select(TranscriptionRequestModel)
            .options(
                selectinload(TranscriptionRequestModel.result).selectinload(
                    TranscriptionResultModel.words
                )
            )
            .where(TranscriptionRequestModel.id == transcription_id)
        )
        result = await self._session.execute(stmt)
        request_model = result.scalar_one_or_none()

        if not request_model or not request_model.result:
            return None

        # Reconstruct domain entity
        stt_request = STTRequest(
            provider=request_model.provider,
            language=request_model.language,
            child_mode=request_model.child_mode,
        )

        word_timings = [
            WordTiming(
                word=w.word,
                start_ms=w.start_ms,
                end_ms=w.end_ms,
                confidence=w.confidence,
                speaker_id=w.speaker_id,
            )
            for w in request_model.result.words
        ]

        return STTResult(
            request=stt_request,
            transcript=request_model.result.transcript,
            confidence=request_model.result.confidence,
            latency_ms=request_model.result.latency_ms,
            words=word_timings,
            metadata=request_model.result.metadata_ or {},
            created_at=request_model.result.created_at,
        )

    async def list_transcriptions(
        self,
        user_id: UUID,
        provider: str | None = None,
        language: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        # Query Requests joined with AudioFile (filtered by user_id)
        query = (
            select(TranscriptionRequestModel)
            .join(AudioFileModel)
            .where(AudioFileModel.user_id == user_id)
            .order_by(desc(TranscriptionRequestModel.created_at))
        )

        if provider:
            query = query.where(TranscriptionRequestModel.provider == provider)
        if language:
            query = query.where(TranscriptionRequestModel.language == language)

        # Count
        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        # Pagination
        stmt = (
            query.options(
                selectinload(TranscriptionRequestModel.result).selectinload(
                    TranscriptionResultModel.wer_analysis
                )
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self._session.execute(stmt)
        requests = result.scalars().all()

        items = []
        for req in requests:
            if not req.result:
                continue

            # Construct summary
            item = {
                "id": str(req.id),
                "provider": req.provider,
                "language": req.language,
                "transcript_preview": req.result.transcript[:100] + "..."
                if len(req.result.transcript) > 100
                else req.result.transcript,
                "duration_ms": None,
                "confidence": req.result.confidence,
                "has_ground_truth": False,
                "error_rate": None,
                "created_at": req.created_at.isoformat(),
            }

            if req.result.wer_analysis:
                item["error_rate"] = req.result.wer_analysis.error_rate
                item["has_ground_truth"] = True

            items.append(item)

        return items, total

    async def delete_transcription(self, transcription_id: UUID) -> bool:
        # Delete request (cascades to result, words, wer)
        stmt = delete(TranscriptionRequestModel).where(
            TranscriptionRequestModel.id == transcription_id
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    # --- Ground Truth Operations ---

    async def save_ground_truth(self, ground_truth: GroundTruth) -> GroundTruth:
        model = GroundTruthModel(
            id=ground_truth.id,
            audio_file_id=ground_truth.audio_file_id,
            text=ground_truth.text,
            language=ground_truth.language,
            created_at=ground_truth.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ground_truth

    async def get_ground_truth(self, audio_file_id: UUID) -> GroundTruth | None:
        stmt = select(GroundTruthModel).where(GroundTruthModel.audio_file_id == audio_file_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return GroundTruth(
            id=model.id,
            audio_file_id=model.audio_file_id,
            text=model.text,
            language=model.language,
            created_at=model.created_at,
        )

    async def update_ground_truth(
        self, audio_file_id: UUID, text: str, language: str
    ) -> GroundTruth | None:
        stmt = select(GroundTruthModel).where(GroundTruthModel.audio_file_id == audio_file_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        model.text = text
        model.language = language
        await self._session.commit()
        await self._session.refresh(model)

        return GroundTruth(
            id=model.id,
            audio_file_id=model.audio_file_id,
            text=model.text,
            language=model.language,
            created_at=model.created_at,
        )

    # --- WER Analysis Operations ---

    async def save_wer_analysis(self, analysis: WERAnalysis) -> WERAnalysis:
        model = WERAnalysisModel(
            id=analysis.id,
            result_id=analysis.result_id,
            ground_truth_id=analysis.ground_truth_id,
            error_rate=analysis.error_rate,
            error_type=analysis.error_type,
            insertions=analysis.insertions,
            deletions=analysis.deletions,
            substitutions=analysis.substitutions,
            alignment=analysis.alignment,
            created_at=analysis.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return analysis

    async def get_wer_analysis(self, result_id: UUID) -> WERAnalysis | None:
        stmt = select(WERAnalysisModel).where(WERAnalysisModel.result_id == result_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return WERAnalysis(
            id=model.id,
            result_id=model.result_id,
            ground_truth_id=model.ground_truth_id,
            error_rate=model.error_rate,
            error_type=model.error_type,
            insertions=model.insertions,
            deletions=model.deletions,
            substitutions=model.substitutions,
            alignment=model.alignment,
            created_at=model.created_at,
        )

    # --- Detailed Retrieval ---

    async def get_transcription_detail(self, transcription_id: UUID) -> dict | None:
        stmt = (
            select(TranscriptionRequestModel)
            .options(
                selectinload(TranscriptionRequestModel.result).selectinload(
                    TranscriptionResultModel.words
                ),
                selectinload(TranscriptionRequestModel.result).selectinload(
                    TranscriptionResultModel.wer_analysis
                ),
                selectinload(TranscriptionRequestModel.audio_file).selectinload(
                    AudioFileModel.ground_truth
                ),
            )
            .where(TranscriptionRequestModel.id == transcription_id)
        )
        result = await self._session.execute(stmt)
        req = result.scalar_one_or_none()

        if not req or not req.result:
            return None

        # Construct detail dict
        detail = {
            "id": str(req.id),
            "provider": req.provider,
            "transcript": req.result.transcript,
            "confidence": req.result.confidence,
            "latency_ms": req.result.latency_ms,
            "language": req.language,
            "words": [
                {
                    "word": w.word,
                    "start_ms": w.start_ms,
                    "end_ms": w.end_ms,
                    "confidence": w.confidence,
                    "speaker_id": w.speaker_id,
                }
                for w in req.result.words
            ],
            "created_at": req.result.created_at.isoformat(),
            "audio_file": {
                "id": str(req.audio_file.id),
                "filename": req.audio_file.filename,
                "duration_ms": req.audio_file.duration_ms,
                "format": req.audio_file.format,
            },
            "child_mode": req.child_mode,
        }

        if req.result.wer_analysis:
            detail["wer_analysis"] = {
                "error_rate": req.result.wer_analysis.error_rate,
                "error_type": req.result.wer_analysis.error_type,
                "insertions": req.result.wer_analysis.insertions,
                "deletions": req.result.wer_analysis.deletions,
                "substitutions": req.result.wer_analysis.substitutions,
                "alignment": req.result.wer_analysis.alignment,
            }

        if req.audio_file.ground_truth:
            detail["ground_truth"] = req.audio_file.ground_truth.text

        return detail
