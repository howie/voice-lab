"""Unit tests for MusicGenerationService cancel/restart operations.

Feature: 012-music-generation
Tests service-layer business logic with mocked repository.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from src.domain.entities.music import (
    MusicGenerationJob,
    MusicGenerationStatus,
    MusicGenerationType,
)
from src.domain.services.music.service import (
    MusicGenerationService,
    MusicJobCancelError,
    QuotaExceededError,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Create a mock music job repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.update = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.count_daily_usage = AsyncMock(return_value=0)
    repo.count_monthly_usage = AsyncMock(return_value=0)
    repo.count_active_jobs = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def service(mock_repo: AsyncMock) -> MusicGenerationService:
    return MusicGenerationService(repository=mock_repo, music_provider=AsyncMock())


def _make_job(
    user_id: uuid.UUID,
    status: MusicGenerationStatus = MusicGenerationStatus.PENDING,
    retry_count: int = 0,
) -> MusicGenerationJob:
    job = MusicGenerationJob(
        user_id=user_id,
        type=MusicGenerationType.INSTRUMENTAL,
        prompt="test prompt for bgm generation",
    )
    job.status = status
    job.retry_count = retry_count
    return job


# =============================================================================
# cancel_job tests
# =============================================================================


class TestCancelJob:
    """Tests for MusicGenerationService.cancel_job()."""

    @pytest.mark.asyncio
    async def test_cancel_pending_job(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.PENDING)
        mock_repo.get_by_id.return_value = job
        mock_repo.update.return_value = job

        result = await service.cancel_job(job.id, user_id)

        assert result.status == MusicGenerationStatus.CANCELLED
        assert result.completed_at is not None
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_processing_job(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.PROCESSING)
        mock_repo.get_by_id.return_value = job
        mock_repo.update.return_value = job

        result = await service.cancel_job(job.id, user_id)

        assert result.status == MusicGenerationStatus.CANCELLED
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_completed_job_raises(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.COMPLETED)
        mock_repo.get_by_id.return_value = job

        with pytest.raises(MusicJobCancelError):
            await service.cancel_job(job.id, user_id)

        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job_raises(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        mock_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await service.cancel_job(uuid.uuid4(), user_id)

    @pytest.mark.asyncio
    async def test_cancel_wrong_user_raises(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        other_user_id = uuid.uuid4()
        job = _make_job(other_user_id, MusicGenerationStatus.PENDING)
        mock_repo.get_by_id.return_value = job

        with pytest.raises(ValueError, match="not found"):
            await service.cancel_job(job.id, user_id)


# =============================================================================
# restart_job tests
# =============================================================================


class TestRestartJob:
    """Tests for MusicGenerationService.restart_job()."""

    @pytest.mark.asyncio
    async def test_restart_cancelled_job_creates_new(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        original = _make_job(user_id, MusicGenerationStatus.CANCELLED)
        original.prompt = "original prompt"
        original.lyrics = "original lyrics"
        original.model = "mureka-01"
        original.provider = "mureka"
        mock_repo.get_by_id.return_value = original

        # Return the saved job as-is
        mock_repo.save.side_effect = lambda j: j

        result = await service.restart_job(original.id, user_id)

        # New job should have same parameters but different ID
        assert result.id != original.id
        assert result.prompt == original.prompt
        assert result.lyrics == original.lyrics
        assert result.model == original.model
        assert result.provider == original.provider
        assert result.status == MusicGenerationStatus.PENDING
        assert result.retry_count == 0
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_restart_exhausted_failed_job(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.FAILED, retry_count=3)
        mock_repo.get_by_id.return_value = job
        mock_repo.save.side_effect = lambda j: j

        result = await service.restart_job(job.id, user_id)

        assert result.status == MusicGenerationStatus.PENDING
        assert result.retry_count == 0
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_restart_pending_job_raises(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.PENDING)
        mock_repo.get_by_id.return_value = job

        with pytest.raises(ValueError, match="cannot be restarted"):
            await service.restart_job(job.id, user_id)

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_failed_with_retries_left_raises(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.FAILED, retry_count=1)
        mock_repo.get_by_id.return_value = job

        with pytest.raises(ValueError, match="cannot be restarted"):
            await service.restart_job(job.id, user_id)

    @pytest.mark.asyncio
    async def test_restart_checks_quota(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        job = _make_job(user_id, MusicGenerationStatus.CANCELLED)
        mock_repo.get_by_id.return_value = job

        # Simulate concurrent limit reached
        mock_repo.count_active_jobs.return_value = 99

        with pytest.raises(QuotaExceededError):
            await service.restart_job(job.id, user_id)

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_nonexistent_job_raises(
        self, service: MusicGenerationService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        mock_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await service.restart_job(uuid.uuid4(), user_id)
