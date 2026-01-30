# Research: TTS 角色管理介面

**Feature**: 013-tts-role-mgmt
**Date**: 2026-01-29

## 研究目標

解析功能實作所需的技術決策和最佳實踐。

---

## Decision 1: 資料模型設計

### Decision
建立獨立的 `voice_customization` 表，以 `voice_cache_id` 作為外鍵關聯 `voice_cache` 表。

### Rationale
1. **資料分離**：VoiceCache 儲存從提供者同步的原始資料，VoiceCustomization 儲存使用者自訂設定。同步時不會覆蓋使用者設定。
2. **可擴展性**：未來支援多租戶時，只需在 VoiceCustomization 加入 `user_id` 欄位。
3. **查詢效率**：JOIN 兩表即可取得完整資訊，無需額外處理。

### Alternatives Considered
- **方案 B**: 在 VoiceCache 表新增欄位（custom_name, is_favorite, is_hidden）
  - 拒絕原因：同步時可能覆蓋使用者設定，需要額外處理邏輯
- **方案 C**: 使用 JSON 欄位儲存自訂設定
  - 拒絕原因：無法建立索引，查詢效能較差

---

## Decision 2: API 設計模式

### Decision
採用 RESTful API 設計，以 `voice_cache_id` 作為資源識別：
- `GET /voice-customizations` - 列出所有自訂設定
- `GET /voice-customizations/{voice_cache_id}` - 取得單一設定
- `PUT /voice-customizations/{voice_cache_id}` - 更新設定（upsert 語意）
- `PATCH /voice-customizations/bulk` - 批量更新

### Rationale
1. **語意清晰**：PUT 代表完整替換，PATCH 代表部分更新
2. **Upsert 語意**：PUT 同時支援建立和更新，減少 API 複雜度
3. **批量操作**：支援一次更新多個角色設定，提升使用體驗

### Alternatives Considered
- **方案 B**: 將自訂設定嵌入 `/voices` 端點
  - 拒絕原因：混合資源邏輯，不利於後續維護
- **方案 C**: 每個設定欄位獨立端點（如 `/voices/{id}/favorite`）
  - 拒絕原因：過於細碎，增加前端複雜度

---

## Decision 3: 現有 voices API 整合方式

### Decision
修改 `GET /voices` 端點，回傳時自動合併 customization 資料：
```json
{
  "id": "azure:zh-TW-HsiaoChenNeural",
  "name": "曉臻",
  "display_name": "溫柔女聲",  // 新增: 優先顯示 custom_name，若無則為 name
  "is_favorite": true,          // 新增
  "is_hidden": false,           // 新增
  ...
}
```

### Rationale
1. **向後相容**：原有欄位保留，新增欄位不影響現有消費者
2. **單一資料來源**：前端無需額外 API 呼叫即可取得完整資訊
3. **預設過濾**：加入 `exclude_hidden=true` 參數，預設過濾隱藏角色

### Alternatives Considered
- **方案 B**: 前端分別呼叫 `/voices` 和 `/voice-customizations` 再合併
  - 拒絕原因：增加網路往返，前端邏輯複雜度高

---

## Decision 4: VoiceSelector 元件修改策略

### Decision
在現有 VoiceSelector 元件中加入以下邏輯：
1. 呼叫 API 時預設帶入 `exclude_hidden=true`
2. 排序邏輯：收藏角色 → 其他角色（按原排序）
3. 顯示 `display_name` 而非 `name`

### Rationale
1. **最小修改**：維持現有元件 API，僅調整內部資料處理
2. **無破壞性變更**：其他使用 VoiceSelector 的頁面自動受益

### Alternatives Considered
- **方案 B**: 建立新的 EnhancedVoiceSelector 元件
  - 拒絕原因：增加維護成本，功能重複

---

## Decision 5: 角色管理頁面入口

### Decision
在側邊欄「設定」區塊下方新增「角色管理」選項，路由為 `/voice-management`。

### Rationale
1. **功能歸屬**：角色管理屬於「設定」類功能，非日常操作
2. **不干擾主流程**：TTS/STT 頁面保持簡潔，進階設定獨立頁面

### Alternatives Considered
- **方案 B**: 在 VoiceSelector 元件內加入編輯按鈕
  - 拒絕原因：破壞選擇流程的簡潔性
- **方案 C**: 在 TTS 頁面新增 Tab
  - 拒絕原因：增加 TTS 頁面複雜度

---

## Decision 6: 搜尋和篩選實作

### Decision
- 後端：在 `list_voices` use case 中支援 `search`、`is_favorite`、`is_hidden` 參數
- 前端：使用 debounced 輸入搜尋（300ms），篩選狀態存於 URL query params

### Rationale
1. **後端篩選**：減少傳輸資料量，尤其在 200+ 角色時
2. **URL 狀態**：允許分享篩選結果連結，重新整理不遺失狀態

### Alternatives Considered
- **方案 B**: 前端全量載入後本地篩選
  - 拒絕原因：首次載入時間較長，不符效能目標

---

## 技術細節備註

### VoiceCache 現有結構（參考）
```python
class VoiceCache(Base):
    id: str                  # provider:voice_id
    provider: str
    voice_id: str
    name: str
    language: str
    gender: str | None
    age_group: str | None
    styles: list[str]        # JSON
    use_cases: list[str]     # JSON
    sample_audio_url: str | None
    is_deprecated: bool
    metadata_: dict | None   # JSON
    synced_at: datetime | None
    updated_at: datetime
```

### 預計新增的 VoiceCustomization 結構
```python
class VoiceCustomization(Base):
    id: int                  # auto-increment PK
    voice_cache_id: str      # FK to voice_cache.id
    custom_name: str | None  # max 50 chars
    is_favorite: bool        # default False
    is_hidden: bool          # default False
    created_at: datetime
    updated_at: datetime

    # 索引
    - voice_cache_id (UNIQUE)
    - is_favorite
    - is_hidden
```

### 前端狀態結構
```typescript
interface VoiceManagementState {
  voices: VoiceWithCustomization[]
  filters: {
    provider: string | null
    language: string | null
    gender: string | null
    search: string
    showFavorites: boolean
    showHidden: boolean
  }
  isLoading: boolean
  error: string | null
}
```
