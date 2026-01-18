"""Audit Service for logging credential operations."""

import uuid
from typing import Any

from src.domain.entities.audit_log import AuditEventType, AuditLog, AuditOutcome
from src.domain.repositories.audit_log_repository import IAuditLogRepository


class AuditService:
    """Service for logging credential operations to audit trail.

    This service provides a high-level interface for creating audit log entries
    for all credential-related operations.
    """

    def __init__(self, audit_repository: IAuditLogRepository):
        self._repository = audit_repository

    async def log_credential_created(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a credential creation event."""
        return await self._log_event(
            user_id=user_id,
            event_type=AuditEventType.CREDENTIAL_CREATED,
            outcome=AuditOutcome.SUCCESS,
            provider=provider,
            resource_id=credential_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_credential_updated(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a credential update event."""
        return await self._log_event(
            user_id=user_id,
            event_type=AuditEventType.CREDENTIAL_UPDATED,
            outcome=AuditOutcome.SUCCESS,
            provider=provider,
            resource_id=credential_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_credential_deleted(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a credential deletion event."""
        return await self._log_event(
            user_id=user_id,
            event_type=AuditEventType.CREDENTIAL_DELETED,
            outcome=AuditOutcome.SUCCESS,
            provider=provider,
            resource_id=credential_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_credential_validated(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        is_valid: bool,
        error_message: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a credential validation event."""
        event_type = (
            AuditEventType.CREDENTIAL_VALIDATED
            if is_valid
            else AuditEventType.CREDENTIAL_VALIDATION_FAILED
        )
        outcome = AuditOutcome.SUCCESS if is_valid else AuditOutcome.FAILURE
        details = {"error_message": error_message} if error_message else None

        return await self._log_event(
            user_id=user_id,
            event_type=event_type,
            outcome=outcome,
            provider=provider,
            resource_id=credential_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_credential_used(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        operation: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a credential usage event."""
        return await self._log_event(
            user_id=user_id,
            event_type=AuditEventType.CREDENTIAL_USED,
            outcome=AuditOutcome.SUCCESS,
            provider=provider,
            resource_id=credential_id,
            details={"operation": operation},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_credential_viewed(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a credential view event."""
        return await self._log_event(
            user_id=user_id,
            event_type=AuditEventType.CREDENTIAL_VIEWED,
            outcome=AuditOutcome.SUCCESS,
            provider=provider,
            resource_id=credential_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_model_selected(
        self,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
        provider: str,
        model_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a model selection event."""
        return await self._log_event(
            user_id=user_id,
            event_type=AuditEventType.MODEL_SELECTED,
            outcome=AuditOutcome.SUCCESS,
            provider=provider,
            resource_id=credential_id,
            details={"model_id": model_id},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _log_event(
        self,
        user_id: uuid.UUID,
        event_type: AuditEventType,
        outcome: AuditOutcome,
        provider: str | None = None,
        resource_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create and save an audit log entry."""
        audit_log = AuditLog.create(
            user_id=user_id,
            event_type=event_type,
            outcome=outcome,
            provider=provider,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self._repository.save(audit_log)
