# STT 多角色對話逐字稿研究

> 最後更新：2026-01

## 概述

本文研究各家 STT 服務對於多角色對話逐字稿 (Speaker Diarization) 的支援情況，目標是產生類似 `A: xxx B: xxx A: xxx` 的對話格式逐字稿。

## 什麼是 Speaker Diarization？

Speaker Diarization（說話者分離）是一種自動識別音頻中「誰在何時說話」的技術。它可以：
- 分離不同說話者的語音段落
- 為每個語音片段標記說話者標籤（如 Speaker A、Speaker B）
- 產生帶有說話者標識的結構化逐字稿

## 各服務商 Speaker Diarization 支援比較

### 原生支援對話格式的服務

| 服務 | 最大說話者數 | 輸出格式 | 即時串流 | 說話者命名 |
|------|-------------|---------|---------|-----------|
| Deepgram | 無明確限制 | `speaker: 0, 1, 2...` | ✅ | ❌ 需自行處理 |
| AssemblyAI | 10+ (可調) | `Speaker A, B, C...` | ✅ | ✅ Speaker Identification |
| ElevenLabs Scribe | 32 | `speaker_id` | ⚠️ 非即時 | ❌ |
| Google Cloud | 6 (預設, 可調) | `speaker_tag: 1, 2...` | ✅ | ❌ |
| Azure Speech | 多人 | `Guest-1, Guest-2...` | ✅ | ❌ |
| OpenAI GPT-4o-transcribe | 支援 | 需 known_speaker | ⚠️ 非即時 | ✅ 可提供參考音訊 |

---

## 各服務商詳細說明

### 1. Deepgram

**支援方式**: 原生 Diarization 功能

**啟用參數**:
```python
# 啟用 diarization 和 utterances
params = {
    "diarize": True,
    "utterances": True,
    "smart_format": True
}
```

**回應格式**:
```json
{
  "utterances": [
    {
      "speaker": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "你好，我是客服人員"
    },
    {
      "speaker": 1,
      "start": 2.8,
      "end": 5.0,
      "text": "你好，我想詢問訂單問題"
    }
  ]
}
```

**轉換為對話格式**:
```python
def format_conversation(utterances):
    speaker_map = {0: "A", 1: "B", 2: "C"}
    result = []
    for u in utterances:
        label = speaker_map.get(u["speaker"], f"Speaker{u['speaker']}")
        result.append(f"{label}: {u['text']}")
    return "\n".join(result)
```

**特點**:
- 🟢 即時串流支援
- 🟢 說話者重疊偵測
- 🟡 只提供數字標籤，需自行轉換

**參考**: [Deepgram Diarization Docs](https://developers.deepgram.com/docs/diarization)

---

### 2. AssemblyAI

**支援方式**: Speaker Labels + Speaker Identification

**啟用參數**:
```python
import assemblyai as aai

config = aai.TranscriptionConfig(
    speaker_labels=True,
    speakers_expected=2  # 可選，預期說話者數量
)
```

**回應格式**:
```json
{
  "utterances": [
    {
      "speaker": "A",
      "text": "你好，請問有什麼需要幫忙的嗎？",
      "start": 0,
      "end": 3500
    },
    {
      "speaker": "B",
      "text": "我想查詢我的訂單狀態",
      "start": 3800,
      "end": 6200
    }
  ]
}
```

**Speaker Identification（進階）**:
```python
config = aai.TranscriptionConfig(
    speaker_labels=True,
    speaker_identification={
        "speakers": [
            {"name": "客服", "role": "agent"},
            {"name": "顧客", "role": "customer"}
        ]
    }
)
```

**特點**:
- 🟢 原生 A/B/C 格式
- 🟢 支援 Speaker Identification（將標籤轉為姓名/角色）
- 🟢 最多 10+ 說話者
- 🟡 建議每位說話者至少連續說 30 秒以提高準確度

**參考**: [AssemblyAI Speaker Diarization](https://www.assemblyai.com/docs/pre-recorded-audio/speaker-diarization)

---

### 3. ElevenLabs Scribe

**支援方式**: Speaker Diarization

**API 參數**:
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=api_key)
result = client.speech_to_text.convert(
    audio=audio_file,
    model_id="scribe_v2",
    diarize=True,
    max_speakers=32
)
```

**特點**:
- 🟢 最多支援 32 位說話者
- 🟢 5 聲道多聲道支援
- 🟡 非即時處理（批次轉錄）
- 🟡 需自行將 speaker_id 轉為標籤

**參考**: [ElevenLabs Transcription](https://elevenlabs.io/docs/overview/capabilities/speech-to-text)

---

### 4. Google Cloud Speech-to-Text

**支援方式**: Speaker Diarization Config

**啟用參數**:
```python
from google.cloud import speech

diarization_config = speech.SpeakerDiarizationConfig(
    enable_speaker_diarization=True,
    min_speaker_count=2,
    max_speaker_count=6
)

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    language_code="zh-TW",
    diarization_config=diarization_config
)
```

**回應格式**:
```json
{
  "results": [{
    "alternatives": [{
      "words": [
        {"word": "你好", "speakerTag": 1},
        {"word": "請問", "speakerTag": 2}
      ]
    }]
  }]
}
```

**特點**:
- 🟢 支援即時串流
- 🟡 預設最多 6 人，可調整
- 🟡 回傳 word-level speaker tag，需自行組合成句子

**參考**: [Google Cloud Multiple Voices](https://cloud.google.com/speech-to-text/v2/docs/multiple-voices)

---

### 5. Azure Speech Services

**支援方式**: Real-time Diarization

**啟用參數**:
```python
speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
speech_config.request_word_level_timestamps = True

auto_detect = speechsdk.AutoDetectSourceLanguageConfig(languages=["zh-TW"])
conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
    speech_config=speech_config
)
```

**輸出格式**:
說話者標籤為 `Guest-1`, `Guest-2` 等格式

**特點**:
- 🟢 即時對話轉錄
- 🟢 企業級支援
- 🟡 說話者標籤格式固定

**參考**: [Azure Diarization Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-stt-diarization)

---

### 6. OpenAI GPT-4o-transcribe-diarize

**支援方式**: 可提供已知說話者參考音訊

**特殊功能**: 可上傳 2-10 秒的參考音訊來識別特定說話者

```python
import openai

response = openai.Audio.transcribe(
    model="gpt-4o-transcribe-diarize",
    file=audio_file,
    known_speaker_names=["Alice", "Bob"],
    known_speaker_references=[alice_audio, bob_audio],
    chunking_strategy="auto"  # 音訊 > 30 秒時需設定
)
```

**特點**:
- 🟢 可用參考音訊識別說話者
- 🟡 最長 25 分鐘（1500 秒）
- 🟡 僅支援批次轉錄，不支援即時 API

**參考**: [OpenAI Speech to Text](https://platform.openai.com/docs/guides/speech-to-text)

---

## 多聲道 vs 說話者分離

### 何時使用多聲道 (Multichannel)

適用於：
- 每位說話者有獨立錄音軌道（如電話客服、Podcast 分軌錄音）
- 需要 100% 準確的說話者分離

```python
# Deepgram 多聲道範例
params = {
    "multichannel": True,
    "channels": 2
}
```

### 何時使用 Diarization

適用於：
- 單一音軌錄音（如現場會議、訪談）
- 無法預先分離音軌

---

## 自行實作對話格式（分段合併策略）

如果 STT 服務不支援原生 Diarization，可考慮以下策略：

### 策略 1: 分軌錄音 + 合併

```
[錄音階段]
├── 說話者 A → 音軌 1 → 轉錄 → A 的逐字稿
└── 說話者 B → 音軌 2 → 轉錄 → B 的逐字稿

[合併階段]
根據時間戳交錯合併：
A: [0:00-0:05] 你好
B: [0:06-0:10] 你好，請問...
A: [0:11-0:15] 沒問題
```

**實作範例**:
```python
def merge_transcripts(transcript_a: list, transcript_b: list) -> str:
    """合併兩個帶時間戳的逐字稿"""
    all_segments = []

    for seg in transcript_a:
        all_segments.append({
            "speaker": "A",
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })

    for seg in transcript_b:
        all_segments.append({
            "speaker": "B",
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })

    # 依時間排序
    all_segments.sort(key=lambda x: x["start"])

    # 格式化輸出
    result = []
    for seg in all_segments:
        result.append(f"{seg['speaker']}: {seg['text']}")

    return "\n".join(result)
```

### 策略 2: VAD + 分段 + 說話者分類

```
[單一音軌]
    ↓
[VAD 偵測] → 切分成語音片段
    ↓
[特徵提取] → 提取每段的聲紋特徵
    ↓
[聚類分析] → 將相似聲紋分到同一說話者
    ↓
[標籤輸出] → A: xxx B: xxx
```

**開源工具**:
- [pyannote-audio](https://github.com/pyannote/pyannote-audio) - 強大的說話者分離模型
- [speechbrain](https://github.com/speechbrain/speechbrain) - 包含 speaker embedding

---

## 推薦方案

### 依場景選擇

| 場景 | 推薦服務 | 原因 |
|------|---------|------|
| 即時對話轉錄 | Deepgram / AssemblyAI | 低延遲 + 原生 diarization |
| 已知說話者名稱 | AssemblyAI (Speaker ID) | 可直接輸出姓名/角色 |
| 大型會議 (10+ 人) | ElevenLabs Scribe | 最多 32 人 |
| 需要參考音訊識別 | OpenAI GPT-4o | 可提供說話者參考 |
| 多聲道錄音 | Deepgram Multichannel | 100% 準確分離 |
| 自建方案 | pyannote + Whisper | 完全自控，無 API 費用 |

### 對話格式輸出範例

```
客服: 您好，這裡是客服中心，請問有什麼可以幫您的？
顧客: 我想查詢訂單 12345 的配送狀態。
客服: 好的，請稍等我為您查詢。
顧客: 謝謝。
客服: 查到了，您的訂單目前正在配送中，預計明天送達。
顧客: 太好了，謝謝您的幫助。
```

---

## 準確度注意事項

1. **連續說話時間**: 每位說話者建議至少連續說 30 秒，短句（如「是」、「好」）較難準確分類
2. **聲音相似度**: 同性別或聲音相似的說話者準確度較低
3. **交叉對話**: 多人同時說話時準確度下降
4. **音質影響**: 背景噪音會影響說話者分離效果
5. **即時 vs 批次**: 批次處理可獲得更高準確度（有完整上下文）

---

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2026-01 | 初始版本 |
