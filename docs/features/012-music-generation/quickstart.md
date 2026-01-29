# Quickstart: Music Generation

**Feature**: 012-music-generation
**Date**: 2026-01-29

---

## 概述

Voice Lab 音樂生成功能整合 Mureka AI 平台，支援：

- **純音樂/BGM 生成**：根據情境描述生成背景音樂
- **歌曲生成**：根據歌詞和風格描述生成完整歌曲（含人聲）
- **歌詞生成**：根據主題生成結構化歌詞

---

## 前置需求

### 環境變數

```bash
# Mureka API 設定
MUREKA_API_KEY=your-api-key-here
MUREKA_API_BASE_URL=https://api.mureka.ai

# 可選：配額設定
MUSIC_DAILY_LIMIT_PER_USER=10
MUSIC_MONTHLY_LIMIT_PER_USER=100
MUSIC_MAX_CONCURRENT_JOBS=3
```

### 取得 API Key

1. 前往 [Mureka API Platform](https://platform.mureka.ai/)
2. 註冊或登入帳號
3. 前往 [API Keys](https://platform.mureka.ai/apiKeys) 頁面
4. 建立新的 API Key

---

## 快速開始

### 1. 生成純音樂（BGM）

```bash
# 提交純音樂生成任務
curl -X POST http://localhost:8000/api/v1/music/instrumental \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "prompt": "magical fantasy forest, whimsical, children friendly",
    "model": "auto"
  }'
```

回應：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "instrumental",
  "status": "pending",
  "prompt": "magical fantasy forest, whimsical, children friendly",
  "model": "auto",
  "created_at": "2026-01-29T10:00:00Z"
}
```

### 2. 查詢任務狀態

```bash
# 輪詢查詢狀態
curl http://localhost:8000/api/v1/music/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

回應（完成時）：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "instrumental",
  "status": "completed",
  "prompt": "magical fantasy forest, whimsical, children friendly",
  "model": "auto",
  "result_url": "/storage/music/550e8400-e29b-41d4-a716-446655440000.mp3",
  "duration_ms": 120000,
  "title": "Enchanted Forest",
  "created_at": "2026-01-29T10:00:00Z",
  "completed_at": "2026-01-29T10:00:45Z"
}
```

### 3. 下載音檔

```bash
# 下載生成的音檔
curl http://localhost:8000/api/v1/music/jobs/550e8400-e29b-41d4-a716-446655440000/download \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o music.mp3
```

---

## 歌曲生成

### 使用自訂歌詞

```bash
curl -X POST http://localhost:8000/api/v1/music/song \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "prompt": "pop, cheerful, children, chinese, female vocal",
    "lyrics": "[Verse]\n收玩具，收玩具\n把玩具收回家\n[Chorus]\n一起來收玩具\n整整齊齊放好它",
    "model": "auto"
  }'
```

### AI 生成歌詞後生成歌曲

```bash
# 步驟 1: 生成歌詞
curl -X POST http://localhost:8000/api/v1/music/lyrics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "prompt": "太空探險主題，適合兒童"
  }'

# 步驟 2: 等待歌詞生成完成後，使用生成的歌詞建立歌曲
curl -X POST http://localhost:8000/api/v1/music/song \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "prompt": "pop, adventure, space, children, energetic",
    "lyrics": "[生成的歌詞內容]",
    "model": "auto"
  }'
```

---

## 歌詞操作

### 生成歌詞

```bash
curl -X POST http://localhost:8000/api/v1/music/lyrics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "prompt": "太空探險"
  }'
```

### 延伸歌詞

```bash
curl -X POST http://localhost:8000/api/v1/music/lyrics/extend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "lyrics": "[Verse]\n飛向宇宙，探索星球\n[Chorus]\n太空冒險，勇敢前行",
    "prompt": "加入更多關於星球的描述"
  }'
```

---

## 配額管理

### 查詢配額狀態

```bash
curl http://localhost:8000/api/v1/music/quota \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

回應：

```json
{
  "daily_used": 3,
  "daily_limit": 10,
  "monthly_used": 25,
  "monthly_limit": 100,
  "concurrent_jobs": 1,
  "max_concurrent_jobs": 3,
  "can_submit": true
}
```

---

## 任務管理

### 列出任務

```bash
# 列出所有任務
curl "http://localhost:8000/api/v1/music/jobs?limit=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 篩選特定狀態
curl "http://localhost:8000/api/v1/music/jobs?status=completed" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 篩選特定類型
curl "http://localhost:8000/api/v1/music/jobs?type=instrumental" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 重試失敗任務

```bash
curl -X POST http://localhost:8000/api/v1/music/jobs/550e8400-e29b-41d4-a716-446655440000/retry \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Magic DJ 整合

在 Magic DJ 控制台中可以快速生成新音軌：

1. 點擊「生成新音軌」按鈕
2. 輸入情境描述
3. 等待生成完成
4. 確認加入音軌列表

---

## 錯誤處理

### 常見錯誤

| 錯誤代碼 | HTTP 狀態 | 說明 |
|----------|-----------|------|
| `QUOTA_EXCEEDED` | 429 | 配額不足 |
| `CONCURRENT_LIMIT` | 429 | 並發任務上限 |
| `INVALID_PROMPT` | 400 | 描述太短或無效 |
| `LYRICS_TOO_LONG` | 400 | 歌詞超過長度限制 |
| `JOB_NOT_FOUND` | 404 | 任務不存在 |
| `JOB_NOT_COMPLETED` | 400 | 任務未完成，無法下載 |

### 錯誤回應格式

```json
{
  "code": "QUOTA_EXCEEDED",
  "message": "音樂生成配額不足，請聯繫管理員",
  "details": {
    "daily_used": 10,
    "daily_limit": 10
  }
}
```

---

## 模型選擇指南

| 模型 | 說明 | 推薦場景 |
|------|------|----------|
| `auto` | 自動選擇最適合模型 | 一般使用（預設） |
| `mureka-01` | 最新旗艦模型 | 高品質要求 |
| `v7.5` | 平衡型模型 | 一般使用 |
| `v6` | 經典穩定模型 | 相容性需求 |

---

## 注意事項

1. **生成時間**：平均約 45 秒，請使用輪詢查詢狀態
2. **歷史保留**：生成結果保留 30 天
3. **並發限制**：每用戶最多 3 個同時進行的任務
4. **配額限制**：每日 10 次，每月 100 次
5. **語言支援**：中文品質最佳，共支援 10 種語言

---

*Last updated: 2026-01-29*
