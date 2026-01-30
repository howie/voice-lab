# Quickstart: API Quota Error Handling

**Feature**: 014-quota-error-handling | **Date**: 2026-01-30

## Overview

本功能統一處理各 API 供應商的配額超限錯誤 (HTTP 429)，提供使用者友善的中文錯誤訊息和可行的解決建議。

## 功能特點

- **統一識別**: 識別 7 個供應商 (Gemini, ElevenLabs, Azure, GCP, OpenAI, Deepgram, VoAI) 的 429 配額錯誤
- **友善訊息**: 中文化、易懂的錯誤說明
- **明確來源**: 清楚標示是哪個 API 供應商的配額問題
- **可行建議**: 提供具體的解決步驟和供應商用量頁面連結
- **重試指引**: 顯示建議的重試等待時間

## 使用方式

### Backend: 拋出 QuotaExceededError

```python
from src.domain.errors import QuotaExceededError

# 在 TTS/STT provider 中捕獲 429 錯誤後
if response.status_code == 429:
    raise QuotaExceededError(
        provider="gemini",
        provider_display_name="Gemini TTS",
        quota_type="daily_requests",
        retry_after=3600,
    )
```

### Backend: 錯誤自動處理

`QuotaExceededError` 會被 `error_handler.py` 自動捕獲並轉換為標準 JSON 回應：

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Gemini TTS API 配額已用盡",
    "details": {
      "provider": "gemini",
      "provider_display_name": "Gemini TTS",
      "retry_after": 3600,
      "quota_type": "daily_requests",
      "help_url": "https://ai.google.dev/pricing",
      "suggestions": [
        "檢查您的 Google AI Studio 用量統計",
        "考慮升級至付費方案",
        "暫時切換到其他 TTS 供應商"
      ]
    },
    "request_id": "uuid"
  }
}
```

### Frontend: 顯示錯誤

`ErrorDisplay` 元件會自動識別並顯示配額錯誤：

```tsx
import { ErrorDisplay } from '@/components/multi-role-tts/ErrorDisplay'

function MyComponent() {
  const [error, setError] = useState<string | null>(null)

  return (
    <ErrorDisplay
      error={error}
      onRetry={() => handleRetry()}
      onSwitchProvider={() => handleSwitchProvider()}
    />
  )
}
```

## 支援的供應商

| Provider | 服務類型 | 配額類型 | 幫助連結 |
|----------|---------|---------|---------|
| Gemini | TTS | daily_requests | [Google AI Studio](https://ai.google.dev/pricing) |
| ElevenLabs | TTS | characters | [ElevenLabs](https://elevenlabs.io/subscription) |
| Azure | TTS/STT | requests | [Azure Portal](https://portal.azure.com) |
| GCP | TTS/STT | requests | [GCP Console](https://console.cloud.google.com/apis) |
| OpenAI | STT | tokens | [OpenAI Platform](https://platform.openai.com/usage) |
| Deepgram | STT | audio_minutes | [Deepgram Console](https://console.deepgram.com) |
| VoAI | TTS | requests | [VoAI](https://voai.ai) |

## 錯誤回應範例

### Gemini TTS 配額超限

```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "provider": "gemini", "voice_id": "Kore"}'

# Response (429):
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Gemini TTS API 配額已用盡",
    "details": {
      "provider": "gemini",
      "provider_display_name": "Gemini TTS",
      "retry_after": 3600,
      "help_url": "https://ai.google.dev/pricing",
      "suggestions": [
        "檢查您的 Google AI Studio 用量統計",
        "考慮升級至付費方案",
        "暫時切換到其他 TTS 供應商"
      ]
    }
  }
}
```

## 測試

### 執行單元測試

```bash
# Backend - 79 tests
cd backend
uv run pytest tests/unit/domain/test_quota_errors.py tests/unit/presentation/test_error_handler.py -v

# Frontend - 19 tests
cd frontend
npx vitest run src/lib/__tests__/errorMessages.test.ts
```

### 執行全部檢查

```bash
# Backend linting + type check
cd backend
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src

# Frontend type check
cd frontend
npx tsc --noEmit
```

### 手動測試

1. 使用已達配額的 API key 發送請求
2. 確認回應為 HTTP 429 且格式符合規範
3. 確認 `Retry-After` header 存在
4. 確認前端正確顯示配額錯誤卡片（amber 色調）
5. 確認卡片包含建議列表和幫助連結

## 相關文件

- [規格文件](./spec.md)
- [實作計畫](./plan.md)
- [資料模型](./data-model.md)
- [API Contract](./contracts/error-response.yaml)
