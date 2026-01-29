# Implementation Plan: Magic DJ Audio Features Enhancement

**Branch**: `011-magic-dj-audio-features` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/011-magic-dj-audio-features/spec.md`

## Summary

增強 Magic DJ 控制器的音軌管理功能，分三階段實作：
1. **Phase 1**: MP3 上傳功能 - 支援拖放上傳 MP3/WAV/OGG 音檔，存儲於 localStorage
2. **Phase 2**: 音量控制功能 - 每個音軌獨立音量控制（0-100%），支援持久化
3. **Phase 3**: 後端儲存 - PostgreSQL + GCS 實現跨裝置同步，多使用者隔離

技術方案採用前端優先策略，Phase 1-2 完全在前端實作（Web Audio API + localStorage），Phase 3 再整合後端。

## Technical Context

**Language/Version**: TypeScript 5.3+ (Frontend), Python 3.11+ (Backend)
**Primary Dependencies**:
- Frontend: React 18+, Zustand, Web Audio API, Tailwind CSS, Lucide Icons
- Backend (Phase 3): FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, google-cloud-storage
**Storage**:
- Phase 1-2: localStorage (5-10MB limit), base64 編碼音檔
- Phase 3: PostgreSQL 16 (metadata), Google Cloud Storage (audio files), Redis 7 (cache)
**Testing**: Jest + React Testing Library (Frontend), pytest + pytest-asyncio (Backend)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend + backend)
**Performance Goals**:
- 音檔上傳 <30s (10MB file)
- 音量調整響應 <500ms
- 音檔載入 <3s (Phase 3)
**Constraints**:
- Phase 1-2: localStorage 5-10MB 限制
- 單檔上限 10MB
- 最多 5 個音軌同時播放
- 每使用者最多 10 個預設組，每預設組最多 20 個音軌
**Scale/Scope**:
- 單一使用者場景（Phase 1-2）
- 多使用者跨裝置（Phase 3）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | ✅ Pass | 需撰寫 AudioDropzone、VolumeSlider 元件測試 |
| II. Unified API Abstraction | ✅ Pass | Phase 3 API 遵循現有 REST 模式 |
| III. Performance Benchmarking | ✅ Pass | 定義 SC-001~SC-010 可量測成功標準 |
| IV. Documentation First | ✅ Pass | 此 plan.md 先於實作 |
| V. Clean Architecture | ✅ Pass | 分層：components → stores → hooks → api |

**Gate Status**: PASSED - 可進入 Phase 0

## Project Structure

### Documentation (this feature)

```text
docs/features/011-magic-dj-audio-features/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts for Phase 3)
│   └── dj-api.yaml      # OpenAPI spec
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
frontend/src/
├── types/
│   └── magic-dj.ts                    # 修改 - Track 類型擴充 (source, volume)
├── components/magic-dj/
│   ├── AudioDropzone.tsx              # 新增 - 拖放上傳元件 (Phase 1)
│   ├── VolumeSlider.tsx               # 新增 - 音量滑桿元件 (Phase 2)
│   ├── TrackEditorModal.tsx           # 修改 - 加入上傳功能 + 音量設定
│   ├── TrackPlayer.tsx                # 修改 - 加入音量控制
│   └── TrackList.tsx                  # 修改 - 顯示來源圖示 + 音量
├── hooks/
│   └── useMultiTrackPlayer.ts         # 修改 - 整合持久化音量
├── stores/
│   └── magicDJStore.ts                # 修改 - 新增 volume actions + 遷移邏輯
└── lib/api/
    └── dj.ts                          # 新增 - DJ API Client (Phase 3)

backend/src/                            # Phase 3 only
├── domain/
│   └── entities/
│       └── dj.py                      # 新增 - DJ Domain Models
├── infrastructure/
│   ├── persistence/
│   │   └── dj_repository.py           # 新增 - DB Repository
│   └── storage/
│       └── gcs.py                     # 修改 - 新增 DJ 音檔儲存方法
├── presentation/api/
│   ├── routes/
│   │   └── dj.py                      # 新增 - DJ API Routes
│   └── schemas/
│       └── dj.py                      # 新增 - Request/Response Schemas
└── application/services/
    └── dj_service.py                  # 新增 - DJ Application Service

migrations/versions/
└── xxxx_add_dj_tables.py              # 新增 - Alembic migration (Phase 3)

tests/
├── frontend/components/magic-dj/
│   ├── AudioDropzone.test.tsx         # 新增
│   └── VolumeSlider.test.tsx          # 新增
└── backend/
    ├── unit/domain/entities/
    │   └── test_dj.py                 # 新增 (Phase 3)
    └── integration/api/
        └── test_dj_routes.py          # 新增 (Phase 3)
```

**Structure Decision**: Web application 模式，frontend/backend 分離。Phase 1-2 僅修改 frontend，Phase 3 加入 backend API。

## Complexity Tracking

> No violations requiring justification. All changes align with existing patterns.

---

## Phase 0: Research (Completed)

技術細節已從現有技術文件 `011-audio-features-spec.md` 獲得，無額外研究需求。

### Key Decisions

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| base64 存儲 (Phase 1-2) | localStorage 原生支援，無需額外依賴 | IndexedDB: 複雜度較高，Phase 3 會改用後端 |
| Web Audio API GainNode | 現有 useMultiTrackPlayer 已使用，支援即時音量調整 | HTML5 Audio volume: 無法精確控制多軌 |
| Zustand persist middleware | 已在使用，自動序列化到 localStorage | 手動 localStorage 操作: 易出錯 |
| GCS Signed URL (Phase 3) | 安全、時效性、不暴露路徑 | Direct URL: 安全風險 |
| Last-write-wins 衝突策略 | 簡單可靠，符合單使用者多裝置場景 | CRDT/OT: 過度工程 |

---

## Phase 1: Design & Contracts

### Data Model

見 [data-model.md](./data-model.md)

**Track 類型擴充摘要**:

```typescript
// Phase 1 新增
type TrackSource = 'tts' | 'upload';

interface Track {
  // 現有欄位...
  source: TrackSource;           // 音軌來源
  originalFileName?: string;     // 上傳時原始檔名

  // Phase 2 新增
  volume: number;                // 0.0 ~ 1.0，預設 1.0
}
```

**Phase 3 新增實體**:

| Entity | Description | Key Fields |
|--------|-------------|------------|
| DJPreset | 預設組（音軌設定集合） | id, user_id, name, settings |
| DJTrack | 單一音軌 | id, preset_id, name, type, source, volume |

### API Contracts (Phase 3)

見 [contracts/dj-api.yaml](./contracts/dj-api.yaml)

**Endpoint Summary**:

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/dj/presets | 列出使用者預設組 |
| POST | /api/v1/dj/presets | 建立預設組 |
| GET | /api/v1/dj/presets/{id} | 取得預設組（含音軌） |
| PUT | /api/v1/dj/presets/{id} | 更新預設組 |
| DELETE | /api/v1/dj/presets/{id} | 刪除預設組 |
| POST | /api/v1/dj/presets/{id}/tracks | 新增音軌 |
| PUT | /api/v1/dj/presets/{id}/tracks/{trackId} | 更新音軌 |
| DELETE | /api/v1/dj/presets/{id}/tracks/{trackId} | 刪除音軌 |
| POST | /api/v1/dj/audio/upload | 上傳音檔 |
| GET | /api/v1/dj/audio/{trackId} | 取得音檔 URL |
| POST | /api/v1/dj/import | 從 localStorage 匯入 |
| GET | /api/v1/dj/export/{presetId} | 匯出預設組 |

### Component Design

**Phase 1 - AudioDropzone**:
- Props: `onFileAccepted`, `onError`, `isProcessing`, `currentFile`
- 支援 drag-and-drop + click-to-select
- 檔案驗證：格式（MP3/WAV/OGG/WebM）、大小（<10MB）
- 顯示：拖放區域、已選檔案資訊、錯誤訊息

**Phase 2 - VolumeSlider**:
- Props: `value`, `onChange`, `disabled`, `size`
- 滑桿控制（0-100%）
- 點擊圖示切換靜音
- 動態圖示（🔇 🔈 🔉 🔊）

### Quickstart

見 [quickstart.md](./quickstart.md)

---

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | ✅ Pass | AudioDropzone, VolumeSlider 有明確測試案例 |
| II. Unified API Abstraction | ✅ Pass | Phase 3 API 遵循 REST 標準 |
| III. Performance Benchmarking | ✅ Pass | 成功標準可量測 |
| IV. Documentation First | ✅ Pass | plan.md, data-model.md, contracts/ 已完成 |
| V. Clean Architecture | ✅ Pass | 組件、store、hook 分層清晰 |

**Final Gate Status**: PASSED - 可進入 `/speckit.tasks` 產生任務
