# Long Text TTS Timeout / Network Error 分析與改善計畫

## 問題描述

使用者在 production 環境透過 Gemini TTS 合成較長文字時，遭遇 "Network Error"。

---

## 1. 根因分析 (Root Cause Analysis)

### 事件紀錄

| 時間 (UTC) | 端點 | 狀態 | 延遲 | 請求大小 |
|---|---|---|---|---|
| 2026-02-11 08:51:17 | `POST /api/v1/tts/synthesize` | **500** | **180.02s** | 2,327 bytes |

- Cloud Run service: `voice-lab-backend` (revision `00102-kzg`)
- Cloud Run request timeout: **300s**
- Gemini httpx client timeout: **180s**
- 延遲 180.02s 精準匹配 httpx client timeout 設定

### 錯誤傳播鏈

```
Gemini API 回應超過 180s
  → httpx.ReadTimeout("") 拋出 (空字串訊息)
    → synthesize_speech.py:97 — "timeout" in "".lower() → False ❌ (偵測失敗!)
      → SynthesisError(status_code=500) 而非 ProviderError(status_code=503)
        → tts.py:199 — HTTPException(500, "Speech synthesis failed: ")
          → 前端收到 500 + 近乎空白的錯誤訊息
```

### 三個核心問題

#### 問題 1: httpx TimeoutException 偵測邏輯有 Bug

**檔案**: `backend/src/application/use_cases/synthesize_speech.py:96-98`

```python
error_msg = str(e)  # httpx.ReadTimeout("") → ""
if "unavailable" in error_msg.lower() or "timeout" in error_msg.lower():
    raise ProviderError(...)  # ← 永遠不會進入!
raise SynthesisError(...)  # ← 所有 timeout 都走這裡
```

`httpx.ReadTimeout` 的 `str()` 輸出為空字串或 `"Timed out"`，都**不包含** `"timeout"` 子字串:

| 例外類別 | `str(e)` | `"timeout" in str(e).lower()` |
|---|---|---|
| `ReadTimeout("")` | `""` | `False` |
| `ReadTimeout("Timed out")` | `"Timed out"` | `False` |

結果：timeout 錯誤被誤分類為 `SynthesisError (500)` 而非 `ProviderError (503)`。

#### 問題 2: Gemini Pro TTS 模型對長文本延遲過高

`gemini-2.5-pro-preview-tts` 在處理接近 4000 bytes 上限的文字時，回應時間可能超過 180 秒。同一時段的其他請求 (`48.66s`) 使用相同模型但較短文本時能正常完成。

#### 問題 3: 前端沒有 request timeout 保護

**檔案**: `frontend/src/lib/api.ts:15-20`

```typescript
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  // ❌ 沒有設定 timeout
})
```

Axios 預設 timeout 為 0 (無限等待)，使用者需等待整整 180 秒才看到錯誤。

---

## 2. 相關環境設定

| 層級 | 設定 | 值 |
|---|---|---|
| Cloud Run | request timeout | 300s |
| Cloud Run | memory | 512Mi |
| Cloud Run | CPU | 1 (cpu_idle=true) |
| Gemini httpx | client timeout | 180s |
| ElevenLabs httpx | client timeout | 60s |
| VoAI httpx | client timeout | 60s |
| Axios (前端) | timeout | 0 (無限) |
| Gemini API | 輸入上限 | 4000 bytes |
| provider_limits | max_text_length | 4000 (字元，非 byte) |

---

## 3. 改善計畫

### Phase 1: 修正超時偵測邏輯 (Critical)

**檔案**: `backend/src/application/use_cases/synthesize_speech.py`

**目標**: 正確識別 httpx timeout 例外，回傳 503 而非 500。

**方案**: 用 `isinstance()` 檢查取代字串匹配。

```python
import httpx

except QuotaExceededError:
    raise
except httpx.TimeoutException as e:
    # 明確捕捉 timeout，轉為 ProviderError (503)
    error_msg = f"Request timed out after waiting for response ({type(e).__name__})"
    if self.logger:
        await self.logger.log_synthesis(request=request, result=None, error=error_msg, user_id=user_id)
    raise ProviderError(request.provider, error_msg) from e
except Exception as e:
    # ... 現有邏輯
```

**影響範圍**: 所有 TTS provider 的 timeout 錯誤都會被正確分類。

### Phase 2: 前端 timeout 與 UX 改善

#### 2a. Axios 設定 request timeout

**檔案**: `frontend/src/lib/api.ts`

```typescript
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120_000, // 120 秒，比後端 180s 短以提供更好的 UX
})
```

#### 2b. TTS 合成增加 AbortController + 進度回饋

**檔案**: `frontend/src/stores/ttsStore.ts`

- 增加 `AbortController` 支援取消請求
- 合成期間顯示經過時間 (elapsed time)
- 超過 30 秒顯示「長文本可能需要較長時間」提示

#### 2c. 改善錯誤訊息

針對 503 `PROVIDER_ERROR` 回應，顯示:
- 提供者暫時無回應的中文訊息
- 建議重試時間
- 替代 provider 建議

### Phase 3: 長文本智慧處理

#### 3a. provider_limits 字元/位元組驗證對齊

**檔案**: `backend/src/domain/config/provider_limits.py`

**問題**: `validate_text_length` 用字元數比對 `max_text_length=4000`，但 Gemini 限制是 **4000 bytes**。中文字 3 bytes/字元，4000 字元 = 12000 bytes，遠超 Gemini 限制。

**方案**: 為 Gemini 增加 byte-level 驗證，或將 `max_text_length` 改為 ~1333 (4000/3)。

```python
"gemini": ProviderLimits(
    provider_id="gemini",
    max_text_length=1300,  # ~4000 bytes / 3 bytes per CJK char (保守值)
    recommended_max_length=800,  # 建議長度，減少 timeout 風險
    warning_message="較長的中文文本可能導致 Gemini TTS 處理時間增加",
),
```

#### 3b. 長文本自動分段合成 (Optional, 較大工程)

對超過建議長度的文本，自動按句子分段合成後拼接:
- 利用 NLTK 或正則表達式按句子分段
- 逐段合成 + pydub 拼接
- 提供逐段串流回饋

### Phase 4: 監控與可觀測性

#### 4a. 增加 timeout 專用日誌

在 Gemini provider 增加 timeout 情境的結構化日誌:
```python
logger.warning(
    "Gemini TTS timeout: model=%s, text_bytes=%d, text_chars=%d, timeout=%ds",
    self._model, byte_length, char_length, 180,
)
```

#### 4b. 考慮 Gemini Flash 作為 fallback

`gemini-2.5-flash-preview-tts` 延遲較低，可作為 Pro 模型超時的 fallback:
- 第一次嘗試 Pro 模型 (設 90s timeout)
- 超時後自動 fallback 到 Flash 模型
- 通知使用者已切換至快速模型

---

## 4. 優先順序

| 優先級 | 項目 | 預估工作量 | 影響 |
|---|---|---|---|
| P0 | Phase 1: 修正 timeout 偵測 bug | 0.5h | 正確的 HTTP 狀態碼和錯誤訊息 |
| P1 | Phase 2a: 前端 timeout 設定 | 0.5h | 使用者不再無限等待 |
| P1 | Phase 3a: 字元/位元組驗證對齊 | 1h | 前置攔截過長文本 |
| P2 | Phase 2b: AbortController + UX | 2h | 可取消 + 進度提示 |
| P2 | Phase 2c: 改善錯誤訊息 | 1h | 更好的使用者體驗 |
| P2 | Phase 4a: timeout 日誌 | 0.5h | 更好的可觀測性 |
| P3 | Phase 3b: 長文本分段合成 | 4-6h | 支援超長文本 |
| P3 | Phase 4b: Flash fallback | 2-3h | 自動降級提高可用性 |

---

## 5. 受影響的檔案清單

| 檔案 | 修改類型 |
|---|---|
| `backend/src/application/use_cases/synthesize_speech.py` | 修正 timeout 偵測 |
| `backend/src/domain/config/provider_limits.py` | Gemini 字元上限調整 |
| `backend/src/infrastructure/providers/tts/gemini_tts.py` | timeout 日誌 |
| `frontend/src/lib/api.ts` | 增加 axios timeout |
| `frontend/src/stores/ttsStore.ts` | AbortController + UX |
