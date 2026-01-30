"""VoAI Text-to-Speech Provider."""

import contextlib
from typing import Any

import httpx

from src.domain.entities.audio import AudioData
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import AgeGroup, Gender, VoiceProfile
from src.domain.errors import QuotaExceededError
from src.infrastructure.providers.tts.base import BaseTTSProvider

# VoAI voice mappings (using actual VoAI speaker names)
# Reference: https://connect.voai.ai/TTS/GetSpeaker
# Neo model has 46+ speakers, Classic model has 35 speakers
VOAI_VOICES: dict[str, list[dict[str, Any]]] = {
    "zh-TW": [
        # ========== 主要真實聲線 (Real Voice) ==========
        {
            "id": "佑希",
            "name": "佑希",
            "gender": "male",
            "age": 22,
            "styles": ["預設", "聊天", "穩重", "激昂"],
            "use_cases": [
                "廣播",
                "教學",
                "新聞",
                "動畫",
                "叫賣",
                "商務談話",
                "家庭對話",
                "廣告",
                "客服",
            ],
        },
        {
            "id": "雨榛",
            "name": "雨榛",
            "gender": "female",
            "age": 25,
            "styles": ["預設", "聊天", "輕柔", "輕鬆"],
            "use_cases": [
                "冥想",
                "廣播",
                "科幻小說",
                "教學",
                "新聞",
                "商務談話",
                "言情小說",
                "廣告",
                "客服",
            ],
        },
        {
            "id": "子墨",
            "name": "子墨",
            "gender": "male",
            "age": 37,
            "styles": ["預設", "穩健"],
            "use_cases": ["夜間DJ", "冥想", "旁白", "動畫", "言情小說", "家庭對話", "廣告"],
        },
        {
            "id": "柔洢",
            "name": "柔洢",
            "gender": "female",
            "age": 26,
            "styles": ["預設", "可愛", "難過", "生氣", "溫暖"],
            "use_cases": ["夜間DJ", "冥想", "旁白", "廣播", "日常對話", "言情小說", "廣告"],
        },
        {
            "id": "竹均",
            "name": "竹均",
            "gender": "female",
            "age": 22,
            "styles": ["預設", "平靜", "開心", "生氣", "難過"],
            "use_cases": ["日常對話", "言情小說", "家庭對話"],
        },
        {
            "id": "昊宇",
            "name": "昊宇",
            "gender": "male",
            "age": 36,
            "styles": ["預設", "溫暖", "開心", "難過"],
            "use_cases": [
                "夜間DJ",
                "商務談話",
                "廣播",
                "科幻小說",
                "新聞",
                "日常對話",
                "言情小說",
                "家庭對話",
            ],
        },
        {
            "id": "采芸",
            "name": "采芸",
            "gender": "female",
            "age": 25,
            "styles": ["預設", "感性", "難過", "懸疑", "生氣"],
            "use_cases": [
                "夜間DJ",
                "冥想",
                "旁白",
                "廣播",
                "恐怖小說",
                "新聞",
                "日常對話",
                "廣告",
                "客服",
            ],
        },
        {
            "id": "樂晰",
            "name": "樂晰",
            "gender": "female",
            "age": 30,
            "styles": ["預設", "聊天", "可愛"],
            "use_cases": [
                "旁白",
                "廣播",
                "科幻小說",
                "兒童教材",
                "童話故事",
                "教學",
                "新聞",
                "動畫",
                "叫賣",
                "商務談話",
                "日常對話",
                "家庭對話",
                "廣告",
                "客服",
            ],
        },
        {
            "id": "璦廷",
            "name": "璦廷",
            "gender": "female",
            "age": 38,
            "styles": ["預設"],
            "use_cases": ["旁白", "廣播", "新聞"],
        },
        {
            "id": "汪一誠",
            "name": "汪一誠",
            "gender": "male",
            "age": 55,
            "styles": ["預設", "聊天"],
            "use_cases": ["旁白", "新聞", "商務談話"],
        },
        # ========== 兒童聲線 (Child Voice) ==========
        {
            "id": "品妍",
            "name": "品妍",
            "gender": "female",
            "age": 6,
            "styles": ["預設"],
            "use_cases": ["兒童教材", "童話故事", "動畫", "叫賣", "日常對話", "家庭對話", "廣告"],
        },
        {
            "id": "子睿",
            "name": "子睿",
            "gender": "male",
            "age": 5,
            "styles": ["預設"],
            "use_cases": ["兒童教材", "童話故事", "動畫", "日常對話", "家庭對話", "廣告"],
        },
        # ========== 長者聲線 (Senior Voice) ==========
        {
            "id": "春枝",
            "name": "春枝",
            "gender": "female",
            "age": 67,
            "styles": ["預設"],
            "use_cases": ["講古", "童話故事", "恐怖小說", "動畫", "日常對話", "家庭對話", "廣告"],
        },
        {
            "id": "麗珠",
            "name": "麗珠",
            "gender": "female",
            "age": 73,
            "styles": ["預設"],
            "use_cases": ["動畫", "叫賣", "日常對話", "家庭對話", "廣告"],
        },
        # ========== 其他成人聲線 ==========
        {
            "id": "李晴",
            "name": "李晴",
            "gender": "female",
            "age": 28,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "婉婷",
            "name": "婉婷",
            "gender": "female",
            "age": 30,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "淑芬",
            "name": "淑芬",
            "gender": "female",
            "age": 45,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "楷心",
            "name": "楷心",
            "gender": "female",
            "age": 25,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "美霞",
            "name": "美霞",
            "gender": "female",
            "age": 40,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "惠婷",
            "name": "惠婷",
            "gender": "female",
            "age": 28,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "辰辰",
            "name": "辰辰",
            "gender": "male",
            "age": 8,
            "styles": ["預設"],
            "use_cases": ["兒童教材", "童話故事", "動畫"],
        },
        {
            "id": "語安",
            "name": "語安",
            "gender": "female",
            "age": 26,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "虹葳",
            "name": "虹葳",
            "gender": "female",
            "age": 24,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "欣妤",
            "name": "欣妤",
            "gender": "female",
            "age": 23,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "柏翰",
            "name": "柏翰",
            "gender": "male",
            "age": 28,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "凡萱",
            "name": "凡萱",
            "gender": "female",
            "age": 27,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "韻菲",
            "name": "韻菲",
            "gender": "female",
            "age": 29,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "士倫",
            "name": "士倫",
            "gender": "male",
            "age": 32,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "袁祺裕",
            "name": "袁祺裕",
            "gender": "male",
            "age": 35,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "皓軒",
            "name": "皓軒",
            "gender": "male",
            "age": 26,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "靜芝",
            "name": "靜芝",
            "gender": "female",
            "age": 31,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "渝函",
            "name": "渝函",
            "gender": "female",
            "age": 24,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "文彬",
            "name": "文彬",
            "gender": "male",
            "age": 30,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "怡婷",
            "name": "怡婷",
            "gender": "female",
            "age": 26,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        # ========== Neo 專屬聲線 ==========
        {
            "id": "娜娜",
            "name": "娜娜",
            "gender": "female",
            "age": 22,
            "styles": ["預設"],
            "use_cases": ["日常對話", "廣告", "客服"],
        },
        {
            "id": "文澤",
            "name": "文澤",
            "gender": "male",
            "age": 28,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "諭書",
            "name": "諭書",
            "gender": "male",
            "age": 30,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "鳳姊",
            "name": "鳳姊",
            "gender": "female",
            "age": 50,
            "styles": ["預設"],
            "use_cases": ["日常對話", "家庭對話"],
        },
        {
            "id": "悅青",
            "name": "悅青",
            "gender": "female",
            "age": 25,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "俊傑",
            "name": "俊傑",
            "gender": "male",
            "age": 32,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "詠芯",
            "name": "詠芯",
            "gender": "female",
            "age": 24,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "建忠",
            "name": "建忠",
            "gender": "male",
            "age": 45,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "立安",
            "name": "立安",
            "gender": "male",
            "age": 28,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "昱翔",
            "name": "昱翔",
            "gender": "male",
            "age": 26,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "佩綺",
            "name": "佩綺",
            "gender": "female",
            "age": 27,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "豪哥",
            "name": "豪哥",
            "gender": "male",
            "age": 40,
            "styles": ["預設"],
            "use_cases": ["日常對話", "家庭對話", "廣告"],
        },
        {
            "id": "政德",
            "name": "政德",
            "gender": "male",
            "age": 35,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "喬喬",
            "name": "喬喬",
            "gender": "female",
            "age": 20,
            "styles": ["預設"],
            "use_cases": ["日常對話", "廣告", "客服"],
        },
        {
            "id": "軒軒",
            "name": "軒軒",
            "gender": "male",
            "age": 7,
            "styles": ["預設"],
            "use_cases": ["兒童教材", "童話故事", "動畫"],
        },
        {
            "id": "阿皮",
            "name": "阿皮",
            "gender": "male",
            "age": 25,
            "styles": ["預設"],
            "use_cases": ["日常對話", "廣告"],
        },
        {
            "id": "布丁",
            "name": "布丁",
            "gender": "female",
            "age": 22,
            "styles": ["預設"],
            "use_cases": ["日常對話", "廣告", "客服"],
        },
        {
            "id": "明達",
            "name": "明達",
            "gender": "male",
            "age": 38,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "旁白"],
        },
        {
            "id": "泡泡",
            "name": "泡泡",
            "gender": "female",
            "age": 20,
            "styles": ["預設"],
            "use_cases": ["日常對話", "廣告", "客服"],
        },
        {
            "id": "佳雯",
            "name": "佳雯",
            "gender": "female",
            "age": 28,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        {
            "id": "雅琪",
            "name": "雅琪",
            "gender": "female",
            "age": 26,
            "styles": ["預設"],
            "use_cases": ["廣播", "新聞", "客服"],
        },
        # ========== Classic 專屬聲線 (不在 Neo 的) ==========
        {
            "id": "阿偉",
            "name": "阿偉",
            "gender": "male",
            "age": 30,
            "styles": ["預設"],
            "use_cases": ["日常對話", "廣告"],
        },
    ],
}


class VoAITTSProvider(BaseTTSProvider):
    """VoAI TTS provider implementation.

    VoAI is a provider focused on Asian languages, particularly
    Chinese and Japanese.
    """

    def __init__(self, api_key: str, api_endpoint: str | None = None):
        """Initialize VoAI TTS provider.

        Args:
            api_key: VoAI API key
            api_endpoint: VoAI API endpoint (e.g., "connect.voai.ai")
                         If not provided, defaults to "api.voai.io"
        """
        super().__init__("voai")
        self._api_key = api_key

        # Use provided endpoint or default
        endpoint = api_endpoint or "api.voai.io"
        # Remove https:// prefix if present
        endpoint = endpoint.replace("https://", "").replace("http://", "")
        self._base_url = f"https://{endpoint}/v1"

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using VoAI API.

        VoAI uses a different API format:
        - Endpoint: /TTS/Speech
        - Headers: x-api-key, x-output-format
        - Body: version, speaker, style, etc.
        """
        audio_format = self._get_output_format(request)

        # Remove /v1 suffix since VoAI uses /TTS/Speech directly
        base_url = self._base_url.replace("/v1", "")
        url = f"{base_url}/TTS/Speech"

        # Map format to VoAI output format
        format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "pcm": "wav",  # VoAI doesn't support raw PCM, use WAV
        }
        output_format = format_map.get(audio_format.value, "wav")

        headers = {
            "x-api-key": self._api_key,
            "x-output-format": output_format,
            "Content-Type": "application/json",
        }

        # Voice ID may arrive in voice_cache_id format ("voai:佑希") from
        # multi-role TTS, or as a plain speaker name ("佑希").
        # Strip the provider prefix if present.
        voice_id = request.voice_id
        if voice_id.startswith("voai:"):
            voice_id = voice_id[len("voai:"):]

        # Also support legacy IDs for backward compatibility
        legacy_speaker_map = {
            "voai-tw-male-1": "佑希",
            "voai-tw-female-1": "雨榛",
            "voai-tw-male-2": "子墨",
            "voai-tw-female-2": "柔洢",
            "voai-tw-female-3": "竹均",
            "voai-tw-male-3": "昊宇",
            "voai-tw-female-4": "采芸",
            "voai-tw-female-5": "樂晰",
            "voai-tw-male-4": "汪一誠",
            "voai-tw-female-6": "璦廷",
        }
        # Use voice_id directly if it's a speaker name, otherwise map from legacy ID
        speaker = legacy_speaker_map.get(voice_id, voice_id)
        # Validate speaker exists, fallback to 佑希 if not found
        valid_speakers = {v["name"] for v in VOAI_VOICES.get("zh-TW", [])}
        if speaker not in valid_speakers:
            speaker = "佑希"

        # Clamp parameters to VoAI API limits
        # VoAI speed range: [0.5, 1.5]
        # VoAI pitch_shift range: [-5, 5]
        speed = max(0.5, min(1.5, request.speed))
        pitch_shift = max(-5, min(5, int(request.pitch)))

        body = {
            "version": "Neo",
            "text": request.text,
            "speaker": speaker,
            "style": "預設",
            "speed": speed,
            "pitch_shift": pitch_shift,
            "style_weight": 0,
            "breath_pause": 0,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code != 200:
                error_detail = response.text

                # T012: Detect 429 quota exceeded
                if response.status_code == 429:
                    retry_after = None
                    if "retry-after" in response.headers:
                        with contextlib.suppress(ValueError, TypeError):
                            retry_after = int(response.headers["retry-after"])
                    raise QuotaExceededError(
                        provider="voai",
                        retry_after=retry_after,
                        original_error=error_detail,
                    )

                raise RuntimeError(
                    f"VoAI TTS failed with status {response.status_code}: {error_detail}"
                )

            # VoAI returns audio directly
            return AudioData(
                data=response.content,
                format=audio_format,
                sample_rate=24000,
            )

    def _get_age_group(self, age: int) -> AgeGroup:
        """Map age to AgeGroup enum."""
        if age <= 12:
            return AgeGroup.CHILD
        elif age <= 25:
            return AgeGroup.YOUNG
        elif age <= 60:
            return AgeGroup.ADULT
        else:
            return AgeGroup.SENIOR

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available VoAI voices.

        Returns hardcoded voice list since VoAI doesn't provide a voices API endpoint.
        """
        voices = []

        def create_voice_profile(v: dict[str, Any], lang: str) -> VoiceProfile:
            """Create a VoiceProfile from voice data."""
            gender = Gender.NEUTRAL
            if v.get("gender") == "female":
                gender = Gender.FEMALE
            elif v.get("gender") == "male":
                gender = Gender.MALE

            age = v.get("age", 30)
            age_group = self._get_age_group(age)

            return VoiceProfile(
                id=f"voai:{v['id']}",
                voice_id=v["id"],
                display_name=v["name"],
                provider="voai",
                language=lang,
                gender=gender,
                age_group=age_group,
                styles=tuple(v.get("styles", ["預設"])),
                use_cases=tuple(v.get("use_cases", [])),
            )

        if language:
            voice_data = VOAI_VOICES.get(language, [])
            for v in voice_data:
                voices.append(create_voice_profile(v, language))
        else:
            # Return all voices for all languages
            for lang, voice_data in VOAI_VOICES.items():
                for v in voice_data:
                    voices.append(create_voice_profile(v, lang))

        return voices

    def get_supported_params(self) -> dict:
        """Get VoAI-specific supported parameter ranges.

        VoAI has different limits than other providers:
        - speed: [0.5, 1.5] (not 2.0)
        - pitch: [-5, 5] (not [-20, 20])
        """
        return {
            "speed": {"min": 0.5, "max": 1.5, "default": 1.0},
            "pitch": {"min": -5.0, "max": 5.0, "default": 0.0},
            "volume": {"min": 0.0, "max": 2.0, "default": 1.0},
        }
