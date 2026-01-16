# Quickstart: Pipecat TTS Server

**Feature Branch**: `001-pipecat-tts-server`
**Date**: 2026-01-16

本指南協助開發者快速啟動 Voice Lab TTS 伺服器，包含後端 API 與前端 Web 介面。

---

## Prerequisites

### 系統需求

- **Python**: 3.11 或更高版本
- **Node.js**: 18 或更高版本
- **PostgreSQL**: 15 或更高版本（可選，用於持久化）
- **Docker & Docker Compose**: （可選，用於容器化部署）

### API 金鑰

您需要取得以下服務的 API 金鑰（至少一個）：

| Provider | 取得連結 | 環境變數 |
|----------|----------|----------|
| Azure Speech | [Azure Portal](https://portal.azure.com/) | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` |
| Google Cloud TTS | [GCP Console](https://console.cloud.google.com/) | `GOOGLE_APPLICATION_CREDENTIALS` |
| ElevenLabs | [ElevenLabs Dashboard](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| VoAI | [VoAI Platform](https://voai.tw/) | `VOAI_API_KEY` |

### Google SSO 設定

為了啟用身份驗證，您需要在 [Google Cloud Console](https://console.cloud.google.com/apis/credentials) 建立 OAuth 2.0 憑證：

1. 建立 OAuth 2.0 Client ID（Web Application 類型）
2. 設定授權的重新導向 URI：
   - 開發環境：`http://localhost:8000/api/v1/auth/google/callback`
   - 生產環境：`https://your-domain.com/api/v1/auth/google/callback`
3. 記下 Client ID 和 Client Secret

---

## 快速啟動

### 方式一：本機開發

#### 1. 後端設定

```bash
# 進入後端目錄
cd backend

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴（含開發套件）
pip install -e ".[dev]"

# 複製環境變數範本
cp .env.example .env
```

編輯 `.env` 檔案，設定必要的環境變數：

```env
# Server
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/voicelab

# Google SSO
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# TTS Providers (至少設定一個)
AZURE_SPEECH_KEY=your-azure-key
AZURE_SPEECH_REGION=eastasia

GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

ELEVENLABS_API_KEY=your-elevenlabs-key

VOAI_API_KEY=your-voai-key

# Storage
STORAGE_PATH=./storage
```

啟動後端伺服器：

```bash
# 執行資料庫遷移（如果使用 PostgreSQL）
alembic upgrade head

# 啟動開發伺服器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API 文件可於 `http://localhost:8000/docs` 查看。

#### 2. 前端設定

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# 複製環境變數範本
cp .env.example .env.local
```

編輯 `.env.local`：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

啟動前端開發伺服器：

```bash
npm run dev
```

前端可於 `http://localhost:5173` 存取。

### 方式二：Docker Compose

```bash
# 在專案根目錄
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

服務將於以下位置可用：
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- API Docs: `http://localhost:8000/docs`

---

## 使用範例

### 1. 基本語音合成（cURL）

```bash
# 批次模式合成
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "text": "你好，歡迎使用 Voice Lab 語音合成服務。",
       "provider": "azure",
       "voice_id": "zh-TW-HsiaoChenNeural",
       "language": "zh-TW"
     }' \
     --output output.mp3

# 播放合成結果
afplay output.mp3  # macOS
# aplay output.mp3  # Linux
```

### 2. 串流模式合成

```bash
curl -X POST "http://localhost:8000/api/v1/tts/stream" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "text": "這是一段串流合成的測試文字。",
       "provider": "elevenlabs",
       "voice_id": "21m00Tcm4TlvDq8ikWAM",
       "language": "zh-TW",
       "speed": 1.2
     }' \
     --output stream_output.mp3
```

### 3. 列出可用音色

```bash
# 列出所有音色
curl "http://localhost:8000/api/v1/voices" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 依語言過濾
curl "http://localhost:8000/api/v1/voices?language=zh-TW" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 依提供者過濾
curl "http://localhost:8000/api/v1/voices?provider=azure" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Python SDK 範例

```python
import httpx
import asyncio

async def synthesize_speech():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/tts/synthesize",
            headers={"Authorization": "Bearer YOUR_JWT_TOKEN"},
            json={
                "text": "你好，這是 Python SDK 範例。",
                "provider": "gcp",
                "voice_id": "cmn-TW-Standard-A",
                "language": "zh-TW",
                "speed": 1.0,
            },
        )

        if response.status_code == 200:
            with open("output.mp3", "wb") as f:
                f.write(response.content)
            print(f"Duration: {response.headers.get('X-Synthesis-Duration-Ms')}ms")
            print(f"Latency: {response.headers.get('X-Synthesis-Latency-Ms')}ms")
        else:
            print(f"Error: {response.json()}")

asyncio.run(synthesize_speech())
```

### 5. JavaScript/TypeScript 範例

```typescript
async function synthesizeSpeech() {
  const response = await fetch('http://localhost:8000/api/v1/tts/synthesize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_JWT_TOKEN',
    },
    body: JSON.stringify({
      text: '這是前端呼叫 API 的範例。',
      provider: 'azure',
      voice_id: 'zh-TW-YunJheNeural',
      language: 'zh-TW',
    }),
  });

  if (response.ok) {
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
  } else {
    const error = await response.json();
    console.error('Error:', error);
  }
}
```

---

## 測試

### 執行測試套件

```bash
cd backend

# 執行所有測試
pytest

# 執行合約測試
pytest tests/contract/

# 執行單元測試並產生覆蓋率報告
pytest tests/unit/ --cov=src --cov-report=html

# 執行整合測試（需要 API 金鑰）
pytest tests/integration/ -v
```

### 效能基準測試

```bash
# 執行效能測試（需要設定環境變數）
pytest tests/benchmark/ -v --benchmark-only
```

---

## 健康檢查

```bash
# 系統健康狀態
curl http://localhost:8000/api/v1/health

# 就緒檢查
curl http://localhost:8000/api/v1/health/ready

# 特定提供者健康狀態
curl "http://localhost:8000/api/v1/providers/azure/health" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 常見問題

### Q: 如何取得 JWT Token？

1. 透過瀏覽器訪問 `http://localhost:8000/api/v1/auth/google`
2. 完成 Google 登入流程
3. 登入成功後，Token 會存儲在 Cookie 或 LocalStorage 中

### Q: 為什麼合成請求返回 503 錯誤？

檢查以下項目：
1. 對應提供者的 API 金鑰是否正確設定
2. 網路連線是否正常
3. 使用 `/providers/{provider}/health` 檢查提供者狀態

### Q: 如何增加文字長度限制？

目前限制為 5000 字元。如需調整，修改 `backend/src/config.py` 中的 `MAX_TEXT_LENGTH` 設定。

---

## 下一步

- 閱讀 [API 合約文件](./contracts/openapi.yaml) 了解完整 API 規格
- 查看 [資料模型文件](./data-model.md) 了解領域實體定義
- 參考 [研究文件](./research.md) 了解技術決策背景
