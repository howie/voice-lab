# 014 - API Quota Error Handling

## Overview

統一處理各 API 供應商的配額超限錯誤（HTTP 429），提供使用者友善的錯誤訊息和可行的解決建議。

## Problem Statement

目前專案整合多個 API 供應商（Gemini、ElevenLabs、Azure、GCP 等），當使用者遇到配額超限錯誤時：
- 錯誤訊息技術性太強，使用者難以理解
- 不同供應商的錯誤格式不一致
- 沒有清楚說明是哪個 API 的配額用盡
- 缺乏具體的解決步驟建議

**實際錯誤範例：**
```
Gemini TTS API error (status 429): You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits.
```

## Goals

1. **統一識別** - 識別各供應商的 429 錯誤和配額相關訊息
2. **友善訊息** - 提供中文化、易懂的錯誤說明
3. **明確來源** - 清楚標示是哪個 API 供應商的配額問題
4. **可行建議** - 提供具體的解決步驟和替代方案
5. **重試指引** - 顯示建議的重試等待時間（如有）

## Target Providers

| Provider | API Type | Quota Error Pattern |
|----------|----------|---------------------|
| Gemini | TTS | HTTP 429, `exceeded your current quota` |
| ElevenLabs | TTS | HTTP 429, `quota_exceeded` |
| Azure | TTS/STT | HTTP 429, `RateLimitExceeded` |
| GCP | TTS/STT | HTTP 429, `RESOURCE_EXHAUSTED` |
| OpenAI | STT | HTTP 429, `rate_limit_exceeded` |
| Deepgram | STT | HTTP 429, `QUOTA_EXCEEDED` |
| VoAI | TTS | HTTP 429, `quota_exceeded` |

## User Stories

### US-1: 看到友善的錯誤訊息
> 作為使用者，當 API 配額用盡時，我希望看到清楚的中文說明，知道是哪個服務出了問題。

### US-2: 獲得解決建議
> 作為使用者，當配額超限時，我希望得到具體的解決步驟，例如去哪裡查看用量或升級方案。

### US-3: 知道何時可以重試
> 作為使用者，我希望知道大概要等多久才能再次使用，或是可以切換到其他供應商。

## Technical Requirements

### Backend

1. **新增 `QuotaExceededError` 例外類別**
   - 繼承現有 `AppError`
   - 包含 provider 名稱、retry_after、quota_info
   - 使用 `ErrorCode.QUOTA_EXCEEDED`

2. **Provider 層級 429 偵測**
   - 在各 TTS/STT provider 中捕獲 429 錯誤
   - 解析供應商特定的錯誤格式
   - 提取 retry-after 資訊（如有）

3. **Error Middleware 增強**
   - 處理 `QuotaExceededError`
   - 設定 `Retry-After` HTTP header
   - 回傳結構化的錯誤詳情

### Frontend

1. **ErrorDisplay 元件增強**
   - 新增 quota 錯誤類別樣式
   - 顯示供應商名稱和友善訊息
   - 提供連結到供應商配額頁面

2. **錯誤訊息本地化**
   - 中文化的錯誤標題和說明
   - 供應商特定的建議步驟

## API Response Format

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
      "help_url": "https://ai.google.dev/gemini-api/docs/rate-limits",
      "suggestions": [
        "檢查 Google AI Studio 的用量統計",
        "考慮升級至付費方案",
        "暫時切換到其他 TTS 供應商"
      ]
    },
    "request_id": "uuid"
  }
}
```

## UI Design

### Error Card 樣式

```
┌─────────────────────────────────────────────────┐
│ ⚠️ Gemini TTS 配額已用盡                         │
├─────────────────────────────────────────────────┤
│ 您已達到 Gemini TTS API 的每日使用上限。          │
│                                                 │
│ 💡 建議：                                        │
│ • 檢查您的 Google AI Studio 用量統計             │
│ • 等待約 1 小時後重試                            │
│ • 暫時切換到其他語音合成服務                      │
│                                                 │
│ [查看用量] [切換服務] [稍後重試]                  │
└─────────────────────────────────────────────────┘
```

## Out of Scope

- 自動切換到備用供應商
- 配額使用量的預警通知
- 配額使用歷史追蹤
- 客製化配額限制設定

## Success Metrics

- 使用者能清楚辨識配額錯誤來源
- 錯誤訊息滿意度提升
- 減少配額相關的支援詢問

## Dependencies

- 現有 `domain/errors.py` 錯誤架構
- 現有 `ErrorDisplay.tsx` 元件
- 各供應商 API 的錯誤格式文件
