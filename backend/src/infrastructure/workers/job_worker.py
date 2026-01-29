"""Job Worker for background TTS synthesis processing.

Feature: 007-async-job-mgmt
This worker polls for pending jobs and executes TTS synthesis in the background.

Tasks covered:
- T021: Job worker polling loop
- T022: SELECT ... FOR UPDATE SKIP LOCKED for job pickup
- T023: Integration with SynthesizeMultiRoleUseCase
- T024: Retry logic (max 3, exponential backoff: 5s, 10s, 20s)
- T025: Result storage (audio_file_id, result_metadata)
- T038: Timeout monitoring (10 min)
- T039: System startup recovery (processing → failed)
- T051: Data retention cleanup (30 days)
"""

import asyncio
import contextlib
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.use_cases.synthesize_multi_role import (
    SynthesizeMultiRoleInput,
    SynthesizeMultiRoleUseCase,
)
from src.domain.entities.job import Job, JobStatus
from src.domain.entities.multi_role_tts import DialogueTurn, VoiceAssignment
from src.infrastructure.persistence.job_repository_impl import JobRepositoryImpl
from src.infrastructure.persistence.models import AudioFileModel
from src.infrastructure.storage.local_storage import LocalStorage

logger = logging.getLogger(__name__)

# Worker configuration
POLL_INTERVAL_SECONDS = 5
RETRY_DELAYS = [5, 10, 20]  # Exponential backoff in seconds
MAX_RETRIES = 3
JOB_TIMEOUT_MINUTES = 10
TIMEOUT_CHECK_INTERVAL_SECONDS = 30
DATA_RETENTION_DAYS = 30
CLEANUP_INTERVAL_SECONDS = 3600  # 1 hour
CLEANUP_BATCH_SIZE = 50


class JobWorker:
    """Background worker that processes pending TTS synthesis jobs.

    Uses PostgreSQL's SELECT ... FOR UPDATE SKIP LOCKED pattern
    for concurrent-safe job acquisition.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        storage_path: str | None = None,
    ) -> None:
        """Initialize the job worker.

        Args:
            session_factory: SQLAlchemy async session factory
            storage_path: Base path for audio storage
        """
        self._session_factory = session_factory
        self._storage = LocalStorage(
            base_path=storage_path or os.getenv("LOCAL_STORAGE_PATH", "./storage")
        )
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._timeout_task: asyncio.Task[None] | None = None
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the worker polling loop."""
        if self._running:
            logger.warning("JobWorker is already running")
            return

        # T039: Recovery - mark stale processing jobs as failed on startup
        # Allow startup to continue even if recovery fails (e.g., DB not ready)
        try:
            await self._recover_stale_jobs()
        except Exception as e:
            logger.warning(f"Failed to recover stale jobs on startup: {e}")
            logger.info("Will retry stale job recovery in background")

        self._running = True
        self._task = asyncio.create_task(self._polling_loop())
        self._timeout_task = asyncio.create_task(self._timeout_monitoring_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("JobWorker started")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._timeout_task:
            self._timeout_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._timeout_task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
        logger.info("JobWorker stopped")

    async def _polling_loop(self) -> None:
        """Main polling loop that processes jobs."""
        logger.info(f"JobWorker polling loop started (interval: {POLL_INTERVAL_SECONDS}s)")

        while self._running:
            try:
                await self._process_next_job()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _process_next_job(self) -> None:
        """Try to acquire and process the next pending job."""
        async with self._session_factory() as session:
            job_repo = JobRepositoryImpl(session)

            # Acquire a pending job (uses FOR UPDATE SKIP LOCKED)
            job = await job_repo.acquire_pending_job()

            if job is None:
                # No pending jobs available
                return

            # Commit the status change to PROCESSING immediately
            # This ensures the job won't be picked up by other workers
            # and the status is persisted even if execution fails later
            await session.commit()

            logger.info(f"Acquired job: id={job.id}, type={job.job_type}, provider={job.provider}")

            try:
                # Process the job
                await self._execute_job(job, session, job_repo)
            except Exception as e:
                # Handle job failure
                await self._handle_job_failure(job, session, job_repo, str(e))

    async def _execute_job(
        self,
        job: Job,
        session: AsyncSession,
        job_repo: JobRepositoryImpl,
    ) -> None:
        """Execute TTS synthesis for a job.

        Args:
            job: The job to execute
            session: Database session
            job_repo: Job repository
        """
        logger.info(f"Executing job: id={job.id}")

        try:
            # Build synthesis input from job parameters
            input_data = self._build_synthesis_input(job.input_params)

            # Execute synthesis
            use_case = SynthesizeMultiRoleUseCase()
            result = await use_case.execute(input_data)

            # Save audio file to storage
            audio_file_id = await self._save_audio_file(
                job=job,
                audio_content=result.audio_content,
                content_type=result.content_type,
                duration_ms=result.duration_ms,
                session=session,
            )

            # Build result metadata
            result_metadata = {
                "duration_ms": result.duration_ms,
                "latency_ms": result.latency_ms,
                "synthesis_mode": result.synthesis_mode.value,
                "content_type": result.content_type,
            }

            # Complete the job
            job.complete(audio_file_id=audio_file_id, result_metadata=result_metadata)
            await job_repo.update(job)
            await session.commit()

            logger.info(f"Job completed: id={job.id}, audio_file_id={audio_file_id}")

        except Exception as e:
            logger.error(f"Job execution failed: id={job.id}, error={e}", exc_info=True)
            raise

    def _build_synthesis_input(self, input_params: dict[str, Any]) -> SynthesizeMultiRoleInput:
        """Build SynthesizeMultiRoleInput from job input parameters.

        Args:
            input_params: Job input parameters dictionary

        Returns:
            SynthesizeMultiRoleInput for the use case
        """
        # Parse turns
        turns = [
            DialogueTurn(
                speaker=turn["speaker"],
                text=turn["text"],
                index=idx,
            )
            for idx, turn in enumerate(input_params.get("turns", []))
        ]

        # Parse voice assignments
        voice_assignments = [
            VoiceAssignment(
                speaker=va["speaker"],
                voice_id=va["voice_id"],
            )
            for va in input_params.get("voice_assignments", [])
        ]

        return SynthesizeMultiRoleInput(
            provider=input_params["provider"],
            turns=turns,
            voice_assignments=voice_assignments,
            language=input_params.get("language", "zh-TW"),
            output_format=input_params.get("output_format", "mp3"),
            gap_ms=input_params.get("gap_ms", 300),
            crossfade_ms=input_params.get("crossfade_ms", 50),
        )

    async def _save_audio_file(
        self,
        job: Job,
        audio_content: bytes,
        content_type: str,
        duration_ms: int,
        session: AsyncSession,
    ) -> uuid.UUID:
        """Save synthesized audio to storage and create AudioFileModel.

        Args:
            job: The job being processed
            audio_content: Raw audio bytes
            content_type: MIME type
            duration_ms: Audio duration in milliseconds
            session: Database session

        Returns:
            UUID of the created AudioFileModel
        """
        # Determine file extension from content type
        extension = ".mp3"
        if "wav" in content_type:
            extension = ".wav"
        elif "ogg" in content_type:
            extension = ".ogg"
        elif "flac" in content_type:
            extension = ".flac"

        # Generate storage path
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        filename = f"{job.id}{extension}"
        storage_key = f"jobs/{job.provider}/{date_str}/{filename}"

        # Upload to storage
        stored_file = await self._storage.upload(
            key=storage_key,
            data=audio_content,
            content_type=content_type,
        )

        # Create AudioFileModel
        audio_file = AudioFileModel(
            id=uuid.uuid4(),
            user_id=job.user_id,
            filename=filename,
            format=extension.replace(".", ""),
            duration_ms=duration_ms,
            sample_rate=44100,  # Default sample rate
            file_size_bytes=stored_file.size_bytes,
            storage_path=stored_file.key,
            source="synthesis",
        )

        session.add(audio_file)
        await session.flush()

        logger.info(f"Saved audio file: id={audio_file.id}, path={stored_file.key}")
        return audio_file.id

    async def _handle_job_failure(
        self,
        job: Job,
        session: AsyncSession,
        job_repo: JobRepositoryImpl,
        error_message: str,
    ) -> None:
        """Handle job failure with retry logic.

        Args:
            job: The failed job
            session: Database session
            job_repo: Job repository
            error_message: Error description
        """
        logger.warning(
            f"Job failed: id={job.id}, retry_count={job.retry_count}, error={error_message}"
        )

        if job.can_retry():
            # Schedule retry with exponential backoff
            job.increment_retry()
            retry_delay = RETRY_DELAYS[min(job.retry_count - 1, len(RETRY_DELAYS) - 1)]

            # Reset to pending for retry
            job.status = JobStatus.PENDING
            job.started_at = None

            await job_repo.update(job)
            await session.commit()

            logger.info(
                f"Job scheduled for retry: id={job.id}, "
                f"retry_count={job.retry_count}, delay={retry_delay}s"
            )

            # Wait before retrying (in real implementation, this would be handled differently)
            await asyncio.sleep(retry_delay)
        else:
            # Max retries exceeded, mark as failed
            job.fail(error_message)
            await job_repo.update(job)
            await session.commit()

            logger.error(
                f"Job permanently failed: id={job.id}, "
                f"retries={job.retry_count}, error={error_message}"
            )

    async def _timeout_monitoring_loop(self) -> None:
        """T038: Monitor and handle timed-out jobs.

        Runs periodically to check for jobs that have been in PROCESSING
        status for longer than JOB_TIMEOUT_MINUTES.
        """
        logger.info(
            f"Timeout monitoring started (interval: {TIMEOUT_CHECK_INTERVAL_SECONDS}s, "
            f"timeout: {JOB_TIMEOUT_MINUTES} min)"
        )

        while self._running:
            try:
                await self._check_timed_out_jobs()
            except Exception as e:
                logger.error(f"Error in timeout monitoring: {e}", exc_info=True)

            await asyncio.sleep(TIMEOUT_CHECK_INTERVAL_SECONDS)

    async def _check_timed_out_jobs(self) -> None:
        """Check for and handle timed-out jobs."""
        async with self._session_factory() as session:
            job_repo = JobRepositoryImpl(session)

            # Get jobs that have timed out
            timeout_delta = timedelta(minutes=JOB_TIMEOUT_MINUTES)
            timed_out_jobs = await job_repo.get_timed_out_jobs(timeout_delta)

            for job in timed_out_jobs:
                logger.warning(f"Job timed out: id={job.id}, started_at={job.started_at}")
                job.fail(f"Job timed out after {JOB_TIMEOUT_MINUTES} minutes")
                await job_repo.update(job)

            if timed_out_jobs:
                await session.commit()
                logger.info(f"Marked {len(timed_out_jobs)} timed-out jobs as failed")

    async def _recover_stale_jobs(self) -> None:
        """T039: Recover stale processing jobs on startup.

        Marks jobs that were in PROCESSING status (likely from a previous
        worker crash) as FAILED.
        """
        async with self._session_factory() as session:
            job_repo = JobRepositoryImpl(session)

            # Get stale processing jobs
            stale_jobs = await job_repo.get_stale_processing_jobs()

            for job in stale_jobs:
                logger.warning(f"Recovering stale job: id={job.id}, started_at={job.started_at}")
                job.fail("Job failed due to worker restart")
                await job_repo.update(job)

            if stale_jobs:
                await session.commit()
                logger.info(f"Recovered {len(stale_jobs)} stale jobs on startup")

    async def _cleanup_loop(self) -> None:
        """T051: Data retention cleanup loop.

        Periodically removes jobs older than DATA_RETENTION_DAYS
        and their associated audio files.
        """
        logger.info(
            f"Cleanup task started (interval: {CLEANUP_INTERVAL_SECONDS}s, "
            f"retention: {DATA_RETENTION_DAYS} days)"
        )

        while self._running:
            try:
                await self._cleanup_old_jobs()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)

            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)

    async def _cleanup_old_jobs(self) -> None:
        """Clean up jobs older than retention period and their audio files."""
        async with self._session_factory() as session:
            job_repo = JobRepositoryImpl(session)

            # Get jobs to clean up
            old_jobs = await job_repo.get_jobs_for_cleanup(
                retention_days=DATA_RETENTION_DAYS,
                limit=CLEANUP_BATCH_SIZE,
            )

            if not old_jobs:
                return

            deleted_count = 0
            for job in old_jobs:
                try:
                    # Delete associated audio file from storage if exists
                    if job.audio_file_id:
                        await self._delete_audio_file(job.audio_file_id, session)

                    # Delete the job
                    await job_repo.delete(job.id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to cleanup job {job.id}: {e}",
                        exc_info=True,
                    )

            if deleted_count > 0:
                await session.commit()
                logger.info(
                    f"Cleaned up {deleted_count} jobs older than {DATA_RETENTION_DAYS} days"
                )

    async def _delete_audio_file(
        self,
        audio_file_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        """Delete audio file from storage and database.

        Args:
            audio_file_id: ID of the audio file to delete
            session: Database session
        """
        from sqlalchemy import delete, select

        from src.infrastructure.persistence.models import AudioFileModel

        # Get the audio file record
        result = await session.execute(
            select(AudioFileModel).where(AudioFileModel.id == audio_file_id)
        )
        audio_file = result.scalar_one_or_none()

        if audio_file is None:
            return

        # Delete from storage
        try:
            deleted = await self._storage.delete(audio_file.storage_path)
            if deleted:
                logger.debug(f"Deleted audio file from storage: {audio_file.storage_path}")
        except Exception as e:
            logger.warning(f"Failed to delete audio file from storage: {e}")

        # Delete from database
        await session.execute(delete(AudioFileModel).where(AudioFileModel.id == audio_file_id))


async def start_job_worker(
    session_factory: async_sessionmaker[AsyncSession],
) -> JobWorker:
    """Create and start a job worker.

    Args:
        session_factory: SQLAlchemy async session factory

    Returns:
        Started JobWorker instance
    """
    worker = JobWorker(session_factory)
    await worker.start()
    return worker
