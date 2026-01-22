# Quickstart: VoAI Multi-Role Voice Generation Enhancement

本指南說明如何使用增強後的多角色語音生成功能。

---

## 功能概覽

### Native 多角色合成

支援在單一 API 請求中合成多角色對話，無需後製合併：

| Provider | 模式 | 特點 |
|----------|------|------|
| Azure | Native (SSML) | 使用 `<voice>` 標籤，最多 10 speakers，限制 64 KB |
| ElevenLabs | Native (Dialogue) | 使用 Text to Dialogue API，無 speaker 數量限制，限制 5,000 字元 |
| OpenAI, GCP, Cartesia, Deepgram | Segmented | 分段合成 + pydub 合併 |

### 聲音資料庫與篩選

- 從各 Provider 同步聲音清單到本地資料庫
- 支援依 `age_group`（年齡層）、`gender`（性別）、`style`（風格）篩選
- 每日自動同步，或手動觸發更新

---

## 快速開始

### 1. 查詢聲音列表

```bash
# 列出所有聲音
curl "http://localhost:8000/api/v1/voices"

# 依年齡層篩選（兒童聲音）
curl "http://localhost:8000/api/v1/voices?age_group=child"

# 依 Provider 和語言篩選
curl "http://localhost:8000/api/v1/voices?provider=azure&language=zh-TW"

# 依風格篩選
curl "http://localhost:8000/api/v1/voices?style=cheerful"
```

**回應範例**：
```json
{
  "voices": [
    {
      "id": "azure:zh-TW-HsiaoYuNeural",
      "provider": "azure",
      "voice_id": "zh-TW-HsiaoYuNeural",
      "name": "曉雨",
      "language": "zh-TW",
      "gender": "female",
      "age_group": "adult",
      "styles": ["cheerful", "sad", "angry"]
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0,
  "cached_at": "2026-01-22T10:30:00Z"
}
```

### 2. 多角色語音合成

#### Azure Native 模式

```bash
curl -X POST "http://localhost:8000/api/v1/multi-role-tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "azure",
    "mode": "native",
    "turns": [
      {"role": "A", "text": "你好，我是小明"},
      {"role": "B", "text": "嗨，很高興認識你"},
      {"role": "A", "text": "今天天氣真好"}
    ],
    "voice_assignments": {
      "A": "zh-TW-YunJheNeural",
      "B": "zh-TW-HsiaoYuNeural"
    }
  }'
```

#### ElevenLabs Native 模式

```bash
curl -X POST "http://localhost:8000/api/v1/multi-role-tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "elevenlabs",
    "mode": "native",
    "turns": [
      {"role": "A", "text": "[excited] 你好！"},
      {"role": "B", "text": "[friendly] 嗨！很高興認識你"}
    ],
    "voice_assignments": {
      "A": "voice_id_1",
      "B": "voice_id_2"
    }
  }'
```

**回應範例**：
```json
{
  "audio_url": "/storage/multi-role/abc123.mp3",
  "duration_seconds": 5.2,
  "synthesis_mode": "native",
  "provider": "azure",
  "metadata": {
    "turns_count": 3,
    "total_characters": 28,
    "ssml_size_bytes": 1024
  }
}
```

### 3. 手動觸發聲音同步（管理員）

```bash
# 同步所有 Provider
curl -X POST "http://localhost:8000/api/v1/admin/voices/sync" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json"

# 同步特定 Provider
curl -X POST "http://localhost:8000/api/v1/admin/voices/sync" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"provider": "azure"}'
```

**回應範例**：
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Voice sync job created and queued",
  "provider": "azure"
}
```

### 4. 查看同步狀態

```bash
# 查看同步狀態概覽
curl "http://localhost:8000/api/v1/admin/voices/sync/status" \
  -H "Authorization: Bearer <admin-token>"
```

**回應範例**：
```json
{
  "providers": [
    {
      "provider": "azure",
      "voice_count": 420,
      "deprecated_count": 5,
      "last_sync": "2026-01-22T02:00:00Z",
      "status": "healthy"
    },
    {
      "provider": "elevenlabs",
      "voice_count": 95,
      "deprecated_count": 2,
      "last_sync": "2026-01-22T02:01:00Z",
      "status": "healthy"
    }
  ],
  "last_full_sync": "2026-01-22T02:00:00Z",
  "total_voices": 785,
  "total_deprecated": 12
}
```

---

## 年齡層分類說明

| age_group | 說明 | 適用場景 |
|-----------|------|---------|
| `child` | 兒童聲音 | 童書、兒童節目、動畫角色 |
| `young` | 青年聲音 | 年輕角色、活潑對話 |
| `adult` | 成人聲音 | 一般旁白、專業場合 |
| `senior` | 長者聲音 | 長輩角色、溫和語調 |

---

## 注意事項

### 字元限制

| Provider | 限制 | 處理方式 |
|----------|------|---------|
| Azure | 64 KB (SSML 含標籤) | 超過自動 fallback 到 segmented 模式 |
| ElevenLabs | 5,000 字元 (所有 speaker 合計) | 超過自動 fallback 到 segmented 模式 |

### ElevenLabs Audio Tags

ElevenLabs 支援在文字中使用 Audio Tags 控制語氣：

```
[excited] 太棒了！
[whispers] 這是個秘密
[sad] 我很難過
[laughs] 哈哈哈
```

### Fallback 機制

當 Native 合成失敗（超過限制、Provider 錯誤等），系統自動切換到 Segmented 模式：

1. 分段呼叫 Provider API 合成每個 turn
2. 使用 pydub 合併音訊檔案
3. 回應中 `synthesis_mode` 會標示為 `"segmented"`

---

## 相關資源

- [Voices API 規格](./contracts/voices-api.yaml)
- [Voice Sync API 規格](./contracts/voice-sync-api.yaml)
- [資料模型文件](./data-model.md)
- [功能規格](./spec.md)
