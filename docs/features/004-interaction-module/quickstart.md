# Quick Start: Voice Interaction Testing Module

本指南說明如何快速開始使用語音互動測試模組。

## 前置需求

### 1. 系統需求
- Node.js 18+ (前端開發)
- Python 3.11+ (後端開發)
- PostgreSQL 16+
- Redis 7+
- 現代瀏覽器 (Chrome, Firefox, Safari) 且支援 WebRTC

### 2. API 憑證
至少需要以下其中一組憑證：

**Realtime API 模式**:
- OpenAI API Key (支援 Realtime API)

**Cascade 模式**:
- STT: Deepgram 或 AssemblyAI API Key
- LLM: OpenAI 或 Google Gemini API Key
- TTS: Azure Speech, Google TTS, 或 ElevenLabs API Key

## 設定步驟

### 1. 環境變數

複製範例檔案並填入憑證：

```bash
cp backend/.env.example backend/.env
```

編輯 `backend/.env`，新增以下變數：

```bash
# OpenAI (Realtime + LLM)
OPENAI_API_KEY=sk-...

# Google Gemini (LLM)
GOOGLE_GEMINI_API_KEY=...

# STT Providers (選擇至少一個)
DEEPGRAM_API_KEY=...
ASSEMBLYAI_API_KEY=...

# TTS Providers (Phase 1 已設定)
# AZURE_SPEECH_KEY=...
# ELEVENLABS_API_KEY=...
```

或者，透過 BYOL 介面在執行時設定憑證。

### 2. 資料庫遷移

```bash
cd backend
uv run alembic upgrade head
```

### 3. 啟動服務

**後端**:
```bash
cd backend
uv run uvicorn src.main:app --reload --port 8000
```

**前端**:
```bash
cd frontend
npm install
npm run dev
```

### 4. 存取應用程式

開啟瀏覽器至 `http://localhost:5173`，導航至「互動測試」頁面。

## 使用指南

### 基本對話流程

1. **選擇模式**
   - **Realtime API**: 最低延遲，適合流暢對話測試
   - **Cascade**: 可自由組合提供者，適合比較測試

2. **設定系統提示詞** (選填)
   - 選擇預設模板或自訂提示詞
   - 例如：「你是一個友善的客服代表，用繁體中文回答問題」

3. **開始對話**
   - 點擊「開始對話」按鈕
   - 授權麥克風存取
   - 對著麥克風說話

4. **查看延遲數據**
   - 每次對話回合結束後顯示延遲統計
   - Cascade 模式會顯示各階段分段延遲

5. **結束對話**
   - 點擊「結束對話」按鈕
   - 查看對話摘要和整體延遲統計

### 打斷測試

1. 確認「打斷功能」已啟用（預設開啟）
2. 在 AI 說話時開始說話
3. 觀察 AI 是否立即停止播放
4. 查看打斷延遲數據

### 對話歷史

1. 導航至「歷史記錄」頁面
2. 使用篩選器選擇日期範圍或模式
3. 點擊任一記錄查看詳情
4. 點擊「播放」回放對話音訊

## API 範例

### WebSocket 連線 (JavaScript)

```javascript
// mode 可以是 'realtime' 或 'cascade'
const ws = new WebSocket('ws://localhost:8000/api/v1/interaction/ws/realtime?token=YOUR_JWT');

ws.onopen = () => {
  // 開始會話
  ws.send(JSON.stringify({
    type: 'start_session',
    mode: 'realtime',
    config: {
      realtime_provider: 'openai',
      voice: 'alloy'
    },
    system_prompt: '你是一個友善的助理'
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case 'session_started':
      console.log('Session started:', msg.session_id);
      // 開始發送音訊
      break;
    case 'audio_chunk':
      // 播放 AI 回應音訊
      playAudio(msg.audio);
      break;
    case 'response_ended':
      console.log('Latency:', msg.latency);
      break;
  }
};

// 發送音訊
function sendAudio(pcm16Base64) {
  ws.send(JSON.stringify({
    type: 'audio_chunk',
    audio: pcm16Base64
  }));
}
```

### REST API (curl)

```bash
# 取得會話列表
curl -X GET "http://localhost:8000/api/v1/interaction/sessions" \
  -H "Authorization: Bearer YOUR_JWT"

# 取得延遲統計
curl -X GET "http://localhost:8000/api/v1/interaction/sessions/{session_id}/latency" \
  -H "Authorization: Bearer YOUR_JWT"

# 取得可用提供者
curl -X GET "http://localhost:8000/api/v1/interaction/providers" \
  -H "Authorization: Bearer YOUR_JWT"
```

## 疑難排解

### 麥克風無法存取

1. 確認瀏覽器已授權麥克風權限
2. 檢查是否使用 HTTPS 或 localhost
3. 嘗試重新整理頁面

### WebSocket 連線失敗

1. 確認後端服務正在執行
2. 檢查 JWT token 是否有效
3. 查看瀏覽器開發者工具的網路標籤

### 高延遲

1. 檢查網路連線品質
2. 嘗試切換到 Realtime API 模式
3. 選擇地理位置較近的提供者

### API 配額超限

1. 檢查提供者的 API 配額限制
2. 透過 BYOL 切換到其他提供者
3. 聯繫提供者提升配額

## 下一步

- 閱讀 [WebSocket API 合約](./contracts/websocket-api.md) 了解完整協議
- 閱讀 [REST API 合約](./contracts/rest-api.yaml) 了解 REST 端點
- 閱讀 [資料模型](./data-model.md) 了解資料結構
