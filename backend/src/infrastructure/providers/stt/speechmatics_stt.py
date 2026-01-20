"""Speechmatics STT Provider.

Speechmatics 是兒童語音辨識領域的業界領導者，使用 SSL (Self-Supervised Learning)
技術達到 91.8% 的兒童語音準確度（英語 Common Voice 基準）。

注意：Speechmatics 沒有專用的「兒童模式」API 參數，其優異的兒童語音辨識效果
來自於模型訓練層面的改進。我們透過以下方式優化兒童語音場景：
- 使用 enhanced operating_point 獲得最高準確度
- 添加 additional_vocab 提高兒童常用詞彙辨識率
- 設定 output_locale 確保正確的繁簡體輸出
"""

import asyncio
import io

from speechmatics.batch_client import BatchClient  # type: ignore[import-not-found,import-untyped]
from speechmatics.models import ConnectionSettings  # type: ignore[import-not-found,import-untyped]

from src.domain.entities.stt import STTRequest, WordTiming
from src.infrastructure.providers.stt.base import BaseSTTProvider

# 兒童語音常用詞彙（中文）- 提高辨識率
CHILD_VOCAB_ZH = [
    {"content": "媽媽"},
    {"content": "爸爸"},
    {"content": "老師"},
    {"content": "小朋友"},
    {"content": "老師好"},
    {"content": "謝謝"},
    {"content": "對不起"},
    {"content": "沒關係"},
    {"content": "ㄅㄆㄇ"},
    {"content": "注音"},
    {"content": "九九乘法表"},
]

# 兒童語音常用詞彙（英文）
CHILD_VOCAB_EN = [
    {"content": "mommy"},
    {"content": "daddy"},
    {"content": "teacher"},
    {"content": "please"},
    {"content": "thank you"},
    {"content": "sorry"},
]


class SpeechmaticsSTTProvider(BaseSTTProvider):
    """Speechmatics STT provider implementation.

    特點：
    - 兒童語音辨識業界最佳 (91.8% 準確度)
    - 支援 50+ 語言
    - 優異的噪音環境表現
    - 支援繁體/簡體中文輸出
    """

    def __init__(self, api_key: str):
        """Initialize Speechmatics provider.

        Args:
            api_key: Speechmatics API key
        """
        super().__init__("speechmatics")
        self._api_key = api_key
        self._url = "https://asr.api.speechmatics.com/v2"

    @property
    def display_name(self) -> str:
        return "Speechmatics"

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_child_mode(self) -> bool:
        # Speechmatics 的兒童語音優化來自模型訓練，
        # 雖然沒有專用 API 參數，但我們透過 enhanced operating_point
        # 和 additional_vocab 來優化兒童語音場景
        return True

    async def _do_transcribe(
        self, request: STTRequest
    ) -> tuple[str, list[WordTiming] | None, float | None]:
        """Transcribe audio using Speechmatics.

        Args:
            request: STT request with audio data and options

        Returns:
            Tuple of (transcript, word_timings, confidence)

        Notes:
            - 兒童模式會添加 additional_vocab 提高常用詞彙辨識率
            - 始終使用 enhanced operating_point 以獲得最佳準確度
            - 中文會根據 zh-TW/zh-CN 設定適當的 output_locale
        """
        if not request.audio:
            raise ValueError("Audio data required")

        settings = ConnectionSettings(url=self._url, auth_token=self._api_key)

        # Audio must be file-like object
        audio_file = io.BytesIO(request.audio.data)
        audio_file.name = f"audio.{request.audio.format}"

        # Build transcription config
        transcription_config: dict = {
            "language": self._map_language(request.language),
            "diarization": "none",
            "operating_point": "enhanced",  # 始終使用最高準確度
            "enable_entities": True,  # 實體辨識（數字、日期等）
        }

        # 設定輸出字元（繁體/簡體）
        output_locale = self._get_output_locale(request.language)
        if output_locale:
            transcription_config["output_locale"] = output_locale

        # 兒童模式：添加常用詞彙提高辨識率
        if request.child_mode:
            additional_vocab = self._get_child_vocab(request.language)
            if additional_vocab:
                transcription_config["additional_vocab"] = additional_vocab

        config = {
            "type": "transcription",
            "transcription_config": transcription_config,
        }

        try:

            def run_batch():
                with BatchClient(settings) as client:
                    job_id = client.submit_job(
                        audio=audio_file, transcription_config=config["transcription_config"]
                    )
                    # wait_for_completion blocks until done
                    return client.wait_for_completion(job_id, transcription_format="json-v2")

            # Run blocking code in thread
            result = await asyncio.to_thread(run_batch)

            # Parse result
            word_timings = []
            full_text = ""

            # Speechmatics json-v2
            results_list = result.get("results", [])
            for item in results_list:
                alternatives = item.get("alternatives", [])
                if not alternatives:
                    continue

                best = alternatives[0]
                content = best.get("content", "")
                confidence = best.get("confidence", 1.0)

                item_type = item.get("type")

                if item_type == "punctuation":
                    full_text += content
                elif item_type == "word":
                    if full_text and not full_text.endswith(" ") and not _is_cjk(content):
                        full_text += " "
                    full_text += content

                    word_timings.append(
                        WordTiming(
                            word=content,
                            start_ms=int(item.get("start_time", 0) * 1000),
                            end_ms=int(item.get("end_time", 0) * 1000),
                            confidence=confidence,
                        )
                    )

            return full_text, word_timings, 1.0

        except Exception as e:
            raise RuntimeError(f"Speechmatics failed: {str(e)}") from e

    def _map_language(self, language: str) -> str:
        """Map language code to Speechmatics format."""
        mapping = {
            "zh-TW": "cmn",  # Mandarin
            "zh-CN": "cmn",
            "en-US": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
        }
        return mapping.get(language, "en")

    def _get_output_locale(self, language: str) -> str | None:
        """Get output locale for character set (Traditional/Simplified Chinese).

        Args:
            language: Language code (e.g., zh-TW, zh-CN)

        Returns:
            Output locale string or None if not applicable
        """
        locale_mapping = {
            "zh-TW": "cmn-Hant",  # 繁體中文
            "zh-CN": "cmn-Hans",  # 簡體中文
        }
        return locale_mapping.get(language)

    def _get_child_vocab(self, language: str) -> list[dict] | None:
        """Get additional vocabulary for child speech recognition.

        Args:
            language: Language code

        Returns:
            List of vocabulary items or None
        """
        if language in ("zh-TW", "zh-CN"):
            return CHILD_VOCAB_ZH
        elif language == "en-US":
            return CHILD_VOCAB_EN
        return None


def _is_cjk(char: str) -> bool:
    """Simple check if char is CJK to avoid spaces."""
    if not char:
        return False
    code = ord(char[0])
    return 0x4E00 <= code <= 0x9FFF
