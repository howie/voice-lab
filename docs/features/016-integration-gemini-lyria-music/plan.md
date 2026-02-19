# Implementation Plan: Gemini Lyria 音樂生成整合

**Branch**: `016-integration-gemini-lyria-music` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/016-integration-gemini-lyria-music/spec.md`

## Summary

整合 Google Gemini Lyria 模型系列為 Voice Lab 新增器樂背景音樂（BGM）生成能力。採用 Lyria 2 (`lyria-002`) 透過 Vertex AI REST API 作為首發 provider，並預留 Lyria 3 (`lyria-003-experimental`) 預覽版整合路徑。本功能插入現有 012-music-generation 的 `IMusicProvider` 架構，無需變更服務層或資料庫結構（僅新增 enum 值）。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+, google-auth, google-cloud-aiplatform (Vertex AI SDK)
**Storage**: PostgreSQL (複用現有 `music_generation_jobs` 表), Local filesystem / S3 (音檔儲存)
**Testing**: pytest, pytest-asyncio (Backend), Vitest (Frontend)
**Target Platform**: Linux server (Cloud Run), Web browser
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Vertex AI 回應 < 10 秒, 音檔下載 < 5 秒
**Constraints**: Lyria 2 僅支援器樂 (~32.8s/WAV/48kHz), 英文 prompt; 每次 $0.06/30s
**Scale/Scope**: 內部工具使用, 與 Mureka 互補, 預估每日 < 50 個生成任務

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| **I. TDD** | ✅ Pass | 為 Lyria API client 撰寫 contract tests，provider 撰寫 unit tests |
| **II. Unified API Abstraction** | ✅ Pass | Lyria 作為新的 provider 實作既有 `IMusicProvider` 介面 |
| **III. Performance Benchmarking** | ✅ Pass | 記錄生成時間、成功率、音質規格等指標 |
| **IV. Documentation First** | ✅ Pass | 本 plan 為文件先行，產出 quickstart.md 和 API contracts |
| **V. Clean Architecture** | ✅ Pass | 遵循現有 domain/application/infrastructure 分層，插入 Factory Pattern |

## Project Structure

### Documentation (this feature)

```text
docs/features/016-integration-gemini-lyria-music/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (已完成，位於 docs/research/2026-music-ai/gemini-lyria-music.md)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── lyria-api.yaml   # OpenAPI spec
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   └── entities/
│   │       └── music.py              # 新增 MusicProvider.LYRIA enum 值
│   ├── application/
│   │   └── interfaces/
│   │       └── music_provider.py     # 不需修改（沿用現有介面）
│   ├── infrastructure/
│   │   ├── adapters/
│   │   │   └── lyria/                # 新增
│   │   │       ├── __init__.py
│   │   │       └── client.py         # LyriaVertexAIClient
│   │   └── providers/
│   │       └── music/
│   │           ├── factory.py        # 新增 "lyria" 分支
│   │           └── lyria_music.py    # 新增 LyriaMusicProvider
│   ├── presentation/
│   │   └── api/
│   │       └── routes/
│   │           └── music.py          # 新增 LYRIA enum 至 MusicProviderEnum
│   └── config.py                     # 新增 lyria 相關設定
└── tests/
    ├── contract/
    │   └── music/
    │       └── test_lyria_contract.py  # 新增
    └── unit/
        └── music/
            └── test_lyria_provider.py  # 新增

frontend/
└── src/
    └── types/
        └── music.ts                   # 新增 "lyria" 至 MusicProvider union type
```

**Structure Decision**: 完全遵循 012-music-generation 建立的 Clean Architecture 分層結構。Lyria 整合是純粹的「新增 provider」操作，利用現有 Factory Pattern 插入，不需改動服務層、資料庫結構或 API 路由（僅新增 enum 值）。

## Complexity Tracking

> 無憲章違規需要說明

---

## Phase 0: Research Summary

研究已完成，詳見 [/docs/research/2026-music-ai/gemini-lyria-music.md](/docs/research/2026-music-ai/gemini-lyria-music.md)。

### 關鍵決策

| 決策 | 選擇 | 理由 | 替代方案 |
|------|------|------|----------|
| 首發 API 版本 | Lyria 2 (`lyria-002`) via Vertex AI | GA 穩定版、REST API、有 IP 賠償保障 | Lyria 3 (預覽版不穩定)、Lyria RealTime (實驗性 WebSocket) |
| 認證方式 | Google Cloud Service Account + OAuth 2.0 | 本專案已有 GCP Terraform 部署、統一認證 | API Key (Gemini API 用，但 Vertex AI 不支援) |
| HTTP 客戶端 | httpx (AsyncClient) | 與 Mureka adapter 一致，支援 async | google-cloud-aiplatform SDK (較重，隱藏 HTTP 細節) |
| 音檔處理 | 下載 base64 WAV → 轉 MP3 → 存至 storage | 與現有儲存機制一致 | 直接儲存 WAV (體積較大) |
| 整合架構 | 插入現有 IMusicProvider Factory | 最小改動、複用既有基礎設施 | 獨立模組 (重複造輪) |
| Lyria 3 策略 | 預留介面、待 GA 後整合 | `lyria-003-experimental` 仍在預覽 | 立即整合預覽版 (API 可能變動) |

---

## Phase 1: Design Artifacts

### 1.1 Data Model

詳見 [data-model.md](./data-model.md)

### 1.2 API Contracts

詳見 [contracts/lyria-api.yaml](./contracts/lyria-api.yaml)

### 1.3 Quickstart Guide

詳見 [quickstart.md](./quickstart.md)

---

## Implementation Phases

### Phase 1: MVP — Lyria 2 器樂 BGM 生成

**目標**: 透過 Vertex AI 整合 Lyria 2 作為新的音樂生成 provider

1. Backend: 設定 Google Cloud 認證與 Vertex AI 設定
2. Backend: LyriaVertexAIClient 實作（REST API 呼叫）
3. Backend: LyriaMusicProvider 實作（IMusicProvider 介面）
4. Backend: 註冊至 MusicProviderFactory
5. Backend: 新增 `MusicProvider.LYRIA` enum 值
6. Backend: WAV → MP3 音檔轉換與儲存
7. Backend: Contract tests + Unit tests
8. Frontend: 新增 Lyria provider 選項至音樂生成 UI

### Phase 2: 進階功能

**目標**: 強化 Lyria 特有功能

1. Backend: Negative prompt 支援
2. Backend: Seed / sample_count 參數支援
3. Backend: 批量生成（多首變體）
4. Frontend: Lyria 特有參數 UI（negative prompt、seed）
5. Frontend: 多首變體選擇 UI

### Phase 3: Lyria 3 整合（待 API 發布）

**目標**: 整合 Lyria 3 全功能音樂生成

1. Backend: 升級 client 支援 `lyria-003` 端點
2. Backend: 人聲 + 歌詞生成支援
3. Backend: 多模態輸入（圖片/影片 prompt）
4. Frontend: 人聲/歌詞生成 UI
5. Frontend: 多模態上傳 UI

---

## Next Steps

1. 執行 `/speckit.tasks` 生成詳細任務清單
2. 開始 Phase 1 MVP 實作

---

*Last updated: 2026-02-19*
