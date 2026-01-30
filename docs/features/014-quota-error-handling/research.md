# Research: API Quota Error Handling

**Feature**: 014-quota-error-handling | **Date**: 2026-01-30

## Research Tasks

### 1. 各供應商 429 錯誤格式研究

#### Gemini (Google AI)

**Decision**: 偵測 HTTP 429 狀態碼 + 錯誤訊息中的 `exceeded your current quota`

**Rationale**:
- Gemini API 在配額超限時返回 HTTP 429
- 錯誤訊息格式：`You exceeded your current quota, please check your plan and billing details`
- 提供 `Retry-After` header（不一定）
- 官方文檔連結：https://ai.google.dev/gemini-api/docs/rate-limits

**Alternatives considered**:
- 僅靠狀態碼判斷 - 被拒絕，因為 429 也可能是速率限制而非配額超限

#### ElevenLabs

**Decision**: 偵測 HTTP 429 + JSON 回應中的 `quota_exceeded` 或 `character_limit_exceeded`

**Rationale**:
- ElevenLabs 返回結構化 JSON 錯誤
- 錯誤格式範例：`{"detail": {"status": "quota_exceeded", "message": "..."}}`
- 區分字元配額和請求配額
- 官方頁面：https://elevenlabs.io/usage

**Alternatives considered**:
- 僅解析訊息字串 - 被拒絕，因為結構化欄位更可靠

#### Azure Cognitive Services

**Decision**: 偵測 HTTP 429 + `error.code` 為 `RateLimitExceeded` 或 `QuotaExceeded`

**Rationale**:
- Azure 使用標準 REST 錯誤格式
- 同時支援 TTS 和 STT 服務
- 提供 `Retry-After` header
- 官方文檔：https://learn.microsoft.com/azure/cognitive-services/speech-service/speech-services-quotas-and-limits

**Alternatives considered**:
- 使用 SDK 例外 - 被拒絕，因為當前實作使用 REST API

#### GCP (Google Cloud TTS/STT)

**Decision**: 偵測 gRPC status `RESOURCE_EXHAUSTED` (14) 或 HTTP 429

**Rationale**:
- GCP 可能用 gRPC 或 REST
- gRPC 錯誤碼 14 表示配額超限
- HTTP 回應包含 `error.status: "RESOURCE_EXHAUSTED"`
- 官方文檔：https://cloud.google.com/speech-to-text/quotas

**Alternatives considered**:
- 僅處理 gRPC - 被拒絕，因為需要同時支援兩種協定

#### OpenAI (Whisper)

**Decision**: 偵測 HTTP 429 + `error.type` 為 `rate_limit_exceeded`

**Rationale**:
- OpenAI 使用標準 REST API
- JSON 格式：`{"error": {"type": "rate_limit_exceeded", "message": "..."}}`
- 區分 RPM (requests per minute) 和 TPM (tokens per minute)
- 官方文檔：https://platform.openai.com/docs/guides/rate-limits

**Alternatives considered**:
- 使用 openai SDK 內建處理 - 保留為未來選項

#### Deepgram

**Decision**: 偵測 HTTP 429 + `err_code: "QUOTA_EXCEEDED"`

**Rationale**:
- Deepgram 返回 JSON 錯誤格式
- 官方 SDK 也會拋出相關例外
- 官方文檔：https://developers.deepgram.com/docs/rate-limits

**Alternatives considered**:
- 依賴 SDK 例外 - 採用，但需要額外 fallback

#### VoAI

**Decision**: 偵測 HTTP 429 + JSON 回應中的 `quota_exceeded` 或類似錯誤訊息

**Rationale**:
- VoAI 使用 REST API (https://connect.voai.ai/TTS/)
- 預期錯誤格式類似其他 REST API 供應商
- 官方平台：https://voai.ai

**Alternatives considered**:
- 無其他方案，VoAI 為台灣本地供應商，需實際測試確認錯誤格式

---

### 2. 現有錯誤處理架構分析

**Decision**: 新增 `QuotaExceededError` 類別繼承 `AppError`

**Rationale**:
- 現有 `domain/errors.py` 已有完整的錯誤架構
- `ErrorCode.QUOTA_EXCEEDED` 已定義但未使用
- 現有 `RateLimitError` 用於應用層速率限制，不同於供應商配額
- 需要額外欄位：`provider`、`provider_display_name`、`help_url`、`suggestions`

**Alternatives considered**:
- 擴展 `RateLimitError` - 被拒絕，因為語意不同且需要不同欄位
- 擴展 `ProviderError` - 被拒絕，因為狀態碼應為 429 而非 503

---

### 3. 前端錯誤顯示最佳實踐

**Decision**: 擴展現有 `ErrorDisplay` 元件，新增 `quota` 錯誤類別

**Rationale**:
- 現有元件已有分類顯示邏輯
- 配額錯誤需要：
  - 明確的供應商標識
  - 中文友善訊息
  - 可點擊的幫助連結
  - 建議的替代方案
  - 可選的重試倒數

**Alternatives considered**:
- 建立獨立 `QuotaErrorDisplay` 元件 - 被拒絕，增加不必要的複雜度

---

### 4. retry-after 處理策略

**Decision**: 解析 HTTP `Retry-After` header，前端顯示倒數

**Rationale**:
- 標準 HTTP header，多數供應商支援
- 可以是秒數（3600）或日期時間
- 前端可選顯示「約 X 分鐘後可重試」

**Implementation**:
```python
# Backend: 解析 Retry-After header
retry_after = response.headers.get("Retry-After")
if retry_after:
    if retry_after.isdigit():
        seconds = int(retry_after)
    else:
        # RFC 7231 date format
        retry_date = parse_http_date(retry_after)
        seconds = max(0, (retry_date - datetime.now()).total_seconds())
```

**Alternatives considered**:
- 固定預設值 - 作為 fallback 使用

---

### 5. 供應商特定建議內容

**Decision**: 預定義各供應商的中文建議列表和幫助連結

**Rationale**:
- 每個供應商有不同的配額頁面和升級方式
- 中文化的具體建議更有幫助

**Content**:

| Provider | 幫助連結 | 建議 |
|----------|---------|------|
| Gemini | https://ai.google.dev/pricing | 1. 檢查 Google AI Studio 用量 2. 升級付費方案 3. 切換其他供應商 |
| ElevenLabs | https://elevenlabs.io/subscription | 1. 檢查 ElevenLabs 用量 2. 購買額外字元 3. 切換其他供應商 |
| Azure | https://portal.azure.com | 1. 檢查 Azure Portal 用量 2. 升級服務層級 3. 切換其他供應商 |
| GCP | https://console.cloud.google.com/apis | 1. 檢查 GCP Console 用量 2. 增加配額限制 3. 切換其他供應商 |
| OpenAI | https://platform.openai.com/usage | 1. 檢查 OpenAI 用量 2. 升級方案 3. 切換其他供應商 |
| Deepgram | https://console.deepgram.com | 1. 檢查 Deepgram Console 用量 2. 升級方案 3. 切換其他供應商 |

---

## Summary

所有研究任務已完成，無待釐清項目。可進入 Phase 1 設計階段。
