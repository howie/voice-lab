# Factory Pattern Proposal: Music Provider Abstraction

> Research Date: 2026-01-30

## Feasibility Assessment

**Result: Feasible and Recommended.**

The existing codebase already uses Factory + Interface patterns for TTS providers (`ITTSProvider` / `TTSProviderFactory`). Applying the same pattern to music generation providers is straightforward and consistent with the project architecture.

## Existing Pattern Reference

The TTS provider pattern serves as a blueprint:

```
application/interfaces/tts_provider.py     -> ITTSProvider (ABC)
infrastructure/providers/tts/base.py       -> BaseTTSProvider
infrastructure/providers/tts/factory.py    -> TTSProviderFactory
infrastructure/providers/tts/elevenlabs_tts.py  -> concrete impl
infrastructure/providers/tts/azure_tts.py       -> concrete impl
...
```

Key design elements reused:
- **Interface (port)** in `application/interfaces/` defines the contract
- **Base class** in `infrastructure/providers/` provides shared logic
- **Factory** handles provider selection, credential injection, and instantiation
- **Lazy imports** in factory to avoid loading unused providers

## Common Surface Area Analysis

Both Suno and Mureka share these operations:

| Operation | Mureka | Suno (unofficial) | Abstractable? |
|-----------|--------|-------------------|---------------|
| Generate song (vocals) | `submit_song(lyrics, prompt, model)` | `custom_generate(prompt, tags, title, lyrics)` | Yes |
| Generate instrumental | `submit_instrumental(prompt, model)` | `generate(prompt, make_instrumental=True)` | Yes |
| Generate lyrics | `submit_lyrics(prompt)` | `generate_lyrics(prompt)` | Yes |
| Poll task status | `query_song_task(task_id)` | `get(ids=clip_ids)` | Yes |
| Extend song | `extend_lyrics(lyrics, prompt)` | `extend_audio(clip_id, continue_at)` | Partially (different semantics) |
| Stem separation | `song/stem` | `generate_stems` | Yes |

**Conclusion**: The core operations (song, instrumental, lyrics, status polling) map well to a unified interface. Extension differs semantically (Mureka extends lyrics, Suno extends audio from a timestamp) but can be accommodated with a union-type request.

## Proposed Architecture

### 1. Interface (Port)

```python
# backend/src/application/interfaces/music_provider.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class MusicTaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MusicSubmitResult:
    """Unified result from submitting a generation task."""
    task_id: str
    provider: str
    status: MusicTaskStatus


@dataclass
class MusicTaskResult:
    """Unified result from querying a task."""
    task_id: str
    provider: str
    status: MusicTaskStatus
    audio_url: str | None = None
    cover_url: str | None = None
    lyrics: str | None = None
    duration_ms: int | None = None
    title: str | None = None
    error_message: str | None = None


class IMusicProvider(ABC):
    """Abstract interface for music generation providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'mureka', 'suno')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""
        ...

    @abstractmethod
    async def generate_song(
        self,
        *,
        lyrics: str | None = None,
        prompt: str | None = None,
        model: str | None = None,
    ) -> MusicSubmitResult:
        """Submit a song generation task (vocals + music)."""
        ...

    @abstractmethod
    async def generate_instrumental(
        self,
        *,
        prompt: str,
        model: str | None = None,
    ) -> MusicSubmitResult:
        """Submit an instrumental/BGM generation task."""
        ...

    @abstractmethod
    async def generate_lyrics(
        self,
        *,
        prompt: str | None = None,
    ) -> MusicSubmitResult:
        """Submit a lyrics generation task."""
        ...

    @abstractmethod
    async def query_task(
        self,
        task_id: str,
        task_type: str,
    ) -> MusicTaskResult:
        """Query the status of a generation task."""
        ...

    async def health_check(self) -> bool:
        """Check if provider is available."""
        return True
```

### 2. Mureka Adapter (wraps existing client)

```python
# backend/src/infrastructure/providers/music/mureka_music.py

from src.application.interfaces.music_provider import (
    IMusicProvider, MusicSubmitResult, MusicTaskResult, MusicTaskStatus,
)
from src.infrastructure.adapters.mureka.client import (
    MurekaAPIClient, MurekaTaskStatus,
)


# Status mapping: Mureka -> unified
_STATUS_MAP = {
    MurekaTaskStatus.PREPARING: MusicTaskStatus.PENDING,
    MurekaTaskStatus.PROCESSING: MusicTaskStatus.PROCESSING,
    MurekaTaskStatus.COMPLETED: MusicTaskStatus.COMPLETED,
    MurekaTaskStatus.FAILED: MusicTaskStatus.FAILED,
}


class MurekaMusicProvider(IMusicProvider):
    """Mureka AI music generation provider."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._client = MurekaAPIClient(api_key=api_key, base_url=base_url)

    @property
    def name(self) -> str:
        return "mureka"

    @property
    def display_name(self) -> str:
        return "Mureka AI"

    async def generate_song(
        self, *, lyrics=None, prompt=None, model=None,
    ) -> MusicSubmitResult:
        result = await self._client.submit_song(
            lyrics=lyrics, prompt=prompt, model=model or "auto",
        )
        return MusicSubmitResult(
            task_id=result.task_id,
            provider="mureka",
            status=MusicTaskStatus.PENDING,
        )

    async def generate_instrumental(
        self, *, prompt, model=None,
    ) -> MusicSubmitResult:
        result = await self._client.submit_instrumental(
            prompt=prompt, model=model or "auto",
        )
        return MusicSubmitResult(
            task_id=result.task_id,
            provider="mureka",
            status=MusicTaskStatus.PENDING,
        )

    async def generate_lyrics(self, *, prompt=None) -> MusicSubmitResult:
        result = await self._client.submit_lyrics(prompt=prompt)
        return MusicSubmitResult(
            task_id=result.task_id,
            provider="mureka",
            status=MusicTaskStatus.COMPLETED,  # Lyrics are synchronous
        )

    async def query_task(self, task_id, task_type) -> MusicTaskResult:
        result = await self._client.query_task(task_id, task_type)
        return MusicTaskResult(
            task_id=result.task_id,
            provider="mureka",
            status=_STATUS_MAP.get(result.status, MusicTaskStatus.PROCESSING),
            audio_url=result.mp3_url,
            cover_url=result.cover_url,
            lyrics=result.lyrics,
            duration_ms=result.duration_ms,
            title=result.title,
            error_message=result.error_message,
        )
```

### 3. Suno Adapter (future, when official API available)

```python
# backend/src/infrastructure/providers/music/suno_music.py  (future)

class SunoMusicProvider(IMusicProvider):
    """Suno AI music generation provider.

    NOTE: Requires official Suno API (not yet available as of Jan 2026).
    Do NOT implement using unofficial cookie-based access for production.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._base_url = "https://api.suno.ai"  # hypothetical official URL

    @property
    def name(self) -> str:
        return "suno"

    @property
    def display_name(self) -> str:
        return "Suno AI"

    async def generate_song(self, *, lyrics=None, prompt=None, model=None):
        # Map to Suno's custom_generate endpoint
        # lyrics -> prompt field in custom mode
        # prompt -> tags field
        # model -> model_version field
        ...

    async def generate_instrumental(self, *, prompt, model=None):
        # Use generate endpoint with make_instrumental=True
        ...

    async def generate_lyrics(self, *, prompt=None):
        # Use generate_lyrics endpoint
        ...

    async def query_task(self, task_id, task_type):
        # Map Suno statuses: submitted/queued -> PENDING,
        # streaming -> PROCESSING, complete -> COMPLETED
        ...
```

### 4. Factory

```python
# backend/src/infrastructure/providers/music/factory.py

from src.application.interfaces.music_provider import IMusicProvider


class MusicProviderNotSupportedError(Exception):
    pass


class MusicProviderFactory:
    """Factory for creating music generation provider instances."""

    SUPPORTED_PROVIDERS = ["mureka"]  # Add "suno" when official API available

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        return cls.SUPPORTED_PROVIDERS.copy()

    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        return provider_name.lower() in cls.SUPPORTED_PROVIDERS

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str | None = None,
        **kwargs,
    ) -> IMusicProvider:
        provider_name = provider_name.lower()

        if provider_name == "mureka":
            from src.infrastructure.providers.music.mureka_music import (
                MurekaMusicProvider,
            )
            return MurekaMusicProvider(
                api_key=api_key,
                base_url=kwargs.get("base_url"),
            )

        # Future: uncomment when Suno official API available
        # if provider_name == "suno":
        #     from src.infrastructure.providers.music.suno_music import (
        #         SunoMusicProvider,
        #     )
        #     return SunoMusicProvider(api_key=api_key)

        raise MusicProviderNotSupportedError(
            f"Provider '{provider_name}' is not supported. "
            f"Supported: {', '.join(cls.SUPPORTED_PROVIDERS)}"
        )

    @classmethod
    def create_default(cls, provider_name: str = "mureka") -> IMusicProvider:
        """Create provider with system credentials from env."""
        return cls.create(provider_name)
```

## Proposed File Structure

```
backend/src/
  application/
    interfaces/
      music_provider.py          # IMusicProvider (NEW)
  infrastructure/
    adapters/
      mureka/
        client.py                # MurekaAPIClient (EXISTING, unchanged)
    providers/
      music/
        __init__.py              # (NEW)
        factory.py               # MusicProviderFactory (NEW)
        mureka_music.py          # MurekaMusicProvider (NEW)
        suno_music.py            # SunoMusicProvider (FUTURE)
```

## Migration Path

### Phase 1: Interface + Factory (Low Risk)

1. Create `IMusicProvider` interface
2. Create `MurekaMusicProvider` wrapping existing `MurekaAPIClient`
3. Create `MusicProviderFactory`
4. **No changes to existing `MusicGenerationService`** -- it continues to work as-is

### Phase 2: Service Layer Integration

1. Update `MusicGenerationService` to accept `IMusicProvider` instead of `MurekaAPIClient`
2. Add `provider` field to `MusicGenerationJob` entity and DB model
3. Update API schemas to accept optional `provider` parameter
4. Default to `mureka` for backward compatibility

### Phase 3: Suno Integration (When Official API Available)

1. Implement `SunoMusicProvider`
2. Add `"suno"` to `MusicProviderFactory.SUPPORTED_PROVIDERS`
3. Add `suno_api_key` to config
4. Status mapping: Suno `submitted`/`queued` -> `PENDING`, `streaming` -> `PROCESSING`, `complete` -> `COMPLETED`

## Design Decisions

### Why Factory Pattern (vs Strategy, Plugin, etc.)

| Pattern | Pros | Cons | Fit |
|---------|------|------|-----|
| **Factory** | Simple, matches existing codebase pattern, lazy imports | Less dynamic than plugin | **Best fit** |
| Strategy | Runtime swapping | Over-engineered for 2 providers | Not needed |
| Plugin (entry points) | Extensible by third parties | Too complex, not needed | No |
| Registry/decorator | Auto-discovery | Magic, harder to debug | No |

The Factory pattern is chosen because:
1. It matches the existing `TTSProviderFactory` pattern exactly
2. The team is already familiar with this approach
3. Simple to implement and maintain
4. Lazy imports prevent loading unused provider dependencies

### Status Mapping Strategy

Each provider has different status values. The interface uses a unified `MusicTaskStatus` enum, and each adapter is responsible for mapping:

```
Mureka:  preparing  -> PENDING
         processing -> PROCESSING
         completed  -> COMPLETED
         failed     -> FAILED

Suno:    submitted  -> PENDING
         queued     -> PENDING
         streaming  -> PROCESSING
         complete   -> COMPLETED
```

### Extension Semantics

Mureka and Suno handle "extension" differently:
- **Mureka**: Extends lyrics text (add more sections)
- **Suno**: Extends audio from a specific timestamp

These are fundamentally different operations. The recommendation is to either:
1. Keep extension as a provider-specific method (not in the interface), or
2. Create a union-type request that accommodates both patterns

Option 1 is simpler and avoids leaky abstractions.

## Conclusion

The factory pattern is well-suited for abstracting music generation providers in this codebase. The implementation aligns with existing architectural patterns and can be done incrementally without breaking changes. Start with Mureka as the sole concrete provider and add Suno when an official API becomes available.
