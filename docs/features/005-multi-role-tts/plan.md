# Implementation Plan: Multi-Role TTS

**Branch**: `005-multi-role-tts` | **Date**: 2025-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/005-multi-role-tts/spec.md`

## Summary

實作多角色 TTS 功能頁面，讓使用者輸入多角色對話逐字稿（如 `A: 你好 B: 嗨`），系統自動解析說話者並為每位說話者分配不同語音，最終產生多角色交替說話的音訊。根據研究，ElevenLabs 和 Azure 原生支援多角色對話，其他 Provider 需使用分段合併方式。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.0+, React 18+, Zustand, pydub (音訊合併)
**Storage**: Local filesystem (音訊檔案), PostgreSQL (元資料)
**Testing**: pytest, pytest-asyncio, Vitest, React Testing Library
**Target Platform**: Web application (Linux server backend, modern browsers)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 介面切換 <1 秒，TTS 產生依 Provider 特性
**Constraints**: 最多 6 位說話者，預設 5000 字元上限（依 Provider 動態調整）
**Scale/Scope**: 單一新頁面，擴展現有 TTS 功能

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. TDD | ✅ Pass | 將在 tasks 階段定義測試先行流程 |
| II. Unified API Abstraction | ✅ Pass | 擴展現有 ITTSProvider 介面，新增 multi-role 支援 |
| III. Performance Benchmarking | ✅ Pass | 將記錄各 Provider 多角色 TTS 延遲指標 |
| IV. Documentation First | ✅ Pass | 本計畫包含 quickstart.md 與 API 合約 |
| V. Clean Architecture | ✅ Pass | 遵循現有 domain/application/infrastructure 分層 |

## Project Structure

### Documentation (this feature)

```text
docs/features/005-multi-role-tts/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── multi-role-tts-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   └── entities/
│   │       └── multi_role_tts.py      # 多角色 TTS 實體
│   ├── application/
│   │   ├── interfaces/
│   │   │   └── multi_role_tts_provider.py  # 多角色 TTS 介面
│   │   └── use_cases/
│   │       └── synthesize_multi_role.py    # 多角色合成用例
│   ├── infrastructure/
│   │   └── providers/
│   │       └── tts/
│   │           └── multi_role/        # 多角色 TTS 實作
│   │               ├── __init__.py
│   │               ├── elevenlabs_multi.py
│   │               ├── azure_multi.py
│   │               └── segmented_merger.py  # 分段合併通用邏輯
│   └── presentation/
│       └── api/
│           └── routes/
│               └── multi_role_tts.py  # API 路由
└── tests/
    ├── unit/
    │   └── domain/
    │       └── test_dialogue_parser.py
    └── integration/
        └── test_multi_role_tts.py

frontend/
├── src/
│   ├── components/
│   │   └── multi-role-tts/
│   │       ├── DialogueInput.tsx      # 對話輸入元件
│   │       ├── SpeakerVoiceTable.tsx  # 說話者語音對應表
│   │       ├── ProviderCapabilityCard.tsx  # Provider 能力卡片
│   │       └── index.ts
│   ├── routes/
│   │   └── multi-role-tts/
│   │       └── MultiRoleTTSPage.tsx   # 多角色 TTS 頁面
│   ├── stores/
│   │   └── multiRoleTTSStore.ts       # 狀態管理
│   └── types/
│       └── multi-role-tts.ts          # TypeScript 型別
└── tests/
    └── components/
        └── multi-role-tts/
```

**Structure Decision**: 採用 Option 2 (Web application)，擴展現有 backend/frontend 結構，新增多角色 TTS 相關檔案。

## Complexity Tracking

> Constitution deviation documented below with approved rationale.

| Decision | Rationale | Constitution Reference |
|----------|-----------|------------------------|
| 使用 domain/application/infrastructure 分層 | 專案既有架構已採用此模式，保持一致性優先於遵循 core/adapters 命名。功能等價：domain≈core, infrastructure/adapters≈adapters | V. Clean Architecture (例外記錄) |
| 新增 multi_role 子目錄 | 功能獨立且複雜度較高，獨立模組有助維護 | - |
| 使用 pydub 合併音訊 | 已在研究文件驗證，為業界標準做法 | - |
| 擴展而非修改現有介面 | 保持向後相容，原有 TTS 功能不受影響 | II. Unified API Abstraction |
