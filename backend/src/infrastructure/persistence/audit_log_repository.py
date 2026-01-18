"""SQLAlchemy implementation of Audit Log Repository."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.audit_log import AuditEventType, AuditLog, AuditOutcome
from src.domain.repositories.audit_log_repository import IAuditLogRepository
from src.infrastructure.persistence.models import AuditLogModel


class SQLAlchemyAuditLogRepository(IAuditLogRepository):
    """SQLAlchemy implementation of the audit log repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Save an audit log entry."""
        model = AuditLogModel(
            id=audit_log.id,
            user_id=audit_log.user_id,
            event_type=audit_log.event_type.value,
            provider=audit_log.provider,
            resource_id=audit_log.resource_id,
            timestamp=audit_log.timestamp,
            details=audit_log.details,
            outcome=audit_log.outcome.value,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
        )
        self._session.add(model)
        await self._session.flush()
        return audit_log

    async def get_by_id(self, log_id: uuid.UUID) -> AuditLog | None:
        """Get an audit log by ID."""
        stmt = select(AuditLogModel).where(AuditLogModel.id == log_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        event_type: AuditEventType | None = None,
        provider: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """List audit logs for a user with optional filters."""
        stmt = select(AuditLogModel).where(AuditLogModel.user_id == user_id)

        if event_type is not None:
            stmt = stmt.where(AuditLogModel.event_type == event_type.value)
        if provider is not None:
            stmt = stmt.where(AuditLogModel.provider == provider)
        if start_date is not None:
            stmt = stmt.where(AuditLogModel.timestamp >= start_date)
        if end_date is not None:
            stmt = stmt.where(AuditLogModel.timestamp <= end_date)

        stmt = stmt.order_by(AuditLogModel.timestamp.desc()).offset(offset).limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def list_by_resource(
        self,
        resource_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """List audit logs for a specific resource (credential)."""
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.resource_id == resource_id)
            .order_by(AuditLogModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_by_user(
        self,
        user_id: uuid.UUID,
        event_type: AuditEventType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count audit logs for a user with optional filters."""
        stmt = select(func.count()).select_from(AuditLogModel).where(
            AuditLogModel.user_id == user_id
        )

        if event_type is not None:
            stmt = stmt.where(AuditLogModel.event_type == event_type.value)
        if start_date is not None:
            stmt = stmt.where(AuditLogModel.timestamp >= start_date)
        if end_date is not None:
            stmt = stmt.where(AuditLogModel.timestamp <= end_date)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    def _to_entity(model: AuditLogModel) -> AuditLog:
        """Convert SQLAlchemy model to domain entity."""
        return AuditLog(
            id=model.id,
            user_id=model.user_id,
            event_type=AuditEventType(model.event_type),
            provider=model.provider,
            resource_id=model.resource_id,
            timestamp=model.timestamp,
            details=model.details,
            outcome=AuditOutcome(model.outcome),
            ip_address=model.ip_address,
            user_agent=model.user_agent,
        )
