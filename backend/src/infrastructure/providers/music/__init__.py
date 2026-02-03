"""Music generation providers.

Provider classes are imported lazily in the factory to avoid
import errors when their dependencies are not installed.

To use a provider, import it directly:
    from src.infrastructure.providers.music.mureka_music import MurekaMusicProvider
"""
