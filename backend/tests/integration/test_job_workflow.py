"""Integration tests for async job workflow.

Feature: 007-async-job-mgmt
Task: T017 - Integration test for job submission → background execution → completion flow

These tests verify the complete job lifecycle:
1. Job submission via API
2. Worker picks up the job
3. TTS synthesis execution
4. Job completion with audio file
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.job import Job, JobStatus, JobType
from src.domain.entities.multi_role_tts import MultiRoleSupportType
from src.infrastructure.workers.job_worker import JobWorker


@pytest.fixture
def sample_input_params():
    """Sample input parameters for a multi-role TTS job."""
    return {
        "provider": "azure",
        "turns": [
            {"speaker": "A", "text": "你好，今天天氣真好！"},
            {"speaker": "B", "text": "是啊，要不要一起去公園走走？"},
        ],
        "voice_assignments": [
            {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural"},
            {"speaker": "B", "voice_id": "zh-TW-YunJheNeural"},
        ],
        "language": "zh-TW",
        "output_format": "mp3",
        "gap_ms": 300,
        "crossfade_ms": 50,
    }


@pytest.fixture
def mock_synthesis_result():
    """Mock result from SynthesizeMultiRoleUseCase."""
    result = MagicMock()
    result.audio_content = b"fake_audio_content_bytes"
    result.content_type = "audio/mpeg"
    result.duration_ms = 5200
    result.latency_ms = 1850
    result.synthesis_mode = MultiRoleSupportType.SEGMENTED
    return result


@pytest.fixture
def mock_session_factory():
    """Create a mock session factory."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.execute = AsyncMock()

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)

    return factory, mock_session


class TestJobWorkerProcessing:
    """Integration tests for JobWorker processing jobs."""

    @pytest.mark.asyncio
    async def test_worker_processes_pending_job_to_completion(
        self,
        sample_input_params,
        mock_synthesis_result,
    ):
        """Worker should pick up pending job, execute synthesis, and mark completed."""
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()

        # Create a job and transition it to PROCESSING (as acquire_pending_job would)
        processing_job = Job(
            id=job_id,
            user_id=user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params=sample_input_params,
            retry_count=0,
            created_at=datetime.now(UTC),
        )
        # Simulate what acquire_pending_job does - sets status to PROCESSING
        processing_job.start_processing()

        # Track job state updates
        updated_jobs: list[Job] = []

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.acquire_pending_job = AsyncMock(side_effect=[processing_job, None])

        async def capture_update(job):
            updated_jobs.append(job)
            return job

        mock_repo.update = AsyncMock(side_effect=capture_update)

        # Create mock session factory
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch(
                "src.infrastructure.workers.job_worker.SynthesizeMultiRoleUseCase"
            ) as MockUseCase:
                mock_use_case = AsyncMock()
                mock_use_case.execute = AsyncMock(return_value=mock_synthesis_result)
                MockUseCase.return_value = mock_use_case

                with patch("src.infrastructure.workers.job_worker.LocalStorage") as MockStorage:
                    mock_storage = MagicMock()
                    mock_stored_file = MagicMock()
                    mock_stored_file.key = f"jobs/azure/2026-01-21/{job_id}.mp3"
                    mock_stored_file.size_bytes = len(mock_synthesis_result.audio_content)
                    mock_storage.upload = AsyncMock(return_value=mock_stored_file)
                    MockStorage.return_value = mock_storage

                    worker = JobWorker(session_factory=mock_factory)
                    await worker._process_next_job()

        # Verify synthesis was called
        mock_use_case.execute.assert_called_once()

        # Verify job was updated
        assert len(updated_jobs) == 1
        final_job = updated_jobs[0]

        assert final_job.status == JobStatus.COMPLETED
        assert final_job.audio_file_id is not None
        assert final_job.result_metadata is not None
        assert final_job.result_metadata["duration_ms"] == 5200
        assert final_job.result_metadata["latency_ms"] == 1850
        assert final_job.result_metadata["synthesis_mode"] == "segmented"

    @pytest.mark.asyncio
    async def test_worker_handles_synthesis_failure_with_retry(
        self,
        sample_input_params,
    ):
        """Worker should retry failed jobs up to max retries."""
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()

        # Create a pending job with 0 retries
        pending_job = Job(
            id=job_id,
            user_id=user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params=sample_input_params,
            retry_count=0,
            created_at=datetime.now(UTC),
        )

        updated_jobs: list[Job] = []

        mock_repo = AsyncMock()
        mock_repo.acquire_pending_job = AsyncMock(side_effect=[pending_job, None])

        async def capture_update(job):
            updated_jobs.append(job)
            return job

        mock_repo.update = AsyncMock(side_effect=capture_update)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch(
                "src.infrastructure.workers.job_worker.SynthesizeMultiRoleUseCase"
            ) as MockUseCase:
                mock_use_case = AsyncMock()
                mock_use_case.execute = AsyncMock(side_effect=Exception("TTS provider error"))
                MockUseCase.return_value = mock_use_case

                with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        worker = JobWorker(session_factory=mock_factory)
                        await worker._process_next_job()

        # Job should be back to PENDING with incremented retry count
        assert len(updated_jobs) == 1
        final_job = updated_jobs[0]

        assert final_job.status == JobStatus.PENDING
        assert final_job.retry_count == 1

    @pytest.mark.asyncio
    async def test_worker_marks_job_failed_after_max_retries(
        self,
        sample_input_params,
    ):
        """Worker should mark job as failed after exhausting retries."""
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()

        # Create a job that has already been retried max times
        pending_job = Job(
            id=job_id,
            user_id=user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PENDING,
            provider="azure",
            input_params=sample_input_params,
            retry_count=3,  # Already at max
            created_at=datetime.now(UTC),
        )
        # Manually set to PROCESSING as worker would
        pending_job.start_processing()

        updated_jobs: list[Job] = []

        mock_repo = AsyncMock()
        mock_repo.acquire_pending_job = AsyncMock(side_effect=[pending_job, None])

        async def capture_update(job):
            updated_jobs.append(job)
            return job

        mock_repo.update = AsyncMock(side_effect=capture_update)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch(
                "src.infrastructure.workers.job_worker.SynthesizeMultiRoleUseCase"
            ) as MockUseCase:
                mock_use_case = AsyncMock()
                mock_use_case.execute = AsyncMock(side_effect=Exception("TTS provider error"))
                MockUseCase.return_value = mock_use_case

                with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                    worker = JobWorker(session_factory=mock_factory)
                    await worker._process_next_job()

        # Job should be FAILED
        assert len(updated_jobs) == 1
        final_job = updated_jobs[0]

        assert final_job.status == JobStatus.FAILED
        assert final_job.error_message is not None
        assert "TTS provider error" in final_job.error_message

    @pytest.mark.asyncio
    async def test_worker_skips_when_no_pending_jobs(self):
        """Worker should do nothing when no pending jobs exist."""
        mock_repo = AsyncMock()
        mock_repo.acquire_pending_job = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                worker = JobWorker(session_factory=mock_factory)
                # Should complete without error
                await worker._process_next_job()

        # Verify acquire was called but nothing else
        mock_repo.acquire_pending_job.assert_called_once()
        mock_repo.update.assert_not_called()


class TestJobWorkerRecovery:
    """Tests for worker recovery scenarios."""

    @pytest.mark.asyncio
    async def test_worker_recovers_stale_processing_jobs_on_startup(
        self,
        sample_input_params,
    ):
        """Worker should mark stale PROCESSING jobs as FAILED on startup."""
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()

        # Create a job stuck in PROCESSING state
        stale_job = Job(
            id=job_id,
            user_id=user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PROCESSING,
            provider="azure",
            input_params=sample_input_params,
            retry_count=0,
            created_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
        )

        updated_jobs: list[Job] = []

        mock_repo = AsyncMock()
        mock_repo.get_stale_processing_jobs = AsyncMock(return_value=[stale_job])

        async def capture_update(job):
            updated_jobs.append(job)
            return job

        mock_repo.update = AsyncMock(side_effect=capture_update)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                worker = JobWorker(session_factory=mock_factory)
                await worker._recover_stale_jobs()

        # Verify job was marked as failed
        assert len(updated_jobs) == 1
        recovered_job = updated_jobs[0]

        assert recovered_job.status == JobStatus.FAILED
        assert "worker restart" in recovered_job.error_message.lower()


class TestJobWorkerTimeout:
    """Tests for job timeout handling."""

    @pytest.mark.asyncio
    async def test_worker_times_out_long_running_jobs(
        self,
        sample_input_params,
    ):
        """Worker should mark jobs as failed if they exceed timeout."""
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()

        # Create a job that started 15 minutes ago
        old_start_time = datetime.now(UTC) - timedelta(minutes=15)

        timed_out_job = Job(
            id=job_id,
            user_id=user_id,
            job_type=JobType.MULTI_ROLE_TTS,
            status=JobStatus.PROCESSING,
            provider="azure",
            input_params=sample_input_params,
            retry_count=0,
            created_at=old_start_time - timedelta(minutes=1),
            started_at=old_start_time,
        )

        updated_jobs: list[Job] = []

        mock_repo = AsyncMock()
        mock_repo.get_timed_out_jobs = AsyncMock(return_value=[timed_out_job])

        async def capture_update(job):
            updated_jobs.append(job)
            return job

        mock_repo.update = AsyncMock(side_effect=capture_update)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                worker = JobWorker(session_factory=mock_factory)
                await worker._check_timed_out_jobs()

        # Verify job was marked as failed
        assert len(updated_jobs) == 1
        timeout_job = updated_jobs[0]

        assert timeout_job.status == JobStatus.FAILED
        assert "timed out" in timeout_job.error_message.lower()


class TestJobWorkerLifecycle:
    """Tests for worker start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_worker_starts_and_stops_gracefully(self):
        """Worker should start background tasks and stop them on shutdown."""
        mock_repo = AsyncMock()
        mock_repo.get_stale_processing_jobs = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.infrastructure.workers.job_worker.JobRepositoryImpl",
            return_value=mock_repo,
        ):
            with patch("src.infrastructure.workers.job_worker.LocalStorage"):
                worker = JobWorker(session_factory=mock_factory)

                # Start worker
                await worker.start()
                assert worker._running is True
                assert worker._task is not None
                assert worker._timeout_task is not None
                assert worker._cleanup_task is not None

                # Stop worker
                await worker.stop()
                assert worker._running is False
