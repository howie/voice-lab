"""Audit Log Repository Interface."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.audit_log import AuditEventType, AuditLog


class IAuditLogRepository(ABC):
    """Abstract repository interface for audit logs.

    This interface defines the contract for audit log storage operations.
    """

    @abstractmethod
    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Save an audit log entry.

        Args:
            audit_log: Audit log to save

        Returns:
            Saved audit log
        """
        pass

    @abstractmethod
    async def get_by_id(self, log_id: uuid.UUID) -> AuditLog | None:
        """Get an audit log by ID.

        Args:
            log_id: Audit log ID

        Returns:
            Audit log if found, None otherwise
        """
        pass

    @abstractmethod
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
        """List audit logs for a user with optional filters.

        Args:
            user_id: User ID
            event_type: Optional filter by event type
            provider: Optional filter by provider
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit logs matching the filters
        """
        pass

    @abstractmethod
    async def list_by_resource(
        self,
        resource_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """List audit logs for a specific resource (credential).

        Args:
            resource_id: Resource ID (credential ID)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit logs for the resource
        """
        pass

    @abstractmethod
    async def count_by_user(
        self,
        user_id: uuid.UUID,
        event_type: AuditEventType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count audit logs for a user with optional filters.

        Args:
            user_id: User ID
            event_type: Optional filter by event type
            start_date: Optional filter by start date
            end_date: Optional filter by end date

        Returns:
            Count of matching audit logs
        """
        pass
