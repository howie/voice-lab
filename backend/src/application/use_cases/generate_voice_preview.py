"""Generate Voice Preview Use Case.

Feature: 013-tts-role-mgmt
US5: 播放聲音預覽 (Voice Preview Playback)
"""

import logging

from src.application.interfaces.storage_service import IStorageService
from src.application.interfaces.tts_provider import ITTSProvider
from src.application.interfaces.voice_cache_repository import IVoiceCacheRepository
from src.domain.entities.tts import TTSRequest
from src.domain.errors import ProviderError, SynthesisError, VoiceNotFoundError

logger = logging.getLogger(__name__)

# Fixed preview text for on-demand synthesis
PREVIEW_TEXT = "大家好，歡迎收聽，我是你的語音助理。"


class GenerateVoicePreview:
    """Generate or retrieve a voice preview audio URL.

    Logic:
    1. Look up the voice in cache → raise VoiceNotFoundError if missing
    2. If sample_audio_url already exists → return it (cache hit)
    3. If ElevenLabs and metadata has preview_url → persist & return
    4. Otherwise → synthesize with fixed text → upload to storage → persist URL
    """

    def __init__(
        self,
        providers: dict[str, ITTSProvider],
        storage: IStorageService,
        voice_cache_repo: IVoiceCacheRepository,
    ) -> None:
        self._providers = providers
        self._storage = storage
        self._voice_cache_repo = voice_cache_repo

    async def execute(self, voice_cache_id: str) -> str:
        """Generate or retrieve a preview URL for the given voice.

        Args:
            voice_cache_id: Voice cache ID (format: provider:voice_id)

        Returns:
            URL to the preview audio file

        Raises:
            VoiceNotFoundError: If the voice doesn't exist in cache
            ProviderError: If the TTS provider is unavailable
            SynthesisError: If synthesis fails
        """
        # 1. Look up voice in cache
        voice = await self._voice_cache_repo.get_by_id(voice_cache_id)
        if not voice:
            raise VoiceNotFoundError(voice_cache_id)

        # 2. Cache hit — already has a preview URL
        if voice.sample_audio_url:
            return voice.sample_audio_url

        # 3. ElevenLabs CDN preview
        if voice.provider == "elevenlabs" and voice.metadata:
            cdn_url = voice.metadata.get("preview_url")
            if cdn_url:
                logger.info("Using ElevenLabs CDN preview for %s", voice_cache_id)
                await self._voice_cache_repo.update_sample_audio_url(
                    voice_cache_id, cdn_url
                )
                return cdn_url

        # 4. On-demand synthesis
        provider = self._providers.get(voice.provider)
        if not provider:
            raise ProviderError(
                voice.provider,
                f"Provider '{voice.provider}' is not configured",
            )

        logger.info("Synthesizing preview for %s via %s", voice_cache_id, voice.provider)

        request = TTSRequest(
            text=PREVIEW_TEXT,
            voice_id=voice.voice_id,
            provider=voice.provider,
            language=voice.language or "zh-TW",
        )

        try:
            result = await provider.synthesize(request)
        except Exception as e:
            error_msg = str(e)
            if "unavailable" in error_msg.lower() or "timeout" in error_msg.lower():
                raise ProviderError(voice.provider, error_msg) from e
            raise SynthesisError(voice.provider, error_msg) from e

        # Upload to storage
        storage_key = f"previews/{voice.provider}/{voice.voice_id}.mp3"
        stored = await self._storage.upload(
            key=storage_key,
            data=result.audio.data,
            content_type="audio/mpeg",
        )

        # Persist the URL
        await self._voice_cache_repo.update_sample_audio_url(
            voice_cache_id, stored.url
        )

        logger.info("Preview generated for %s → %s", voice_cache_id, stored.url)
        return stored.url
