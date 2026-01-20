"""Audio storage service for interaction module.

T016: Manages audio file storage for user and AI recordings.
"""

import shutil
from pathlib import Path
from uuid import UUID

import aiofiles
import aiofiles.os


class AudioStorageService:
    """Service for managing interaction audio files.

    Storage structure:
    storage/interactions/{session_id}/
        turn_001_user.webm
        turn_001_ai.mp3
        turn_002_user.webm
        turn_002_ai.mp3
    """

    def __init__(self, base_path: str = "storage/interactions") -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: UUID) -> Path:
        """Get directory path for a session."""
        return self._base_path / str(session_id)

    def _user_audio_path(self, session_id: UUID, turn_number: int, format: str = "webm") -> Path:
        """Get path for user audio file."""
        return self._session_dir(session_id) / f"turn_{turn_number:03d}_user.{format}"

    def _ai_audio_path(self, session_id: UUID, turn_number: int, format: str = "mp3") -> Path:
        """Get path for AI audio file."""
        return self._session_dir(session_id) / f"turn_{turn_number:03d}_ai.{format}"

    async def ensure_session_dir(self, session_id: UUID) -> Path:
        """Create session directory if it doesn't exist."""
        dir_path = self._session_dir(session_id)
        await aiofiles.os.makedirs(dir_path, exist_ok=True)
        return dir_path

    async def save_user_audio(
        self, session_id: UUID, turn_number: int, audio_data: bytes, format: str = "webm"
    ) -> str:
        """Save user audio and return relative path."""
        await self.ensure_session_dir(session_id)
        path = self._user_audio_path(session_id, turn_number, format)

        async with aiofiles.open(path, "wb") as f:
            await f.write(audio_data)

        return str(path.relative_to(self._base_path.parent))

    async def save_ai_audio(
        self, session_id: UUID, turn_number: int, audio_data: bytes, format: str = "mp3"
    ) -> str:
        """Save AI audio and return relative path."""
        await self.ensure_session_dir(session_id)
        path = self._ai_audio_path(session_id, turn_number, format)

        async with aiofiles.open(path, "wb") as f:
            await f.write(audio_data)

        return str(path.relative_to(self._base_path.parent))

    async def append_user_audio(
        self, session_id: UUID, turn_number: int, audio_chunk: bytes, format: str = "webm"
    ) -> str:
        """Append audio chunk to user audio file (for streaming)."""
        await self.ensure_session_dir(session_id)
        path = self._user_audio_path(session_id, turn_number, format)

        async with aiofiles.open(path, "ab") as f:
            await f.write(audio_chunk)

        return str(path.relative_to(self._base_path.parent))

    async def append_ai_audio(
        self, session_id: UUID, turn_number: int, audio_chunk: bytes, format: str = "mp3"
    ) -> str:
        """Append audio chunk to AI audio file (for streaming)."""
        await self.ensure_session_dir(session_id)
        path = self._ai_audio_path(session_id, turn_number, format)

        async with aiofiles.open(path, "ab") as f:
            await f.write(audio_chunk)

        return str(path.relative_to(self._base_path.parent))

    async def get_audio(self, relative_path: str) -> bytes | None:
        """Read audio file by relative path."""
        full_path = self._base_path.parent / relative_path
        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def get_audio_path(self, relative_path: str) -> Path | None:
        """Get full path for audio file."""
        full_path = self._base_path.parent / relative_path
        return full_path if full_path.exists() else None

    async def delete_session_audio(self, session_id: UUID) -> bool:
        """Delete all audio files for a session."""
        dir_path = self._session_dir(session_id)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            return True
        return False

    async def delete_turn_audio(self, session_id: UUID, turn_number: int) -> bool:
        """Delete audio files for a specific turn."""
        deleted = False
        for format in ["webm", "mp3", "wav"]:
            user_path = self._user_audio_path(session_id, turn_number, format)
            ai_path = self._ai_audio_path(session_id, turn_number, format)

            for path in [user_path, ai_path]:
                if path.exists():
                    await aiofiles.os.remove(path)
                    deleted = True

        return deleted

    async def get_session_audio_size(self, session_id: UUID) -> int:
        """Get total size of all audio files for a session in bytes."""
        dir_path = self._session_dir(session_id)
        if not dir_path.exists():
            return 0

        total_size = 0
        for file_path in dir_path.iterdir():
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size
