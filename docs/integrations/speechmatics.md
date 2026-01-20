# Speechmatics Integration

Speechmatics 是專注於高精度語音辨識 (STT) 的服務，以多語言支援和高準確率著稱，特別擅長處理口音、方言和專業術語。

## Step 1: 建立 Speechmatics 帳戶

1. 前往 [Speechmatics Portal](https://portal.speechmatics.com/)

2. 點擊「**Sign Up**」註冊

3. 填寫註冊資訊：
   - Email
   - 密碼
   - 公司名稱（可選）

4. 驗證 Email

5. 免費帳戶提供試用額度

## Step 2: 取得 API Key

1. 登入 [Speechmatics Portal](https://portal.speechmatics.com/)

2. 在左側選單點擊「**API Keys**」

3. 點擊「**Create API Key**」

4. 填寫 API Key 資訊：

   | 欄位 | 說明 | 建議值 |
   |------|------|--------|
   | **Name** | API Key 名稱 | `voice-lab-key` |
   | **Expiry** | 過期時間 | 依需求選擇 |

5. 點擊「**Create**」

6. **立即複製並保存 API Key**（只會顯示一次）

## Step 3: 設定環境變數

```bash
# .env
SPEECHMATICS_API_KEY=your_api_key_here
```

## API 使用方式

### API 類型

Speechmatics 提供兩種 API：

| API 類型 | 說明 | 適用場景 |
|----------|------|----------|
| **Batch API** | 上傳檔案，非同步處理 | 預錄音檔、大量處理 |
| **Real-Time API** | WebSocket 串流 | 即時轉錄、直播 |

### REST API 端點

| 服務 | 端點 |
|------|------|
| Batch 轉錄 | `https://asr.api.speechmatics.com/v2/jobs` |
| 查詢任務 | `https://asr.api.speechmatics.com/v2/jobs/{job_id}` |
| 取得結果 | `https://asr.api.speechmatics.com/v2/jobs/{job_id}/transcript` |
| Real-Time | `wss://eu2.rt.speechmatics.com/v2` |

### 認證方式

使用 `Authorization: Bearer` header：

```bash
curl -X GET "https://asr.api.speechmatics.com/v2/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 實作範例

### Python (speechmatics-python SDK)

#### 安裝 SDK

```bash
pip install speechmatics-python
```

#### Batch 轉錄

```python
from speechmatics.batch_client import BatchClient
from speechmatics.models import BatchTranscriptionConfig

def speechmatics_batch_transcribe(audio_path: str, language: str = "zh"):
    """Speechmatics batch transcription."""
    api_key = "YOUR_API_KEY"

    settings = BatchTranscriptionConfig(
        language=language,
        enable_entities=True,
    )

    with BatchClient(api_key) as client:
        job_id = client.submit_job(
            audio=audio_path,
            transcription_config=settings,
        )

        transcript = client.wait_for_completion(job_id, transcription_format="txt")
        return transcript
```

#### Real-Time 轉錄

```python
import asyncio
from speechmatics.client import WebsocketClient
from speechmatics.models import (
    AudioSettings,
    TranscriptionConfig,
    ServerMessageType,
)

async def speechmatics_realtime_transcribe(audio_stream):
    """Speechmatics real-time transcription."""
    api_key = "YOUR_API_KEY"

    transcription_config = TranscriptionConfig(
        language="zh",
        enable_partials=True,
        max_delay=2.0,
    )

    audio_settings = AudioSettings(
        sample_rate=16000,
        encoding="pcm_s16le",
    )

    results = []

    async def on_transcript(message):
        if message["message"] == "AddTranscript":
            transcript = message["metadata"]["transcript"]
            results.append(transcript)
            print(f"Transcript: {transcript}")

    client = WebsocketClient(api_key)

    client.add_event_handler(
        ServerMessageType.AddTranscript,
        on_transcript,
    )

    await client.connect(
        transcription_config=transcription_config,
        audio_settings=audio_settings,
    )

    # 發送音訊資料
    async for chunk in audio_stream:
        await client.send_audio(chunk)

    await client.close()
    return "".join(results)
```

### Python (REST API with httpx)

#### Batch 轉錄

```python
import httpx
import asyncio

async def speechmatics_batch_rest(audio_path: str, language: str = "zh"):
    """Speechmatics batch transcription using REST API."""
    api_key = "YOUR_API_KEY"
    base_url = "https://asr.api.speechmatics.com/v2"

    headers = {"Authorization": f"Bearer {api_key}"}

    config = {
        "type": "transcription",
        "transcription_config": {
            "language": language,
            "enable_entities": True,
        },
    }

    async with httpx.AsyncClient() as client:
        # Step 1: 提交任務
        with open(audio_path, "rb") as f:
            files = {
                "data_file": (audio_path, f, "audio/wav"),
                "config": (None, json.dumps(config), "application/json"),
            }
            response = await client.post(
                f"{base_url}/jobs",
                headers=headers,
                files=files,
            )
            response.raise_for_status()
            job_id = response.json()["id"]

        # Step 2: 等待完成
        while True:
            response = await client.get(
                f"{base_url}/jobs/{job_id}",
                headers=headers,
            )
            status = response.json()["job"]["status"]
            if status == "done":
                break
            elif status == "rejected":
                raise Exception("Job rejected")
            await asyncio.sleep(2)

        # Step 3: 取得結果
        response = await client.get(
            f"{base_url}/jobs/{job_id}/transcript",
            headers=headers,
            params={"format": "txt"},
        )
        return response.text
```

### cURL

#### 提交 Batch 任務

```bash
# 提交轉錄任務
curl -X POST "https://asr.api.speechmatics.com/v2/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "data_file=@audio.wav" \
  -F 'config={
    "type": "transcription",
    "transcription_config": {
      "language": "zh"
    }
  };type=application/json'

# 回應範例：{"id": "job_abc123"}
```

#### 查詢任務狀態

```bash
curl "https://asr.api.speechmatics.com/v2/jobs/job_abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 取得轉錄結果

```bash
# JSON 格式（含時間戳記）
curl "https://asr.api.speechmatics.com/v2/jobs/job_abc123/transcript?format=json-v2" \
  -H "Authorization: Bearer YOUR_API_KEY"

# 純文字格式
curl "https://asr.api.speechmatics.com/v2/jobs/job_abc123/transcript?format=txt" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 支援語言

### 主要語言

| 語言代碼 | 語言 | 說明 |
|----------|------|------|
| `zh` | 中文（普通話） | 簡體/繁體自動偵測 |
| `yue` | 粵語 | 廣東話 |
| `en` | 英語 | 多口音支援 |
| `ja` | 日語 | |
| `ko` | 韓語 | |

### 取得完整語言列表

```bash
curl "https://asr.api.speechmatics.com/v2/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  --head
```

或參考 [官方文檔](https://docs.speechmatics.com/introduction/supported-languages)

## 轉錄設定選項

### transcription_config

| 參數 | 類型 | 說明 |
|------|------|------|
| `language` | string | 語言代碼（必填） |
| `enable_partials` | boolean | 啟用部分結果（Real-Time） |
| `enable_entities` | boolean | 啟用實體辨識（日期、數字等） |
| `max_delay` | float | 最大延遲秒數（Real-Time） |
| `operating_point` | string | `standard` 或 `enhanced`（精度） |
| `diarization` | string | 說話者分離：`none`、`speaker` |
| `punctuation_overrides` | object | 標點符號設定 |

### 範例設定

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "zh",
    "enable_entities": true,
    "operating_point": "enhanced",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "max_speakers": 4
    },
    "punctuation_overrides": {
      "permitted_marks": [".", ",", "?", "!"]
    }
  }
}
```

## 輸出格式

### JSON-v2 格式（推薦）

```json
{
  "job": {
    "id": "job_abc123",
    "status": "done"
  },
  "results": [
    {
      "type": "word",
      "start_time": 0.24,
      "end_time": 0.56,
      "alternatives": [
        {"content": "你好", "confidence": 0.98}
      ]
    }
  ]
}
```

### 輸出格式選項

| 格式 | 說明 |
|------|------|
| `json-v2` | 完整 JSON，含時間戳記和信心度 |
| `txt` | 純文字 |
| `srt` | SRT 字幕格式 |

## 定價方案

| 方案 | 價格 | 特色 |
|------|------|------|
| **Pay As You Go** | $0.60 USD/小時 | Batch API |
| **Real-Time** | $1.20 USD/小時 | WebSocket 串流 |
| **Enterprise** | 聯繫銷售 | 客製化、SLA |

> 定價可能因語言和功能而異，請參考 [官方定價頁面](https://www.speechmatics.com/pricing)

## 配額與限制

| 限制項目 | Batch API | Real-Time API |
|----------|-----------|---------------|
| 單檔最大大小 | 1 GB | N/A |
| 單檔最大時長 | 10 小時 | N/A |
| 並行任務數 | 依方案 | 依方案 |
| 支援音訊格式 | WAV, MP3, FLAC, OGG, M4A | PCM, OPUS |

## 音訊要求

### Batch API

| 參數 | 建議值 |
|------|--------|
| 格式 | WAV, MP3, FLAC |
| 取樣率 | 16kHz 以上 |
| 聲道 | 單聲道（建議） |

### Real-Time API

| 參數 | 支援值 |
|------|--------|
| 編碼 | `pcm_s16le`, `pcm_f32le`, `mulaw`, `opus` |
| 取樣率 | 8000, 16000, 44100, 48000 Hz |
| 聲道 | 1（單聲道） |

## 進階功能

### 說話者分離（Diarization）

自動識別不同說話者：

```json
{
  "transcription_config": {
    "language": "zh",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "max_speakers": 4
    }
  }
}
```

### 自訂詞彙（Custom Dictionary）

提高特定詞彙辨識率：

```json
{
  "transcription_config": {
    "language": "zh",
    "additional_vocab": [
      {"content": "Speechmatics", "sounds_like": ["史比馬提克斯"]},
      {"content": "API"},
      {"content": "語音辨識"}
    ]
  }
}
```

### 實體辨識（Entity Detection）

自動偵測日期、時間、數字等：

```json
{
  "transcription_config": {
    "language": "zh",
    "enable_entities": true
  }
}
```

## 故障排除

### 常見錯誤

| 錯誤代碼 | 說明 | 解決方案 |
|----------|------|----------|
| `401` | 認證失敗 | 檢查 API Key 是否正確 |
| `400` | 請求格式錯誤 | 檢查 config JSON 格式 |
| `413` | 檔案太大 | 壓縮或分割音訊檔案 |
| `429` | 請求過多 | 降低請求頻率 |

### 驗證設定

```bash
# 測試 API Key 是否有效
curl "https://asr.api.speechmatics.com/v2/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY"

# 成功會返回任務列表（可能為空）
```

### 檢查任務狀態

```bash
# 列出所有任務
curl "https://asr.api.speechmatics.com/v2/jobs?limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  | jq '.jobs[] | {id, status, created_at}'
```

## 與其他 STT 服務比較

| 特色 | Speechmatics | Google STT | Azure STT |
|------|--------------|------------|-----------|
| 中文支援 | 優秀 | 優秀 | 優秀 |
| 口音處理 | 極佳 | 良好 | 良好 |
| 說話者分離 | 內建 | 需額外設定 | 需額外設定 |
| 自訂詞彙 | 簡單 | 複雜 | 中等 |
| 定價 | 中等 | 較低 | 較低 |

## 相關資源

- [Speechmatics 官網](https://www.speechmatics.com/)
- [API 文檔](https://docs.speechmatics.com/)
- [Python SDK](https://github.com/speechmatics/speechmatics-python)
- [Portal 管理介面](https://portal.speechmatics.com/)
- [定價資訊](https://www.speechmatics.com/pricing)
- [支援語言列表](https://docs.speechmatics.com/introduction/supported-languages)

---

*Last updated: 2026-01-20*
