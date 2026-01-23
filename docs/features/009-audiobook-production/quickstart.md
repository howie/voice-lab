# Quickstart: Audiobook Production System

本指南說明如何使用有聲書製作系統建立多角色有聲故事。

---

## 功能概覽

### 核心功能

| 功能 | 說明 |
|------|------|
| 專案管理 | 建立、編輯、複製、刪除專案 |
| 劇本編輯 | 貼上劇本，自動識別角色 |
| 角色設定 | 為每個角色選擇聲音、調整參數 |
| 非同步生成 | 長篇故事分段生成，支援進度追蹤 |
| 背景音樂 | 上傳背景音樂並混音 |
| 匯出 | 輸出為 MP3/WAV 格式 |

### 支援的故事長度

- 建議：10-20 分鐘（約 2,000-4,000 字）
- 上限：無硬性限制，但超長內容建議分章節處理

---

## 快速開始

### 1. 建立專案

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "豬探長的冒險",
    "description": "一個關於偵探豬的故事",
    "language": "zh-TW"
  }'
```

**回應範例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "豬探長的冒險",
  "status": "draft",
  "character_count": 0,
  "turn_count": 0,
  "created_at": "2026-01-22T10:30:00Z"
}
```

### 2. 輸入劇本

```bash
curl -X PUT "http://localhost:8000/api/v1/audiobook/projects/{project_id}/script" \
  -H "Content-Type: application/json" \
  -d '{
    "script_content": "旁白：在一個寧靜的小鎮上，住著一位大名鼎鼎的偵探。\n豬探長：哼，又有案件了嗎？\n小豬助手：探長，這次的案件很棘手！\n豬探長：沒有我解決不了的案件。走吧！\n旁白：於是，豬探長和小豬助手踏上了冒險之旅。"
  }'
```

**劇本格式**：
```
角色名：台詞內容
角色名: 台詞內容（英文冒號也可以）
```

**回應範例**：
```json
{
  "characters": [
    {"id": "...", "name": "旁白", "turn_count": 2},
    {"id": "...", "name": "豬探長", "turn_count": 2},
    {"id": "...", "name": "小豬助手", "turn_count": 1}
  ],
  "turn_count": 5,
  "warnings": []
}
```

### 3. 設定角色聲音

```bash
# 為「豬探長」選擇聲音
curl -X PATCH "http://localhost:8000/api/v1/audiobook/projects/{project_id}/characters/{character_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "voice_id": "azure:zh-TW-YunJheNeural",
    "gender": "male",
    "age_group": "adult",
    "speech_rate": 0.9,
    "pitch": -5
  }'
```

**語音參數**：
| 參數 | 範圍 | 說明 |
|------|------|------|
| `speech_rate` | 0.5 - 2.0 | 語速，1.0 為正常 |
| `pitch` | -50 - 50 | 音調，0 為正常 |

### 4. 預覽角色聲音

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects/{project_id}/characters/{character_id}/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "哼，又有案件了嗎？"
  }'
```

**回應範例**：
```json
{
  "audio_url": "/storage/preview/abc123.mp3",
  "duration_ms": 2500,
  "text": "哼，又有案件了嗎？"
}
```

### 5. 開始生成

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects/{project_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "skip_completed": true,
    "regenerate_failed": true
  }'
```

**回應範例**：
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "total_turns": 5,
  "message": "Generation job created and queued"
}
```

### 6. 查看生成進度

```bash
curl "http://localhost:8000/api/v1/audiobook/projects/{project_id}/jobs/{job_id}"
```

**回應範例**：
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "running",
  "total_turns": 5,
  "completed_turns": 3,
  "failed_turns": 0,
  "progress_percent": 60,
  "estimated_remaining_seconds": 30,
  "current_turn": {
    "sequence": 4,
    "character_name": "豬探長",
    "text": "沒有我解決不了的案件。走吧！"
  }
}
```

### 7. 上傳背景音樂（可選）

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects/{project_id}/background-music" \
  -F "file=@background.mp3"
```

**支援格式**：MP3、WAV（最大 50MB）

### 8. 混音（可選）

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects/{project_id}/mix" \
  -H "Content-Type: application/json" \
  -d '{
    "volume": 0.3,
    "fade_in_ms": 2000,
    "fade_out_ms": 3000
  }'
```

### 9. 匯出成品

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects/{project_id}/export" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "mp3",
    "bitrate": 192,
    "include_chapters": true,
    "metadata": {
      "title": "豬探長的冒險",
      "artist": "Voice Lab Studio"
    }
  }'
```

**回應範例**：
```json
{
  "download_url": "/storage/export/final-abc123.mp3",
  "format": "mp3",
  "file_size_bytes": 15728640,
  "duration_ms": 600000,
  "expires_at": "2026-01-23T10:30:00Z"
}
```

---

## 聲音選擇指南

### 依年齡層篩選

使用 008 功能的聲音 API：

```bash
# 列出所有兒童聲音
curl "http://localhost:8000/api/v1/voices?age_group=child&language=zh-TW"

# 列出所有成人男性聲音
curl "http://localhost:8000/api/v1/voices?age_group=adult&gender=male&language=zh-TW"
```

### 建議聲音搭配

| 角色類型 | 建議設定 |
|---------|---------|
| 旁白 | `age_group=adult`, `style=news` |
| 主角（成人） | `age_group=adult`, 依性別選擇 |
| 小孩角色 | `age_group=child` |
| 長輩角色 | `age_group=senior` |
| 反派角色 | `pitch=-10`, `speech_rate=0.85` |

---

## 劇本格式最佳實踐

### 標準格式

```
旁白：故事的開場白。
角色A：第一句台詞。
角色B：第二句台詞。
角色A：繼續對話。
```

### 章節分隔（進階）

```
【第一章：案件的開始】
旁白：在一個寧靜的小鎮上...
豬探長：有案件了！

【第二章：調查展開】
旁白：豬探長來到了現場...
```

### 常見問題

**Q: 如何處理旁白？**
A: 將「旁白」作為角色名稱，系統會自動識別。

**Q: 角色名稱可以有空格嗎？**
A: 可以，例如「小豬 助手」會被識別為一個角色。

**Q: 如何插入停頓？**
A: 在台詞中使用「...」或「——」，TTS 會自動處理為停頓。

---

## 生成失敗處理

### 查看失敗的片段

```bash
curl "http://localhost:8000/api/v1/audiobook/projects/{project_id}/turns?status=failed"
```

### 重新生成失敗片段

```bash
curl -X POST "http://localhost:8000/api/v1/audiobook/projects/{project_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "skip_completed": true,
    "regenerate_failed": true
  }'
```

---

## 相關資源

- [Projects API 規格](./contracts/projects-api.yaml)
- [Characters API 規格](./contracts/characters-api.yaml)
- [Generation API 規格](./contracts/generation-api.yaml)
- [資料模型文件](./data-model.md)
- [功能規格](./spec.md)
