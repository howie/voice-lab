"""Audit Log domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditEventType(str, Enum):
    """Audit event types for credential operations."""

    CREDENTIAL_CREATED = "credential.created"
    CREDENTIAL_UPDATED = "credential.updated"
    CREDENTIAL_DELETED = "credential.deleted"
    CREDENTIAL_VALIDATED = "credential.validated"
    CREDENTIAL_VALIDATION_FAILED = "credential.validation_failed"
    CREDENTIAL_USED = "credential.used"
    CREDENTIAL_VIEWED = "credential.viewed"
    MODEL_SELECTED = "model.selected"


class AuditOutcome(str, Enum):
    """Outcome of an audited operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class AuditLog:
    """Audit log entry for security and compliance tracking.

    Records all credential-related operations for traceability.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    event_type: AuditEventType
    outcome: AuditOutcome
    provider: str | None = None
    resource_id: uuid.UUID | None = None  # Credential ID
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate audit log attributes."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not isinstance(self.event_type, AuditEventType):
            raise ValueError("Invalid event type")
        if not isinstance(self.outcome, AuditOutcome):
            raise ValueError("Invalid outcome")

    @staticmethod
    def create(
        user_id: uuid.UUID,
        event_type: AuditEventType,
        outcome: AuditOutcome,
        provider: str | None = None,
        resource_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "AuditLog":
        """Factory method to create an audit log entry."""
        return AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            outcome=outcome,
            provider=provider,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )
