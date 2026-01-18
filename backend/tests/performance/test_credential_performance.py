"""Performance tests for credential operations.

T083: Performance testing for credential operations.

These tests measure the response times of credential-related operations
to ensure they meet acceptable performance standards.
"""

import statistics
import time
import uuid
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock

import pytest

# Performance thresholds (in seconds)
THRESHOLDS = {
    "audit_log_write": 0.01,  # 10ms max for audit log writes (with mock)
    "audit_log_max": 0.05,  # 50ms max for any single audit log operation
}


async def measure_operation(
    operation: Callable[[], Any],
    iterations: int = 10,
) -> dict[str, float]:
    """Measure operation performance over multiple iterations.

    Returns:
        Dict with min, max, avg, median, p95 times in seconds.
    """
    times: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter()
        await operation()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    times_sorted = sorted(times)
    p95_index = int(len(times_sorted) * 0.95)

    return {
        "min": min(times),
        "max": max(times),
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "p95": times_sorted[p95_index] if p95_index < len(times_sorted) else times_sorted[-1],
    }


class TestAuditLogPerformance:
    """Performance tests for audit logging operations."""

    @pytest.mark.asyncio
    async def test_audit_log_write_performance(self) -> None:
        """Test that audit log writes are performant with mock repository."""
        from src.application.services.audit_service import AuditService

        mock_repo = AsyncMock()

        async def mock_save(audit_log: Any) -> Any:
            return audit_log

        mock_repo.save = mock_save

        service = AuditService(mock_repo)
        user_id = uuid.uuid4()
        credential_id = uuid.uuid4()

        async def operation() -> None:
            await service.log_credential_created(
                user_id=user_id,
                credential_id=credential_id,
                provider="elevenlabs",
                ip_address="127.0.0.1",
                user_agent="TestAgent/1.0",
            )

        metrics = await measure_operation(operation, iterations=100)

        # Audit log writes (with mock) should complete within 10ms on average
        assert metrics["avg"] < THRESHOLDS["audit_log_write"], (
            f"Audit log write avg latency ({metrics['avg']:.4f}s) "
            f"exceeded threshold ({THRESHOLDS['audit_log_write']}s)"
        )

    @pytest.mark.asyncio
    async def test_audit_service_all_event_types_performance(self) -> None:
        """Test that all audit event type methods are performant."""
        from src.application.services.audit_service import AuditService

        mock_repo = AsyncMock()

        async def mock_save(audit_log: Any) -> Any:
            return audit_log

        mock_repo.save = mock_save

        service = AuditService(mock_repo)
        user_id = uuid.uuid4()
        credential_id = uuid.uuid4()

        event_methods = [
            lambda: service.log_credential_created(
                user_id=user_id, credential_id=credential_id, provider="test"
            ),
            lambda: service.log_credential_updated(
                user_id=user_id, credential_id=credential_id, provider="test"
            ),
            lambda: service.log_credential_deleted(
                user_id=user_id, credential_id=credential_id, provider="test"
            ),
            lambda: service.log_credential_validated(
                user_id=user_id,
                credential_id=credential_id,
                provider="test",
                is_valid=True,
            ),
            lambda: service.log_credential_used(
                user_id=user_id,
                credential_id=credential_id,
                provider="test",
                operation="tts.synthesize",
            ),
            lambda: service.log_credential_viewed(
                user_id=user_id, credential_id=credential_id, provider="test"
            ),
            lambda: service.log_model_selected(
                user_id=user_id,
                credential_id=credential_id,
                provider="test",
                model_id="test-model",
            ),
        ]

        all_times: list[float] = []

        for method in event_methods:
            for _ in range(20):
                start = time.perf_counter()
                await method()
                elapsed = time.perf_counter() - start
                all_times.append(elapsed)

        avg_time = statistics.mean(all_times)
        max_time = max(all_times)

        # All audit events should complete within 10ms on average
        assert avg_time < THRESHOLDS["audit_log_write"], (
            f"Audit events avg latency ({avg_time:.4f}s) exceeded threshold "
            f"({THRESHOLDS['audit_log_write']}s)"
        )
        # No single event should take more than 50ms
        assert max_time < THRESHOLDS["audit_log_max"], (
            f"Audit events max latency ({max_time:.4f}s) exceeded threshold "
            f"({THRESHOLDS['audit_log_max']}s)"
        )


class TestValidatorPerformance:
    """Performance tests for provider validators."""

    @pytest.mark.asyncio
    async def test_validation_result_creation_performance(self) -> None:
        """Test that ValidationResult objects are created efficiently."""
        from src.infrastructure.providers.validators.base import ValidationResult

        def create_valid_result() -> ValidationResult:
            return ValidationResult(
                is_valid=True,
                quota_info={"character_count": 1000, "character_limit": 10000},
            )

        def create_invalid_result() -> ValidationResult:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid API key",
            )

        times: list[float] = []

        for _ in range(1000):
            start = time.perf_counter()
            create_valid_result()
            create_invalid_result()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time = statistics.mean(times)

        # Creating 2 ValidationResult objects should take less than 1ms
        assert avg_time < 0.001, (
            f"ValidationResult creation avg latency ({avg_time:.6f}s) exceeded threshold (0.001s)"
        )


class TestMaskingPerformance:
    """Performance tests for API key masking utility."""

    @pytest.mark.asyncio
    async def test_api_key_masking_performance(self) -> None:
        """Test that API key masking is performant."""
        from src.domain.utils.masking import mask_api_key

        test_keys = [
            "sk-1234567890abcdef",
            "AIzaSy1234567890abcdefghijklmnopqrstuv",
            "short",
            "a" * 100,
            "",
        ]

        times: list[float] = []

        for _ in range(1000):
            for key in test_keys:
                start = time.perf_counter()
                mask_api_key(key)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

        avg_time = statistics.mean(times)

        # Masking should take less than 0.1ms per operation
        assert avg_time < 0.0001, (
            f"API key masking avg latency ({avg_time:.6f}s) exceeded threshold (0.0001s)"
        )


class TestDomainEntityPerformance:
    """Performance tests for domain entity creation."""

    @pytest.mark.asyncio
    async def test_credential_entity_creation_performance(self) -> None:
        """Test that credential entities are created efficiently."""
        from src.domain.entities.provider_credential import UserProviderCredential

        user_id = uuid.uuid4()

        def create_credential() -> UserProviderCredential:
            return UserProviderCredential(
                id=uuid.uuid4(),
                user_id=user_id,
                provider="elevenlabs",
                api_key="encrypted_key_value",
                is_valid=True,
                selected_model_id="test-model",
            )

        times: list[float] = []

        for _ in range(1000):
            start = time.perf_counter()
            create_credential()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time = statistics.mean(times)

        # Creating a credential entity should take less than 1ms
        assert avg_time < 0.001, (
            f"Credential entity creation avg latency ({avg_time:.6f}s) exceeded threshold (0.001s)"
        )

    @pytest.mark.asyncio
    async def test_audit_log_entity_creation_performance(self) -> None:
        """Test that audit log entities are created efficiently."""
        from src.domain.entities.audit_log import AuditEventType, AuditLog, AuditOutcome

        user_id = uuid.uuid4()
        resource_id = uuid.uuid4()

        def create_audit_log() -> AuditLog:
            return AuditLog(
                id=uuid.uuid4(),
                user_id=user_id,
                event_type=AuditEventType.CREDENTIAL_CREATED,
                outcome=AuditOutcome.SUCCESS,
                provider="elevenlabs",
                resource_id=resource_id,
                ip_address="127.0.0.1",
                user_agent="TestAgent/1.0",
                details={"key": "value"},
            )

        times: list[float] = []

        for _ in range(1000):
            start = time.perf_counter()
            create_audit_log()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time = statistics.mean(times)

        # Creating an audit log entity should take less than 1ms
        assert avg_time < 0.001, (
            f"AuditLog entity creation avg latency ({avg_time:.6f}s) exceeded threshold (0.001s)"
        )
