# Voice Lab - Overall Technical Plan

**Version**: 1.0
**Created**: 2026-01-16
**Status**: Draft

---

## 1. Project Overview

Voice Lab 是一個 Web-based 的語音服務測試平台，採用前後端分離架構，透過 Provider Abstraction Layer 統一管理多家語音服務商的 API。

### 1.1 Core Objectives

1. **易用性**：非技術人員能透過 Web UI 直接測試，無需寫程式
2. **可擴展性**：輕鬆新增支援的 Provider，無需修改核心邏輯
3. **可比較性**：同一測試可同時送出多家 Provider，並排比較結果
4. **可追溯性**：所有測試紀錄保存，支援歷史查詢與報表匯出

### 1.2 Target Providers

| Provider | 官方 SDK / API | 主要用途 |
|----------|---------------|----------|
| Google Cloud | google-cloud-speech, google-cloud-texttospeech | TTS, STT, Interaction |
| Microsoft Azure | azure-cognitiveservices-speech | TTS, STT, Interaction |
| ElevenLabs | elevenlabs | 高品質 TTS |
| VoAI | REST API | 中文 TTS, STT |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Voice Lab Platform                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Frontend (React + Vite)                      │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ │   │
│  │  │ TTS Panel │  │ STT Panel │  │Interaction│  │ Advanced/PostEdit │ │   │
│  │  │           │  │           │  │   Panel   │  │      Panel        │ │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ REST API / WebSocket                   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       Backend (Python FastAPI)                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │                    API Layer (Routes/Controllers)              │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │                      Service Layer                             │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │  │   │
│  │  │  │   TTS    │  │   STT    │  │Interaction│  │   History    │   │  │   │
│  │  │  │ Service  │  │ Service  │  │  Service  │  │   Service    │   │  │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │              Provider Abstraction Layer (PAL)                  │  │   │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐   │  │   │
│  │  │  │ TTSProvider│  │ STTProvider│  │   InteractionProvider  │   │  │   │
│  │  │  │   (ABC)    │  │   (ABC)    │  │         (ABC)          │   │  │   │
│  │  │  └────────────┘  └────────────┘  └────────────────────────┘   │  │   │
│  │  │           │              │                    │                │  │   │
│  │  │  ┌────────┴────────┬─────┴────────┬─────────┴──────────┐      │  │   │
│  │  │  ▼                 ▼              ▼                    ▼      │  │   │
│  │  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────────┐  │  │   │
│  │  │ │ GCP │ │Azure│ │Elev.│ │VoAI │ │ GCP │ │Azure│ │  VoAI   │  │  │   │
│  │  │ │ TTS │ │ TTS │ │Labs │ │ TTS │ │ STT │ │ STT │ │   STT   │  │  │   │
│  │  │ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────────┘  │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │ Database │    │  Storage │    │  Cache   │
              │(PostgreSQL)   │  (S3/GCS)│    │ (Redis)  │
              └──────────┘    └──────────┘    └──────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React 18 + Vite 5 + TypeScript | 極快 HMR、輕量打包、純 SPA 適合內部系統 |
| **UI Framework** | Tailwind CSS + Shadcn/ui | 快速開發、一致性設計 |
| **Routing** | React Router v6 | 成熟穩定、支援 nested routes |
| **State Management** | Zustand + TanStack Query | 輕量、適合中型應用 |
| **Backend** | Python 3.11 + FastAPI | 非同步支援、OpenAPI 自動文件 |
| **Provider SDK** | 各家官方 SDK | 最佳相容性 |
| **Database** | PostgreSQL 15 | 穩定、JSON 支援 |
| **Cache** | Redis | Session、暫存音檔 |
| **Storage** | AWS S3 / GCS | 音檔儲存 |
| **Auth** | react-oidc-context + OIDC | 公司 SSO 整合（純前端 OIDC） |
| **Real-time** | WebSocket (FastAPI WebSockets) | 串流辨識、即時互動 |

---

## 3. Provider Abstraction Layer (PAL)

參考 StoryBuddy 的 008-provider-abstraction-layer 設計，建立統一的 Provider 介面。

### 3.1 Core Interfaces

```python
# src/providers/base.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from enum import Enum

class AudioFormat(Enum):
    MP3 = "mp3"
    WAV = "wav"
    OPUS = "opus"
    WEBM = "webm"

@dataclass
class TTSRequest:
    text: str
    voice_id: str
    language: str = "zh-TW"
    speed: float = 1.0          # 0.5 - 2.0
    pitch: float = 0.0          # -20 to +20 semitones
    volume: float = 1.0         # 0.0 - 2.0
    output_format: AudioFormat = AudioFormat.MP3

@dataclass
class TTSResponse:
    audio_data: bytes
    format: AudioFormat
    duration_ms: int
    latency_ms: int
    cost_estimate: float
    provider: str
    voice_id: str

@dataclass
class STTRequest:
    audio_data: Optional[bytes] = None
    audio_url: Optional[str] = None
    language: str = "zh-TW"
    enable_streaming: bool = False
    child_mode: bool = False    # 兒童語音最佳化

@dataclass
class STTResponse:
    transcript: str
    confidence: float
    latency_ms: int
    words: list[dict]           # 逐字時間戳
    provider: str

@dataclass
class InteractionRequest:
    audio_data: bytes
    system_prompt: str
    context: list[dict]         # 對話歷史
    language: str = "zh-TW"

@dataclass
class InteractionResponse:
    user_transcript: str
    ai_text: str
    ai_audio: bytes
    stt_latency_ms: int
    llm_latency_ms: int
    tts_latency_ms: int
    total_latency_ms: int
    provider_config: dict


class TTSProvider(ABC):
    """TTS Provider 抽象介面"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名稱"""
        pass

    @property
    @abstractmethod
    def supported_voices(self) -> list[dict]:
        """支援的語音列表"""
        pass

    @property
    @abstractmethod
    def supported_params(self) -> dict:
        """支援的參數及其範圍"""
        pass

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """合成語音"""
        pass


class STTProvider(ABC):
    """STT Provider 抽象介面"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> list[str]:
        pass

    @abstractmethod
    async def transcribe(self, request: STTRequest) -> STTResponse:
        """轉錄音檔"""
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "zh-TW"
    ) -> AsyncIterator[STTResponse]:
        """串流轉錄"""
        pass


class InteractionProvider(ABC):
    """Interaction Provider 抽象介面（組合 STT + LLM + TTS）"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def process(self, request: InteractionRequest) -> InteractionResponse:
        """處理完整互動流程"""
        pass
```

### 3.2 Provider Factory

```python
# src/providers/factory.py

from typing import Type
from .base import TTSProvider, STTProvider, InteractionProvider

class ProviderFactory:
    _tts_registry: dict[str, Type[TTSProvider]] = {}
    _stt_registry: dict[str, Type[STTProvider]] = {}
    _interaction_registry: dict[str, Type[InteractionProvider]] = {}

    @classmethod
    def register_tts(cls, name: str, provider_class: Type[TTSProvider]):
        cls._tts_registry[name] = provider_class

    @classmethod
    def register_stt(cls, name: str, provider_class: Type[STTProvider]):
        cls._stt_registry[name] = provider_class

    @classmethod
    def register_interaction(cls, name: str, provider_class: Type[InteractionProvider]):
        cls._interaction_registry[name] = provider_class

    @classmethod
    def get_tts(cls, name: str, **kwargs) -> TTSProvider:
        if name not in cls._tts_registry:
            raise ValueError(f"Unknown TTS provider: {name}")
        return cls._tts_registry[name](**kwargs)

    @classmethod
    def get_stt(cls, name: str, **kwargs) -> STTProvider:
        if name not in cls._stt_registry:
            raise ValueError(f"Unknown STT provider: {name}")
        return cls._stt_registry[name](**kwargs)

    @classmethod
    def list_tts_providers(cls) -> list[str]:
        return list(cls._tts_registry.keys())

    @classmethod
    def list_stt_providers(cls) -> list[str]:
        return list(cls._stt_registry.keys())
```

### 3.3 Provider Implementations

```
src/providers/
├── __init__.py
├── base.py                    # 抽象介面定義
├── factory.py                 # Provider Factory
├── exceptions.py              # 統一例外類型
├── tts/
│   ├── __init__.py
│   ├── gcp_tts.py            # Google Cloud TTS
│   ├── azure_tts.py          # Azure Speech Services
│   ├── elevenlabs_tts.py     # ElevenLabs
│   └── voai_tts.py           # VoAI
├── stt/
│   ├── __init__.py
│   ├── gcp_stt.py            # Google Cloud Speech-to-Text
│   ├── azure_stt.py          # Azure Speech Services
│   └── voai_stt.py           # VoAI
└── interaction/
    ├── __init__.py
    ├── gcp_interaction.py     # GCP Dialogflow 或自組
    ├── azure_interaction.py   # Azure 或自組
    └── voai_interaction.py    # VoAI
```

---

## 4. Database Schema

### 4.1 Core Tables

```sql
-- 測試紀錄主表
CREATE TABLE test_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    test_type VARCHAR(20) NOT NULL,  -- 'tts', 'stt', 'interaction'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- TTS 測試紀錄
CREATE TABLE tts_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id UUID REFERENCES test_records(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    input_text TEXT NOT NULL,
    voice_id VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    speed DECIMAL(3,2),
    pitch DECIMAL(5,2),
    volume DECIMAL(3,2),
    output_format VARCHAR(10),
    audio_url TEXT,
    duration_ms INTEGER,
    latency_ms INTEGER,
    cost_estimate DECIMAL(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- STT 測試紀錄
CREATE TABLE stt_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id UUID REFERENCES test_records(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    audio_url TEXT NOT NULL,
    language VARCHAR(10) NOT NULL,
    child_mode BOOLEAN DEFAULT FALSE,
    transcript TEXT,
    confidence DECIMAL(5,4),
    latency_ms INTEGER,
    ground_truth TEXT,          -- 正確答案（用於計算 WER）
    wer DECIMAL(5,4),           -- Word Error Rate
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interaction 測試紀錄
CREATE TABLE interaction_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id UUID REFERENCES test_records(id) ON DELETE CASCADE,
    stt_provider VARCHAR(50) NOT NULL,
    llm_provider VARCHAR(50) NOT NULL,
    tts_provider VARCHAR(50) NOT NULL,
    system_prompt TEXT,
    user_audio_url TEXT,
    user_transcript TEXT,
    ai_text TEXT,
    ai_audio_url TEXT,
    stt_latency_ms INTEGER,
    llm_latency_ms INTEGER,
    tts_latency_ms INTEGER,
    total_latency_ms INTEGER,
    user_rating SMALLINT,       -- 1-5
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 語音設定檔
CREATE TABLE voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    voice_id VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    gender VARCHAR(20),
    description TEXT,
    sample_audio_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    UNIQUE(provider, voice_id)
);
```

---

## 5. API Design

### 5.1 REST API Endpoints

```yaml
# TTS APIs
POST   /api/v1/tts/synthesize           # 產生語音
GET    /api/v1/tts/providers            # 列出可用 Provider
GET    /api/v1/tts/providers/{name}/voices   # 列出 Provider 的語音
GET    /api/v1/tts/providers/{name}/params   # 列出 Provider 支援的參數

# STT APIs
POST   /api/v1/stt/transcribe           # 辨識音檔
GET    /api/v1/stt/providers            # 列出可用 Provider
WS     /api/v1/stt/stream               # 串流辨識 (WebSocket)

# Interaction APIs
POST   /api/v1/interaction/start        # 開始互動
WS     /api/v1/interaction/session      # 即時互動 (WebSocket)
GET    /api/v1/interaction/providers    # 列出可用組合

# History APIs
GET    /api/v1/history                  # 查詢測試紀錄
GET    /api/v1/history/{id}             # 取得單筆紀錄
GET    /api/v1/history/export           # 匯出報表
DELETE /api/v1/history/{id}             # 刪除紀錄

# Voice Profiles
GET    /api/v1/voices                   # 列出所有語音
GET    /api/v1/voices/{provider}        # 列出特定 Provider 語音
```

### 5.2 WebSocket Messages

```typescript
// STT Streaming
interface STTStreamMessage {
  type: 'audio_chunk' | 'transcript' | 'final' | 'error';
  data: {
    audio?: string;          // base64 encoded
    transcript?: string;
    confidence?: number;
    is_final?: boolean;
    error?: string;
  };
}

// Interaction Session
interface InteractionMessage {
  type: 'user_audio' | 'ai_response' | 'metrics' | 'error';
  data: {
    audio?: string;
    transcript?: string;
    ai_text?: string;
    latency?: {
      stt_ms: number;
      llm_ms: number;
      tts_ms: number;
      total_ms: number;
    };
    error?: string;
  };
}
```

---

## 6. Frontend Structure

```
frontend/
├── index.html                        # Vite 入口 HTML
├── vite.config.ts                    # Vite 設定
├── tailwind.config.js                # Tailwind 設定
├── tsconfig.json
├── package.json
├── public/
│   └── favicon.ico
└── src/
    ├── main.tsx                      # React 入口
    ├── App.tsx                       # 主應用 + Router 設定
    ├── routes/                       # React Router 頁面
    │   ├── index.tsx                 # 路由定義
    │   ├── Dashboard.tsx             # 首頁 Dashboard
    │   ├── tts/
    │   │   └── TTSPage.tsx           # TTS 測試頁面
    │   ├── stt/
    │   │   └── STTPage.tsx           # STT 測試頁面
    │   ├── interaction/
    │   │   └── InteractionPage.tsx   # 互動測試頁面
    │   ├── history/
    │   │   └── HistoryPage.tsx       # 歷史紀錄頁面
    │   └── advanced/
    │       └── AdvancedPage.tsx      # 進階功能頁面
    ├── components/
    │   ├── ui/                       # Shadcn/ui 元件
    │   ├── layout/
    │   │   ├── AppLayout.tsx         # 主版面配置
    │   │   ├── Sidebar.tsx           # 側邊欄
    │   │   └── Header.tsx            # 頂部導航
    │   ├── tts/
    │   │   ├── TTSForm.tsx
    │   │   ├── VoiceSelector.tsx
    │   │   ├── ParamSliders.tsx
    │   │   └── AudioComparison.tsx
    │   ├── stt/
    │   │   ├── AudioRecorder.tsx
    │   │   ├── FileUploader.tsx
    │   │   ├── TranscriptDisplay.tsx
    │   │   └── WERCalculator.tsx
    │   ├── interaction/
    │   │   ├── VoiceChat.tsx
    │   │   ├── LatencyMetrics.tsx
    │   │   └── ProviderSelector.tsx
    │   └── shared/
    │       ├── AudioPlayer.tsx
    │       ├── ProviderBadge.tsx
    │       └── LoadingSpinner.tsx
    ├── hooks/
    │   ├── useTTS.ts
    │   ├── useSTT.ts
    │   ├── useInteraction.ts
    │   └── useAudioRecorder.ts
    ├── lib/
    │   ├── api.ts                    # API client (axios/ky)
    │   ├── websocket.ts              # WebSocket client
    │   └── auth.ts                   # OIDC 設定
    ├── stores/
    │   └── useAppStore.ts            # Zustand store
    └── types/
        └── index.ts                  # TypeScript 型別定義
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**目標**：建立專案骨架與 Provider 抽象層

| Task | Description | Priority |
|------|-------------|----------|
| P1-01 | 專案初始化（React + Vite + FastAPI） | P0 |
| P1-02 | 建立 Provider Abstraction Layer 介面 | P0 |
| P1-03 | 實作 GCP TTS Provider | P0 |
| P1-04 | 實作 Azure TTS Provider | P0 |
| P1-05 | 建立 Database Schema | P0 |
| P1-06 | TTS API endpoints | P0 |
| P1-07 | 基本 TTS 前端頁面 | P0 |

**Deliverable**: 可測試 GCP 與 Azure TTS 的基本功能

### Phase 2: TTS Complete (Week 3-4)

**目標**：完成 TTS 模組全部功能

| Task | Description | Priority |
|------|-------------|----------|
| P2-01 | 實作 ElevenLabs TTS Provider | P0 |
| P2-02 | 實作 VoAI TTS Provider | P0 |
| P2-03 | 語音參數調整功能（速度、音調、音量） | P1 |
| P2-04 | A/B 比較功能 | P0 |
| P2-05 | 音檔下載功能 | P0 |
| P2-06 | 測試歷史紀錄 | P1 |

**Deliverable**: 完整的 TTS 測試平台

### Phase 3: STT Module (Week 5-6)

**目標**：完成 STT 模組

| Task | Description | Priority |
|------|-------------|----------|
| P3-01 | 實作 GCP STT Provider | P0 |
| P3-02 | 實作 Azure STT Provider | P0 |
| P3-03 | 實作 VoAI STT Provider | P0 |
| P3-04 | 麥克風錄音功能 | P0 |
| P3-05 | 音檔上傳功能 | P0 |
| P3-06 | 串流辨識 (WebSocket) | P1 |
| P3-07 | WER 計算功能 | P1 |
| P3-08 | 兒童語音模式 | P1 |

**Deliverable**: 完整的 STT 測試平台

### Phase 4: Interaction Module (Week 7-8)

**目標**：完成即時互動模組

| Task | Description | Priority |
|------|-------------|----------|
| P4-01 | Interaction Provider 架構 | P0 |
| P4-02 | 即時語音對話功能 | P0 |
| P4-03 | Provider 組合選擇 | P0 |
| P4-04 | 延遲量測與顯示 | P0 |
| P4-05 | 對話歷史紀錄 | P1 |
| P4-06 | System Prompt 設定 | P1 |

**Deliverable**: 完整的即時互動測試平台

### Phase 5: Polish & Advanced (Week 9-10)

**目標**：完善功能與進階特性

| Task | Description | Priority |
|------|-------------|----------|
| P5-01 | 報表匯出功能 | P2 |
| P5-02 | 批次處理功能 | P2 |
| P5-03 | UI/UX 優化 | P1 |
| P5-04 | 效能優化 | P1 |
| P5-05 | 混音基礎功能 | P2 |
| P5-06 | 使用者文件 | P1 |

**Deliverable**: Production-ready 平台

---

## 8. Milestones

| Milestone | Target Date | Criteria |
|-----------|-------------|----------|
| M1: TTS MVP | Week 2 | GCP + Azure TTS 可用 |
| M2: TTS Complete | Week 4 | 4 家 TTS + A/B 比較 |
| M3: STT Complete | Week 6 | 3 家 STT + 串流辨識 |
| M4: Interaction Complete | Week 8 | 即時對話 + 延遲量測 |
| M5: Production Ready | Week 10 | 完整功能 + 文件 |

---

## 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Provider API 變更 | Medium | High | 使用官方 SDK，持續監控更新 |
| 延遲不符預期 | Medium | Medium | 加入快取、選擇低延遲 region |
| VoAI API 不穩定 | Medium | Low | 實作 fallback 機制 |
| 音檔儲存成本過高 | Low | Medium | 設定自動清理策略 |
| 使用者難以上手 | Low | High | 充分測試、提供教學文件 |

---

## 10. Development Guidelines

### 10.1 Code Style

- **Python**: PEP 8, Black formatter, mypy type checking
- **TypeScript**: ESLint, Prettier
- **Commit**: Conventional Commits

### 10.2 Testing Strategy

| Level | Coverage Target | Tools |
|-------|-----------------|-------|
| Unit Tests | > 80% | pytest, Vitest |
| Integration Tests | Core flows | pytest-asyncio |
| E2E Tests | Critical paths | Playwright |

### 10.3 CI/CD

```yaml
# .github/workflows/ci.yml
- Lint & Format check
- Type check
- Unit tests
- Build check
- Deploy to staging (on PR merge)
- Deploy to production (on release tag)
```

---

## 11. Next Steps

1. **立即**：建立專案 repository 結構
2. **Week 1**：完成 Phase 1 基礎建設
3. **持續**：每週 Demo 進度，收集 feedback

---

## Appendix A: Provider SDK References

| Provider | SDK / API | Documentation |
|----------|-----------|---------------|
| GCP TTS | google-cloud-texttospeech | https://cloud.google.com/text-to-speech/docs |
| GCP STT | google-cloud-speech | https://cloud.google.com/speech-to-text/docs |
| Azure | azure-cognitiveservices-speech | https://learn.microsoft.com/azure/cognitive-services/speech-service/ |
| ElevenLabs | elevenlabs | https://docs.elevenlabs.io/ |
| VoAI | REST API | (內部文件) |

## Appendix B: Environment Variables

```bash
# GCP
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Azure
AZURE_SPEECH_KEY=xxx
AZURE_SPEECH_REGION=eastasia

# ElevenLabs
ELEVENLABS_API_KEY=xxx

# VoAI
VOAI_API_KEY=xxx
VOAI_API_ENDPOINT=https://api.voai.com

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/voicelab

# Redis
REDIS_URL=redis://localhost:6379

# Storage
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET=voicelab-audio
```
