# OpenAI Whisper 深入研究

> 最後更新：2026-01

## 概述

OpenAI Whisper 是目前語音轉文字 (STT) 領域的**黃金標準 (Gold Standard)**。作為開源模型，它定義了現代 STT 的準確度基準。雖然官方 API 僅提供批次處理，但其生態系極為豐富。

| 項目 | 說明 |
|------|------|
| 官網 | https://openai.com/research/whisper |
| API 文件 | https://platform.openai.com/docs/guides/speech-to-text |
| GitHub | https://github.com/openai/whisper |
| 狀態 | ✅ 生產推薦 (準確度基準) |

---

## 版本與模型

| 模型 | 參數量 | 用途 | 特點 |
|------|--------|------|------|
| **large-v3** | 1550M | 通用高精度 | 目前最強大的開源模型，多語言表現極佳 |
| **large-v3-turbo** | - | 速度優化 | 2024 下半年推出，犧牲極少準確度換取 8x 速度 |
| **distil-whisper** | 多種 | 極速推論 | Hugging Face 蒸餾版本，適合邊緣裝置 |
| **whisper-1** | - | OpenAI API | 官方 API 端點背後的模型 (通常是最新 Large 版本) |

---

## 定價與部署方式

Whisper 的獨特性在於它既是 **API 服務**，也是 **開源模型**。

### 1. OpenAI 官方 API

| 方案 | 價格 | 備註 |
|------|------|------|
| Whisper-1 | $0.006 / 分鐘 | 約 $0.36 / 小時。簡單易用，但僅限批次。 |

### 2. 第三方託管 (Groq / DeepInfra)

針對需要極低延遲或更低成本的用戶。

| 供應商 | 價格 | 速度 (Real-time Factor) | 備註 |
|--------|------|-------------------------|------|
| **Groq** | **$0.04 / 小時** | > 100x | ⚡️ 驚人的推論速度，適合即時應用 |
| DeepInfra| ~$0.002 / 分鐘 | ~50x | |

### 3. 自行部署 (Self-Hosted)

*   **成本**: GPU 運算成本 (AWS g4dn, RunPod 等)。
*   **優點**: 資料隱私完全掌控，無 API Rate Limit。
*   **工具**: `faster-whisper`, `insanely-fast-whisper`。

---

## API 串接

### OpenAI 官方 API (Python)

```python
from openai import OpenAI

client = OpenAI()

audio_file = open("speech.mp3", "rb")
transcript = client.audio.transcriptions.create(
  model="whisper-1", 
  file=audio_file,
  response_format="text" # 或 json, srt, vtt
)

print(transcript)
```

### Groq API (相容 OpenAI SDK)

```python
from groq import Groq

client = Groq()
filename = "audio.m4a"

with open(filename, "rb") as file:
    transcription = client.audio.transcriptions.create(
      file=(filename, file.read()),
      model="whisper-large-v3-turbo", # 或 whisper-large-v3
      response_format="json",
      language="zh",
      temperature=0.0
    )
    print(transcription.text)
```

### 本地執行 (使用 `faster-whisper`)

```python
from faster_whisper import WhisperModel

model_size = "large-v3"
# Run on GPU with FP16
model = WhisperModel(model_size, device="cuda", compute_type="float16")

segments, info = model.transcribe("audio.mp3", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
```

---

## 功能特點

### ✅ 優點

1.  **👑 準確度天花板**
    *   `large-v3` 在絕大多數基準測試中仍是冠軍，特別是冷門語言或口音。
    *   對背景音樂、噪音的抗性極強。

2.  **開源自由**
    *   無 Vendor Lock-in，可以隨時切換供應商或轉為自架。
    *   社群生態極強 (C++ port, WebAssembly, CoreML)。

3.  **多語言翻譯**
    *   支援直接將音訊翻譯成英文 (Translate 任務)，效果往往比 STT + 翻譯 更好。

4.  **Groq 加持**
    *   透過 Groq LPU，Whisper 也能實現 "即時" (Real-time) 體驗，延遲極低。

### ❌ 缺點

1.  **官方 API 延遲高**
    *   OpenAI 官方端點不支援 Streaming，僅能上傳檔案後等待結果，不適合即時對話。
    *   需依賴 Groq 或自架解決即時需求。

2.  **幻覺 (Hallucination)**
    *   在長時間靜音或非語音片段，Whisper 偶爾會 "腦補" 出不存在的句子 (如 "Thank you for watching")。
    *   `v3-turbo` 已有改善，但仍需後處理機制 (VAD) 配合。

3.  **缺乏進階功能**
    *   原生不支援 **Speaker Diarization** (說話者分離)。需搭配 `pyannote-audio` 等額外模型，增加了整合複雜度。
    *   無 Word-level timestamp (官方 API 不支援，需透過 verbose_json 或自架獲取)。

---

## 網路評價

### 常見評價

**正面:**
*   "準確度沒話說，特別是中文和日文混雜時。"
*   "Groq + Whisper 改變了遊戲規則，又快又便宜。"
*   "開源讓我們不用擔心資料外洩。"

**負面:**
*   "幻覺問題有時候很惱人，需要額外寫程式碼過濾。"
*   "沒有內建 Diarization 是最大痛點，Deepgram 在這點方便很多。"

---

## 與競品比較

| 項目 | OpenAI Whisper (API) | Deepgram Nova-2 | ElevenLabs Scribe |
|------|----------------------|-----------------|-------------------|
| 準確度 | ⭐⭐⭐⭐⭐ (基準) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 速度/延遲 | 慢 (批次) | ⭐ 極快 (<300ms) | 中等 |
| 價格 | $0.36/hr | $0.26/hr | $0.40/hr |
| Diarization | ❌ (需外掛) | ✅ 內建優異 | ✅ 內建 |
| 部署彈性 | ✅ (可自架/雲端) | ❌ (SaaS Only) | ❌ (SaaS Only) |

---

## 適用場景

| 場景 | 適合度 | 說明 |
|------|--------|------|
| **離線字幕製作** | ⭐⭐⭐⭐⭐ | 準確度優先，不趕時間 |
| **多語言會議記錄** | ⭐⭐⭐⭐ | 需自行整合 Diarization |
| **極致低成本 (Groq)**| ⭐⭐⭐⭐⭐ | $0.04/hr 無人能敵 |
| **隱私敏感資料** | ⭐⭐⭐⭐⭐ | 可完全離線執行 (On-premise) |
| **即時語音機器人** | ⭐⭐⭐ | 僅在使用 Groq 或高階 GPU 自架時可行 |

---

## 參考連結

*   [Whisper 論文](https://arxiv.org/abs/2212.04356)
*   [Hugging Face Whisper](https://huggingface.co/openai/whisper-large-v3)
*   [Groq Cloud](https://console.groq.com/docs/models)
*   [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
