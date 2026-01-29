# Data Model: TTS 角色管理介面

**Feature**: 013-tts-role-mgmt
**Date**: 2026-01-29

## Entity Relationship Diagram

```
┌─────────────────────────────────────┐
│           voice_cache               │
├─────────────────────────────────────┤
│ id (PK)        : VARCHAR            │  ←── provider:voice_id
│ provider       : VARCHAR(50)        │
│ voice_id       : VARCHAR(128)       │
│ name           : VARCHAR            │
│ language       : VARCHAR(20)        │
│ gender         : VARCHAR(20)        │
│ age_group      : VARCHAR(20)        │
│ styles         : JSONB              │
│ use_cases      : JSONB              │
│ sample_audio_url: VARCHAR           │
│ is_deprecated  : BOOLEAN            │
│ metadata_      : JSONB              │
│ synced_at      : TIMESTAMP          │
│ updated_at     : TIMESTAMP          │
└─────────────────────────────────────┘
                │
                │ 1:1 (optional)
                ▼
┌─────────────────────────────────────┐
│       voice_customization           │  ←── 新增表
├─────────────────────────────────────┤
│ id (PK)        : SERIAL             │
│ voice_cache_id : VARCHAR (FK, UQ)   │  ←── 外鍵關聯 voice_cache.id
│ custom_name    : VARCHAR(50)        │  ←── 自訂顯示名稱
│ is_favorite    : BOOLEAN            │  ←── 收藏狀態
│ is_hidden      : BOOLEAN            │  ←── 隱藏狀態
│ created_at     : TIMESTAMP          │
│ updated_at     : TIMESTAMP          │
└─────────────────────────────────────┘
```

## Entity Definitions

### VoiceCustomization (新增)

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | SERIAL | PK, NOT NULL | 自動遞增主鍵 |
| voice_cache_id | VARCHAR | FK, UNIQUE, NOT NULL | 關聯 voice_cache.id |
| custom_name | VARCHAR(50) | NULLABLE | 使用者自訂顯示名稱 |
| is_favorite | BOOLEAN | NOT NULL, DEFAULT FALSE | 收藏狀態 |
| is_hidden | BOOLEAN | NOT NULL, DEFAULT FALSE | 隱藏狀態 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 建立時間 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新時間 |

### Indexes

```sql
-- 主要查詢索引
CREATE UNIQUE INDEX ix_voice_customization_voice_cache_id
    ON voice_customization(voice_cache_id);

-- 篩選索引
CREATE INDEX ix_voice_customization_is_favorite
    ON voice_customization(is_favorite) WHERE is_favorite = TRUE;

CREATE INDEX ix_voice_customization_is_hidden
    ON voice_customization(is_hidden) WHERE is_hidden = TRUE;
```

### Validation Rules

1. **custom_name**:
   - 最大長度 50 字元
   - 允許 NULL（使用原始名稱）
   - 去除首尾空白
   - 空字串視為 NULL

2. **is_favorite + is_hidden 互斥**:
   - 若 is_hidden = TRUE，則自動設定 is_favorite = FALSE
   - 業務邏輯層處理，非資料庫約束

3. **voice_cache_id 存在性**:
   - 外鍵約束確保 voice_cache 記錄存在
   - ON DELETE CASCADE：刪除 voice_cache 時同步刪除 customization

## Domain Entity (Python)

```python
@dataclass
class VoiceCustomization:
    """使用者對 TTS 角色的自訂設定"""

    id: int | None                # 資料庫主鍵
    voice_cache_id: str           # 關聯的 VoiceCache ID
    custom_name: str | None       # 自訂顯示名稱 (max 50)
    is_favorite: bool             # 收藏狀態
    is_hidden: bool               # 隱藏狀態
    created_at: datetime | None
    updated_at: datetime | None

    def get_display_name(self, original_name: str) -> str:
        """取得顯示名稱，優先使用自訂名稱"""
        return self.custom_name or original_name

    def mark_as_hidden(self) -> None:
        """標記為隱藏，同時取消收藏"""
        self.is_hidden = True
        self.is_favorite = False

    def validate(self) -> list[str]:
        """驗證欄位，回傳錯誤訊息列表"""
        errors = []
        if self.custom_name and len(self.custom_name) > 50:
            errors.append("custom_name 最多 50 字元")
        return errors
```

## Frontend Type (TypeScript)

```typescript
interface VoiceCustomization {
  id: number
  voiceCacheId: string
  customName: string | null
  isFavorite: boolean
  isHidden: boolean
  createdAt: string  // ISO 8601
  updatedAt: string  // ISO 8601
}

interface VoiceWithCustomization extends VoiceProfile {
  // 繼承自 VoiceProfile: id, name, provider, language, gender, etc.
  displayName: string      // computed: customName || name
  isFavorite: boolean
  isHidden: boolean
  customization: VoiceCustomization | null
}

// API Request/Response
interface UpdateVoiceCustomizationRequest {
  customName?: string | null
  isFavorite?: boolean
  isHidden?: boolean
}

interface BulkUpdateVoiceCustomizationRequest {
  updates: Array<{
    voiceCacheId: string
    customName?: string | null
    isFavorite?: boolean
    isHidden?: boolean
  }>
}
```

## State Transitions

### is_favorite 狀態轉換

```
                    toggle_favorite
    ┌──────────────────────────────────────┐
    │                                      │
    ▼                                      │
┌─────────┐                          ┌─────────┐
│ favorite│                          │  normal │
│  =TRUE  │ ◄────────────────────────│  =FALSE │
└─────────┘    toggle_favorite       └─────────┘
    │
    │ mark_as_hidden
    ▼
┌─────────┐
│ hidden  │
│  =TRUE  │
└─────────┘
```

### is_hidden 狀態轉換

```
                   toggle_hidden
    ┌──────────────────────────────────────┐
    │                                      │
    ▼                                      │
┌─────────┐                          ┌─────────┐
│ hidden  │                          │ visible │
│  =TRUE  │ ◄────────────────────────│  =FALSE │
└─────────┘    toggle_hidden         └─────────┘
    │               (auto: is_favorite = FALSE)
    │
    │ toggle_hidden
    ▼
┌─────────┐
│ visible │
│  =FALSE │
└─────────┘
```

## Migration Script

```sql
-- Migration: 013_create_voice_customization.sql

CREATE TABLE voice_customization (
    id SERIAL PRIMARY KEY,
    voice_cache_id VARCHAR NOT NULL REFERENCES voice_cache(id) ON DELETE CASCADE,
    custom_name VARCHAR(50),
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_voice_customization_voice_cache_id UNIQUE (voice_cache_id)
);

-- 索引
CREATE INDEX ix_voice_customization_is_favorite
    ON voice_customization(is_favorite) WHERE is_favorite = TRUE;

CREATE INDEX ix_voice_customization_is_hidden
    ON voice_customization(is_hidden) WHERE is_hidden = TRUE;

-- 觸發器：自動更新 updated_at
CREATE OR REPLACE FUNCTION update_voice_customization_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_voice_customization_updated_at
    BEFORE UPDATE ON voice_customization
    FOR EACH ROW
    EXECUTE FUNCTION update_voice_customization_updated_at();
```
