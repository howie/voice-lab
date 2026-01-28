"""Infrastructure Providers - Adapters for external services.

Provider classes are imported lazily in the DI container to avoid
import errors when their dependencies are not installed.

To use a provider, import it directly:
    from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider
"""
