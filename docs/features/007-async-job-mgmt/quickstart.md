# Quickstart: Async Job Management

本指南說明如何使用背景工作管理 API 進行 Multi-Role TTS 合成。

---

## 概述

背景工作管理讓您可以：
- 提交 TTS 合成工作後立即離開頁面
- 稍後查詢工作狀態和進度
- 下載已完成的音檔
- 查看 30 天內的歷史記錄

---

## 基本流程

```
1. 提交工作 (POST /api/v1/jobs)
       ↓
2. 取得工作 ID
       ↓
3. 查詢狀態 (GET /api/v1/jobs/{id})
       ↓
4. 下載結果 (GET /api/v1/jobs/{id}/download)
```

---

## 1. 提交工作

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "azure",
    "turns": [
      {"speaker": "A", "text": "你好，今天天氣真好！", "index": 0},
      {"speaker": "B", "text": "是啊，要不要一起去公園走走？", "index": 1}
    ],
    "voice_assignments": [
      {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural", "voice_name": "曉雨"},
      {"speaker": "B", "voice_id": "zh-TW-YunJheNeural", "voice_name": "雲哲"}
    ],
    "language": "zh-TW",
    "output_format": "mp3"
  }'
```

**回應**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "job_type": "multi_role_tts",
  "provider": "azure",
  "created_at": "2026-01-20T10:30:00Z"
}
```

---

## 2. 查詢工作狀態

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**進行中回應**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "started_at": "2026-01-20T10:30:05Z"
}
```

**完成回應**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "completed_at": "2026-01-20T10:30:25Z",
  "result_metadata": {
    "duration_ms": 5200,
    "latency_ms": 1850,
    "synthesis_mode": "segmented"
  },
  "audio_file_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

---

## 3. 下載音檔

```bash
curl -O http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/download
```

---

## 4. 列出所有工作

```bash
# 列出所有工作
curl http://localhost:8000/api/v1/jobs

# 篩選已完成的工作
curl "http://localhost:8000/api/v1/jobs?status=completed"

# 分頁查詢
curl "http://localhost:8000/api/v1/jobs?limit=10&offset=0"
```

---

## 5. 取消工作

僅限 `pending` 狀態的工作可取消：

```bash
curl -X DELETE http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

---

## 工作狀態說明

| 狀態 | 說明 | 可執行操作 |
|------|------|------------|
| `pending` | 等待中 | 取消 |
| `processing` | 處理中 | 等待 |
| `completed` | 已完成 | 下載、播放 |
| `failed` | 失敗 | 查看錯誤、重新提交 |
| `cancelled` | 已取消 | 重新提交 |

---

## 限制與注意事項

### 並發限制
- 每個使用者最多同時 3 個進行中工作（`pending` + `processing`）
- 超過時會收到 HTTP 429 錯誤

### 逾時
- 工作執行超過 10 分鐘會自動標記為失敗
- 錯誤訊息：「執行逾時」

### 重試
- TTS Provider 呼叫失敗時會自動重試最多 3 次
- 重試間隔遞增：5 秒、10 秒、20 秒

### 資料保留
- 已完成/失敗的工作保留 30 天
- 超過 30 天後自動清理（包含音檔）

---

## 錯誤處理

### 常見錯誤代碼

| 錯誤代碼 | HTTP 狀態 | 說明 |
|----------|-----------|------|
| `JOB_NOT_FOUND` | 404 | 工作不存在 |
| `JOB_LIMIT_EXCEEDED` | 429 | 已達並發上限 |
| `JOB_CANNOT_CANCEL` | 409 | 無法取消（非 pending 狀態） |
| `JOB_NOT_COMPLETED` | 404 | 音檔尚未完成 |

### 錯誤回應格式

```json
{
  "error": "JOB_LIMIT_EXCEEDED",
  "message": "已達並發上限，請等待現有工作完成",
  "details": {
    "current_jobs": 3,
    "max_jobs": 3
  }
}
```

---

## 前端整合範例

### React + TanStack Query

```tsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { jobApi } from '@/services/jobApi';

// 提交工作
const { mutate: submitJob } = useMutation({
  mutationFn: jobApi.createJob,
  onSuccess: (data) => {
    console.log('Job submitted:', data.id);
  }
});

// 查詢工作狀態（輪詢）
const { data: job } = useQuery({
  queryKey: ['job', jobId],
  queryFn: () => jobApi.getJob(jobId),
  refetchInterval: (data) =>
    data?.status === 'pending' || data?.status === 'processing'
      ? 5000 // 每 5 秒輪詢
      : false
});

// 下載音檔
const handleDownload = () => {
  window.open(jobApi.getDownloadUrl(jobId), '_blank');
};
```

---

## 下一步

- 查看 [API 合約規格](./contracts/jobs-api.yaml)
- 查看 [資料模型設計](./data-model.md)
- 查看 [研究文件](./research.md)
