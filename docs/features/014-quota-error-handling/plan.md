# Implementation Plan: API Quota Error Handling

**Branch**: `014-quota-error-handling` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/014-quota-error-handling/spec.md`

## Summary

統一處理各 API 供應商的配額超限錯誤 (HTTP 429)，透過新增 `QuotaExceededError` 例外類別、在各 TTS/STT provider 捕獲 429 錯誤，並於 Frontend 提供友善的中文錯誤訊息與解決建議。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, httpx, Pydantic 2.0+, React 18+, Lucide React (icons)
**Storage**: N/A (此功能不涉及新增儲存需求)
**Testing**: pytest, pytest-asyncio (Backend), Vitest (Frontend)
**Target Platform**: Linux server (Docker), Web browser
**Project Type**: web (backend + frontend)
**Performance Goals**: 錯誤回應延遲 < 50ms
**Constraints**: 保持向下相容的 API 回應格式
**Scale/Scope**: 支援 7 個 TTS/STT provider (Gemini, ElevenLabs, Azure, GCP, OpenAI, Deepgram, VoAI)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. TDD | ✅ PASS | 將先撰寫 quota 錯誤偵測的單元測試，再實作偵測邏輯 |
| II. Unified API Abstraction | ✅ PASS | 延伸現有 `AppError` 統一例外架構，新增 `QuotaExceededError` |
| III. Performance Benchmarking | ⚠️ N/A | 錯誤處理不涉及效能基準，僅需確保回應時間合理 |
| IV. Documentation First | ✅ PASS | 本計畫包含 data-model 及 API contracts 定義 |
| V. Clean Architecture | ✅ PASS | 遵循現有分層：domain/errors → infrastructure/providers → presentation/middleware |

## Project Structure

### Documentation (this feature)

```text
docs/features/014-quota-error-handling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── error-response.yaml
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   └── errors.py                    # 新增 QuotaExceededError
│   ├── infrastructure/
│   │   └── providers/
│   │       ├── tts/                     # 各 TTS provider 新增 429 偵測
│   │       │   ├── gemini_tts.py
│   │       │   ├── elevenlabs_tts.py
│   │       │   ├── azure_tts.py
│   │       │   ├── gcp_tts.py
│   │       │   └── voai_tts.py
│   │       └── stt/                     # 各 STT provider 新增 429 偵測
│   │           ├── whisper_stt.py       # OpenAI
│   │           ├── deepgram_stt.py
│   │           ├── azure_stt.py
│   │           └── gcp_stt.py
│   └── presentation/
│       └── api/
│           └── middleware/
│               └── error_handler.py     # 新增 QuotaExceededError handler
└── tests/
    └── unit/
        └── domain/
            └── test_quota_errors.py     # 新增測試

frontend/
├── src/
│   ├── components/
│   │   └── multi-role-tts/
│   │       └── ErrorDisplay.tsx         # 增強 quota 錯誤顯示
│   └── lib/
│       └── error-messages.ts            # 新增中文錯誤訊息對照
└── tests/
    └── components/
        └── ErrorDisplay.test.tsx        # 新增測試
```

**Structure Decision**: 採用 Option 2 (Web application) 的現有結構，此功能修改跨 backend/frontend 多個現有檔案，並新增測試檔案。

## Complexity Tracking

> 本功能無憲章違規情況，不需填寫。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
