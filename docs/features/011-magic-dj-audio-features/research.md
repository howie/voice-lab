# Research: Magic DJ Audio Features Enhancement

**Date**: 2026-01-29
**Feature**: 011-magic-dj-audio-features

## Overview

本功能已有詳細技術規格文件（`docs/features/010-magic-dj-controller/011-audio-features-spec.md`），技術決策已明確，無需額外研究。

## Key Decisions Summary

### 1. 音檔儲存策略 (Phase 1-2)

**Decision**: 使用 localStorage + base64 編碼

**Rationale**:
- localStorage 為瀏覽器原生 API，無需額外依賴
- Zustand persist middleware 已整合 localStorage
- Phase 3 會遷移到後端，無需在 Phase 1-2 過度投資

**Alternatives Rejected**:
| Alternative | Reason |
|-------------|--------|
| IndexedDB | 複雜度高，Phase 3 會改用後端 |
| Service Worker Cache | 過度工程，不適合音檔儲存 |
| WebSQL | 已棄用，不建議使用 |

**Implications**:
- 儲存空間限制 5-10MB
- base64 編碼增加 ~33% 資料大小
- 需處理儲存空間不足的錯誤情況

---

### 2. 音量控制實作方式

**Decision**: 使用 Web Audio API GainNode

**Rationale**:
- 現有 `useMultiTrackPlayer` hook 已使用 Web Audio API
- GainNode 支援精確的音量控制（0.0 - 1.0 浮點數）
- 支援即時調整，無需重新載入音訊

**Alternatives Rejected**:
| Alternative | Reason |
|-------------|--------|
| HTML5 Audio volume | 無法精確控制多軌同時播放 |
| CSS Audio filters | 瀏覽器支援度不一 |

**Implications**:
- 每個音軌需獨立的 GainNode
- Master volume 透過獨立的 GainNode 實現
- 音量調整響應時間 <500ms

---

### 3. 衝突處理策略 (Phase 3)

**Decision**: Last-write-wins（最後寫入者勝出）

**Rationale**:
- 簡單可靠，實作成本低
- 符合單使用者多裝置的使用場景
- 研究人員通常不會同時在兩台裝置編輯

**Alternatives Rejected**:
| Alternative | Reason |
|-------------|--------|
| CRDT | 過度工程，複雜度高 |
| Operational Transform | 實作複雜，不適合此場景 |
| 手動合併 | 使用者體驗差 |

**Implications**:
- 可能遺失同時編輯的資料
- 建議在 UI 顯示「最後儲存時間」提示

---

### 4. 雲端儲存方案 (Phase 3)

**Decision**: Google Cloud Storage (GCS) + Signed URL

**Rationale**:
- 專案已使用 GCP 基礎設施
- Signed URL 提供安全的臨時存取
- 支援大檔案上傳（遠超 localStorage 限制）

**Alternatives Rejected**:
| Alternative | Reason |
|-------------|--------|
| AWS S3 | 專案已使用 GCP |
| Azure Blob | 專案已使用 GCP |
| Firebase Storage | 額外依賴，GCS 足夠 |
| 直接存資料庫 | 不適合大型二進位檔案 |

**Implications**:
- 需設定 GCS bucket 和 CORS
- Signed URL 有時效性（建議 1 小時）
- 需處理 URL 過期後的重新獲取邏輯

---

### 5. API 設計風格 (Phase 3)

**Decision**: RESTful API，遵循現有 voice-lab 模式

**Rationale**:
- 與現有 API（/tts, /stt, /voices）一致
- 團隊熟悉 REST 模式
- FastAPI 原生支援

**Alternatives Rejected**:
| Alternative | Reason |
|-------------|--------|
| GraphQL | 過度工程，此功能查詢需求簡單 |
| gRPC | 前端整合複雜度高 |

**Implications**:
- 遵循 `/api/v1/dj/` 路徑前綴
- 使用標準 HTTP 動詞（GET, POST, PUT, DELETE）
- 回傳 JSON 格式

---

## Technology Validation

### 瀏覽器相容性

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Web Audio API | ✅ | ✅ | ✅ | ✅ |
| Drag and Drop API | ✅ | ✅ | ✅ | ✅ |
| File API | ✅ | ✅ | ✅ | ✅ |
| localStorage | ✅ | ✅ | ✅ | ✅ |

### 效能基準

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| 上傳 10MB 檔案 | <30s | 手動測試 |
| 音量調整響應 | <500ms | 自動化測試 |
| 頁面載入（含 5 音軌） | <3s | Lighthouse |
| 同時播放 5 軌 | 無卡頓 | 手動測試 |

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| 同時播放上限？ | 5 個音軌（Clarification Session 2026-01-29） |
| 衝突處理策略？ | Last-write-wins（Clarification Session 2026-01-29） |
| 儲存空間不足處理？ | 阻止上傳並顯示錯誤（Clarification Session 2026-01-29） |

---

## References

- [Web Audio API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [HTML Drag and Drop API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)
- [GCS Signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls)
- [Zustand Persist Middleware](https://docs.pmnd.rs/zustand/integrations/persisting-store-data)
