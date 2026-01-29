# Implementation Plan: TTS 角色管理介面

**Branch**: `013-tts-role-mgmt` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/013-tts-role-mgmt/spec.md`

## Summary

本功能讓使用者能夠管理 TTS 角色的顯示方式：自訂顯示名稱（如「Puck」→「陽光男孩聲」）、標記收藏角色、隱藏不常用角色。技術實作上，將新增 `VoiceCustomization` 資料表儲存使用者設定，並修改現有的 voices API 和 VoiceSelector 元件以整合自訂設定。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+, Zustand
**Storage**: PostgreSQL (voice_customization 表), 關聯現有 VoiceCache 表
**Testing**: pytest, pytest-asyncio (Backend), Vitest (Frontend)
**Target Platform**: Web application (Cloud Run)
**Project Type**: Web (backend + frontend)
**Performance Goals**: 頁面載入 < 2 秒，支援 200+ 角色管理
**Constraints**: 單一使用者環境，自訂名稱最多 50 字元
**Scale/Scope**: VoAI 55 個 + Gemini 30 個 + Azure/ElevenLabs 100+ 個角色

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (Phase 0)

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. TDD | ✅ Pass | 將撰寫 contract tests 驗證 API，unit tests 驗證 use cases |
| II. Unified API Abstraction | ✅ Pass | 不涉及新 TTS 提供者，使用既有 VoiceCache |
| III. Performance Benchmarking | ⚠️ N/A | 非效能敏感功能，但會確保頁面載入時間 |
| IV. Documentation First | ✅ Pass | 此 plan 即為設計文件 |
| V. Clean Architecture | ✅ Pass | 遵循既有四層架構 (domain/application/infrastructure/presentation) |

**Gate Result**: ✅ PASS - 可進入 Phase 0

### Post-Design Check (Phase 1)

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. TDD | ✅ Pass | API contract 已定義於 contracts/voice-customization-api.yaml，可撰寫 contract tests |
| II. Unified API Abstraction | ✅ Pass | 使用既有 VoiceCache 結構，新增獨立的 customization 層 |
| III. Performance Benchmarking | ⚠️ N/A | 頁面載入目標 < 2 秒已記錄於 spec |
| IV. Documentation First | ✅ Pass | 已產生 research.md, data-model.md, quickstart.md, contracts/ |
| V. Clean Architecture | ✅ Pass | 設計遵循四層架構，domain entity → repository interface → implementation → API routes |

**Gate Result**: ✅ PASS - 可進入 Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
docs/features/013-tts-role-mgmt/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── voice-customization-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   └── voice_customization.py    # 新增: VoiceCustomization 實體
│   │   └── repositories/
│   │       └── voice_customization.py    # 新增: IVoiceCustomizationRepository
│   ├── application/
│   │   └── use_cases/
│   │       ├── list_voices.py            # 修改: 整合 customization
│   │       ├── get_voice_customization.py    # 新增
│   │       ├── update_voice_customization.py # 新增
│   │       └── bulk_update_voice_customization.py # 新增
│   ├── infrastructure/
│   │   └── persistence/
│   │       ├── models.py                 # 修改: 新增 VoiceCustomizationModel
│   │       └── voice_customization_repository_impl.py # 新增
│   └── presentation/
│       └── api/
│           ├── routes/
│           │   ├── voices.py             # 修改: 新增 customization 回傳
│           │   └── voice_customizations.py   # 新增: CRUD 端點
│           └── schemas/
│               └── voice_customization.py    # 新增: Pydantic schemas
└── tests/
    ├── unit/
    │   └── use_cases/
    │       └── test_voice_customization.py
    └── integration/
        └── api/
            └── test_voice_customization_api.py

frontend/
├── src/
│   ├── components/
│   │   └── voice-management/             # 新增: 角色管理元件
│   │       ├── VoiceManagementTable.tsx
│   │       ├── VoiceCustomizationRow.tsx
│   │       ├── VoiceNameEditor.tsx
│   │       ├── FavoriteToggle.tsx
│   │       ├── HiddenToggle.tsx
│   │       └── VoiceFilters.tsx
│   ├── routes/
│   │   └── voice-management/
│   │       └── VoiceManagementPage.tsx   # 新增: 角色管理頁面
│   ├── stores/
│   │   └── voiceManagementStore.ts       # 新增: 角色管理狀態
│   ├── services/
│   │   └── voiceCustomizationApi.ts      # 新增: API 服務
│   └── types/
│       └── voice-customization.ts        # 新增: TypeScript 類型
└── tests/
    └── components/
        └── voice-management/
            └── VoiceManagementTable.test.tsx
```

**Structure Decision**: 採用 Web application 結構，符合既有 backend/ + frontend/ 分離架構。新功能遵循 Clean Architecture，在各層新增對應檔案。

## Complexity Tracking

> **No violations - table not needed**

本功能遵循既有架構模式，無需額外複雜度。
