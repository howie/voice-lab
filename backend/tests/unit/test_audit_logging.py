"""Unit tests for Audit Logging Service.

T075: Unit tests for audit logging service.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.services.audit_service import AuditService
from src.domain.entities.audit_log import AuditEventType, AuditLog, AuditOutcome


@pytest.fixture
def mock_audit_repository() -> AsyncMock:
    """Create a mock audit log repository."""
    repo = AsyncMock()

    # Configure save to return the audit log that was passed
    async def save_impl(audit_log: AuditLog) -> AuditLog:
        return audit_log

    repo.save.side_effect = save_impl
    return repo


@pytest.fixture
def audit_service(mock_audit_repository: AsyncMock) -> AuditService:
    """Create an AuditService with a mock repository."""
    return AuditService(mock_audit_repository)


@pytest.fixture
def user_id() -> uuid.UUID:
    """Create a test user ID."""
    return uuid.uuid4()


@pytest.fixture
def credential_id() -> uuid.UUID:
    """Create a test credential ID."""
    return uuid.uuid4()


class TestAuditServiceLogCredentialCreated:
    """Tests for log_credential_created method."""

    @pytest.mark.asyncio
    async def test_logs_credential_created_event(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that credential created events are logged correctly."""
        result = await audit_service.log_credential_created(
            user_id=user_id,
            credential_id=credential_id,
            provider="elevenlabs",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        assert result is not None
        assert result.user_id == user_id
        assert result.event_type == AuditEventType.CREDENTIAL_CREATED
        assert result.outcome == AuditOutcome.SUCCESS
        assert result.provider == "elevenlabs"
        assert result.resource_id == credential_id
        assert result.ip_address == "192.168.1.1"
        assert result.user_agent == "TestAgent/1.0"
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceLogCredentialUpdated:
    """Tests for log_credential_updated method."""

    @pytest.mark.asyncio
    async def test_logs_credential_updated_event(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that credential updated events are logged correctly."""
        result = await audit_service.log_credential_updated(
            user_id=user_id,
            credential_id=credential_id,
            provider="azure",
            details={"key_updated": True},
        )

        assert result is not None
        assert result.user_id == user_id
        assert result.event_type == AuditEventType.CREDENTIAL_UPDATED
        assert result.outcome == AuditOutcome.SUCCESS
        assert result.provider == "azure"
        assert result.details == {"key_updated": True}
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceLogCredentialDeleted:
    """Tests for log_credential_deleted method."""

    @pytest.mark.asyncio
    async def test_logs_credential_deleted_event(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that credential deleted events are logged correctly."""
        result = await audit_service.log_credential_deleted(
            user_id=user_id,
            credential_id=credential_id,
            provider="gemini",
        )

        assert result is not None
        assert result.user_id == user_id
        assert result.event_type == AuditEventType.CREDENTIAL_DELETED
        assert result.outcome == AuditOutcome.SUCCESS
        assert result.provider == "gemini"
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceLogCredentialValidated:
    """Tests for log_credential_validated method."""

    @pytest.mark.asyncio
    async def test_logs_successful_validation(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that successful validation events are logged correctly."""
        result = await audit_service.log_credential_validated(
            user_id=user_id,
            credential_id=credential_id,
            provider="elevenlabs",
            is_valid=True,
        )

        assert result is not None
        assert result.event_type == AuditEventType.CREDENTIAL_VALIDATED
        assert result.outcome == AuditOutcome.SUCCESS
        mock_audit_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_failed_validation(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that failed validation events are logged correctly."""
        result = await audit_service.log_credential_validated(
            user_id=user_id,
            credential_id=credential_id,
            provider="elevenlabs",
            is_valid=False,
            error_message="Invalid API key",
        )

        assert result is not None
        assert result.event_type == AuditEventType.CREDENTIAL_VALIDATION_FAILED
        assert result.outcome == AuditOutcome.FAILURE
        assert result.details == {"error_message": "Invalid API key"}
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceLogCredentialUsed:
    """Tests for log_credential_used method."""

    @pytest.mark.asyncio
    async def test_logs_credential_used_event(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that credential used events are logged correctly."""
        result = await audit_service.log_credential_used(
            user_id=user_id,
            credential_id=credential_id,
            provider="azure",
            operation="tts.synthesize",
            ip_address="10.0.0.1",
        )

        assert result is not None
        assert result.event_type == AuditEventType.CREDENTIAL_USED
        assert result.outcome == AuditOutcome.SUCCESS
        assert result.details == {"operation": "tts.synthesize"}
        assert result.ip_address == "10.0.0.1"
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceLogCredentialViewed:
    """Tests for log_credential_viewed method."""

    @pytest.mark.asyncio
    async def test_logs_credential_viewed_event(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that credential viewed events are logged correctly."""
        result = await audit_service.log_credential_viewed(
            user_id=user_id,
            credential_id=credential_id,
            provider="gemini",
        )

        assert result is not None
        assert result.event_type == AuditEventType.CREDENTIAL_VIEWED
        assert result.outcome == AuditOutcome.SUCCESS
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceLogModelSelected:
    """Tests for log_model_selected method."""

    @pytest.mark.asyncio
    async def test_logs_model_selected_event(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that model selected events are logged correctly."""
        result = await audit_service.log_model_selected(
            user_id=user_id,
            credential_id=credential_id,
            provider="azure",
            model_id="zh-TW-HsiaoChenNeural",
        )

        assert result is not None
        assert result.event_type == AuditEventType.MODEL_SELECTED
        assert result.outcome == AuditOutcome.SUCCESS
        assert result.details == {"model_id": "zh-TW-HsiaoChenNeural"}
        mock_audit_repository.save.assert_called_once()


class TestAuditServiceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_none_optional_fields(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that None values for optional fields are handled correctly."""
        result = await audit_service.log_credential_created(
            user_id=user_id,
            credential_id=credential_id,
            provider="elevenlabs",
            ip_address=None,
            user_agent=None,
        )

        assert result is not None
        assert result.ip_address is None
        assert result.user_agent is None

    @pytest.mark.asyncio
    async def test_repository_save_is_called_with_audit_log(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that repository.save is called with an AuditLog instance."""
        await audit_service.log_credential_created(
            user_id=user_id,
            credential_id=credential_id,
            provider="elevenlabs",
        )

        # Verify save was called with an AuditLog instance
        call_args = mock_audit_repository.save.call_args
        assert call_args is not None
        saved_log = call_args[0][0]
        assert isinstance(saved_log, AuditLog)
        assert saved_log.user_id == user_id
        assert saved_log.resource_id == credential_id

    @pytest.mark.asyncio
    async def test_audit_log_has_timestamp(
        self,
        audit_service: AuditService,
        mock_audit_repository: AsyncMock,
        user_id: uuid.UUID,
        credential_id: uuid.UUID,
    ) -> None:
        """Test that audit logs have a timestamp set."""
        result = await audit_service.log_credential_created(
            user_id=user_id,
            credential_id=credential_id,
            provider="elevenlabs",
        )

        assert result.timestamp is not None
        # Verify timestamp is recent (within last minute)
        now = datetime.now(UTC)
        # Handle both timezone-aware and naive datetimes
        result_ts = result.timestamp
        if result_ts.tzinfo is None:
            result_ts = result_ts.replace(tzinfo=UTC)
        time_diff = abs((now - result_ts).total_seconds())
        assert time_diff < 60  # Within 60 seconds
