# Deepgram 深入研究

> 最後更新：2026-01

## 概述

Deepgram 是專注於語音 AI 的平台，以極致的**速度**（低延遲）和**性價比**著稱。其自研的 End-to-End Deep Learning 架構使其在即時串流（Real-time Streaming）場景中表現卓越。

| 項目 | 說明 |
|------|------|
| 官網 | https://deepgram.com |
| 文件 | https://developers.deepgram.com |
| GitHub SDK | https://github.com/deepgram/deepgram-python-sdk |
| 狀態 | ✅ 生產推薦 (即時應用首選) |

---

## 版本與模型

| 模型 | 用途 | 特點 |
|------|------|------|
| **Nova-2** | 通用轉錄 | 業界領先的準確度與速度平衡 (WER ~5%) |
| **Nova-3** (預測/Beta) | 下一代通用 | 預計 2025 下半年推出，進一步提升多語言能力 |
| **Flux** | 對話式 AI | 專為語音助理設計，超低延遲，內建 End-of-Speech 偵測 |
| **Enhanced** | 特殊場景 | 針對特定領域優化的舊版模型 |

---

## 定價

Deepgram 採用 "Pay As You Go" 模式，價格極具競爭力。

| 方案 | 價格 (批次) | 價格 (即時) | 備註 |
|------|-------------|-------------|------|
| Nova-2 | $0.0043/min (~$0.26/hr) | $0.0043/min | 💰 **極高性價比** |
| Enhanced | $0.006/min | $0.006/min | |
| Base | $0.0048/min | $0.0059/min | |

*新用戶通常有 $200 的免費額度。*

---

## API 串接

### 安裝

```bash
pip install deepgram-sdk
```

### 批次轉錄 (Prerecorded)

```python
import os
from deepgram import DeepgramClient, PrerecordedOptions

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

def main():
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)

    with open("audio.mp3", "rb") as buffer:
        payload = {"buffer": buffer}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="zh-TW",
            diarize=True,
        )
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
        print(response.to_json(indent=4))

if __name__ == "__main__":
    main()
```

### 即時串流 (Live Streaming)

Deepgram 的強項在於 WebSocket 即時串流，延遲可低至 <300ms (甚至 100ms)。

```python
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

def main():
    deepgram = DeepgramClient(api_key="YOUR_API_KEY")

    connection = deepgram.listen.live.v("1")

    def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) > 0:
            print(f"Transcript: {sentence}")

    connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        interim_results=True, # 取得中間結果以降低體感延遲
    )

    connection.start(options)
    
    # 這裡需實作音訊串流發送邏輯 (如從麥克風讀取)
    # connection.send(audio_data)

    connection.finish()

if __name__ == "__main__":
    main()
```

---

## 功能特點

### ✅ 優點

1.  **🚀 極致速度與低延遲**
    *   即時串流延遲極低 (Nova-2 可達 ~300ms 內，Flux 更低)，非常適合語音機器人。
    *   批次處理速度極快 (通常是音訊長度的 1/100 時間)。

2.  **💰 高性價比**
    *   Nova-2 $0.26/hr 的價格遠低於 OpenAI Whisper API ($0.36/hr) 和 Google STT。

3.  **強大的功能集**
    *   **Smart Formatting**: 自動標點、數字格式化 (日期、貨幣)。
    *   **Diarization**: 優秀的說話者分離能力。
    *   **Topic Detection / Summarization**: 內建 NLP 功能 (需額外付費)。

4.  **Flux 模型 (2025 新亮點)**
    *   專為 Voice Agent 設計，整合了 VAD (Voice Activity Detection) 和打斷處理，減少開發者自行實作的痛苦。

5.  **廣泛的語言支援**
    *   支援 30+ 種語言，且 Nova-2 在多語言混雜場景表現不錯。

### ❌ 缺點

1.  **準確度上限**
    *   雖然 Nova-2 很強，但在某些極端噪音或冷門專有名詞上，可能略遜於 OpenAI Whisper Large-v3 或 ElevenLabs Scribe。

2.  **繁體中文支援**
    *   支援繁體中文 (zh-TW)，但訓練資料量可能不如英文龐大，偶爾會有同音字錯誤。

3.  **自訂化限制**
    *   雖然有 Custom Vocabulary，但微調 (Fine-tuning) 門檻較高 (主要針對企業方案)。

---

## 網路評價

### 評分彙整

| 來源 | 評分 | 評論數 |
|------|------|--------|
| G2 | 4.7/5 ⭐ | 200+ |
| Product Hunt | Top Rated | - |

### 常見評價

**正面:**
*   "速度快得不可思議，即時應用的唯一選擇。"
*   "API 設計非常開發者友善 (DX is great)。"
*   "價格讓我們能大規模部署而不破產。"

**負面:**
*   "非英語系語言的準確度有時不如 Whisper。"
*   "文檔更新有時跟不上 SDK 的變化。"

---

## 與競品比較

| 項目 | Deepgram Nova-2 | OpenAI Whisper API | AssemblyAI |
|------|-----------------|--------------------|------------|
| 定價/hr | ~$0.26 ⭐ | $0.36 | $0.15 |
| 即時延遲 | <300ms ⭐ | 需自架 | ~300ms+ |
| 準確度 (En) | 優異 | 極優 (Large-v3) | 優異 |
| 適用場景 | 即時對話、語音助理 | 離線高精度轉錄 | 內容分析、摘要 |

---

## 適用場景

| 場景 | 適合度 | 說明 |
|------|--------|------|
| **即時語音助理 (AI Agent)** | ⭐⭐⭐⭐⭐ | 延遲低、Flux 模型優化 |
| **電話客服中心** | ⭐⭐⭐⭐⭐ | 速度快、成本低、支援雙軌分離 |
| **大量媒體轉錄** | ⭐⭐⭐⭐ | 處理速度極快，省時 |
| **學術/醫療高精度** | ⭐⭐⭐ | 可能需評估 Whisper 或 Speechmatics |

---

## 參考連結

*   [官方文件](https://developers.deepgram.com)
*   [Nova-2 介紹](https://deepgram.com/learn/nova-2-speech-to-text-api)
*   [Python SDK](https://github.com/deepgram/deepgram-python-sdk)
*   [Pricing 頁面](https://deepgram.com/pricing)
