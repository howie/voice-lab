"""Unit tests for MusicGenerationJob entity state transitions.

Feature: 012-music-generation
Tests cancel/restart/is_terminal state machine logic.
"""

import uuid

import pytest

from src.domain.entities.music import (
    MusicGenerationJob,
    MusicGenerationStatus,
    MusicGenerationType,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def pending_job() -> MusicGenerationJob:
    """Create a pending music generation job."""
    return MusicGenerationJob(
        user_id=uuid.uuid4(),
        type=MusicGenerationType.INSTRUMENTAL,
        prompt="test prompt for bgm",
    )


@pytest.fixture
def processing_job(pending_job: MusicGenerationJob) -> MusicGenerationJob:
    """Create a processing music generation job."""
    pending_job.start_processing(provider_task_id="task-123")
    return pending_job


@pytest.fixture
def completed_job(processing_job: MusicGenerationJob) -> MusicGenerationJob:
    """Create a completed music generation job."""
    processing_job.complete(result_url="/storage/test.mp3")
    return processing_job


@pytest.fixture
def failed_job(processing_job: MusicGenerationJob) -> MusicGenerationJob:
    """Create a failed music generation job."""
    processing_job.fail(error_message="Provider timeout")
    return processing_job


@pytest.fixture
def cancelled_job(pending_job: MusicGenerationJob) -> MusicGenerationJob:
    """Create a cancelled music generation job."""
    pending_job.cancel()
    return pending_job


@pytest.fixture
def exhausted_failed_job() -> MusicGenerationJob:
    """Create a failed job that has exhausted all retries (retry_count=3, status=FAILED)."""
    job = MusicGenerationJob(
        user_id=uuid.uuid4(),
        type=MusicGenerationType.SONG,
        prompt="test song",
        lyrics="la la la",
    )
    # Simulate 3 retry cycles: fail → retry (x3), then one final fail
    for i in range(3):
        job.start_processing(provider_task_id=f"task-{i}")
        job.fail(error_message="timeout")
        job.retry()  # retry_count becomes 1, 2, 3
    # Final attempt that stays failed
    job.start_processing(provider_task_id="task-final")
    job.fail(error_message="timeout")
    return job


# =============================================================================
# can_cancel tests
# =============================================================================


class TestCanCancel:
    """Tests for MusicGenerationJob.can_cancel()."""

    def test_pending_can_cancel(self, pending_job: MusicGenerationJob) -> None:
        assert pending_job.can_cancel() is True

    def test_processing_can_cancel(self, processing_job: MusicGenerationJob) -> None:
        assert processing_job.can_cancel() is True

    def test_completed_cannot_cancel(self, completed_job: MusicGenerationJob) -> None:
        assert completed_job.can_cancel() is False

    def test_failed_cannot_cancel(self, failed_job: MusicGenerationJob) -> None:
        assert failed_job.can_cancel() is False

    def test_cancelled_cannot_cancel(self, cancelled_job: MusicGenerationJob) -> None:
        assert cancelled_job.can_cancel() is False


# =============================================================================
# cancel tests
# =============================================================================


class TestCancel:
    """Tests for MusicGenerationJob.cancel()."""

    def test_cancel_pending_sets_status(self, pending_job: MusicGenerationJob) -> None:
        pending_job.cancel()
        assert pending_job.status == MusicGenerationStatus.CANCELLED

    def test_cancel_sets_completed_at(self, pending_job: MusicGenerationJob) -> None:
        assert pending_job.completed_at is None
        pending_job.cancel()
        assert pending_job.completed_at is not None

    def test_cancel_processing_sets_status(self, processing_job: MusicGenerationJob) -> None:
        processing_job.cancel()
        assert processing_job.status == MusicGenerationStatus.CANCELLED

    def test_cancel_completed_raises(self, completed_job: MusicGenerationJob) -> None:
        with pytest.raises(ValueError, match="Cannot cancel"):
            completed_job.cancel()

    def test_cancel_failed_raises(self, failed_job: MusicGenerationJob) -> None:
        with pytest.raises(ValueError, match="Cannot cancel"):
            failed_job.cancel()

    def test_cancel_already_cancelled_raises(self, cancelled_job: MusicGenerationJob) -> None:
        with pytest.raises(ValueError, match="Cannot cancel"):
            cancelled_job.cancel()


# =============================================================================
# can_restart tests
# =============================================================================


class TestCanRestart:
    """Tests for MusicGenerationJob.can_restart()."""

    def test_cancelled_can_restart(self, cancelled_job: MusicGenerationJob) -> None:
        assert cancelled_job.can_restart() is True

    def test_failed_exhausted_can_restart(self, exhausted_failed_job: MusicGenerationJob) -> None:
        assert exhausted_failed_job.status == MusicGenerationStatus.FAILED
        assert exhausted_failed_job.retry_count >= exhausted_failed_job.MAX_RETRY_COUNT
        assert exhausted_failed_job.can_restart() is True

    def test_failed_with_retries_left_cannot_restart(self, failed_job: MusicGenerationJob) -> None:
        assert failed_job.retry_count < failed_job.MAX_RETRY_COUNT
        assert failed_job.can_restart() is False

    def test_pending_cannot_restart(self, pending_job: MusicGenerationJob) -> None:
        assert pending_job.can_restart() is False

    def test_processing_cannot_restart(self, processing_job: MusicGenerationJob) -> None:
        assert processing_job.can_restart() is False

    def test_completed_cannot_restart(self, completed_job: MusicGenerationJob) -> None:
        assert completed_job.can_restart() is False


# =============================================================================
# is_terminal tests
# =============================================================================


class TestIsTerminal:
    """Tests for MusicGenerationJob.is_terminal()."""

    def test_pending_not_terminal(self, pending_job: MusicGenerationJob) -> None:
        assert pending_job.is_terminal() is False

    def test_processing_not_terminal(self, processing_job: MusicGenerationJob) -> None:
        assert processing_job.is_terminal() is False

    def test_completed_is_terminal(self, completed_job: MusicGenerationJob) -> None:
        assert completed_job.is_terminal() is True

    def test_failed_is_terminal(self, failed_job: MusicGenerationJob) -> None:
        assert failed_job.is_terminal() is True

    def test_cancelled_is_terminal(self, cancelled_job: MusicGenerationJob) -> None:
        assert cancelled_job.is_terminal() is True
