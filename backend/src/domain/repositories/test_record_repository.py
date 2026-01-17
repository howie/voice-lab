"""Test Record Repository Interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.entities.test_record import TestRecord, TestType


class ITestRecordRepository(ABC):
    """Abstract repository interface for test records.

    This interface defines the contract for test record persistence.
    Implementations can be SQL, NoSQL, in-memory, etc.
    """

    @abstractmethod
    async def save(self, record: TestRecord) -> TestRecord:
        """Save a test record.

        Args:
            record: Test record to save

        Returns:
            Saved test record with generated ID if new
        """
        pass

    @abstractmethod
    async def get_by_id(self, record_id: UUID) -> TestRecord | None:
        """Get a test record by ID.

        Args:
            record_id: Record UUID

        Returns:
            Test record if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete(self, record_id: UUID) -> bool:
        """Delete a test record.

        Args:
            record_id: Record UUID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        test_type: TestType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TestRecord]:
        """List test records for a user.

        Args:
            user_id: User ID
            test_type: Filter by test type
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of test records matching the filters
        """
        pass

    @abstractmethod
    async def count(
        self,
        user_id: str | None = None,
        test_type: TestType | None = None,
        provider: str | None = None,
    ) -> int:
        """Count test records with filters.

        Args:
            user_id: Filter by user ID
            test_type: Filter by test type
            provider: Filter by provider

        Returns:
            Total count of matching records
        """
        pass
