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

## 功能比較表

| 功能 | Cartesia | ElevenLabs | Deepgram | Azure |
|------|----------|------------|----------|-------|
| 串流輸出 | ✅✅ | ✅ | ✅ | ✅ |
| 中文支援 | ✅ | ✅ | ⚠️ 有限 | ✅✅ |
| 台語支援 | ❌ | ⚠️ | ❌ | ⚠️ |
| 聲音複製 | ✅ | ✅✅ | ❌ | ✅ |
| 情感控制 | ✅ | ✅✅ | ❌ | ✅ |
| SSML | ⚠️ | ⚠️ | ❌ | ✅✅ |
| 自部署 | ❌ | ❌ | ❌ | ⚠️ |

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
| 2025-01 | 初始版本 |
