# Implementation Plan: Pipecat TTS Server

**Branch**: `001-pipecat-tts-server` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/001-pipecat-tts-server/spec.md`

## Summary

建立基於 Pipecat 的多提供者 TTS API 伺服器，支援 Azure Speech、ElevenLabs、Google Cloud TTS 與 VoAI 四個提供者，並提供 React + Vite Web 介面進行即時試聽。系統支援批次合成與即時串流兩種輸出模式，使用 Google SSO 進行身份驗證，音訊檔案永久儲存於本地。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, Pipecat-AI 0.50+, azure-cognitiveservices-speech, google-cloud-texttospeech, elevenlabs, httpx
- Frontend: React 18.2+, Vite 5.0+, TanStack Query, Zustand, WaveSurfer.js (待加入)

**Storage**: Local filesystem (`storage/{provider}/{uuid}.mp3`), SQLAlchemy + PostgreSQL (metadata)
**Testing**: pytest, pytest-asyncio (Backend), vitest (Frontend)
**Target Platform**: Linux server (Docker), Modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: web (frontend + backend)
**Performance Goals**: TTFB < 500ms (streaming), < 5s total (batch, 100 chars), 10 concurrent requests
**Constraints**: < 5000 字元輸入限制, 語速 0.5x-2.0x 範圍
**Scale/Scope**: 單一伺服器部署，10 並發用戶，展示/測試用途

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-design Check (Phase 0)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-Driven Development | ✅ PASS | 規格明確定義驗收情境，tests/ 目錄已包含 contract/、integration/、unit/ 結構 |
| II. Unified API Abstraction | ✅ PASS | 規格要求 FR-012 用戶可指定 TTS 提供者，研究文件定義統一 Service 介面 |
| III. Performance Benchmarking | ✅ PASS | Success Criteria SC-001~SC-003 定義可量測效能指標 |
| IV. Documentation First | ✅ PASS | 本計畫先於實作產生，quickstart.md 將於 Phase 1 產生 |
| V. Clean Architecture | ✅ PASS | 現有結構 domain/application/infrastructure/presentation 符合分層原則 |

### Technical Standards Check

| Standard | Status | Evidence |
|----------|--------|----------|
| Python 3.11+ | ✅ PASS | pyproject.toml: `requires-python = ">=3.11"` |
| pytest + pytest-asyncio | ✅ PASS | pyproject.toml dev dependencies 已包含 |
| mypy strict mode | ✅ PASS | pyproject.toml: `strict = true` |
| ruff formatting | ✅ PASS | pyproject.toml: ruff 設定完整 |
| 環境變數設定 | ✅ PASS | 使用 pydantic-settings，無硬編碼 |

**GATE RESULT**: ✅ PASS - 可進行 Phase 0

## Project Structure

### Documentation (this feature)

```text
docs/features/001-pipecat-tts-server/
├── plan.md              # This file
├── research.md          # Phase 0 output (已完成)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # REST API 合約
├── checklists/          # 需求追蹤
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/              # 領域模型（無外部依賴）
│   │   └── entities/
│   │       └── tts.py       # TTSRequest, TTSResult, VoiceOption
│   ├── application/         # 應用服務層
│   │   ├── interfaces/      # 抽象介面 (Protocols)
│   │   │   ├── tts_provider.py
│   │   │   └── storage_service.py
│   │   ├── use_cases/       # 業務邏輯
│   │   │   └── synthesize_speech.py
│   │   └── dto/             # 資料傳輸物件
│   ├── infrastructure/      # 外部服務實作
│   │   ├── providers/
│   │   │   └── tts/
│   │   │       ├── base.py
│   │   │       ├── azure.py
│   │   │       ├── elevenlabs.py
│   │   │       ├── google.py
│   │   │       └── voai.py
│   │   ├── storage/
│   │   │   └── local_storage.py
│   │   └── persistence/
│   │       ├── database.py
│   │       └── models.py
│   └── presentation/        # API 層
│       └── api/
│           ├── routes/
│           │   └── tts.py
│           ├── middleware/
│           └── schemas/
├── tests/
│   ├── contract/            # API 合約測試
│   ├── integration/         # 整合測試
│   └── unit/                # 單元測試
├── alembic/                 # 資料庫遷移
└── pyproject.toml

frontend/
├── src/
│   ├── components/          # UI 元件
│   │   ├── ui/              # shadcn/ui 基礎元件
│   │   ├── tts/             # TTS 專用元件 (待建立)
│   │   │   ├── TextInput.tsx
│   │   │   ├── VoiceSelector.tsx
│   │   │   ├── AudioPlayer.tsx
│   │   │   └── WaveformDisplay.tsx
│   │   └── auth/            # 認證元件 (待建立)
│   ├── hooks/               # 自訂 hooks
│   ├── lib/                 # 工具函式
│   ├── routes/              # 頁面路由
│   ├── stores/              # Zustand 狀態管理
│   └── types/               # TypeScript 類型定義
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

**Structure Decision**: 採用 Web Application 結構 (Option 2)，前後端分離。後端遵循 Clean Architecture 四層結構，前端使用 React + Vite + shadcn/ui 技術棧。

## Complexity Tracking

> 無違反憲章原則的情況，無需填寫。

---

## Phase 0: Research Summary

**Status**: ✅ 完成

研究結果已記錄於 [research.md](./research.md)，主要決策：

| 項目 | 決策 | 理由 |
|------|------|------|
| TTS Engine | Pipecat 內建 Services | 已封裝串流邏輯，統一 Frame 介面 |
| VoAI 整合 | 自訂 TTSService | 繼承 BaseTTSService 快速實作 |
| 串流播放 | Web Audio API + WaveSurfer.js | 主流瀏覽器支援，波形視覺化 |
| 語言支援 | 統一內部映射 | 各提供者代碼不同，由 backend 處理 |

所有 NEEDS CLARIFICATION 項目已於 spec.md Session 2026-01-16 解決。

---

## Phase 1: Design Artifacts

### Artifacts to Generate

1. **data-model.md** - 領域實體定義與關係
2. **contracts/openapi.yaml** - REST API OpenAPI 3.0 規格
3. **quickstart.md** - 開發者快速開始指南

### Post-design Constitution Re-check

*Phase 1 設計完成，驗證結果如下：*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. TDD | ✅ PASS | `contracts/openapi.yaml` 定義完整 API 規格，可作為合約測試依據；`quickstart.md` 包含測試執行指南 |
| II. Unified API | ✅ PASS | `data-model.md` 定義 `ITTSProvider` 統一介面，四個提供者實作相同協定 |
| III. Benchmarking | ✅ PASS | `quickstart.md` 包含效能測試指南；`data-model.md` 定義 `latency_ms`, `duration_ms` 效能指標 |
| IV. Documentation First | ✅ PASS | 所有設計文件（plan.md, research.md, data-model.md, contracts/, quickstart.md）先於實作產生 |
| V. Clean Architecture | ✅ PASS | 專案結構遵循 domain/application/infrastructure/presentation 四層架構 |

**GATE RESULT**: ✅ PASS - Phase 1 設計完成，可進行 Phase 2 任務生成（/speckit.tasks）
