# Voice Lab

語音服務測試平台 - 比較各家 TTS、STT 和即時互動服務

## 功能特色

- **TTS 測試**: 輸入文字，比較 Google Cloud、Azure、ElevenLabs、VoAI 的語音合成品質
  - 支援批次與串流模式
  - 可調整語速 (0.5x - 2.0x)、音調 (-20 到 +20)、音量 (0% - 200%)
  - 多語言支援：繁體中文、簡體中文、英文、日文、韓文
  - 即時波形顯示
- **STT 測試**: 錄音或上傳音檔，測試各家語音辨識準確度
  - 支援 8 家 Provider：Azure、GCP、Whisper、Deepgram、AssemblyAI、ElevenLabs、Speechmatics
  - WER/CER 準確度計算與對齊視覺化
  - 兒童語音模式 (Azure, GCP)
  - 多 Provider 並行比較
  - 麥克風錄音 (WebM/MP4) 與檔案上傳 (MP3, WAV, M4A, FLAC, WEBM)
- **API Key 管理**: BYOL (Bring Your Own License) 模式，安全儲存和驗證 API 金鑰
- **歷史紀錄**: 保存所有測試結果，支援搜尋和篩選
- **Google SSO 登入**: 安全的 OAuth 2.0 身份驗證

## 技術棧

### Frontend
- React 18 + Vite 5 + TypeScript
- Tailwind CSS + Shadcn/ui
- React Router v6
- Zustand + TanStack Query

### Backend
- Python 3.11 + FastAPI
- PostgreSQL + Redis
- Provider Abstraction Layer (PAL)

## 快速開始

### 環境需求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- [uv](https://github.com/astral-sh/uv) (Python 套件管理器)

### 安裝

```bash
# Clone 專案
git clone https://github.com/your-org/voice-lab.git
cd voice-lab

# 安裝所有依賴
make install

# 設定環境變數
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# 編輯 .env 填入各家 Provider 的 API Key
```

### 開發

```bash
# 同時啟動前後端開發伺服器
make dev

# 或分開啟動
make dev-back   # Backend: http://localhost:8000
make dev-front  # Frontend: http://localhost:5173
```

### 其他指令

```bash
make help       # 查看所有指令
make test       # 執行測試
make lint       # 檢查程式碼風格
make format     # 格式化程式碼
make build      # 建構前端
```

## 專案結構

```
voice-lab/
├── backend/                 # FastAPI 後端
│   ├── src/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心功能
│   │   ├── db/             # 資料庫
│   │   ├── models/         # Pydantic 模型
│   │   ├── providers/      # Provider 抽象層
│   │   │   ├── tts/        # TTS Provider 實作
│   │   │   ├── stt/        # STT Provider 實作
│   │   │   └── interaction/# 互動 Provider 實作
│   │   └── services/       # 業務邏輯
│   └── tests/
├── frontend/               # React + Vite 前端
│   └── src/
│       ├── components/     # UI 元件
│       ├── routes/         # 頁面
│       ├── hooks/          # Custom Hooks
│       ├── lib/            # 工具函式
│       └── types/          # TypeScript 型別
├── docs/                   # 文件
│   └── planning/           # PRD 和規劃文件
└── Makefile               # 開發指令
```

## 支援的 Provider

### TTS (Text-to-Speech)

| Provider | 批次模式 | 串流模式 | 備註 |
|----------|---------|---------|------|
| Google Cloud | ✅ | ✅ | Cloud Text-to-Speech |
| Microsoft Azure | ✅ | ✅ | Azure Speech Services |
| ElevenLabs | ✅ | ✅ | 高品質 TTS |
| VoAI | ✅ | ✅ | 台灣本土服務 |

### STT (Speech-to-Text)

| Provider | 兒童模式 | Word Timestamps | 最大檔案 | 備註 |
|----------|---------|----------------|---------|------|
| Microsoft Azure | ✅ | ✅ | 200 MB | Azure Speech Services |
| Google Cloud | ✅ | ✅ | 480 MB | Cloud Speech-to-Text |
| OpenAI Whisper | ❌ | ✅ | 25 MB | 高準確度 |
| Deepgram | ❌ | ✅ | 2 GB | Nova-2 模型 |
| AssemblyAI | ❌ | ✅ | 5 GB | Universal-2 模型 |
| ElevenLabs | ❌ | ✅ | 1 GB | Scribe 模型 |
| Speechmatics | ❌ | ✅ | 1 GB | 多語言支援 |

## 文件

- [PRD](docs/planning/PRD.md) - 產品需求文件
- [Overall Plan](docs/planning/overall-plan.md) - 技術架構和實作計劃
- [Roadmap](docs/features/roadmap.md) - 產品開發路線圖
- [TTS Quickstart](docs/features/001-pipecat-tts-server/quickstart.md) - TTS 功能快速入門
- [STT Quickstart](docs/features/003-stt-testing-module/quickstart.md) - STT 功能快速入門
- [API Reference](docs/features/001-pipecat-tts-server/api-reference.md) - API 參考文件

## API 快速範例

### TTS (語音合成)

```bash
# 語音合成
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "text": "你好，歡迎使用 Voice Lab",
       "provider": "azure",
       "voice_id": "zh-TW-HsiaoChenNeural"
     }' --output output.mp3

# 列出可用語音
curl "http://localhost:8000/api/v1/voices?language=zh-TW" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### STT (語音辨識)

```bash
# 語音辨識
curl -X POST "http://localhost:8000/api/v1/stt/transcribe" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "audio=@test_audio.mp3" \
     -F "provider=azure" \
     -F "language=zh-TW"

# 多 Provider 比較
curl -X POST "http://localhost:8000/api/v1/stt/compare" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "audio=@test_audio.mp3" \
     -F "providers=azure" \
     -F "providers=whisper" \
     -F "language=zh-TW" \
     -F "ground_truth=正確的轉錄文字"

# 列出可用 Provider
curl "http://localhost:8000/api/v1/stt/providers" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## License

MIT
