# Implementation Plan: STT Speech-to-Text Testing Module

**Branch**: `003-stt-testing-module` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/003-stt-testing-module/spec.md`

## Summary

建立一個 STT 語音辨識測試平台，讓使用者可以透過上傳音檔或麥克風錄音，測試 Azure、GCP、OpenAI Whisper 三家 STT Provider 的辨識效果。系統採用**批次辨識模式**，專注於 WER/CER 準確度計算與多 Provider 比較功能。

> **Note**: Streaming STT 延後至 Phase 4 Interaction 模組，更適合即時對話場景。

技術方案：
- 後端參照現有 TTS Provider 抽象層架構，建立對稱的 STT Provider 抽象層 (`ISTTProvider`)
- 前端新增 STT 測試頁面，整合 MediaRecorder API 進行麥克風錄音
- 批次辨識：錄音/上傳完成後送出 REST API 進行辨識
- 擴展現有 domain entities (`STTRequest`, `STTResult`) 並新增 WER 計算服務

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, google-cloud-speech, azure-cognitiveservices-speech, openai (Whisper)
- Frontend: React 18, Vite 5, WaveSurfer.js, MediaRecorder API
**Storage**: PostgreSQL (transcription history), Local filesystem (uploaded audio)
**Testing**: pytest, pytest-asyncio (Backend), Vitest (Frontend)
**Target Platform**: Web application (Linux server + Modern browsers)
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- Batch transcription response within 30 seconds for 1-minute audio
- WER calculation within 1 second
- 3 concurrent transcription requests
**Constraints**:
- Provider-specific file size/duration limits
- Audio recording minimum 16kHz sample rate
- Batch mode only (no streaming in this phase)
**Scale/Scope**: Single-tenant testing platform, history per user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Notes |
|-----------|--------|------------------|
| **I. TDD** | ✅ PASS | Contract tests 先行定義 STT Provider 介面，再實作各 Provider adapter |
| **II. Unified API Abstraction** | ✅ PASS | 建立 `ISTTProvider` 介面，參照現有 `ITTSProvider` 結構 |
| **III. Performance Benchmarking** | ✅ PASS | WER/CER 計算即為 STT 準確度基準，延遲追蹤已納入 `STTResult` |
| **IV. Documentation First** | ✅ PASS | 本 plan 及 quickstart.md 先於實作產出 |
| **V. Clean Architecture** | ✅ PASS | 遵循現有分層：domain → application → infrastructure |

**Gate Result**: ✅ ALL PASS - 可進入 Phase 0

## Project Structure

### Documentation (this feature)

```text
docs/features/003-stt-testing-module/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   └── stt-api.yaml
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── stt.py              # [EXTEND] STTRequest, STTResult, WordTiming
│   │   │   └── wer_analysis.py     # [NEW] WER/CER analysis entity
│   │   ├── services/
│   │   │   └── wer_calculator.py   # [NEW] WER/CER calculation logic
│   │   └── repositories/
│   │       └── transcription_repository.py  # [NEW] History persistence
│   ├── application/
│   │   ├── interfaces/
│   │   │   └── stt_provider.py     # [NEW] ISTTProvider interface
│   │   └── services/
│   │       └── stt_service.py      # [NEW] STT orchestration service
│   ├── infrastructure/
│   │   ├── providers/
│   │   │   └── stt/                # [NEW] STT provider implementations
│   │   │       ├── __init__.py
│   │   │       ├── base.py         # BaseSTTProvider
│   │   │       ├── azure_stt.py    # Azure Speech Services
│   │   │       ├── gcp_stt.py      # Google Cloud Speech-to-Text
│   │   │       ├── whisper_stt.py  # OpenAI Whisper
│   │   │       └── factory.py      # Provider factory
│   │   └── persistence/
│   │       └── transcription_repository_impl.py  # [NEW]
│   └── presentation/
│       └── api/
│           └── stt_routes.py       # [NEW] STT API endpoints (REST only)
└── tests/
    ├── contract/
    │   └── test_stt_provider_contract.py  # [NEW]
    ├── integration/
    │   └── test_stt_integration.py        # [NEW]
    └── unit/
        └── test_wer_calculator.py         # [NEW]

frontend/
├── src/
│   ├── routes/
│   │   └── STTTest.tsx             # [NEW] STT testing page
│   ├── components/
│   │   ├── stt/                    # [NEW] STT-specific components
│   │   │   ├── AudioRecorder.tsx   # Microphone recording (batch upload)
│   │   │   ├── AudioUploader.tsx   # File upload
│   │   │   ├── TranscriptDisplay.tsx  # Result display
│   │   │   ├── WERDisplay.tsx      # WER/CER visualization
│   │   │   └── ProviderComparison.tsx  # Multi-provider comparison
│   │   └── shared/
│   │       └── WaveformDisplay.tsx # Audio waveform (reuse from TTS)
│   ├── services/
│   │   └── sttApi.ts               # [NEW] STT API client (REST)
│   ├── stores/
│   │   └── sttStore.ts             # [NEW] STT state management
│   └── types/
│       └── stt.ts                  # [NEW] STT TypeScript types
└── tests/
    └── stt/
        └── STTTest.test.tsx        # [NEW] Component tests
```

**Structure Decision**: Web application 結構（Option 2），與現有 001/002 feature 一致。STT 模組對稱於 TTS 模組，放置於相同目錄層級。

## Complexity Tracking

> No violations requiring justification. Design follows existing patterns.

| Item | Notes |
|------|-------|
| Provider pattern | 複用 TTS 已建立的 Provider 抽象模式 |
| REST API only | 無 WebSocket，簡化架構（Streaming 留給 Phase 4） |
| BYOL integration | 複用 002 feature 的 credential management |

## Scope Boundaries

### In Scope (003 STT Testing)
- 批次辨識（上傳檔案、錄音後辨識）
- WER/CER 準確度計算
- 多 Provider 比較
- 歷史紀錄管理

### Out of Scope (Deferred to Phase 4 Interaction)
- ❌ Streaming STT（即時串流辨識）
- ❌ WebSocket 連線
- ❌ 即時對話 UI
- ❌ STT → LLM → TTS 整合
