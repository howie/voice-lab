# AssemblyAI 深入研究

> 最後更新：2026-01

## 概述

AssemblyAI 是專注於語音 AI 的公司，以高性價比和開發者體驗著稱。Universal-2 模型在準確度和成本間取得優異平衡。

| 項目 | 說明 |
|------|------|
| 官網 | https://www.assemblyai.com |
| 文件 | https://www.assemblyai.com/docs |
| GitHub SDK | https://github.com/AssemblyAI/assemblyai-python-sdk |
| 狀態 | ✅ 生產推薦 (性價比最高) |

---

## 版本與模型

| 模型 | 用途 | 特點 |
|------|------|------|
| Universal-2 | 批次轉錄 | 最高準確度、100+ 語言 |
| Universal-Streaming | 即時串流 | ~300ms 延遲、不可變轉錄 |
| Slam | 專有名詞 | 57% 更準確的關鍵詞辨識 |

---

## 定價

| 方案 | 價格 | 備註 |
|------|------|------|
| 標準 | $0.15/hour | 💰 **所有語言同價** |
| 即時串流 | $0.15/hour | 與批次同價 |

**無免費層**，但有試用額度。

---

## API 串接

### 安裝

```bash
pip install assemblyai
```

### 批次轉錄

```python
import assemblyai as aai

aai.settings.api_key = "your-api-key"

transcriber = aai.Transcriber()

# 從檔案轉錄
transcript = transcriber.transcribe("audio.mp3")

# 從 URL 轉錄
transcript = transcriber.transcribe("https://example.com/audio.mp3")

print(transcript.text)
```

### 進階選項

```python
config = aai.TranscriptionConfig(
    language_code="zh",
    speaker_labels=True,           # 說話者分離
    auto_chapters=True,            # 自動分章
    entity_detection=True,         # 實體偵測
    sentiment_analysis=True,       # 情感分析
    iab_categories=True,           # 主題分類
    word_boost=["NVIDIA", "GPT"],  # 關鍵詞增強
    boost_param="high"
)

transcript = transcriber.transcribe("audio.mp3", config=config)

# 說話者分離結果
for utterance in transcript.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.text}")
```

### 即時串流 (Universal-Streaming)

```python
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingParameters,
    TurnEvent
)

def on_turn(turn: TurnEvent):
    print(f"Turn: {turn.transcript}")

params = StreamingParameters(
    sample_rate=16000,
    format_turns=True  # False 可減少 ~50ms 延遲
)

client = StreamingClient(api_key="your-api-key")
client.on("turn", on_turn)

# 開始串流
await client.connect(params)
await client.send_audio(audio_chunk)
await client.close()
```

### 麥克風即時轉錄

```python
import assemblyai as aai

aai.settings.api_key = "your-api-key"

def on_data(transcript: aai.RealtimeTranscript):
    if isinstance(transcript, aai.RealtimeFinalTranscript):
        print(transcript.text)

transcriber = aai.RealtimeTranscriber(
    sample_rate=16000,
    on_data=on_data,
    on_error=lambda e: print(f"Error: {e}")
)

transcriber.connect()

# 使用 MicrophoneStream helper
stream = aai.extras.MicrophoneStream(sample_rate=16000)
transcriber.stream(stream)

transcriber.close()
```

---

## 功能特點

### ✅ 優點

1. **💰 極佳性價比**
   - $0.15/hour 所有語言同價
   - 業界最低價之一

2. **高準確度**
   - 93.3% Word Accuracy Rate
   - 比 Whisper Large-v3 WER 低 17.3%
   - 幻覺率降低 30%

3. **100+ 語言支援**
   - 包含多語言即時串流 (2025-10 新增)
   - 西班牙語、法語、德語、義大利語、葡萄牙語

4. **不可變轉錄 (Streaming)**
   - 已產出的文字不會被覆蓋
   - 適合語音助理和即時應用

5. **豐富的附加功能**
   - 說話者分離 (64% 錯誤減少)
   - 自動分章、情感分析、主題分類
   - PII 遮蔽

6. **優秀開發者體驗**
   - 文件清晰完整
   - SDK 設計良好
   - 快速上手

7. **專有名詞優化**
   - Word Boost / Keyterm prompting
   - 1000 詞上下文感知提示

### ❌ 缺點

1. **即時延遲**
   - ~300ms 延遲
   - 相比 Deepgram (~100ms) 較慢

2. **口音準確度**
   - 重口音、快速語音仍有問題
   - 法語準確度有時不佳

3. **語言支援限制**
   - 部分語言功能受限
   - 非英語即時串流 2025-10 才支援

4. **自訂化有限**
   - 無法針對特定領域微調
   - 域名特定詞彙支援有限

5. **回應時間不一致**
   - 高負載時延遲變異大

6. **低品質音訊**
   - 音質差時準確度下降明顯

---

## 網路評價

### 評分彙整

| 來源 | 評分 | 評論數 |
|------|------|--------|
| G2 | 4.6/5 ⭐ | 100+ |
| Product Hunt | 正面 | - |

### 常見評價

**正面:**
- "性價比無敵，$0.15/hr 超划算"
- "文件清晰，上手超快"
- "說話者分離終於準確了"
- "比 Whisper 準確度更高且更穩定"

**負面:**
- "即時延遲不夠低，不適合快節奏對話"
- "重口音辨識還有改進空間"
- "價格對某些貨幣來說還是偏高"

---

## 與競品比較

| 項目 | AssemblyAI | Deepgram | ElevenLabs |
|------|------------|----------|------------|
| 定價/hr | $0.15 ⭐ | ~$0.26 | $0.40 |
| 即時延遲 | ~300ms | ~100ms ⭐ | ~150ms |
| WER | 5.2% | 5-8% | 3.1% ⭐ |
| 語言數 | 100+ ⭐ | 36+ | 99 |
| 說話者分離 | ✅ | ✅ | ✅ (32人) |

---

## 適用場景

| 場景 | 適合度 | 說明 |
|------|--------|------|
| 預算考量 | ⭐⭐⭐⭐⭐ | 業界最低價 |
| 多語言客服 | ⭐⭐⭐⭐⭐ | 100+ 語言同價 |
| 會議轉錄 | ⭐⭐⭐⭐⭐ | 說話者分離佳 |
| 內容分析 | ⭐⭐⭐⭐⭐ | 情感、主題、分章 |
| 即時語音助理 | ⭐⭐⭐ | 延遲稍高 |
| 極高準確度需求 | ⭐⭐⭐ | 不如 ElevenLabs |

---

## 參考連結

- [官方文件](https://www.assemblyai.com/docs)
- [Python SDK](https://github.com/AssemblyAI/assemblyai-python-sdk)
- [Universal-1 研究](https://www.assemblyai.com/research/universal-1)
- [Streaming 指南](https://www.assemblyai.com/docs/guides/real-time-streaming-transcription)
- [G2 評價](https://www.g2.com/products/assemblyai-speech-to-text-api/reviews)
- [基準測試](https://www.assemblyai.com/benchmarks)

---

## 更新追蹤

| 日期 | 事件 |
|------|------|
| 2025-10 | 多語言即時串流發布 (英/西/法/德/義/葡) |
| 2025-10 | 說話者分離準確度提升 64% |
| 2025-10 | Slam 模型專有名詞準確度提升 57% |
| 2025-12 | Python SDK 更新 (支援 Python 3.8-3.14) |
