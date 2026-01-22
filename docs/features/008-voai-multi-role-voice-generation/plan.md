# Implementation Plan: VoAI Multi-Role Voice Generation Enhancement

**Branch**: `008-voai-multi-role-voice-generation` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/008-voai-multi-role-voice-generation/spec.md`

## Summary

實作 Native 多角色語音合成（Azure SSML、ElevenLabs Audio Tags）、聲音資料庫儲存與同步機制，以提升多角色 TTS 的效能與使用者體驗。主要工作包括：

1. 擴展 `VoiceCache` 資料模型，新增 `age_group`、`styles`、`use_cases`、`is_deprecated`、`synced_at` 欄位
2. 實作 `VoiceCacheRepositoryImpl`（DB-backed）取代 In-Memory 實作
3. 建立背景聲音同步任務，整合現有 JobWorker 架構
4. 實作 `AzureSSMLBuilder` 與 `ElevenLabsAudioTagsBuilder` 支援 Native 多角色合成

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.5+, pipecat-ai, azure-cognitiveservices-speech, elevenlabs
**Storage**: PostgreSQL (via asyncpg + SQLAlchemy), Local filesystem (audio files)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (Docker/Cloud Run)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 聲音查詢 <50ms, Native 合成延遲減少 30%
**Constraints**: Azure SSML 限制 50,000 Unicode 字元, 指數退避重試最多 3 次
**Scale/Scope**: ~800 聲音 (Azure ~400, GCP ~300, ElevenLabs ~100), 每日同步一次

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-Driven Development | ✅ Pass | 規格已定義驗收場景與測試案例，將先撰寫 contract/integration tests |
| II. Unified API Abstraction | ✅ Pass | 透過 `MultiRoleTTSProvider` 介面統一存取，Native/Segmented 模式對外一致 |
| III. Performance Benchmarking | ✅ Pass | SC-001/SC-002 定義明確效能指標（延遲減少 30%、查詢 <50ms） |
| IV. Documentation First | ✅ Pass | 本計畫先於實作，將產出 quickstart.md 與 API contracts |
| V. Clean Architecture | ✅ Pass | 遵循現有分層：domain/entities → application/use_cases → infrastructure/persistence |

## Project Structure

### Documentation (this feature)

```text
docs/features/008-voai-multi-role-voice-generation/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   ├── voices-api.yaml
│   └── voice-sync-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   └── entities/
│   │       ├── voice.py              # 擴展 VoiceProfile, 新增 AgeGroup enum
│   │       └── voice_sync_job.py     # 新增 VoiceSyncJob entity
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── synthesize_multi_role.py  # 修改: 實作 _synthesize_native()
│   │   │   └── sync_voices.py            # 新增: 聲音同步 use case
│   │   └── interfaces/
│   │       └── voice_repository.py       # 新增: VoiceCacheRepository protocol
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── models.py             # 修改: VoiceCache 新增欄位
│   │   │   └── voice_repository.py   # 新增: VoiceCacheRepositoryImpl
│   │   ├── providers/
│   │   │   ├── azure/
│   │   │   │   └── ssml_builder.py   # 新增: AzureSSMLBuilder
│   │   │   └── elevenlabs/
│   │   │       └── audio_tags_builder.py  # 新增: ElevenLabsAudioTagsBuilder
│   │   └── workers/
│   │       └── job_worker.py         # 修改: 新增 sync_voices job type
│   └── presentation/
│       └── api/
│           └── routes/
│               └── voices.py         # 修改: 新增篩選參數與同步 endpoint
├── tests/
│   ├── contract/
│   │   └── test_voice_sync_contract.py   # 新增
│   ├── integration/
│   │   ├── test_native_synthesis.py      # 新增
│   │   └── test_voice_repository.py      # 新增
│   └── unit/
│       ├── test_ssml_builder.py          # 新增
│       └── test_audio_tags_builder.py    # 新增
└── alembic/
    └── versions/
        └── xxx_add_voice_cache_fields.py # 新增: migration

frontend/
└── src/
    └── components/
        └── VoiceSelector/            # 修改: 新增 age_group 篩選 UI
```

**Structure Decision**: 沿用現有 Web application 結構（backend/ + frontend/），遵循 Clean Architecture 分層。

## Complexity Tracking

> **無違規需要記錄** - 所有設計符合 Constitution 原則。
