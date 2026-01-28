# TTS (文字轉語音) 服務研究

> 最後更新：2025-01

## 概述

TTS 將 LLM 生成的文字轉換為語音。對於 Voice AI，關鍵指標是：TTFB (Time To First Byte)、音質自然度、情感表現力。

## 服務比較

### Cartesia

**狀態**: ✅ 生產推薦 - 延遲之王

| 項目 | 說明 |
|------|------|
| TTFB | ~50-100ms |
| 音質 | MOS 4.2+ |
| 定價 | $0.040/1K chars |

**特點**:
- 業界最低延遲
- Sonic 模型專為對話設計
- 串流輸出極佳
- 情感控制
- 聲音複製

**API 範例**:
```python
from cartesia import Cartesia

client = Cartesia(api_key=api_key)
audio = client.tts.stream(
    model_id="sonic-2",
    voice_id="your-voice-id",
    text="你好，我是你的語音助理",
    output_format="pcm_16000"
)
```

**適用場景**: 即時對話、低延遲要求、Voice AI

---

### ElevenLabs

**狀態**: ✅ 生產推薦 - 品質之選

| 項目 | 說明 |
|------|------|
| TTFB | ~150-300ms |
| 音質 | MOS 4.5+ |
| 定價 | $0.18-0.30/1K chars |

**特點**:
- 業界頂尖音質
- 豐富的聲音庫
- 優秀的聲音複製
- 多語言支援
- 情感控制精細

**API 範例**:
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)
audio = client.text_to_speech.convert_as_stream(
    voice_id="your-voice-id",
    text="你好，我是你的語音助理",
    model_id="eleven_turbo_v2_5"
)
```

**適用場景**: 高品質要求、品牌聲音、內容創作

---

### Deepgram (Aura)

**狀態**: ✅ 生產就緒

| 項目 | 說明 |
|------|------|
| TTFB | ~100-200ms |
| 音質 | MOS 4.0+ |
| 定價 | $0.015/1K chars |

**特點**:
- 極具競爭力的價格
- 與 Deepgram STT 整合佳
- API 簡潔
- 穩定可靠

**API 範例**:
```python
from deepgram import DeepgramClient, SpeakOptions

client = DeepgramClient(api_key)
response = client.speak.v("1").stream(
    {"text": "你好，我是你的語音助理"},
    SpeakOptions(model="aura-asteria-en")
)
```

**適用場景**: 成本敏感、STT+TTS 整合、大規模部署

---

### Azure Speech (Microsoft)

**狀態**: ✅ 企業級選擇

| 項目 | 說明 |
|------|------|
| TTFB | ~200-400ms |
| 音質 | MOS 4.3+ |
| 定價 | $15/1M chars |

**特點**:
- 400+ 聲音選擇
- Neural TTS 品質佳
- 中文支援優秀
- 企業級 SLA
- SSML 完整支援

**適用場景**: 企業應用、合規要求、Azure 生態系統

---

### Google 語音服務架構

> **2025-01 更新**: Google 有多種語音合成服務，架構如下：

```
Google 語音服務
├── Google Cloud Platform (GCP)
│   ├── Cloud Text-to-Speech API (texttospeech.googleapis.com)
│   │   ├── Standard voices (舊，機器人感)
│   │   ├── WaveNet voices (舊，稍好)
│   │   ├── Neural2 voices (較新，cmn-TW 沒有)
│   │   └── Gemini-TTS voices ✅ (最新，支援 cmn-TW)
│   │
│   └── Vertex AI API (aiplatform.googleapis.com)
│       └── Gemini 模型 (gemini-2.5-flash-tts / pro-tts) ✅
│
└── Google AI Studio (ai.google.dev)
    └── Gemini API (generativelanguage.googleapis.com)
        └── 開發者直接存取 Gemini-TTS ✅
```

#### 存取方式比較

| 方式 | API Endpoint | SDK | 適合場景 |
|------|-------------|-----|---------|
| Cloud TTS API | `texttospeech.googleapis.com` | `google-cloud-texttospeech` | 現有 GCP 用戶 |
| Vertex AI API | `aiplatform.googleapis.com` | `google-cloud-aiplatform` | 企業級、統一 AI |
| Google AI | `generativelanguage.googleapis.com` | `google-genai` | 快速開發 |

---

### Google Cloud TTS (傳統)

**狀態**: ⚠️ 台灣中文不推薦

| 項目 | 說明 |
|------|------|
| TTFB | ~200-400ms |
| 音質 | MOS 3.5-4.0 (台灣中文) |
| 定價 | $4/1M chars (Standard), $16/1M chars (WaveNet) |

**台灣中文 (cmn-TW) 可用聲音**:

| Voice | Type | 品質 |
|-------|------|------|
| cmn-TW-Standard-A/B/C | Standard | ❌ 機器人感 |
| cmn-TW-Wavenet-A/B/C | WaveNet | ⚠️ 不自然 |

**關鍵限制**:
- **Neural2、Studio、Journey、Chirp 不支援台灣中文**
- 這些高品質聲音只支援 cmn-CN（中國大陸普通話）
- 台灣中文只有 Standard 和 WaveNet，聽起來像機器人

**適用場景**: ❌ 不推薦用於台灣中文

---

### Gemini-TTS ✅ 推薦

**狀態**: ✅ 台灣中文推薦（Preview）

| 項目 | 說明 |
|------|------|
| TTFB | ~100-200ms |
| 音質 | MOS 4.3+ |
| 定價 | 見 [pricing](https://cloud.google.com/text-to-speech/pricing) |

**支援語言**: 68+ 語言，包含 **cmn-tw (繁體中文台灣)** (Preview)

**可用聲音**: 28 種全語言共用聲音
- 女聲: Aoede, Kore, Leda, Zephyr, Sulafat, Achernar...
- 男聲: Charon, Puck, Fenrir, Enceladus, Orus, Schedar...

**模型選擇**:

| 模型 | 用途 | 狀態 |
|------|------|------|
| `gemini-2.5-flash-tts` | 低延遲、高性價比 | GA |
| `gemini-2.5-pro-tts` | 高品質、精細控制 | GA |
| `gemini-2.5-flash-lite-tts` | 單人快速 | Preview |

**核心優勢**:
- ✅ 自然語言控制風格、語氣、情感
- ✅ 多角色對話（最多 2 人）
- ✅ 特效標籤：`[sigh]`、`[laughing]`、`[whispering]`
- ✅ 台灣中文品質遠優於傳統 Cloud TTS

**API 範例**:

```python
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash-tts",
    contents="你好，歡迎來到我們的節目！",
    config={
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}
        }
    }
)

# 取得音訊資料
audio_data = response.candidates[0].content.parts[0].inline_data.data
```

**風格控制**:

```python
# 用自然語言指定風格
contents = """
請用溫暖友善的語氣，語速稍慢地說：
你好，歡迎來到我們的節目！今天我們要聊聊 AI 的發展。
"""

# 或使用標籤
contents = "[輕快地] 你好！[笑] 今天天氣真好。"
```

**適用場景**: 台灣中文內容、需要情感控制、多角色對話

---

### VoAI

**狀態**: ✅ 台灣中文推薦

| 項目 | 說明 |
|------|------|
| TTFB | ~150-250ms |
| 音質 | MOS 4.0+ |
| 定價 | 依方案 |

**特點**:
- 專注台灣市場
- 多種風格（聊天、輕柔、激昂等）
- 台灣口音自然
- 支援多角色對話

**可用聲音**:
- 佑希、雨榛、子墨等多種選擇

**適用場景**: 台灣中文內容、本土化需求、多角色對話

---

## 功能比較表

| 功能 | Cartesia | ElevenLabs | Deepgram | Azure | Google Cloud | VoAI |
|------|----------|------------|----------|-------|--------------|------|
| 串流輸出 | ✅✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 台灣中文 | ✅ | ✅ | ⚠️ 有限 | ✅✅ | ❌ 不自然 | ✅✅ |
| 台語支援 | ❌ | ⚠️ | ❌ | ⚠️ | ❌ | ⚠️ |
| 聲音複製 | ✅ | ✅✅ | ❌ | ✅ | ❌ | ❌ |
| 情感控制 | ✅ | ✅✅ | ❌ | ✅ | ⚠️ | ✅ |
| SSML | ⚠️ | ⚠️ | ❌ | ✅✅ | ✅ | ❌ |
| 多角色對話 | ⚠️ 需合併 | ✅✅ | ⚠️ 需合併 | ✅ | ❌ 不推薦 | ✅ |

## 延遲分析

### TTFB 排名 (2025-01 測試)

```
Cartesia   ████████░░░░░░░░ ~80ms
Deepgram   ████████████░░░░ ~150ms
ElevenLabs ████████████████ ~250ms
Azure      ████████████████████ ~350ms
```

### 延遲組成

```
TTFB = 網路延遲 + 模型處理 + 音訊編碼
```

## 音質考量

### MOS (Mean Opinion Score)

| 分數 | 等級 | 說明 |
|------|------|------|
| 4.5+ | 優秀 | 接近人聲 |
| 4.0-4.5 | 良好 | 適合大多數場景 |
| 3.5-4.0 | 可接受 | 有明顯合成感 |

### 自然度因素

1. **韻律 (Prosody)**: 語調變化
2. **停頓 (Pausing)**: 自然的句間停頓
3. **情感**: 語氣表達
4. **連貫性**: 長句的一致性

## 中文 TTS 注意事項

### 1. 多音字處理
```
# 問題
"大夫" → dà fū (醫生) vs dài fu (官員)

# 解決：使用 SSML 或特定標記
<phoneme alphabet="pinyin" ph="dai4 fu">大夫</phoneme>
```

### 2. 數字讀法
```
# 確保正確讀法
"110" → "一一零" (報警) vs "一百一十" (數字)
```

### 3. 標點符號
```
# TTS 對標點敏感
"好，我來處理。" → 自然停頓
"好 我來處理" → 可能連讀
```

## 成本估算

假設：每日 10,000 次對話，每次平均 200 字元輸出

| 服務 | 日成本 | 月成本 |
|------|--------|--------|
| Cartesia | $80 | ~$2,400 |
| ElevenLabs | $360-600 | ~$12,000 |
| Deepgram | $30 | ~$900 |
| Azure | $30 | ~$900 |

## 選型建議

```
                    ┌─────────────────┐
                    │   主要考量？     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
    延遲優先              品質優先             成本優先
        │                    │                    │
        ▼                    ▼                    ▼
   ┌──────────┐        ┌───────────┐        ┌──────────┐
   │ Cartesia │        │ElevenLabs │        │ Deepgram │
   └──────────┘        └───────────┘        └──────────┘

                    ┌─────────────────┐
                    │  台灣中文優先？  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
    企業級需求            本土化需求           多角色對話
        │                    │                    │
        ▼                    ▼                    ▼
   ┌──────────┐        ┌───────────┐        ┌──────────┐
   │  Azure   │        │   VoAI    │        │  Azure   │
   │ Neural   │        │           │        │  /VoAI   │
   └──────────┘        └───────────┘        └──────────┘

   ⚠️ 不推薦：Google Cloud TTS（台灣中文無高品質聲音）
```

## 整合範例

### Pipecat
```python
from pipecat.services.cartesia import CartesiaTTSService

tts = CartesiaTTSService(
    api_key=os.getenv("CARTESIA_API_KEY"),
    voice_id="your-voice-id"
)
```

### LiveKit
```python
from livekit.plugins import cartesia

tts = cartesia.TTS(
    voice="your-voice-id",
    model="sonic-2"
)
```

## 進階技巧

### 1. Text Preprocessing
```python
def preprocess_for_tts(text):
    # 移除 markdown
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # 替換縮寫
    text = text.replace("AI", "A I")
    # 加入適當停頓
    text = text.replace("，", "，... ")
    return text
```

### 2. Sentence Chunking
```python
# 分句處理，加快首字節時間
sentences = split_into_sentences(llm_output)
for sentence in sentences:
    audio = tts.synthesize(sentence)
    yield audio
```

### 3. Audio Caching
```python
# 快取常用語句
cache = {}
def get_tts(text):
    if text in cache:
        return cache[text]
    audio = tts.synthesize(text)
    cache[text] = audio
    return audio
```

## 參考連結

- [Cartesia Docs](https://docs.cartesia.ai/)
- [ElevenLabs Docs](https://elevenlabs.io/docs)
- [Deepgram TTS](https://developers.deepgram.com/docs/text-to-speech)
- [Azure Speech](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/)

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2025-01-28 | 新增 Gemini-TTS 完整介紹；區分 Google 語音服務架構（傳統 Cloud TTS vs Gemini-TTS） |
| 2025-01-28 | 新增 Google Cloud TTS、VoAI 評測；標註傳統 Cloud TTS 台灣中文不推薦 |
| 2025-01 | 初始版本 |
