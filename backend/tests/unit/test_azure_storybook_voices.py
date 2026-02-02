"""Unit tests for Azure storybook voice features.

Covers:
- AzureVoiceFetcher.fetch_storybook_voices() filtering & sorting
- VoiceMetadataInferrer.infer_storybook_suitability()
- SyncVoicesUseCase._azure_to_voice_profile() storybook use_case tagging
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.domain.services.voice_metadata_inferrer import VoiceMetadataInferrer
from src.infrastructure.providers.tts.voice_fetchers.azure_voice_fetcher import (
    AzureVoiceFetcher,
    AzureVoiceInfo,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_voice(
    short_name: str = "zh-TW-HsiaoChenNeural",
    locale: str = "zh-TW",
    gender: str = "Female",
    style_list: list[str] | None = None,
    role_play_list: list[str] | None = None,
    display_name: str = "HsiaoChen",
    local_name: str = "曉臻",
) -> AzureVoiceInfo:
    return AzureVoiceInfo(
        short_name=short_name,
        display_name=display_name,
        local_name=local_name,
        locale=locale,
        gender=gender,
        voice_type="Neural",
        style_list=style_list or [],
        role_play_list=role_play_list or [],
    )


# ===========================================================================
# VoiceMetadataInferrer.infer_storybook_suitability
# ===========================================================================


class TestInferStorybookSuitability:
    """Unit tests for VoiceMetadataInferrer.infer_storybook_suitability."""

    def setup_method(self):
        self.inferrer = VoiceMetadataInferrer()

    def test_zh_tw_locale_is_suitable(self):
        assert self.inferrer.infer_storybook_suitability(locale="zh-TW") is True

    def test_zh_cn_locale_without_styles_is_not_suitable(self):
        assert self.inferrer.infer_storybook_suitability(locale="zh-CN") is False

    def test_en_us_locale_without_styles_is_not_suitable(self):
        assert self.inferrer.infer_storybook_suitability(locale="en-US") is False

    def test_gentle_style_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(style_list=["gentle"], locale="zh-CN") is True
        )

    def test_cheerful_style_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(style_list=["cheerful"], locale="zh-CN")
            is True
        )

    def test_story_style_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(style_list=["story"], locale="zh-CN") is True
        )

    def test_calm_style_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(style_list=["calm"], locale="zh-CN") is True
        )

    def test_affectionate_style_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(style_list=["affectionate"], locale="zh-CN")
            is True
        )

    def test_newscast_style_alone_is_not_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(style_list=["newscast"], locale="zh-CN")
            is False
        )

    def test_girl_role_play_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(role_play_list=["Girl"], locale="zh-CN")
            is True
        )

    def test_boy_role_play_is_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(role_play_list=["Boy"], locale="zh-CN")
            is True
        )

    def test_olderadult_role_alone_is_not_suitable(self):
        assert (
            self.inferrer.infer_storybook_suitability(role_play_list=["OlderAdult"], locale="zh-CN")
            is False
        )

    def test_no_args_is_not_suitable(self):
        assert self.inferrer.infer_storybook_suitability() is False


# ===========================================================================
# AzureVoiceFetcher.fetch_storybook_voices
# ===========================================================================


class TestFetchStorybookVoices:
    """Unit tests for AzureVoiceFetcher.fetch_storybook_voices."""

    @pytest.mark.asyncio
    async def test_returns_only_chinese_voices(self):
        """Non-Chinese voices should be excluded."""
        voices = [
            _make_voice("zh-TW-HsiaoChenNeural", locale="zh-TW"),
            _make_voice("en-US-JennyNeural", locale="en-US"),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert len(result) == 1
        assert result[0].locale == "zh-TW"

    @pytest.mark.asyncio
    async def test_includes_zh_tw_without_styles(self):
        """All zh-TW voices should be included even without storybook styles."""
        voices = [
            _make_voice("zh-TW-YunJheNeural", locale="zh-TW"),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_includes_zh_cn_with_storybook_style(self):
        """zh-CN voices with gentle/cheerful styles should be included."""
        voices = [
            _make_voice(
                "zh-CN-XiaomoNeural",
                locale="zh-CN",
                style_list=["gentle", "cheerful"],
                role_play_list=["Girl", "Boy"],
            ),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert len(result) == 1
        assert result[0].short_name == "zh-CN-XiaomoNeural"

    @pytest.mark.asyncio
    async def test_excludes_zh_cn_without_qualifying_attrs(self):
        """zh-CN voices with no storybook styles/roles should be excluded."""
        voices = [
            _make_voice(
                "zh-CN-YunxiNeural",
                locale="zh-CN",
                style_list=["newscast"],
            ),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_sort_order_zh_tw_first(self):
        """zh-TW voices should sort before zh-CN voices."""
        voices = [
            _make_voice("zh-CN-XiaomoNeural", locale="zh-CN", style_list=["gentle"]),
            _make_voice("zh-TW-HsiaoChenNeural", locale="zh-TW"),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert result[0].locale == "zh-TW"
        assert result[1].locale == "zh-CN"

    @pytest.mark.asyncio
    async def test_sort_order_styled_before_unstyled(self):
        """Voices with styles should sort before those without."""
        voices = [
            _make_voice("zh-TW-YunJheNeural", locale="zh-TW", style_list=[]),
            _make_voice("zh-TW-HsiaoChenNeural", locale="zh-TW", style_list=["cheerful"]),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert result[0].short_name == "zh-TW-HsiaoChenNeural"
        assert result[1].short_name == "zh-TW-YunJheNeural"

    @pytest.mark.asyncio
    async def test_includes_voice_with_boy_role(self):
        """Voices with Boy role-play should be included."""
        voices = [
            _make_voice("zh-CN-YunyeNeural", locale="zh-CN", role_play_list=["Boy", "Girl"]),
        ]
        fetcher = AzureVoiceFetcher(api_key="fake", region="eastasia")

        with patch.object(fetcher, "fetch_voices", new_callable=AsyncMock, return_value=voices):
            result = await fetcher.fetch_storybook_voices()

        assert len(result) == 1


# ===========================================================================
# SyncVoicesUseCase._azure_to_voice_profile storybook tagging
# ===========================================================================


class TestAzureToVoiceProfileStorybookTag:
    """Unit tests for storybook use_case tagging in _azure_to_voice_profile."""

    def _build_use_case(self):
        from src.application.use_cases.sync_voices import SyncVoicesUseCase

        return SyncVoicesUseCase(
            voice_cache_repo=AsyncMock(),
            sync_job_repo=AsyncMock(),
        )

    def test_zh_tw_voice_gets_storybook_tag(self):
        uc = self._build_use_case()
        voice = _make_voice("zh-TW-HsiaoChenNeural", locale="zh-TW")
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" in profile.use_cases

    def test_gentle_style_gets_storybook_tag(self):
        uc = self._build_use_case()
        voice = _make_voice("zh-CN-XiaomoNeural", locale="zh-CN", style_list=["gentle", "newscast"])
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" in profile.use_cases

    def test_girl_role_gets_storybook_tag(self):
        uc = self._build_use_case()
        voice = _make_voice("zh-CN-XiaomoNeural", locale="zh-CN", role_play_list=["Girl"])
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" in profile.use_cases

    def test_en_us_no_styles_no_storybook_tag(self):
        uc = self._build_use_case()
        voice = _make_voice("en-US-JennyNeural", locale="en-US")
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" not in profile.use_cases

    def test_zh_cn_newscast_only_no_storybook_tag(self):
        uc = self._build_use_case()
        voice = _make_voice("zh-CN-YunxiNeural", locale="zh-CN", style_list=["newscast"])
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" not in profile.use_cases

    def test_cheerful_style_gets_storybook_tag(self):
        uc = self._build_use_case()
        voice = _make_voice("zh-CN-XiaoyiNeural", locale="zh-CN", style_list=["cheerful"])
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" in profile.use_cases

    def test_storybook_coexists_with_other_use_cases(self):
        """Storybook tag should coexist with news/assistant tags."""
        uc = self._build_use_case()
        voice = _make_voice(
            "zh-TW-HsiaoChenNeural",
            locale="zh-TW",
            style_list=["newscast", "chat", "cheerful"],
        )
        profile = uc._azure_to_voice_profile(voice)
        assert "storybook" in profile.use_cases
        assert "news" in profile.use_cases
        assert "assistant" in profile.use_cases
