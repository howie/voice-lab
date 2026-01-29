# Tasks: Magic DJ Audio Features Enhancement

**Input**: Design documents from `/docs/features/011-magic-dj-audio-features/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/dj-api.yaml, research.md, quickstart.md

**Tests**: 不包含測試任務（規格書未要求 TDD 流程）

**Organization**: 任務按 User Story 分組，每個 Story 可獨立實作和測試

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行（不同檔案，無相依性）
- **[Story]**: 所屬 User Story（US1, US2, US3）
- 所有路徑為絕對路徑或相對於專案根目錄

## Path Conventions

- **Frontend**: `frontend/src/`
- **Backend**: `backend/src/`（Phase 3）

---

## Phase 1: Setup (共用基礎建設)

**Purpose**: 專案初始化和類型定義擴充

- [x] T001 擴充 TrackSource 類型定義，新增 `'tts' | 'upload'` 在 `frontend/src/types/magic-dj.ts`
- [x] T002 [P] 擴充 Track 介面，新增 `source`, `originalFileName`, `volume` 欄位在 `frontend/src/types/magic-dj.ts`
- [x] T003 [P] 新增 FileUploadState 介面定義在 `frontend/src/types/magic-dj.ts`
- [x] T004 [P] 新增常數定義（SUPPORTED_AUDIO_TYPES, MAX_FILE_SIZE, MAX_CONCURRENT_TRACKS）在 `frontend/src/types/magic-dj.ts`
- [x] T005 擴充 TrackPlaybackState 介面，新增 `isMuted`, `previousVolume` 欄位在 `frontend/src/types/magic-dj.ts`

---

## Phase 2: Foundational (阻塞性前置作業)

**Purpose**: 所有 User Story 都需要的核心基礎設施

**⚠️ CRITICAL**: 必須完成此階段才能開始任何 User Story

- [x] T006 在 magicDJStore 新增資料遷移邏輯，為舊 Track 補上 `source: 'tts'` 和 `volume: 1.0` 預設值在 `frontend/src/stores/magicDJStore.ts`
- [x] T007 [P] 新增 `setTrackVolume(trackId, volume)` action 在 `frontend/src/stores/magicDJStore.ts`
- [x] T008 [P] 新增 `toggleTrackMute(trackId)` action 在 `frontend/src/stores/magicDJStore.ts`
- [x] T009 確認 Zustand persist middleware 正確序列化新欄位（source, volume）在 `frontend/src/stores/magicDJStore.ts`

**Checkpoint**: 基礎建設完成 - 可開始實作 User Story

---

## Phase 3: User Story 1 - 上傳自訂音檔 (Priority: P1) 🎯 MVP

**Goal**: 研究人員可以上傳 MP3/WAV/OGG 音檔作為音軌，取代只能用 TTS 生成的限制

**Independent Test**: 上傳一個 MP3 檔案，儲存後重新載入頁面，音檔仍可正常播放

### Implementation for User Story 1

- [x] T010 [P] [US1] 建立 AudioDropzone 元件骨架（props 定義、基本結構）在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T011 [US1] 實作 AudioDropzone 拖放上傳功能（HTML5 Drag and Drop API）在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T012 [US1] 實作 AudioDropzone 點擊選擇檔案功能在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T013 [US1] 實作檔案驗證邏輯（格式、大小）在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T014 [US1] 實作檔案處理邏輯（ArrayBuffer → base64 → blob URL）在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T015 [US1] 實作音訊時長取得功能在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T016 [US1] 實作儲存空間不足錯誤處理在 `frontend/src/components/magic-dj/AudioDropzone.tsx`
- [x] T017 [US1] 修改 TrackEditorModal，新增「音源方式」切換（TTS / 上傳）在 `frontend/src/components/magic-dj/TrackEditorModal.tsx`
- [x] T018 [US1] 整合 AudioDropzone 到 TrackEditorModal（當選擇上傳時顯示）在 `frontend/src/components/magic-dj/TrackEditorModal.tsx`
- [x] T019 [US1] 實作音訊預覽播放功能在 TrackEditorModal 中 `frontend/src/components/magic-dj/TrackEditorModal.tsx`
- [x] T020 [US1] 修改 TrackList，根據 source 欄位顯示來源圖示（🎤 TTS / 📁 上傳）在 `frontend/src/components/magic-dj/TrackList.tsx`
- [x] T021 [US1] 匯出 AudioDropzone 元件在 `frontend/src/components/magic-dj/index.ts`

**Checkpoint**: User Story 1 完成 - 可獨立測試上傳功能

---

## Phase 4: User Story 2 - 調整音軌音量 (Priority: P2)

**Goal**: 每個音軌可獨立調整音量（0-100%），設定持久化，支援靜音切換

**Independent Test**: 調整音軌音量後播放，重新載入頁面，音量設定保留

### Implementation for User Story 2

- [x] T022 [P] [US2] 建立 VolumeSlider 元件骨架（props 定義、基本結構）在 `frontend/src/components/magic-dj/VolumeSlider.tsx`
- [x] T023 [US2] 實作 VolumeSlider 滑桿拖動調整功能在 `frontend/src/components/magic-dj/VolumeSlider.tsx`
- [x] T024 [US2] 實作 VolumeSlider 音量圖示動態切換（🔇 🔈 🔉 🔊）在 `frontend/src/components/magic-dj/VolumeSlider.tsx`
- [x] T025 [US2] 實作 VolumeSlider 點擊圖示靜音切換功能在 `frontend/src/components/magic-dj/VolumeSlider.tsx`
- [x] T026 [US2] 實作 VolumeSlider 百分比顯示在 `frontend/src/components/magic-dj/VolumeSlider.tsx`
- [x] T027 [US2] 修改 TrackPlayer，整合 VolumeSlider 元件在 `frontend/src/components/magic-dj/TrackPlayer.tsx`
- [x] T028 [US2] 修改 useMultiTrackPlayer，整合持久化音量（從 store 讀取 volume）在 `frontend/src/hooks/useMultiTrackPlayer.ts`
- [x] T029 [US2] 修改 useMultiTrackPlayer，實作即時音量調整（GainNode）在 `frontend/src/hooks/useMultiTrackPlayer.ts`
- [x] T030 [US2] 修改 TrackEditorModal，新增預設音量設定欄位在 `frontend/src/components/magic-dj/TrackEditorModal.tsx`
- [x] T031 [US2] 修改 TrackList，調整佈局加入音量控制顯示在 `frontend/src/components/magic-dj/TrackList.tsx`
- [x] T032 [US2] 實作同時播放 5 軌上限檢查，超過時顯示提示在 `frontend/src/hooks/useMultiTrackPlayer.ts`
- [x] T033 [US2] 匯出 VolumeSlider 元件在 `frontend/src/components/magic-dj/index.ts`

**Checkpoint**: User Story 1 + 2 完成 - 前端功能完整

---

## Phase 5: User Story 3 - 跨裝置同步設定 (Priority: P3)

**Goal**: 使用者可在不同裝置存取相同的音軌設定，支援多使用者隔離

**Independent Test**: 在裝置 A 建立設定，在裝置 B 登入同帳號可看到相同設定

### Backend Implementation

- [ ] T034 [P] [US3] 建立 Alembic migration 新增 dj_presets, dj_tracks 資料表在 `migrations/versions/xxxx_add_dj_tables.py`
- [ ] T035 [P] [US3] 建立 DJ Domain Entities（TrackType, TrackSource, DJSettings, DJPreset, DJTrack）在 `backend/src/domain/entities/dj.py`
- [ ] T036 [P] [US3] 建立 DJ API Schemas（Request/Response Models）在 `backend/src/presentation/api/schemas/dj.py`
- [ ] T037 [US3] 建立 DJRepository（CRUD operations for presets and tracks）在 `backend/src/infrastructure/persistence/dj_repository.py`
- [ ] T038 [US3] 擴充 GCS storage 模組，新增 DJ 音檔上傳/下載/刪除方法在 `backend/src/infrastructure/storage/gcs.py`
- [ ] T039 [US3] 建立 DJService（業務邏輯：preset 管理、track 管理、audio 管理）在 `backend/src/application/services/dj_service.py`
- [ ] T040 [US3] 實作 Preset CRUD API endpoints 在 `backend/src/presentation/api/routes/dj.py`
- [ ] T041 [US3] 實作 Track CRUD API endpoints 在 `backend/src/presentation/api/routes/dj.py`
- [ ] T042 [US3] 實作 Audio upload/download API endpoints 在 `backend/src/presentation/api/routes/dj.py`
- [ ] T043 [US3] 實作 Import/Export API endpoints 在 `backend/src/presentation/api/routes/dj.py`
- [ ] T044 [US3] 註冊 DJ router 到 FastAPI app 在 `backend/src/main.py`

### Frontend Integration

- [ ] T045 [P] [US3] 建立 DJ API Client（djApi）在 `frontend/src/lib/api/dj.ts`
- [ ] T046 [US3] 修改 magicDJStore，改為 API-backed（移除 persist middleware for tracks）在 `frontend/src/stores/magicDJStore.ts`
- [ ] T047 [US3] 新增 loadPreset, saveTrack, deleteTrack async actions 在 `frontend/src/stores/magicDJStore.ts`
- [ ] T048 [US3] 建立 PresetSelector 元件（預設組下拉選單）在 `frontend/src/components/magic-dj/PresetSelector.tsx`
- [ ] T049 [US3] 建立 ImportDialog 元件（從 localStorage 匯入）在 `frontend/src/components/magic-dj/ImportDialog.tsx`
- [ ] T050 [US3] 整合 PresetSelector 到 MagicDJPage 在 `frontend/src/routes/magic-dj/MagicDJPage.tsx`

**Checkpoint**: 所有 User Stories 完成 - 功能完整

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨 User Story 的改善和收尾工作

- [ ] T051 [P] 驗證 quickstart.md 文件步驟可正確執行
- [ ] T052 [P] 程式碼清理和重構（移除 console.log, 統一錯誤訊息格式）
- [x] T053 [P] 確認所有新增元件已匯出在 index.ts
- [x] T054 執行 `make check` 確認通過 linting 和 type checking
- [ ] T055 更新 CLAUDE.md 相關章節（如有需要）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無相依性 - 可立即開始
- **Foundational (Phase 2)**: 相依於 Setup 完成 - **阻塞所有 User Stories**
- **User Stories (Phase 3-5)**: 相依於 Foundational 完成
  - US1 和 US2 可平行進行
  - US3 相依於 US1、US2 完成（需要前端功能穩定）
- **Polish (Phase 6)**: 相依於所需 User Stories 完成

### User Story Dependencies

```
Setup (Phase 1)
     │
     ▼
Foundational (Phase 2)
     │
     ├─────────────┬─────────────┐
     ▼             ▼             │
  US1 (P1)     US2 (P2)         │
     │             │             │
     └──────┬──────┘             │
            ▼                    │
         US3 (P3) ◄──────────────┘
            │
            ▼
      Polish (Phase 6)
```

### Within Each User Story

- 元件骨架 → 元件功能實作 → 整合到現有元件
- 後端 Entity → Repository → Service → API Routes（US3）
- 核心功能 → 錯誤處理 → UI 完善

### Parallel Opportunities

**Phase 1 內部**:
```
T002, T003, T004 可平行執行（不同介面定義）
```

**Phase 2 內部**:
```
T007, T008 可平行執行（不同 store actions）
```

**User Story 1 內部**:
```
T010 獨立執行後，T011-T016 為序列
T020 可在 T017-T019 完成後平行執行
```

**User Story 2 內部**:
```
T022-T026 (VolumeSlider) 可與 T028-T029 (hook 修改) 部分平行
```

**User Story 3 內部**:
```
T034, T035, T036 可平行執行（不同檔案）
T045 (API Client) 可與 T037-T044 (Backend) 平行開發
```

---

## Implementation Strategy

### MVP First (僅 User Story 1)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（**關鍵 - 阻塞所有 Stories**）
3. 完成 Phase 3: User Story 1
4. **停止並驗證**: 測試上傳功能獨立運作
5. 可部署/展示 MVP

### Incremental Delivery

1. Setup + Foundational → 基礎完成
2. 新增 User Story 1 → 測試 → 部署（MVP!）
3. 新增 User Story 2 → 測試 → 部署
4. 新增 User Story 3 → 測試 → 部署
5. 每個 Story 增加價值而不破壞前一個 Story

### Parallel Team Strategy

若有多位開發者：

1. 團隊共同完成 Setup + Foundational
2. Foundational 完成後：
   - 開發者 A: User Story 1（Frontend）
   - 開發者 B: User Story 2（Frontend）
   - 開發者 C: User Story 3 Backend（待 US1/US2 穩定後整合 Frontend）
3. 各 Story 獨立完成並整合

---

## Summary

| Phase | Task Count | Parallelizable |
|-------|------------|----------------|
| Setup | 5 | 3 |
| Foundational | 4 | 2 |
| US1 (P1) | 12 | 1 |
| US2 (P2) | 12 | 1 |
| US3 (P3) | 17 | 4 |
| Polish | 5 | 3 |
| **Total** | **55** | **14** |

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) = **21 tasks**

---

## Notes

- [P] 標記 = 不同檔案，無相依性
- [Story] 標籤對應 spec.md 中的 User Story
- 每個 User Story 可獨立完成並測試
- 每個任務或邏輯群組後進行 commit
- 在任何 Checkpoint 停下來驗證 Story 獨立運作
- 避免：模糊任務、同一檔案衝突、破壞獨立性的跨 Story 相依
