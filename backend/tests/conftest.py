"""Shared test fixtures and utilities."""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.job import Job, JobStatus, JobType
from src.main import app
from src.presentation.api.routes import credentials as credentials_module


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Create a mock database session."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@asynccontextmanager
async def override_dependencies(
    user_id: uuid.UUID,
    session: MagicMock,
    credential_repo: AsyncMock | None = None,
    provider_repo: AsyncMock | None = None,
    audit_repo: AsyncMock | None = None,
) -> AsyncGenerator[None, None]:
    """Context manager to override FastAPI dependencies for testing.

    Args:
        user_id: The user ID to return from get_current_user_id
        session: The mock database session
        credential_repo: Optional mock credential repository
        provider_repo: Optional mock provider repository
        audit_repo: Optional mock audit log repository
    """

    async def override_get_current_user_id() -> uuid.UUID:
        return user_id

    async def override_get_db_session() -> Any:
        return session

    # Set overrides
    app.dependency_overrides[credentials_module.get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

    try:
        yield
    finally:
        # Clear all overrides
        app.dependency_overrides.clear()


# =============================================================================
# Job-related test fixtures (Feature 007 - Async Job Management)
# =============================================================================


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Return a consistent test user ID."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_job_input_params() -> dict[str, Any]:
    """Return sample input parameters for a multi-role TTS job."""
    return {
        "turns": [
            {"speaker": "A", "text": "Hello, how are you?", "index": 0},
            {"speaker": "B", "text": "I am fine, thank you!", "index": 1},
        ],
        "voice_assignments": [
            {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural", "voice_name": "Xiao Yu"},
            {"speaker": "B", "voice_id": "zh-TW-YunJheNeural", "voice_name": "Yun Jhe"},
        ],
        "language": "zh-TW",
        "output_format": "mp3",
        "gap_ms": 300,
        "crossfade_ms": 50,
    }


@pytest.fixture
def job_factory(sample_user_id: uuid.UUID, sample_job_input_params: dict[str, Any]):
    """Factory fixture for creating Job instances with customizable attributes.

    Usage:
        job = job_factory()  # Creates a default pending job
        job = job_factory(status=JobStatus.PROCESSING)  # Creates a processing job
        job = job_factory(provider="google", retry_count=2)  # Custom attributes
    """

    def _create_job(
        id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        job_type: JobType = JobType.MULTI_ROLE_TTS,
        status: JobStatus = JobStatus.PENDING,
        provider: str = "azure",
        input_params: dict[str, Any] | None = None,
        audio_file_id: uuid.UUID | None = None,
        result_metadata: dict[str, Any] | None = None,
        error_message: str | None = None,
        retry_count: int = 0,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> Job:
        return Job(
            id=id or uuid.uuid4(),
            user_id=user_id or sample_user_id,
            job_type=job_type,
            status=status,
            provider=provider,
            input_params=input_params or sample_job_input_params,
            audio_file_id=audio_file_id,
            result_metadata=result_metadata,
            error_message=error_message,
            retry_count=retry_count,
            created_at=created_at or datetime.utcnow(),
            started_at=started_at,
            completed_at=completed_at,
        )

    return _create_job


@pytest.fixture
def pending_job(job_factory) -> Job:
    """Create a pending job for testing."""
    return job_factory(status=JobStatus.PENDING)


@pytest.fixture
def processing_job(job_factory) -> Job:
    """Create a processing job for testing."""
    job = job_factory(status=JobStatus.PENDING)
    job.start_processing()
    return job


@pytest.fixture
def completed_job(job_factory) -> Job:
    """Create a completed job for testing."""
    job = job_factory(status=JobStatus.PENDING)
    job.start_processing()
    job.complete(
        audio_file_id=uuid.uuid4(),
        result_metadata={
            "duration_ms": 5000,
            "latency_ms": 1500,
            "synthesis_mode": "segmented",
        },
    )
    return job


@pytest.fixture
def failed_job(job_factory) -> Job:
    """Create a failed job for testing."""
    job = job_factory(status=JobStatus.PENDING)
    job.start_processing()
    job.fail(error_message="Test failure message")
    return job


@pytest.fixture
def mock_job_repository() -> AsyncMock:
    """Create a mock job repository for testing."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_user_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.count_active_jobs = AsyncMock(return_value=0)
    repo.get_pending_jobs = AsyncMock(return_value=[])
    repo.get_timed_out_jobs = AsyncMock(return_value=[])
    return repo
