"""SQLAlchemy implementation of InteractionRepository.

T015: Concrete repository implementation for interaction sessions.
"""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import (
    ConversationTurn,
    InteractionMode,
    InteractionSession,
    LatencyMetrics,
    SessionStatus,
)
from src.domain.repositories.interaction_repository import InteractionRepository
from src.infrastructure.persistence.models import (
    ConversationTurnModel,
    InteractionSessionModel,
    LatencyMetricsModel,
)


class SQLAlchemyInteractionRepository(InteractionRepository):
    """SQLAlchemy-based implementation of InteractionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Session operations
    async def create_session(self, session: InteractionSession) -> InteractionSession:
        model = InteractionSessionModel(
            id=session.id,
            user_id=session.user_id,
            mode=session.mode,
            provider_config=session.provider_config,
            system_prompt=session.system_prompt,
            started_at=session.started_at,
            ended_at=session.ended_at,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return session

    async def get_session(self, session_id: UUID) -> InteractionSession | None:
        result = await self._session.execute(
            select(InteractionSessionModel).where(InteractionSessionModel.id == session_id)
        )
        model = result.scalar_one_or_none()
        return self._session_model_to_entity(model) if model else None

    async def update_session(self, session: InteractionSession) -> InteractionSession:
        result = await self._session.execute(
            select(InteractionSessionModel).where(InteractionSessionModel.id == session.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.mode = session.mode
            model.provider_config = session.provider_config
            model.system_prompt = session.system_prompt
            model.ended_at = session.ended_at
            model.status = session.status
            model.updated_at = session.updated_at
            await self._session.flush()
        return session

    async def delete_session(self, session_id: UUID) -> bool:
        result = await self._session.execute(
            select(InteractionSessionModel).where(InteractionSessionModel.id == session_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    async def list_sessions(
        self,
        user_id: UUID,
        mode: InteractionMode | None = None,
        status: SessionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[InteractionSession], int]:
        query = select(InteractionSessionModel).where(InteractionSessionModel.user_id == user_id)

        if mode:
            query = query.where(InteractionSessionModel.mode == mode)
        if status:
            query = query.where(InteractionSessionModel.status == status)
        if start_date:
            query = query.where(InteractionSessionModel.started_at >= start_date)
        if end_date:
            query = query.where(InteractionSessionModel.started_at <= end_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        # Paginate
        query = query.order_by(InteractionSessionModel.started_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(query)
        models = result.scalars().all()

        sessions = [self._session_model_to_entity(m) for m in models]
        return sessions, total

    # Turn operations
    async def create_turn(self, turn: ConversationTurn) -> ConversationTurn:
        model = ConversationTurnModel(
            id=turn.id,
            session_id=turn.session_id,
            turn_number=turn.turn_number,
            user_audio_path=turn.user_audio_path,
            user_transcript=turn.user_transcript,
            ai_response_text=turn.ai_response_text,
            ai_audio_path=turn.ai_audio_path,
            interrupted=turn.interrupted,
            started_at=turn.started_at,
            ended_at=turn.ended_at,
            created_at=turn.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return turn

    async def get_turn(self, turn_id: UUID) -> ConversationTurn | None:
        result = await self._session.execute(
            select(ConversationTurnModel).where(ConversationTurnModel.id == turn_id)
        )
        model = result.scalar_one_or_none()
        return self._turn_model_to_entity(model) if model else None

    async def update_turn(self, turn: ConversationTurn) -> ConversationTurn:
        result = await self._session.execute(
            select(ConversationTurnModel).where(ConversationTurnModel.id == turn.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.user_audio_path = turn.user_audio_path
            model.user_transcript = turn.user_transcript
            model.ai_response_text = turn.ai_response_text
            model.ai_audio_path = turn.ai_audio_path
            model.interrupted = turn.interrupted
            model.ended_at = turn.ended_at
            await self._session.flush()
        return turn

    async def list_turns(self, session_id: UUID) -> Sequence[ConversationTurn]:
        result = await self._session.execute(
            select(ConversationTurnModel)
            .where(ConversationTurnModel.session_id == session_id)
            .order_by(ConversationTurnModel.turn_number)
        )
        models = result.scalars().all()
        return [self._turn_model_to_entity(m) for m in models]

    async def get_next_turn_number(self, session_id: UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(ConversationTurnModel.turn_number), 0)).where(
                ConversationTurnModel.session_id == session_id
            )
        )
        max_turn = result.scalar() or 0
        return max_turn + 1

    # Latency operations
    async def create_latency_metrics(self, metrics: LatencyMetrics) -> LatencyMetrics:
        model = LatencyMetricsModel(
            id=metrics.id,
            turn_id=metrics.turn_id,
            total_latency_ms=metrics.total_latency_ms,
            stt_latency_ms=metrics.stt_latency_ms,
            llm_ttft_ms=metrics.llm_ttft_ms,
            tts_ttfb_ms=metrics.tts_ttfb_ms,
            realtime_latency_ms=metrics.realtime_latency_ms,
            created_at=metrics.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return metrics

    async def get_latency_metrics(self, turn_id: UUID) -> LatencyMetrics | None:
        result = await self._session.execute(
            select(LatencyMetricsModel).where(LatencyMetricsModel.turn_id == turn_id)
        )
        model = result.scalar_one_or_none()
        return self._latency_model_to_entity(model) if model else None

    async def get_session_latency_stats(self, session_id: UUID) -> dict[str, float | int | None]:
        # Get all latency metrics for session turns
        result = await self._session.execute(
            select(LatencyMetricsModel)
            .join(ConversationTurnModel)
            .where(ConversationTurnModel.session_id == session_id)
        )
        models = result.scalars().all()

        if not models:
            return {
                "total_turns": 0,
                "avg_total_ms": None,
                "min_total_ms": None,
                "max_total_ms": None,
                "p95_total_ms": None,
                "avg_stt_ms": None,
                "avg_llm_ttft_ms": None,
                "avg_tts_ttfb_ms": None,
            }

        total_latencies = [m.total_latency_ms for m in models]
        stt_latencies = [m.stt_latency_ms for m in models if m.stt_latency_ms is not None]
        llm_latencies = [m.llm_ttft_ms for m in models if m.llm_ttft_ms is not None]
        tts_latencies = [m.tts_ttfb_ms for m in models if m.tts_ttfb_ms is not None]

        # Calculate P95
        sorted_total = sorted(total_latencies)
        p95_idx = int(len(sorted_total) * 0.95)
        p95_total = sorted_total[min(p95_idx, len(sorted_total) - 1)]

        return {
            "total_turns": len(models),
            "avg_total_ms": sum(total_latencies) / len(total_latencies),
            "min_total_ms": min(total_latencies),
            "max_total_ms": max(total_latencies),
            "p95_total_ms": p95_total,
            "avg_stt_ms": sum(stt_latencies) / len(stt_latencies) if stt_latencies else None,
            "avg_llm_ttft_ms": sum(llm_latencies) / len(llm_latencies) if llm_latencies else None,
            "avg_tts_ttfb_ms": sum(tts_latencies) / len(tts_latencies) if tts_latencies else None,
        }

    # Helper methods
    def _session_model_to_entity(self, model: InteractionSessionModel) -> InteractionSession:
        return InteractionSession(
            id=model.id,
            user_id=model.user_id,
            mode=model.mode,
            provider_config=model.provider_config,
            system_prompt=model.system_prompt,
            started_at=model.started_at,
            ended_at=model.ended_at,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _turn_model_to_entity(self, model: ConversationTurnModel) -> ConversationTurn:
        return ConversationTurn(
            id=model.id,
            session_id=model.session_id,
            turn_number=model.turn_number,
            user_audio_path=model.user_audio_path,
            user_transcript=model.user_transcript,
            ai_response_text=model.ai_response_text,
            ai_audio_path=model.ai_audio_path,
            interrupted=model.interrupted,
            started_at=model.started_at,
            ended_at=model.ended_at,
            created_at=model.created_at,
        )

    def _latency_model_to_entity(self, model: LatencyMetricsModel) -> LatencyMetrics:
        return LatencyMetrics(
            id=model.id,
            turn_id=model.turn_id,
            total_latency_ms=model.total_latency_ms,
            stt_latency_ms=model.stt_latency_ms,
            llm_ttft_ms=model.llm_ttft_ms,
            tts_ttfb_ms=model.tts_ttfb_ms,
            realtime_latency_ms=model.realtime_latency_ms,
            created_at=model.created_at,
        )
