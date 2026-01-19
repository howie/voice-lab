# ElevenLabs Scribe 深入研究

> 最後更新：2026-01

## 概述

ElevenLabs Scribe 是 ElevenLabs 於 2025 年推出的首個獨立 STT 模型，被認為是目前最準確的語音轉文字服務之一。

| 項目 | 說明 |
|------|------|
| 官網 | https://elevenlabs.io/speech-to-text |
| 文件 | https://elevenlabs.io/docs/overview/capabilities/speech-to-text |
| GitHub SDK | https://github.com/elevenlabs/elevenlabs-python |
| 狀態 | ✅ 生產就緒 |

---

## 版本與模型

| 模型 | 用途 | 延遲 | 特點 |
|------|------|------|------|
| Scribe v1 | 批次處理 | - | 高準確度 |
| Scribe v2 | 批次處理 | - | 更高準確度、Keyterm prompting |
| Scribe v2 Realtime | 即時串流 | ~150ms | 低延遲、即時轉錄 |

---

## 定價

| 方案 | 價格 | 備註 |
|------|------|------|
| Pay-as-you-go | $0.40/hour | 標準價格 |
| Enterprise | $0.22/hour 起 | 量大優惠 |

---

## API 串接

### 安裝

```bash
pip install elevenlabs
```

### 批次轉錄

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="your-api-key")

# 基本轉錄
result = client.speech_to_text.convert(
    audio=open("audio.mp3", "rb"),
    model_id="scribe_v2",
    language_code="zh"  # 可選，支援自動偵測
)

print(result.text)
```

### 進階選項

```python
result = client.speech_to_text.convert(
    audio=open("audio.mp3", "rb"),
    model_id="scribe_v2",
    language_code="zh",
    tag_audio_events=True,       # 標記音訊事件 (笑聲、掌聲等)
    diarize=True,                # 說話者分離
    timestamps_granularity="word" # 字級時間戳
)

# 取得說話者分離結果
for utterance in result.utterances:
    print(f"Speaker {utterance.speaker_id}: {utterance.text}")
```

### 即時串流 (WebSocket)

```python
import asyncio
import websockets
import json

async def realtime_transcribe():
    uri = "wss://api.elevenlabs.io/v1/speech-to-text/stream"

    async with websockets.connect(uri) as ws:
        # 發送配置
        config = {
            "api_key": "your-api-key",
            "model_id": "scribe_v2_realtime",
            "language_code": "en",
            "sample_rate": 16000,
            "encoding": "pcm_s16le"
        }
        await ws.send(json.dumps(config))

        # 發送音訊 chunks
        # await ws.send(audio_chunk)

        # 接收轉錄結果
        async for message in ws:
            result = json.loads(message)
            print(result["text"])
```

### Keyterm Prompting (Scribe v2)

```python
result = client.speech_to_text.convert(
    audio=open("audio.mp3", "rb"),
    model_id="scribe_v2",
    keyterms=["NVIDIA", "GPT-4", "Anthropic", "Claude"]  # 最多 100 個
)
```

---

## 支援格式

### 音訊格式
- MP3, WAV, FLAC, M4A, AAC, OGG, WebM

### 音訊編碼 (串流)
- PCM (8-48 kHz)
- μ-law (電話系統)

### 輸出格式
- JSON (含時間戳、說話者、音訊事件)
- SRT/VTT 字幕

---

## 功能特點

### ✅ 優點

1. **極高準確度**
   - WER 3.1% (英文 FLEURS 基準)
   - 超越 Whisper Large V3、Gemini 2.0 Flash、Deepgram Nova-3

2. **99 語言支援**
   - 包含多種較少資源語言 (塞爾維亞語、粵語、馬拉雅拉姆語)
   - 代碼切換支援

3. **說話者分離**
   - 單一錄音最多辨識 32 位說話者
   - 多聲道支援 (最多 5 聲道)

4. **Keyterm Prompting**
   - 可指定最多 100 個專有名詞/術語
   - 適合技術領域、品牌名稱

5. **實體偵測**
   - 自動偵測信用卡號、姓名、醫療資訊、身分證號
   - 提供精確時間戳

6. **企業合規**
   - SOC 2、HIPAA、GDPR 合規
   - EU 資料駐留選項
   - Zero Retention 模式

7. **低延遲即時版**
   - Scribe v2 Realtime ~150ms 延遲

### ❌ 缺點

1. **API 限制**
   - 目前僅支援檔案串流，不支援 URL
   - 說話者分離僅限 8 分鐘以內檔案

2. **無開源選項**
   - 僅雲端服務，無法自架
   - 資料隱私需透過 SLA 協議

3. **即時版說話者分離**
   - Realtime 版本尚不支援說話者分離

4. **預設資料使用**
   - 預設可能用於模型訓練
   - 需 SLA 才能完全控制

---

## 網路評價

### G2 / Product Hunt 評價

| 來源 | 評分 | 評論數 |
|------|------|--------|
| TheToolsVerse | 4.9/5 ⭐ | - |
| 開發者社群 | 正面 | - |

### 常見評價

**正面:**
- "準確度明顯超越 Whisper 和其他競品"
- "多語言和代碼切換表現優異"
- "API 整合簡單直覺"

**負面:**
- "價格比 Whisper API 稍高"
- "即時版功能還不完整"
- "需要 SLA 才能確保資料不被用於訓練"

---

## 與競品比較

| 項目 | ElevenLabs Scribe | Whisper Large V3 | Deepgram Nova-2 |
|------|-------------------|------------------|-----------------|
| WER (英文) | 3.1% | ~5% | ~5-8% |
| 即時延遲 | ~150ms | 需自架 | ~100ms |
| 說話者分離 | ✅ (32人) | ❌ | ✅ |
| 開源 | ❌ | ✅ | ❌ |
| 定價/hr | $0.40 | $0.36 (API) | ~$0.26 |

---

## 適用場景

| 場景 | 適合度 | 說明 |
|------|--------|------|
| 高準確度需求 | ⭐⭐⭐⭐⭐ | WER 最低 |
| 多說話者會議 | ⭐⭐⭐⭐⭐ | 32 人分離 |
| 合規環境 (醫療/金融) | ⭐⭐⭐⭐⭐ | HIPAA 合規 |
| 即時語音助理 | ⭐⭐⭐⭐ | 150ms 延遲 |
| 預算有限 | ⭐⭐⭐ | 價格中等 |
| 自架需求 | ❌ | 僅雲端 |

---

## 參考連結

- [官方文件](https://elevenlabs.io/docs/overview/capabilities/speech-to-text)
- [Scribe v2 介紹](https://elevenlabs.io/blog/introducing-scribe-v2)
- [Scribe v2 Realtime 介紹](https://elevenlabs.io/blog/introducing-scribe-v2-realtime)
- [Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [評測文章](https://latenode.com/blog/tools-software-reviews/best-ai-tools-2025/elevenlabs-scribe-review-and-accuracy-test)

---

## 更新追蹤

| 日期 | 事件 |
|------|------|
| 2025-02 | Scribe v1 發布 |
| 2025-Q3 | Scribe v2 發布 (Keyterm prompting) |
| 2025-11 | Scribe v2 Realtime 發布 |
