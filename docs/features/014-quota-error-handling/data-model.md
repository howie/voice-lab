# Data Model: API Quota Error Handling

**Feature**: 014-quota-error-handling | **Date**: 2026-01-30

## Domain Entities

### QuotaExceededError (新增)

繼承自 `AppError`，用於表示 API 供應商配額超限錯誤。

```python
class QuotaExceededError(AppError):
    """API quota exceeded error (429).

    Raised when an API provider reports that the usage quota has been exceeded.
    Provides provider-specific information and actionable suggestions.
    """

    def __init__(
        self,
        provider: str,
        provider_display_name: str,
        quota_type: str | None = None,
        retry_after: int | None = None,
        help_url: str | None = None,
        suggestions: list[str] | None = None,
        original_error: str | None = None,
    ) -> None:
        ...
```

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | `str` | Yes | 供應商識別碼 (e.g., "gemini", "elevenlabs") |
| `provider_display_name` | `str` | Yes | 供應商顯示名稱 (e.g., "Gemini TTS", "ElevenLabs") |
| `quota_type` | `str \| None` | No | 配額類型 (e.g., "daily_requests", "characters", "tokens") |
| `retry_after` | `int \| None` | No | 建議重試等待秒數 |
| `help_url` | `str \| None` | No | 供應商配額/用量頁面連結 |
| `suggestions` | `list[str] \| None` | No | 中文建議列表 |
| `original_error` | `str \| None` | No | 原始 API 錯誤訊息 (用於除錯) |

**Inherited from AppError**:

| Field | Type | Value |
|-------|------|-------|
| `code` | `ErrorCode` | `ErrorCode.QUOTA_EXCEEDED` |
| `message` | `str` | 自動生成的中文訊息 |
| `status_code` | `int` | `429` |
| `details` | `dict` | 包含所有欄位的字典 |

---

### ProviderQuotaInfo (新增常數類別)

定義各供應商的配額相關資訊。

```python
class ProviderQuotaInfo:
    """Provider-specific quota information and suggestions."""

    PROVIDERS: dict[str, dict[str, Any]] = {
        "gemini": {
            "display_name": "Gemini TTS",
            "help_url": "https://ai.google.dev/pricing",
            "default_retry_after": 3600,  # 1 hour
            "suggestions": [
                "檢查您的 Google AI Studio 用量統計",
                "考慮升級至付費方案",
                "暫時切換到其他 TTS 供應商",
            ],
        },
        "elevenlabs": {
            "display_name": "ElevenLabs",
            "help_url": "https://elevenlabs.io/subscription",
            "default_retry_after": 3600,
            "suggestions": [
                "檢查您的 ElevenLabs 用量統計",
                "購買額外的字元配額",
                "暫時切換到其他 TTS 供應商",
            ],
        },
        "azure": {
            "display_name": "Azure Speech",
            "help_url": "https://portal.azure.com",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 Azure Portal 用量統計",
                "考慮升級服務層級",
                "暫時切換到其他語音服務",
            ],
        },
        "gcp": {
            "display_name": "Google Cloud Speech",
            "help_url": "https://console.cloud.google.com/apis",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 GCP Console 配額用量",
                "申請增加配額限制",
                "暫時切換到其他語音服務",
            ],
        },
        "openai": {
            "display_name": "OpenAI Whisper",
            "help_url": "https://platform.openai.com/usage",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 OpenAI 用量統計",
                "考慮升級方案",
                "暫時切換到其他 STT 供應商",
            ],
        },
        "deepgram": {
            "display_name": "Deepgram",
            "help_url": "https://console.deepgram.com",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 Deepgram Console 用量",
                "考慮升級方案",
                "暫時切換到其他 STT 供應商",
            ],
        },
        "voai": {
            "display_name": "VoAI TTS",
            "help_url": "https://voai.ai",
            "default_retry_after": 60,
            "suggestions": [
                "檢查您的 VoAI 帳戶用量",
                "考慮升級方案",
                "暫時切換到其他 TTS 供應商",
            ],
        },
    }

    @classmethod
    def get(cls, provider: str) -> dict[str, Any]:
        """Get quota info for a provider, with fallback defaults."""
        return cls.PROVIDERS.get(provider, {
            "display_name": provider.title(),
            "help_url": None,
            "default_retry_after": 60,
            "suggestions": ["請稍後再試或切換到其他供應商"],
        })
```

---

## API Response Schema

### Quota Error Response

```yaml
# 詳見 contracts/error-response.yaml
QuotaErrorResponse:
  error:
    code: "QUOTA_EXCEEDED"
    message: "Gemini TTS API 配額已用盡"
    details:
      provider: "gemini"
      provider_display_name: "Gemini TTS"
      retry_after: 3600
      quota_type: "daily_requests"
      help_url: "https://ai.google.dev/pricing"
      suggestions:
        - "檢查您的 Google AI Studio 用量統計"
        - "考慮升級至付費方案"
        - "暫時切換到其他 TTS 供應商"
    request_id: "550e8400-e29b-41d4-a716-446655440000"
```

---

## Frontend Types

### TypeScript Interface

```typescript
// frontend/src/lib/error-types.ts

interface QuotaErrorDetails {
  provider: string;
  provider_display_name: string;
  retry_after?: number;
  quota_type?: string;
  help_url?: string;
  suggestions?: string[];
}

interface QuotaError {
  code: 'QUOTA_EXCEEDED';
  message: string;
  details: QuotaErrorDetails;
  request_id?: string;
}

// Type guard
function isQuotaError(error: unknown): error is { error: QuotaError } {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    (error as any).error?.code === 'QUOTA_EXCEEDED'
  );
}
```

---

## State Transitions

此功能不涉及狀態機，錯誤為單次事件。

---

## Validation Rules

1. `provider` 必須為非空字串
2. `retry_after` 若有值必須 >= 0
3. `suggestions` 若有值必須為非空陣列
4. `help_url` 若有值必須為有效 URL 格式

---

## Relationships

```
AppError (base)
    └── QuotaExceededError (new)
            ├── uses → ProviderQuotaInfo (for defaults)
            └── handled by → error_handler.py (middleware)

ErrorDisplay (frontend)
    └── renders → QuotaErrorCard (new pattern in existing component)
```
