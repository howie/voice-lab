# TTS 長篇內容生成研究

> 最後更新：2025-01

## 概述

本文件研究各 TTS Provider 生成長時間音訊（如播客、有聲書）的能力。由於多數 API 有字元限制（通常 500-4096 字元），需要評估各家的原生長篇支援或分段合併策略。

## 各家 API 字元限制

| Provider | 單次請求限制 | 備註 |
|----------|-------------|------|
| OpenAI | 4,096 chars | 文件未明載，超過回傳 400 錯誤 |
| Deepgram | 2,000 chars | 超過回傳 413 錯誤 |
| Azure | ~10,000 chars | SSML 大小限制 |
| Google Cloud | 5,000 chars | Standard voices；Chirp 不同 |
| ElevenLabs | 5,000 chars | 一般 API；Projects 無限制 |
| Cartesia | 無明確限制 | 建議分段處理 |

## Provider 長篇支援

### ElevenLabs ✅ 原生完整支援

**Studio（原 Projects）- 推薦**

ElevenLabs 提供完整的長篇內容製作工具：

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)

# 方法 1: 上傳文件建立 audiobook
project = client.studio.add_chapter(
    name="第一章",
    content="章節內容...",
    voice_id="voice_id",
    model_id="eleven_multilingual_v2"
)

# 方法 2: GenFM 自動生成播客
podcast = client.studio.create_podcast(
    name="AI 技術週報",
    source_type="url",
    source="https://example.com/article",
    mode="conversation",  # 雙主持人對話
    quality="ultra"       # 最高品質
)
```

**功能特色**:
- 自動章節分割
- 多聲音管理（為角色設定 alias）
- GenFM 自動生成播客（32 語言）
- 編輯逐字稿即可調整音訊
- 匯出格式：standard、high、ultra、ultra lossless

**API 分段生成**

若需更細緻控制，可使用 `previous_text` 參數保持連續性：

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)

def generate_long_audio(text: str, voice_id: str, chunk_size: int = 4000) -> bytes:
    chunks = split_text(text, chunk_size)
    audio_parts = []
    previous = ""

    for chunk in chunks:
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=chunk,
            model_id="eleven_multilingual_v2",
            previous_text=previous[-1000:] if previous else None,  # 上文
            next_text=chunks[i+1][:1000] if i < len(chunks)-1 else None  # 下文
        )
        audio_parts.append(audio)
        previous = chunk

    return merge_audio(audio_parts)
```

**定價考量**:
- 標準 API: $0.18-0.30/1K chars
- Studio 專案: 同樣字元計費
- v3 到 2025/06 有 80% 折扣

---

### Azure Speech ✅ 原生支援

**2025 更新：一次轉換整個檔案**

Azure Speech 在 2025 年大幅改進，現已支援一次轉換長篇文件：

```python
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription=subscription_key,
    region=region
)

# 長篇文字直接合成
synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=speechsdk.audio.AudioOutputConfig(filename="audiobook.wav")
)

# 使用 SSML 控制整個文件
ssml = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xml:lang="zh-TW">
    <voice name="zh-TW-HsiaoChenNeural">
        {long_text}
    </voice>
</speak>
"""

result = synthesizer.speak_ssml_async(ssml).get()
```

**Batch Synthesis（批次合成）**

適合超長內容的非同步處理：

```python
import requests

# 建立批次合成任務
response = requests.post(
    f"https://{region}.customvoice.api.speech.microsoft.com/api/texttospeech/3.1-preview1/batchsynthesis",
    headers={
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json"
    },
    json={
        "displayName": "有聲書專案",
        "description": "長篇內容合成",
        "textType": "PlainText",
        "inputs": [
            {"text": chapter_1_text},
            {"text": chapter_2_text},
            # ...
        ],
        "properties": {
            "outputFormat": "audio-24khz-160kbitrate-mono-mp3",
            "concatenateResult": True  # 自動合併結果
        }
    }
)
```

---

### Google Cloud TTS ✅ 支援長篇

**非同步 API（Long Audio Synthesis）**

```python
from google.cloud import texttospeech_v1beta1 as texttospeech

client = texttospeech.TextToSpeechLongAudioSynthesizeClient()

# 長篇音訊合成請求
request = texttospeech.SynthesizeLongAudioRequest(
    parent=f"projects/{project_id}/locations/{location}",
    input=texttospeech.SynthesisInput(text=long_text),
    audio_config=texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    ),
    voice=texttospeech.VoiceSelectionParams(
        language_code="zh-TW",
        name="zh-TW-Wavenet-A"
    ),
    output_gcs_uri="gs://bucket/output.mp3"
)

operation = client.synthesize_long_audio(request=request)
result = operation.result()  # 等待完成
```

**限制與定價**:
- 配額限制：每分鐘 100K 字元
- 輸出到 GCS bucket
- 標準定價 + 額外長篇處理費

---

### OpenAI TTS ⚠️ 需分段處理

OpenAI TTS 有 4096 字元限制，需自行分段：

```python
from openai import OpenAI
from pydub import AudioSegment
import io

client = OpenAI()

def generate_long_audio_openai(
    text: str,
    voice: str = "nova",
    max_chars: int = 4000
) -> AudioSegment:
    """
    分段生成長篇音訊
    """
    chunks = split_into_sentences(text, max_chars)
    audio_segments = []

    for chunk in chunks:
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=chunk,
            response_format="mp3"
        )
        audio_data = io.BytesIO(response.content)
        segment = AudioSegment.from_mp3(audio_data)
        audio_segments.append(segment)

    # 合併
    final = audio_segments[0]
    for segment in audio_segments[1:]:
        final += segment

    return final

def split_into_sentences(text: str, max_chars: int) -> list:
    """
    智慧分割：在句子邊界切分
    """
    import re

    sentences = re.split(r'([。！？.!?])', text)
    chunks = []
    current = ""

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]

        if len(current) + len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current += sentence

    if current:
        chunks.append(current.strip())

    return chunks
```

---

### Deepgram Aura ⚠️ 需分段處理

限制 2000 字元，需分段：

```python
from deepgram import DeepgramClient, SpeakOptions

client = DeepgramClient(api_key)

def generate_long_audio_deepgram(text: str, model: str = "aura-asteria-en") -> bytes:
    chunks = split_text(text, max_chars=2000)
    audio_parts = []

    for chunk in chunks:
        response = client.speak.v("1").save(
            f"temp_{i}.mp3",
            {"text": chunk},
            SpeakOptions(model=model)
        )
        audio_parts.append(f"temp_{i}.mp3")

    # 使用 pydub 或 ffmpeg 合併
    return merge_files(audio_parts)
```

**注意**:
- WebSocket 有 2400 chars/min 限制
- 價格便宜：$0.015/1K chars（Aura-2: $0.030）

---

### Cartesia ⚠️ 建議分段

雖無明確限制，但建議分段以維持品質：

```python
from cartesia import Cartesia

client = Cartesia(api_key=api_key)

async def generate_long_audio_cartesia(text: str, voice_id: str) -> bytes:
    chunks = split_text(text, max_chars=3000)
    audio_parts = []

    async with client.tts.websocket() as ws:
        for i, chunk in enumerate(chunks):
            audio = await ws.send(
                model_id="sonic-2",
                voice_id=voice_id,
                text=chunk,
                context_id=f"long_audio_{i}",
                output_format="pcm_16000"
            )
            audio_parts.append(audio)

    return merge_pcm_audio(audio_parts)
```

---

### Microsoft VibeVoice ✅ 開源長篇專用

Microsoft 開源的 VibeVoice 專為長篇設計：

```python
# VibeVoice - 支援最長 90 分鐘，4 說話者
# 需要本地部署

# 1.5B 模型：~7GB VRAM
# 7B 模型：~18GB VRAM
# 0.5B 模型：即時生成（開發中）

# 特色：
# - 64K token context（約 90 分鐘）
# - 4 個不同說話者
# - 保持 speaker consistency
# - 自然的輪流說話
```

**適用場景**: 需要完整掌控、不想使用雲端服務

---

## 分段合併通用策略

### 1. 智慧文字分割

```python
import re
from typing import List

def smart_split(text: str, max_chars: int = 4000, overlap: int = 100) -> List[str]:
    """
    智慧分割長文字

    策略：
    1. 優先在段落邊界切分
    2. 其次在句子邊界切分
    3. 最後在字元限制處切分
    4. 可選重疊以保持連貫性
    """
    # 先按段落分
    paragraphs = text.split('\n\n')
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars:
            if current:
                chunks.append(current.strip())

            # 段落太長，按句子分
            if len(para) > max_chars:
                sentences = re.split(r'([。！？.!?])', para)
                for i in range(0, len(sentences), 2):
                    sent = sentences[i]
                    if i + 1 < len(sentences):
                        sent += sentences[i + 1]

                    if len(current) + len(sent) > max_chars:
                        if current:
                            chunks.append(current.strip())
                        current = sent
                    else:
                        current += sent
            else:
                current = para
        else:
            current += "\n\n" + para if current else para

    if current:
        chunks.append(current.strip())

    return chunks
```

### 2. 音訊合併與平滑化

```python
from pydub import AudioSegment
from typing import List
import io

def merge_audio_seamless(
    audio_chunks: List[bytes],
    format: str = "mp3",
    crossfade_ms: int = 100,
    normalize: bool = True
) -> bytes:
    """
    無縫合併多段音訊

    Args:
        audio_chunks: 音訊資料列表
        format: 輸入格式
        crossfade_ms: 交叉淡入淡出毫秒數
        normalize: 是否正規化音量
    """
    segments = [
        AudioSegment.from_file(io.BytesIO(chunk), format=format)
        for chunk in audio_chunks
    ]

    if not segments:
        return b""

    # 正規化音量
    if normalize:
        target_dBFS = -20
        segments = [
            seg.apply_gain(target_dBFS - seg.dBFS)
            for seg in segments
        ]

    # 合併
    final = segments[0]
    for segment in segments[1:]:
        final = final.append(segment, crossfade=crossfade_ms)

    # 匯出
    buffer = io.BytesIO()
    final.export(buffer, format="mp3", bitrate="192k")
    return buffer.getvalue()
```

### 3. 完整長篇生成類別

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import asyncio

@dataclass
class LongAudioConfig:
    max_chunk_size: int = 4000
    crossfade_ms: int = 100
    normalize_volume: bool = True
    output_format: str = "mp3"
    output_bitrate: str = "192k"

class LongAudioGenerator(ABC):
    def __init__(self, config: LongAudioConfig = None):
        self.config = config or LongAudioConfig()

    @abstractmethod
    async def synthesize_chunk(self, text: str) -> bytes:
        """由子類別實作具體 TTS 呼叫"""
        pass

    async def generate(self, text: str) -> bytes:
        """生成長篇音訊"""
        # 1. 分割文字
        chunks = smart_split(text, self.config.max_chunk_size)

        # 2. 並行生成（若 provider 支援）
        tasks = [self.synthesize_chunk(chunk) for chunk in chunks]
        audio_chunks = await asyncio.gather(*tasks)

        # 3. 合併
        return merge_audio_seamless(
            audio_chunks,
            crossfade_ms=self.config.crossfade_ms,
            normalize=self.config.normalize_volume
        )

# 具體實作範例
class ElevenLabsLongAudio(LongAudioGenerator):
    def __init__(self, api_key: str, voice_id: str, config: LongAudioConfig = None):
        super().__init__(config)
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self._previous_text = ""

    async def synthesize_chunk(self, text: str) -> bytes:
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            previous_text=self._previous_text[-500:] if self._previous_text else None
        )
        self._previous_text = text
        return audio
```

## 功能比較表

| Provider | 原生長篇 | 最大長度 | 自動分段 | 合併支援 | 推薦度 |
|----------|---------|---------|---------|---------|--------|
| ElevenLabs | ✅ Studio | 無限 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Azure | ✅ Batch | 無限 | ✅ | ✅ | ⭐⭐⭐⭐ |
| Google | ✅ Long Audio | 配額限制 | ✅ | ✅ | ⭐⭐⭐⭐ |
| OpenAI | ❌ | 4096 chars | ❌ | ❌ | ⭐⭐⭐ |
| Deepgram | ❌ | 2000 chars | ❌ | ❌ | ⭐⭐⭐ |
| Cartesia | ⚠️ | 建議分段 | ❌ | ❌ | ⭐⭐⭐ |
| VibeVoice | ✅ 開源 | 90 分鐘 | ✅ | ✅ | ⭐⭐⭐⭐ |

## 選型建議

```
                    ┌─────────────────────┐
                    │   長篇音訊需求？     │
                    └──────────┬──────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
  完整專案管理            企業/合規需求             自行部署
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ ElevenLabs  │         │    Azure    │         │ VibeVoice   │
│  Studio     │         │   Batch     │         │  (開源)      │
└─────────────┘         └─────────────┘         └─────────────┘
```

### 使用場景建議

| 場景 | 推薦方案 | 原因 |
|------|---------|------|
| 播客製作 | ElevenLabs Studio | GenFM 自動生成、完整編輯流程 |
| 有聲書 | ElevenLabs / Azure | 章節管理、多聲音支援 |
| 大量生成 | Azure Batch | 非同步處理、成本效益 |
| 隱私要求 | VibeVoice 自部署 | 資料不離開伺服器 |
| 預算有限 | Deepgram + 自行合併 | 最低成本 |

## 成本估算

假設：生成 1 小時播客（約 30,000 字元）

| Provider | 估算成本 | 備註 |
|----------|---------|------|
| ElevenLabs | $5.4-9 | 視方案 |
| Azure | $0.45 | Batch 更便宜 |
| Google | ~$0.48 | Standard |
| Deepgram | $0.45-0.9 | Aura/Aura-2 |
| VibeVoice | 免費 | 需自有 GPU |

## 參考連結

- [ElevenLabs Studio](https://elevenlabs.io/projects)
- [ElevenLabs Create Podcast API](https://elevenlabs.io/docs/api-reference/studio/create-podcast)
- [Azure Batch Synthesis](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/batch-synthesis)
- [Google Long Audio Synthesis](https://docs.cloud.google.com/text-to-speech/docs/create-audio-text-long-audio-synthesis)
- [Microsoft VibeVoice](https://github.com/microsoft/VibeVoice)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2025-01 | 初始版本 |
