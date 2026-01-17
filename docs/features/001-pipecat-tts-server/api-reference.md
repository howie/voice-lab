# API Reference: Pipecat TTS Server

**Version**: 1.0.0
**Base URL**: `/api/v1`

本文件描述 Voice Lab TTS 伺服器的完整 API 端點規格。

---

## 認證

所有 API 端點（除健康檢查和認證端點外）都需要 JWT Bearer Token：

```
Authorization: Bearer <jwt_token>
```

### 取得 Token

1. 導向至 `GET /auth/google` 啟動 Google OAuth 流程
2. 完成 Google 登入後，Token 會在回調中返回

---

## 端點總覽

| 方法 | 端點 | 說明 |
|------|------|------|
| **認證** | | |
| GET | `/auth/google` | 啟動 Google OAuth 登入 |
| GET | `/auth/google/callback` | OAuth 回調處理 |
| GET | `/auth/me` | 取得當前用戶資訊 |
| POST | `/auth/logout` | 登出 |
| **TTS 合成** | | |
| POST | `/tts/synthesize` | 批次語音合成 |
| POST | `/tts/stream` | 串流語音合成 |
| **語音管理** | | |
| GET | `/voices` | 列出所有可用語音 |
| GET | `/voices/{provider}` | 列出特定提供者的語音 |
| GET | `/voices/{provider}/{voice_id}` | 取得語音詳細資訊 |
| **提供者** | | |
| GET | `/providers` | 列出所有 TTS 提供者 |
| GET | `/providers/{provider}/health` | 檢查提供者健康狀態 |
| **系統** | | |
| GET | `/health` | 系統健康檢查 |
| GET | `/health/ready` | 就緒檢查 |

---

## TTS 合成 API

### POST /tts/synthesize

批次模式語音合成，等待完整音訊生成後返回。

#### 請求

```json
{
  "text": "要合成的文字內容",
  "provider": "azure",
  "voice_id": "zh-TW-HsiaoChenNeural",
  "language": "zh-TW",
  "speed": 1.0,
  "pitch": 0,
  "volume": 1.0,
  "output_format": "mp3"
}
```

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `text` | string | 是 | 要合成的文字（最大 5000 字元） |
| `provider` | string | 是 | 提供者：`azure`, `gcp`, `elevenlabs`, `voai` |
| `voice_id` | string | 是 | 語音 ID（依提供者不同） |
| `language` | string | 否 | 語言代碼，預設 `zh-TW` |
| `speed` | float | 否 | 語速 0.5-2.0，預設 1.0 |
| `pitch` | float | 否 | 音調 -20 到 +20，預設 0 |
| `volume` | float | 否 | 音量 0.0-2.0，預設 1.0 |
| `output_format` | string | 否 | 格式：`mp3`, `wav`, `ogg`，預設 `mp3` |

#### 回應

**成功 (200)**

```json
{
  "audio_content": "base64_encoded_audio_data",
  "content_type": "audio/mpeg",
  "duration_ms": 3500,
  "latency_ms": 450,
  "ttfb_ms": 120,
  "storage_path": "storage/azure/abc123.mp3"
}
```

#### 回應標頭

| 標頭 | 說明 |
|------|------|
| `X-Synthesis-Duration-Ms` | 音訊時長（毫秒） |
| `X-Synthesis-Latency-Ms` | 合成延遲（毫秒） |
| `X-Synthesis-TTFB-Ms` | 首字節時間（毫秒） |
| `X-RateLimit-Remaining-Minute` | 每分鐘剩餘請求數 |
| `X-RateLimit-Remaining-Hour` | 每小時剩餘請求數 |

---

### POST /tts/stream

串流模式語音合成，立即開始返回音訊資料。

#### 請求

與 `/tts/synthesize` 相同。

#### 回應

返回 `audio/mpeg` 串流資料，使用 chunked transfer encoding。

---

## 語音管理 API

### GET /voices

列出所有可用語音，支援過濾。

#### 查詢參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `provider` | string | 按提供者過濾 |
| `language` | string | 按語言過濾 |
| `gender` | string | 按性別過濾：`male`, `female` |
| `limit` | int | 返回數量限制（預設 100） |
| `offset` | int | 分頁偏移 |

#### 回應 (200)

```json
{
  "voices": [
    {
      "id": "zh-TW-HsiaoChenNeural",
      "name": "HsiaoChen",
      "provider": "azure",
      "language": "zh-TW",
      "gender": "female",
      "styles": ["cheerful", "sad", "angry"]
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

---

### GET /voices/{provider}

列出特定提供者的語音。

#### 路徑參數

| 參數 | 說明 |
|------|------|
| `provider` | 提供者名稱 |

---

### GET /voices/{provider}/{voice_id}

取得特定語音的詳細資訊。

#### 回應 (200)

```json
{
  "id": "zh-TW-HsiaoChenNeural",
  "name": "HsiaoChen",
  "provider": "azure",
  "language": "zh-TW",
  "gender": "female",
  "styles": ["cheerful", "sad", "angry"],
  "sample_audio_url": "https://..."
}
```

---

## 提供者 API

### GET /providers

列出所有已設定的 TTS 提供者。

#### 回應 (200)

```json
{
  "providers": [
    {
      "id": "azure",
      "name": "Microsoft Azure Speech",
      "enabled": true,
      "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
      "supported_params": {
        "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
        "pitch": {"min": -20, "max": 20, "default": 0},
        "volume": {"min": 0.0, "max": 2.0, "default": 1.0}
      }
    }
  ]
}
```

---

### GET /providers/{provider}/health

檢查特定提供者的健康狀態。

#### 回應 (200)

```json
{
  "provider": "azure",
  "status": "healthy",
  "latency_ms": 45,
  "last_checked": "2026-01-17T00:00:00Z"
}
```

---

## 錯誤回應

所有錯誤回應遵循統一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "人類可讀的錯誤訊息",
    "details": {
      "field": "額外資訊"
    },
    "request_id": "uuid-v4"
  }
}
```

### 錯誤代碼

| 代碼 | HTTP 狀態 | 說明 |
|------|-----------|------|
| `VALIDATION_ERROR` | 400 | 請求參數驗證失敗 |
| `TEXT_EMPTY` | 400 | 文字內容為空 |
| `TEXT_TOO_LONG` | 400 | 文字超過長度限制 |
| `INVALID_PROVIDER` | 400 | 無效的提供者 |
| `INVALID_VOICE_ID` | 400 | 無效的語音 ID |
| `AUTHENTICATION_REQUIRED` | 401 | 需要認證 |
| `TOKEN_EXPIRED` | 401 | Token 已過期 |
| `FORBIDDEN` | 403 | 無權限存取 |
| `VOICE_NOT_FOUND` | 404 | 語音不存在 |
| `RATE_LIMIT_EXCEEDED` | 429 | 超過速率限制 |
| `PROVIDER_ERROR` | 503 | 提供者暫時不可用 |
| `SERVICE_UNAVAILABLE` | 503 | 服務暫時不可用 |

### 提供者錯誤的重試建議

當提供者暫時不可用時，回應會包含重試建議：

```json
{
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "Provider 'azure' is temporarily unavailable",
    "details": {
      "provider": "azure",
      "retry_after_seconds": 5,
      "alternative_providers": ["gcp", "elevenlabs"],
      "suggestion": "Please retry after 5 seconds or try alternative providers: gcp, elevenlabs"
    }
  }
}
```

---

## 速率限制

API 實施以下速率限制：

| 端點類型 | 每分鐘限制 | 每小時限制 |
|----------|------------|------------|
| 一般端點 | 60 | 1000 |
| TTS 合成端點 | 20 | 200 |

超過限制時返回 429 狀態碼，`Retry-After` 標頭指示等待秒數。

---

## 支援的語言

| 代碼 | 語言 | 提供者支援 |
|------|------|------------|
| `zh-TW` | 繁體中文（台灣） | Azure, GCP, ElevenLabs, VoAI |
| `zh-CN` | 簡體中文（中國） | Azure, GCP, ElevenLabs |
| `en-US` | 英文（美國） | Azure, GCP, ElevenLabs, VoAI |
| `ja-JP` | 日文 | Azure, GCP, ElevenLabs |
| `ko-KR` | 韓文 | Azure, GCP, ElevenLabs |

---

## SDK 範例

### Python

```python
import httpx

async def synthesize(text: str, provider: str = "azure"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/tts/synthesize",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "text": text,
                "provider": provider,
                "voice_id": "zh-TW-HsiaoChenNeural",
            },
        )
        return response.json()
```

### TypeScript

```typescript
async function synthesize(text: string, provider = 'azure') {
  const response = await fetch('/api/v1/tts/synthesize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      text,
      provider,
      voice_id: 'zh-TW-HsiaoChenNeural',
    }),
  });
  return response.json();
}
```
