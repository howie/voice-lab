# Voice Lab

語音服務測試平台 - 比較各家 TTS、STT 和即時互動服務

## 功能特色

- **TTS 測試**: 輸入文字，比較 Google Cloud、Azure、ElevenLabs、VoAI 的語音合成品質
- **STT 測試**: 錄音或上傳音檔，測試各家語音辨識準確度（支援兒童語音模式）
- **互動測試**: 測試即時語音對話的延遲和回應品質
- **歷史紀錄**: 保存所有測試結果，支援匯出報表

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

| Provider | TTS | STT | 備註 |
|----------|-----|-----|------|
| Google Cloud | ✅ | ✅ | Cloud Text-to-Speech, Cloud Speech-to-Text |
| Microsoft Azure | ✅ | ✅ | Azure Speech Services |
| ElevenLabs | ✅ | ❌ | 高品質 TTS |
| VoAI | ✅ | ✅ | 台灣本土服務 |

## 文件

- [PRD](docs/planning/PRD.md) - 產品需求文件
- [Overall Plan](docs/planning/overall-plan.md) - 技術架構和實作計劃

## License

MIT
