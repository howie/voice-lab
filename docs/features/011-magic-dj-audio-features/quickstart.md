# Quickstart: Magic DJ Audio Features

本指南說明如何開發和測試 Magic DJ Audio Features。

## Prerequisites

- Node.js 18+
- pnpm (frontend package manager)
- Python 3.11+ (Phase 3)
- Docker & Docker Compose (Phase 3)

## Phase 1-2: Frontend Development

### 1. 啟動開發環境

```bash
# 進入 frontend 目錄
cd frontend

# 安裝依賴
pnpm install

# 啟動開發伺服器
pnpm dev
```

前端會在 `http://localhost:5173` 啟動。

### 2. 訪問 Magic DJ Controller

在瀏覽器開啟：`http://localhost:5173/magic-dj`

### 3. 測試 Phase 1 功能（MP3 上傳）

1. 點擊「新增音軌」或編輯現有音軌
2. 選擇「上傳 MP3」作為音源方式
3. 拖放或選擇一個 MP3/WAV/OGG 檔案
4. 確認檔案資訊顯示正確
5. 點擊播放預覽
6. 儲存音軌
7. 重新載入頁面，確認音軌仍可播放

### 4. 測試 Phase 2 功能（音量控制）

1. 在音軌列表找到任一音軌
2. 拖動音量滑桿調整音量
3. 點擊音量圖示切換靜音
4. 播放音軌確認音量效果
5. 重新載入頁面，確認音量設定保留

### 5. 執行測試

```bash
# 執行所有前端測試
pnpm test

# 執行特定測試
pnpm test AudioDropzone
pnpm test VolumeSlider
```

---

## Phase 3: Backend Development

### 1. 啟動後端環境

```bash
# 進入 backend 目錄
cd backend

# 建立虛擬環境並安裝依賴
uv sync

# 啟動資料庫
docker-compose up -d postgres redis

# 執行資料庫遷移
alembic upgrade head

# 啟動後端伺服器
uvicorn src.main:app --reload
```

後端會在 `http://localhost:8000` 啟動。

### 2. 設定 GCS（音檔儲存）

```bash
# 設定 GCP 認證
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# 建立 GCS bucket（如果不存在）
gsutil mb gs://voice-lab-audio

# 設定 CORS
gsutil cors set cors.json gs://voice-lab-audio
```

`cors.json` 範例：

```json
[
  {
    "origin": ["http://localhost:5173", "https://your-domain.com"],
    "method": ["GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
```

### 3. API 測試

```bash
# 列出預設組
curl http://localhost:8000/api/v1/dj/presets

# 建立預設組
curl -X POST http://localhost:8000/api/v1/dj/presets \
  -H "Content-Type: application/json" \
  -d '{"name": "測試預設組"}'

# 上傳音檔
curl -X POST http://localhost:8000/api/v1/dj/audio/upload \
  -F "file=@/path/to/audio.mp3" \
  -F "track_id=<uuid>"
```

### 4. 執行後端測試

```bash
cd backend

# 執行所有測試
pytest

# 執行 DJ 相關測試
pytest tests/ -k dj

# 執行覆蓋率報告
pytest --cov=src/domain/entities/dj --cov-report=html
```

---

## Development Workflow

### 新增元件

1. 在 `frontend/src/components/magic-dj/` 建立新元件
2. 在 `frontend/src/components/magic-dj/index.ts` 匯出
3. 撰寫測試在 `frontend/tests/components/magic-dj/`

### 修改 Store

1. 編輯 `frontend/src/stores/magicDJStore.ts`
2. 更新型別定義在 `frontend/src/types/magic-dj.ts`
3. 確保 Zustand persist middleware 正確序列化新欄位

### 新增 API Endpoint（Phase 3）

1. 定義 Schema 在 `backend/src/presentation/api/schemas/dj.py`
2. 實作 Route 在 `backend/src/presentation/api/routes/dj.py`
3. 撰寫整合測試在 `backend/tests/integration/api/test_dj_routes.py`

---

## Troubleshooting

### localStorage 空間不足

```javascript
// 檢查 localStorage 使用量
const used = new Blob(Object.values(localStorage)).size;
console.log(`localStorage used: ${(used / 1024 / 1024).toFixed(2)} MB`);
```

解決方案：刪除不需要的音軌，或升級到 Phase 3 後端儲存。

### 音檔無法播放

1. 檢查瀏覽器 Console 是否有錯誤
2. 確認檔案格式為支援的類型（MP3, WAV, OGG, WebM）
3. 確認檔案未損壞

### GCS Signed URL 過期（Phase 3）

Signed URL 預設 1 小時過期。如果音檔無法載入：

1. 重新載入頁面
2. 系統會自動重新取得新的 Signed URL

---

## Key Files Reference

### Frontend

| File | Description |
|------|-------------|
| `src/types/magic-dj.ts` | 型別定義 |
| `src/stores/magicDJStore.ts` | Zustand Store |
| `src/hooks/useMultiTrackPlayer.ts` | Web Audio API Hook |
| `src/components/magic-dj/AudioDropzone.tsx` | 拖放上傳元件 |
| `src/components/magic-dj/VolumeSlider.tsx` | 音量滑桿元件 |
| `src/components/magic-dj/TrackEditorModal.tsx` | 音軌編輯 Modal |

### Backend (Phase 3)

| File | Description |
|------|-------------|
| `src/domain/entities/dj.py` | Domain Models |
| `src/presentation/api/routes/dj.py` | API Routes |
| `src/presentation/api/schemas/dj.py` | Request/Response Schemas |
| `src/infrastructure/storage/gcs.py` | GCS 儲存服務 |
| `src/infrastructure/persistence/dj_repository.py` | DB Repository |
