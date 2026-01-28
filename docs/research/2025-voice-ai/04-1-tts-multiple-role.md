# TTS 多角色對話研究

> 最後更新：2025-01

## 概述

本文件研究各 TTS Provider 產生多角色對話（如 A:xxx B:xxx A:xxx）的能力。目標是評估是否有原生 API 支援，還是需要自行分段生成後合併。

## 需求情境

```
逐字稿輸入:
A: 你好，歡迎來到我們的節目！
B: 謝謝邀請，很高興能參加。
A: 今天我們要討論 AI 語音技術的發展...

期望輸出:
一段包含兩種不同聲音交替對話的音訊檔案
```

## Provider 能力比較

### ElevenLabs ✅ 原生支援最完整

**方案 1: Eleven v3 Audio Tags（推薦）**

Eleven v3 支援使用 Audio Tags 在單一請求中產生多角色對話：

```
[dialogue]
[S1] 你好，歡迎來到我們的節目！
[S2] 謝謝邀請，很高興能參加。
[S1] 今天我們要討論 AI 語音技術的發展...
[/dialogue]
```

進階功能：
- `[interrupting]` - 打斷效果
- `[overlapping]` - 重疊說話
- `[laughs]` - 笑聲
- 情感轉換

**方案 2: Studio / GenFM（完整專案管理）**

適合較長內容的製作流程：

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)

# 建立播客專案
podcast = client.studio.create_podcast(
    name="我的播客",
    source_type="url",
    source="https://example.com/article",
    mode="conversation",
    quality="high"
)
```

**方案 3: API 多聲音切換**

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)

# 為每段對話指定不同聲音
segments = [
    {"voice_id": "voice_a", "text": "你好，歡迎來到我們的節目！"},
    {"voice_id": "voice_b", "text": "謝謝邀請，很高興能參加。"},
    {"voice_id": "voice_a", "text": "今天我們要討論 AI 語音技術的發展..."},
]

audio_chunks = []
for segment in segments:
    audio = client.text_to_speech.convert(
        voice_id=segment["voice_id"],
        text=segment["text"],
        model_id="eleven_multilingual_v2",
        previous_text=segments[i-1]["text"] if i > 0 else None  # 保持連續性
    )
    audio_chunks.append(audio)

# 合併音訊
```

**優點**:
- v3 原生支援多角色對話語法
- Studio 提供完整專案管理
- `previous_text` 參數可維持語氣連續性
- API 完整可程式化

**注意**: v3 即時版本仍在開發中，即時對話建議用 v2.5 Turbo

---

### Azure Speech ✅ SSML 完整支援

使用 SSML 的 `<voice>` 元素切換聲音：

```xml
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-TW">

    <voice name="zh-TW-HsiaoChenNeural">
        你好，歡迎來到我們的節目！
    </voice>

    <voice name="zh-TW-YunJheNeural">
        謝謝邀請，很高興能參加。
    </voice>

    <voice name="zh-TW-HsiaoChenNeural">
        今天我們要討論 AI 語音技術的發展...
    </voice>

</speak>
```

**Multi-talker Voices（新功能）**

2025 年新增的 Multi-talker voices 功能，專為自然對話設計：

```python
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription=subscription_key,
    region=region
)

ssml = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-TW">
    <voice name="zh-TW-HsiaoChenNeural">
        <mstts:express-as style="chat">
            你好，歡迎來到我們的節目！
        </mstts:express-as>
    </voice>
    <voice name="zh-TW-YunJheNeural">
        <mstts:express-as style="friendly">
            謝謝邀請，很高興能參加。
        </mstts:express-as>
    </voice>
</speak>
"""

synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
result = synthesizer.speak_ssml_async(ssml).get()
```

**優點**:
- 單一 SSML 文件即可產生完整對話
- 支援 400+ 聲音
- 中文支援優秀（zh-TW）
- 可混合多語言
- 支援情感風格（chat、friendly、newscast 等）

**限制**:
- 無法混合自訂聲音與預設聲音
- Multilingual voices 部分 SSML 標籤支援有限

---

### Google Cloud TTS (傳統) ❌ 不推薦

> **2025-01 更新**: 傳統 Google Cloud TTS 的台灣中文 (cmn-TW) **不適合多角色對話**。

**台灣中文 (cmn-TW) 可用聲音**:

| Voice | Type | 品質評估 |
|-------|------|---------|
| cmn-TW-Standard-A/B/C | Standard | ❌ 機器人感重 |
| cmn-TW-Wavenet-A/B/C | WaveNet | ⚠️ 稍好但仍不自然 |

**關鍵問題**:
- **沒有 Neural2、Studio、Journey、Chirp 等高品質聲音**
- 這些更自然的聲音只支援 cmn-CN（中國大陸普通話），不支援 cmn-TW
- Standard/WaveNet 聲音聽起來像機器人，不適合對話場景

**建議**: 請改用 **Gemini-TTS**、**Azure** 或 **VoAI**。

---

### Gemini-TTS ✅ 推薦（Google 新一代）

> **2025-01 更新**: Gemini-TTS 是 Google 最新的語音合成服務，支援台灣中文且品質優秀。

**服務架構**:
```
存取 Gemini-TTS 的方式：
├── Cloud TTS API (texttospeech.googleapis.com) - 新版支援 Gemini voices
├── Vertex AI API (aiplatform.googleapis.com) - 企業級
└── Google AI API (generativelanguage.googleapis.com) - 開發者友善
```

**多角色對話支援**: ✅ 原生支援最多 2 人對話

```python
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 多角色對話 - 使用 speaker 標籤
dialogue = """
<speaker name="主持人" voice="Kore">
你好，歡迎來到我們的節目！
</speaker>
<speaker name="來賓" voice="Charon">
謝謝邀請，很高興能參加。
</speaker>
<speaker name="主持人" voice="Kore">
今天我們要討論 AI 語音技術的發展...
</speaker>
"""

response = client.models.generate_content(
    model="gemini-2.5-flash-tts",
    contents=dialogue,
    config={
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "multi_speaker_config": {
                "speaker_voice_configs": [
                    {"speaker": "主持人", "voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}},
                    {"speaker": "來賓", "voice_config": {"prebuilt_voice_config": {"voice_name": "Charon"}}}
                ]
            }
        }
    }
)
```

**風格控制（自然語言）**:

```python
# 可以用自然語言指定每個角色的說話風格
dialogue = """
[主持人用熱情活潑的語氣說]
你好，歡迎來到我們的節目！

[來賓用謙虛友善的語氣回應]
謝謝邀請，很高興能參加。
"""
```

**特效標籤**:

```python
# 支援情感和效果標籤
dialogue = """
主持人: [興奮地] 哇！這真是太棒了！[laughing]
來賓: [思考中] 嗯...讓我想想...[sigh] 這確實是個好問題。
"""
```

**可用聲音** (28 種):
- 女聲: Aoede, Kore, Leda, Zephyr, Sulafat...
- 男聲: Charon, Puck, Fenrir, Enceladus, Orus...

**優點**:
- ✅ 台灣中文 (cmn-tw) 品質優秀
- ✅ 自然語言控制風格、情感
- ✅ 原生多角色支援
- ✅ 豐富的特效標籤
- ✅ 28 種聲音可選

**限制**:
- 最多 2 位說話者
- cmn-tw 目前為 Preview 狀態

---

### OpenAI TTS ⚠️ 需分段合併

OpenAI TTS 目前不支援原生多聲音切換，需自行分段處理：

```python
from openai import OpenAI
from pydub import AudioSegment
import io

client = OpenAI()

dialogue = [
    {"voice": "nova", "text": "你好，歡迎來到我們的節目！"},
    {"voice": "onyx", "text": "謝謝邀請，很高興能參加。"},
    {"voice": "nova", "text": "今天我們要討論 AI 語音技術的發展..."},
]

audio_segments = []
for turn in dialogue:
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=turn["voice"],
        input=turn["text"],
        instructions="說話自然、語速適中"  # steerability 功能
    )
    audio_data = io.BytesIO(response.content)
    segment = AudioSegment.from_mp3(audio_data)
    audio_segments.append(segment)

# 合併音訊，加入適當間隔
final_audio = AudioSegment.empty()
for i, segment in enumerate(audio_segments):
    final_audio += segment
    if i < len(audio_segments) - 1:
        final_audio += AudioSegment.silent(duration=300)  # 300ms 間隔

final_audio.export("dialogue.mp3", format="mp3")
```

**優點**:
- gpt-4o-mini-tts 的 steerability 可控制語氣
- 聲音品質高

**缺點**:
- 無原生多聲音支援
- 需自行處理音訊合併
- 聲音切換處可能不自然

---

### Cartesia ⚠️ 需使用 Context 管理

Cartesia 使用 `context_id` 管理對話，但不支援原生多聲音：

```python
from cartesia import Cartesia
import asyncio

client = Cartesia(api_key=api_key)

async def generate_dialogue():
    dialogue = [
        {"voice_id": "voice_a_id", "text": "你好，歡迎來到我們的節目！"},
        {"voice_id": "voice_b_id", "text": "謝謝邀請，很高興能參加。"},
        {"voice_id": "voice_a_id", "text": "今天我們要討論 AI 語音技術的發展..."},
    ]

    audio_chunks = []

    async with client.tts.websocket() as ws:
        for i, turn in enumerate(dialogue):
            context_id = f"dialogue_{i}"

            audio = await ws.send(
                model_id="sonic-2",
                voice_id=turn["voice_id"],
                text=turn["text"],
                context_id=context_id,
                output_format="pcm_16000"
            )
            audio_chunks.append(audio)

    return audio_chunks
```

**優點**:
- WebSocket 支援並行生成多個對話
- 延遲極低（~80ms TTFB）
- 單一連線可處理數十個並發生成

**缺點**:
- 無原生多聲音語法
- 需自行合併音訊

---

### Deepgram Aura ❌ 不支援

Deepgram Aura 目前不支援多聲音切換：

```python
from deepgram import DeepgramClient, SpeakOptions

# 只能分段生成，每段指定不同聲音
# 然後自行合併
```

---

## 功能比較表

| Provider | 原生多聲音 | 方法 | 台灣中文 | 合併難度 | 備註 |
|----------|-----------|------|---------|---------|------|
| ElevenLabs | ✅✅ | Audio Tags / Studio | ✅ | 無需合併 | 品質最佳 |
| Azure | ✅ | SSML `<voice>` | ✅✅ | 無需合併 | Neural 聲音自然 |
| **Gemini-TTS** | ✅ | Multi-speaker API | ✅✅ | 無需合併 | **Google 新一代，推薦** |
| VoAI | ✅ | 分段合併 | ✅✅ | 中等 | 本土化、多風格 |
| Google Cloud (傳統) | ~~✅~~ | SSML | ❌ | - | **不推薦**: 只有 Standard/WaveNet |
| OpenAI | ❌ | 分段合併 | ✅ | 中等 | |
| Cartesia | ❌ | Context + 合併 | ✅ | 中等 | 低延遲 |
| Deepgram | ❌ | 分段合併 | ⚠️ | 中等 | |

## 分段合併通用方案

若 Provider 不支援原生多聲音，以下是通用的分段合併策略：

### 解析逐字稿

```python
import re
from dataclasses import dataclass
from typing import List

@dataclass
class DialogueTurn:
    speaker: str
    text: str

def parse_dialogue(transcript: str) -> List[DialogueTurn]:
    """
    解析格式: A: 文字內容 或 [A] 文字內容
    """
    pattern = r'(?:\[([^\]]+)\]|([A-Z]))\s*[:：]\s*(.+?)(?=(?:\[[^\]]+\]|[A-Z])[:：]|$)'
    matches = re.findall(pattern, transcript, re.DOTALL)

    turns = []
    for match in matches:
        speaker = match[0] or match[1]
        text = match[2].strip()
        if text:
            turns.append(DialogueTurn(speaker=speaker, text=text))

    return turns

# 使用範例
transcript = """
A: 你好，歡迎來到我們的節目！
B: 謝謝邀請，很高興能參加。
A: 今天我們要討論 AI 語音技術的發展...
"""

turns = parse_dialogue(transcript)
```

### 音訊合併

```python
from pydub import AudioSegment
from typing import List

def merge_audio_segments(
    audio_files: List[bytes],
    gap_ms: int = 300,
    crossfade_ms: int = 50
) -> AudioSegment:
    """
    合併多段音訊，加入自然間隔

    Args:
        audio_files: 音訊資料列表
        gap_ms: 段落間隔（毫秒）
        crossfade_ms: 交叉淡入淡出（毫秒）
    """
    segments = [AudioSegment.from_file(io.BytesIO(f)) for f in audio_files]

    final = segments[0]
    for segment in segments[1:]:
        # 加入間隔
        final += AudioSegment.silent(duration=gap_ms)
        # 可選：交叉淡入淡出讓轉換更自然
        final = final.append(segment, crossfade=crossfade_ms)

    return final
```

### 完整流程範例

```python
from typing import Dict

class DialogueGenerator:
    def __init__(self, provider: str, voice_map: Dict[str, str]):
        """
        Args:
            provider: TTS provider 名稱
            voice_map: 說話者到聲音 ID 的對應，如 {"A": "voice_id_1", "B": "voice_id_2"}
        """
        self.provider = provider
        self.voice_map = voice_map
        self.tts_client = self._init_client()

    def generate(self, transcript: str) -> bytes:
        # 1. 解析逐字稿
        turns = parse_dialogue(transcript)

        # 2. 為每個說話段落生成音訊
        audio_chunks = []
        for turn in turns:
            voice_id = self.voice_map.get(turn.speaker, self.voice_map.get("default"))
            audio = self._synthesize(turn.text, voice_id)
            audio_chunks.append(audio)

        # 3. 合併音訊
        final_audio = merge_audio_segments(audio_chunks)

        return final_audio.export(format="mp3").read()

    def _synthesize(self, text: str, voice_id: str) -> bytes:
        # 根據 provider 實作
        pass
```

## 選型建議

```
                    ┌─────────────────────┐
                    │   需要多角色對話？   │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
      原生支援優先         成本敏感            低延遲需求
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ ElevenLabs  │     │    Azure    │     │  Cartesia   │
    │ (v3 Tags)   │     │   (SSML)    │     │ (需合併)     │
    └─────────────┘     └─────────────┘     └─────────────┘
```

### 推薦選擇

1. **品質優先**: ElevenLabs Eleven v3 + Audio Tags
2. **台灣中文優先**:
   - **Gemini-TTS** (Google 新一代，原生多角色)
   - Azure Speech (HsiaoChenNeural, YunJheNeural)
   - VoAI (本土化)
3. **企業/合規**: Azure Speech + SSML 或 Vertex AI (Gemini-TTS)
4. **成本考量**: Azure Speech（$15/1M chars）
5. **低延遲**: Cartesia + 自行合併

> ⚠️ **不推薦**: 傳統 Google Cloud TTS（台灣中文只有 Standard/WaveNet，聲音不自然）
> ✅ **推薦**: Gemini-TTS 取代傳統 Google Cloud TTS

## 參考連結

- [ElevenLabs v3 Audio Tags](https://elevenlabs.io/blog/eleven-v3-audio-tags-bringing-multi-character-dialogue-to-life)
- [ElevenLabs Multi-voice Support](https://elevenlabs.io/docs/agents-platform/customization/voice/multi-voice-support)
- [Azure SSML Voice](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice)
- [Google Cloud TTS SSML](https://docs.cloud.google.com/text-to-speech/docs/ssml)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2025-01-28 | 新增 Gemini-TTS 多角色支援；區分傳統 Cloud TTS 與 Gemini-TTS |
| 2025-01-28 | 移除傳統 Google Cloud TTS 推薦（台灣中文無高品質聲音） |
| 2025-01 | 初始版本 |
