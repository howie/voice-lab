# Quick Start: Gemini Lyria 音樂生成

**Feature**: 016-integration-gemini-lyria-music
**Date**: 2026-02-19

---

## 1. 環境設定

### 1.1 GCP 認證

Lyria 透過 Vertex AI 存取，需要 GCP Service Account 認證：

```bash
# 方法 A：使用 Service Account Key（本地開發）
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# 方法 B：使用 gcloud CLI（本地開發）
gcloud auth application-default login

# 方法 C：Cloud Run 自動使用附加的 Service Account（生產環境）
# 不需額外設定，由 Terraform 配置
```

### 1.2 環境變數

```bash
# .env 或 Cloud Run 環境變數
LYRIA_GCP_PROJECT_ID=your-gcp-project-id   # 可選，ADC 會自動偵測
LYRIA_GCP_LOCATION=us-central1              # Vertex AI 部署區域
LYRIA_MODEL=lyria-002                       # 模型代號
LYRIA_TIMEOUT=30.0                          # API 逾時秒數
```

### 1.3 GCP IAM 權限

Service Account 需要以下角色：

```
roles/aiplatform.user    # Vertex AI 使用者
```

或更精確的權限：

```
aiplatform.endpoints.predict    # 呼叫 predict 端點
```

### 1.4 依賴安裝

```bash
cd backend && uv sync
# 新增依賴：google-auth, httpx (已有)
```

---

## 2. API 使用範例

### 2.1 基本器樂生成

```bash
curl -X POST http://localhost:8000/api/v1/music/instrumental \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A calm acoustic folk song with gentle guitar melody and soft strings",
    "provider": "lyria"
  }'
```

回應：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "instrumental",
  "status": "pending",
  "provider": "lyria",
  "model": "lyria-002",
  "prompt": "A calm acoustic folk song with gentle guitar melody and soft strings",
  "created_at": "2026-02-19T10:30:00Z"
}
```

### 2.2 使用 Negative Prompt

```bash
curl -X POST http://localhost:8000/api/v1/music/instrumental \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Upbeat electronic dance music with synthesizer and crisp drum machine",
    "negative_prompt": "vocals, acoustic guitar, distortion",
    "provider": "lyria"
  }'
```

### 2.3 使用 Seed（可重現結果）

```bash
curl -X POST http://localhost:8000/api/v1/music/instrumental \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Relaxing ambient piano with gentle reverb",
    "seed": 42,
    "provider": "lyria"
  }'
```

### 2.4 批量生成（多首變體）

```bash
curl -X POST http://localhost:8000/api/v1/music/instrumental \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Epic cinematic orchestral with soaring strings and triumphant brass",
    "sample_count": 3,
    "provider": "lyria"
  }'
```

### 2.5 查詢任務狀態

```bash
curl http://localhost:8000/api/v1/music/jobs/550e8400-e29b-41d4-a716-446655440000
```

完成後回應：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "instrumental",
  "status": "completed",
  "provider": "lyria",
  "model": "lyria-002",
  "prompt": "A calm acoustic folk song with gentle guitar melody and soft strings",
  "result_url": "/api/v1/music/jobs/550e8400-e29b-41d4-a716-446655440000/download",
  "duration_ms": 32800,
  "created_at": "2026-02-19T10:30:00Z",
  "started_at": "2026-02-19T10:30:01Z",
  "completed_at": "2026-02-19T10:30:12Z"
}
```

### 2.6 下載生成結果

```bash
curl -O http://localhost:8000/api/v1/music/jobs/550e8400-e29b-41d4-a716-446655440000/download
```

### 2.7 列出可用 Providers

```bash
curl http://localhost:8000/api/v1/music/providers
```

回應：

```json
{
  "providers": [
    {
      "name": "mureka",
      "display_name": "Mureka AI",
      "available": true,
      "capabilities": ["song", "instrumental", "lyrics"],
      "supported_models": ["auto", "mureka-01", "v7.5", "v6"]
    },
    {
      "name": "lyria",
      "display_name": "Google Lyria",
      "available": true,
      "capabilities": ["instrumental"],
      "supported_models": ["lyria-002"],
      "limitations": [
        "僅支援英文 prompt",
        "固定 ~30 秒長度",
        "僅器樂（無人聲/歌詞）"
      ]
    }
  ]
}
```

---

## 3. Prompt 撰寫指南

### 3.1 基本原則

| 原則 | 說明 | 範例 |
|------|------|------|
| 具體描述 | 使用形容詞描繪音效畫面 | "warm acoustic guitar" 優於 "guitar" |
| 指明曲風 | 明確陳述類別和時代 | "90s trip-hop", "Baroque chamber music" |
| 指定樂器 | 點名具體樂器 | "Rhodes piano, cello, tabla" |
| 描述情緒 | 加入情感描述 | "melancholic", "upbeat", "ethereal" |
| 善用 negative | 排除不想要的元素 | "no vocals, no distortion" |

### 3.2 Prompt 範例

**簡單**：
```
prompt: "An uplifting and hopeful orchestral piece with soaring string melody"
```

**詳細**：
```
prompt: "Create a track that merges 1970s funk with modern synthwave. 110 BPM. Slap bass, Moog synthesizer, crisp drum machine with reverb."
negative_prompt: "vocals, distortion, acoustic instruments"
```

**品牌音效**：
```
prompt: "Gentle, warm corporate background music with soft piano and light strings. Professional, trustworthy, modern feel."
negative_prompt: "drums, electronic, bass-heavy"
```

---

## 4. 錯誤處理

| 錯誤碼 | 原因 | 處理方式 |
|--------|------|---------|
| `validation_error` | 非英文 prompt、seed+sample_count 衝突 | 修正輸入 |
| `provider_unavailable` | GCP 認證失敗或 Vertex AI 不可用 | 檢查 Service Account 設定 |
| `safety_filtered` | Prompt 被安全過濾器攔截 | 修改描述內容 |
| `quota_exceeded` | 配額已滿 | 等待配額重設或聯繫管理員 |
| `generation_failed` | Vertex AI 回傳錯誤 | 重試任務 |

---

## 5. Lyria vs Mureka 使用指南

| 場景 | 建議 Provider | 理由 |
|------|--------------|------|
| 純器樂 BGM | **Lyria** | 48 kHz 高音質、IP 保障、$0.06/30s |
| 含人聲歌曲 | **Mureka** | Lyria 2 不支援人聲 |
| 歌詞生成 | **Mureka** | Lyria 2 不支援歌詞 |
| 中文描述 | **Mureka** | Lyria 2 僅支援英文 |
| 需要 IP 保障 | **Lyria** | Google 提供雙重 IP 賠償保障 |
| 需要長音樂 (>30s) | **Mureka** | Mureka 支援至 5 分鐘 |
| 需要可重現結果 | **Lyria** | seed 參數確保結果一致 |

---

## 6. Vertex AI 直接呼叫（參考）

如需繞過 Voice Lab 直接測試 Vertex AI API：

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/lyria-002:predict" \
  -d '{
    "instances": [
      {
        "prompt": "A calm acoustic folk song with gentle guitar",
        "negative_prompt": "drums, electric guitar"
      }
    ],
    "parameters": {
      "sample_count": 1
    }
  }'
```

回應包含 base64 編碼的 WAV 音訊：

```json
{
  "predictions": [
    {
      "audioContent": "UklGRi...(base64 WAV data)...",
      "mimeType": "audio/wav"
    }
  ]
}
```

解碼並播放：

```bash
echo '<base64_audio_content>' | base64 -d > output.wav
ffplay output.wav
```

---

*Last updated: 2026-02-19*
