# Research: STT Speech-to-Text Testing Module

**Date**: 2026-01-18
**Feature Branch**: `003-stt-testing-module`

## Executive Summary

本研究調查 STT Provider API、WER/CER 計算方法與瀏覽器錄音最佳實踐，為 STT 測試模組提供技術決策依據。

**關鍵發現**:
- ElevenLabs **不提供** STT 服務，需改用 OpenAI Whisper 作為第三個 Provider
- 專案已有 STT domain entities (`STTRequest`, `STTResult`) 可直接擴展
- WER 計算已有自製 Levenshtein 實作，需擴展支援 CER

---

## 1. Azure Speech Services STT

### Decision
使用 Azure Speech SDK (`azure-cognitiveservices-speech`) 進行批次與串流辨識。

### Rationale
- 專案已安裝 `azure-cognitiveservices-speech>=1.35.0`
- 現有 TTS 架構可直接複用配置模式
- 支援繁體中文 (`zh-TW`) 且有 word-level timestamps

### Technical Details

**API 架構**:
- 批次辨識: `SpeechRecognizer.recognize_once_async()`
- 串流辨識: `PushAudioInputStream` + continuous recognition callbacks

**Python SDK 使用**:
```python
import azure.cognitiveservices.speech as speechsdk

config = speechsdk.SpeechConfig(subscription=api_key, region="eastasia")
config.speech_recognition_language = "zh-TW"
config.request_word_level_timestamps()

# 串流模式
push_stream = speechsdk.audio.PushAudioInputStream()
audio_config = speechsdk.AudioConfig(stream=push_stream)
recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio_config)
```

**限制**:
| Parameter | Limit |
|-----------|-------|
| 單次請求 | 30 秒 |
| 串流 | ~10 分鐘/session |
| 支援格式 | WAV, MP3, OGG, FLAC |

**兒童語音優化**:
- 無原生 child mode 參數
- 建議使用 16-24kHz 取樣率
- 可透過 phrase hints 加入兒童常用詞彙

### Alternatives Considered
- Google Cloud only: 拒絕，需多 Provider 比較
- 自建 ASR: 拒絕，超出專案範圍

---

## 2. Google Cloud Speech-to-Text

### Decision
使用 Google Cloud Speech API (`google-cloud-speech`) 作為第二個 Provider。

### Rationale
- 專案已安裝 `google-cloud-speech>=2.23.0`
- 支援 `model="command_and_search"` 優化兒童語音
- 提供 speech context boost 功能

### Technical Details

**語言代碼映射**:
| 系統語言 | GCP 語言代碼 |
|----------|-------------|
| `zh-TW` | `cmn-Hant-TW` |
| `zh-CN` | `cmn-Hans-CN` |
| `en-US` | `en-US` |
| `ja-JP` | `ja-JP` |
| `ko-KR` | `ko-KR` |

**Python SDK 使用**:
```python
from google.cloud import speech_v1 as speech

client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="cmn-Hant-TW",
    enable_word_time_offsets=True,
    enable_automatic_punctuation=True,
    model="command_and_search",  # 兒童模式
)
```

**兒童語音優化**:
```python
speech_contexts=[
    speech.SpeechContext(
        phrases=["媽媽", "爸爸", "老師", "小朋友"],
        boost=10.0,
    )
]
```

**限制**:
| Parameter | Limit |
|-----------|-------|
| 批次檔案 | 480 MB |
| 串流 | 即時，無檔案限制 |
| 最長時間 | 480 分鐘 |

### Alternatives Considered
- AWS Transcribe: 拒絕，專案未使用 AWS
- AssemblyAI: 拒絕，非主流選擇

---

## 3. 第三個 Provider 選擇

### Decision
使用 **OpenAI Whisper API** 取代 ElevenLabs 作為第三個 STT Provider。

### Rationale
- **ElevenLabs 不提供 STT 服務** ❌
- OpenAI Whisper 已在專案依賴中 (`openai>=1.12.0`)
- Whisper 對 CJK 語言有優異準確度

### Technical Details

**限制**:
| Parameter | Limit |
|-----------|-------|
| 檔案大小 | 25 MB |
| 支援格式 | MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM |
| 模式 | 僅批次（無串流） |

**Python SDK 使用**:
```python
from openai import OpenAI

client = OpenAI()
with open("audio.mp3", "rb") as audio_file:
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="zh",
        response_format="verbose_json",
        timestamp_granularities=["word"]
    )
```

**串流支援**:
- Whisper API **不支援串流**
- 當使用者選擇串流模式時，Whisper 應呈現灰色不可選取（符合 spec FR-005）

### Alternatives Considered
- 本地 Whisper 模型: 拒絕，需 GPU 資源
- 其他小型 STT: 拒絕，準確度不足

---

## 4. WER/CER 計算

### Decision
擴展現有 `wer_calculator.py`，新增 CER 計算與對齊視覺化。

### Rationale
- 專案已有自製 Levenshtein 實作
- 無外部依賴，可控性高
- 需擴展支援 CJK 字元級計算

### Technical Details

**現有實作位置**: `backend/src/domain/services/wer_calculator.py`

**WER 計算** (英文):
```python
def calculate_wer(reference: str, hypothesis: str) -> float:
    """WER = (S + D + I) / N"""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    distance = _levenshtein_distance(ref_words, hyp_words)
    return distance / len(ref_words) if ref_words else 0.0
```

**CER 計算** (CJK):
```python
def calculate_cer(reference: str, hypothesis: str) -> float:
    """CER = character-level edit distance"""
    ref_chars = list(reference.replace(" ", ""))
    hyp_chars = list(hypothesis.replace(" ", ""))
    distance = _levenshtein_distance(ref_chars, hyp_chars)
    return distance / len(ref_chars) if ref_chars else 0.0
```

**語言判定邏輯**:
```python
def calculate_error_rate(reference: str, hypothesis: str, language: str) -> tuple[float, str]:
    """Auto-select WER or CER based on language"""
    cjk_languages = {"zh-TW", "zh-CN", "ja-JP", "ko-KR"}
    if language in cjk_languages:
        return calculate_cer(reference, hypothesis), "CER"
    return calculate_wer(reference, hypothesis), "WER"
```

### Alternatives Considered
- jiwer library: 拒絕，增加依賴且 CJK 支援有限
- Google Diff Match Patch: 拒絕，過於複雜

---

## 5. Browser MediaRecorder API

### Decision
使用 WebM + Opus 編碼，16kHz 取樣率，搭配噪音抑制選項。

### Rationale
- WebM Opus 有最佳壓縮率與瀏覽器支援
- 16kHz 是語音辨識最佳平衡點
- 噪音抑制提升 STT 準確度

### Technical Details

**推薦配置**:
```typescript
const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: { ideal: 16000 }
    }
});

const mediaRecorder = new MediaRecorder(stream, {
    mimeType: 'audio/webm;codecs=opus'
});
```

**瀏覽器相容性**:
| Format | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| WebM Opus | ✅ | ✅ | ❌ | ✅ |
| WAV | ✅ | ✅ | ⚠️ | ✅ |
| MP3 | ✅ | ❌ | ✅ | ✅ |

**Safari Fallback**:
```typescript
const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : 'audio/mp4';  // Safari fallback
```

**取樣率建議**:
| Provider | 最佳 | 最低 | 最高 |
|----------|------|------|------|
| Azure | 16 kHz | 8 kHz | 48 kHz |
| GCP | 16 kHz | 8 kHz | 48 kHz |
| Whisper | 16 kHz | 8 kHz | 48 kHz |

### Alternatives Considered
- 純 WAV: 拒絕，檔案過大
- 強制 48kHz: 拒絕，對 STT 無益且浪費頻寬

---

## 6. Provider 功能對比

| Feature | Azure | GCP | Whisper |
|---------|-------|-----|---------|
| 批次辨識 | ✅ | ✅ | ✅ |
| 串流辨識 | ✅ | ✅ | ❌ |
| Word Timestamps | ✅ | ✅ | ✅ |
| 兒童模式 | ⚠️ phrase hints | ✅ model selection | ❌ |
| 繁中支援 | ✅ | ✅ | ✅ |
| BYOL Key | ✅ | ✅ | ✅ |

---

## 7. 規格更新建議

根據研究結果，建議更新 spec.md：

1. **FR-002**: 將 ElevenLabs 改為 OpenAI Whisper
2. **FR-005**: 明確標示 Whisper 不支援串流模式
3. **FR-015**: 新增各 Provider 具體限制表格

---

## Summary of Decisions

| Topic | Decision | Key Reason |
|-------|----------|------------|
| Provider 1 | Azure Speech Services | 現有依賴，串流支援 |
| Provider 2 | Google Cloud STT | 兒童模式優化 |
| Provider 3 | OpenAI Whisper | ElevenLabs 無 STT |
| WER/CER | 自製 Levenshtein | 無外部依賴 |
| 錄音格式 | WebM Opus @ 16kHz | 最佳壓縮與相容性 |
| Safari fallback | MP4 | WebM 不支援 |
