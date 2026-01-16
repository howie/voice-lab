"""In-Memory Test Record Repository Implementation."""

from datetime import datetime
from typing import Any
import uuid

from src.domain.entities.test_record import TestRecord, TestType
from src.domain.repositories.test_record_repository import ITestRecordRepository


class InMemoryTestRecordRepository(ITestRecordRepository):
    """In-memory implementation of test record repository.

    Useful for development and testing. Data is lost when server restarts.
    """

    def __init__(self):
        self._records: dict[uuid.UUID, TestRecord] = {}

    async def save(self, record: TestRecord) -> TestRecord:
        """Save a test record."""
        # Ensure record has an ID
        if record.id is None:
            record = TestRecord(
                id=uuid.uuid4(),
                user_id=record.user_id,
                test_type=record.test_type,
                provider=record.provider,
                input_text=record.input_text,
                output_text=record.output_text,
                latency_ms=record.latency_ms,
                created_at=record.created_at,
                metadata=record.metadata,
            )

        self._records[record.id] = record
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> TestRecord | None:
        """Get a test record by ID."""
        return self._records.get(record_id)

    async def list_by_user(
        self,
        user_id: str,
        test_type: TestType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TestRecord]:
        """List test records for a user."""
        # Filter by user
        records = [r for r in self._records.values() if r.user_id == user_id]

        # Filter by test type if specified
        if test_type:
            records = [r for r in records if r.test_type == test_type]

        # Sort by creation time (newest first)
        records.sort(key=lambda r: r.created_at, reverse=True)

        # Apply pagination
        return records[offset : offset + limit]

    async def delete(self, record_id: uuid.UUID) -> bool:
        """Delete a test record."""
        if record_id in self._records:
            del self._records[record_id]
            return True
        return False

    async def count_by_user(
        self, user_id: str, test_type: TestType | None = None
    ) -> int:
        """Count test records for a user."""
        records = [r for r in self._records.values() if r.user_id == user_id]

        if test_type:
            records = [r for r in records if r.test_type == test_type]

        return len(records)

    async def get_statistics(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get statistics for a user's test records."""
        records = [r for r in self._records.values() if r.user_id == user_id]

        # Filter by date range
        if start_date:
            records = [r for r in records if r.created_at >= start_date]
        if end_date:
            records = [r for r in records if r.created_at <= end_date]

        if not records:
            return {
                "total_tests": 0,
                "by_type": {},
                "by_provider": {},
                "avg_latency_ms": None,
            }

        # Count by type
        by_type = {}
        for r in records:
            by_type[r.test_type.value] = by_type.get(r.test_type.value, 0) + 1

        # Count by provider
        by_provider = {}
        for r in records:
            by_provider[r.provider] = by_provider.get(r.provider, 0) + 1

        # Calculate average latency
        latencies = [r.latency_ms for r in records if r.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        return {
            "total_tests": len(records),
            "by_type": by_type,
            "by_provider": by_provider,
            "avg_latency_ms": avg_latency,
        }
