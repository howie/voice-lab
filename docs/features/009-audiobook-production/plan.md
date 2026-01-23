# Implementation Plan: Audiobook Production System

**Branch**: `009-audiobook-production` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/009-audiobook-production/spec.md`

## Summary

實作有聲書製作系統，支援長篇多角色故事（10-20 分鐘）的非同步生成、角色管理、背景音樂融合與專案管理。主要工作包括：

1. 建立 `AudiobookProject`、`Character`、`ScriptTurn` 等資料模型
2. 實作劇本格式解析與角色自動識別
3. 建立非同步生成 Worker，整合現有 JobWorker 架構
4. 實作背景音樂混音功能（使用 pydub）
5. 建立完整的前端專案編輯介面

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.5+, pydub, React 18+, Zustand
**Storage**: PostgreSQL (metadata), Local filesystem / S3 (audio files)
**Testing**: pytest, pytest-asyncio, Vitest
**Target Platform**: Linux server (Docker/Cloud Run)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 10 分鐘故事生成 < 15 分鐘, 進度查詢 < 3 秒
**Constraints**: 背景音樂檔案 < 50MB, 單一專案角色數建議 < 10
**Scale/Scope**: 單一專案最多 ~4,000 字（20 分鐘）, ~200 個 ScriptTurn

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-Driven Development | ✅ Pass | 規格已定義驗收場景，將先撰寫 contract/integration tests |
| II. Unified API Abstraction | ✅ Pass | 整合 008 聲音 API，統一存取各 Provider |
| III. Performance Benchmarking | ✅ Pass | SC-003 定義明確效能指標（10 分鐘故事 < 15 分鐘生成） |
| IV. Documentation First | ✅ Pass | 本計畫先於實作，將產出 quickstart.md 與 API contracts |
| V. Clean Architecture | ✅ Pass | 遵循現有分層：domain/entities → application/use_cases → infrastructure |

## Project Structure

### Documentation (this feature)

```text
docs/features/009-audiobook-production/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (if needed)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   ├── projects-api.yaml
│   ├── characters-api.yaml
│   └── generation-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   └── entities/
│   │       ├── audiobook_project.py    # 新增: AudiobookProject entity
│   │       ├── character.py            # 新增: Character entity
│   │       ├── script_turn.py          # 新增: ScriptTurn entity
│   │       ├── audiobook_job.py        # 新增: AudiobookGenerationJob entity
│   │       └── background_music.py     # 新增: BackgroundMusic entity
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── create_audiobook_project.py   # 新增
│   │   │   ├── parse_script.py               # 新增: 劇本解析
│   │   │   ├── generate_audiobook.py         # 新增: 非同步生成
│   │   │   ├── mix_audio.py                  # 新增: 混音
│   │   │   └── export_audiobook.py           # 新增: 匯出
│   │   └── interfaces/
│   │       ├── audiobook_repository.py       # 新增
│   │       └── audio_mixer.py                # 新增
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── models.py                # 修改: 新增 audiobook 相關 models
│   │   │   └── audiobook_repository.py  # 新增
│   │   ├── audio/
│   │   │   ├── script_parser.py         # 新增: 劇本解析器
│   │   │   └── audio_mixer.py           # 新增: pydub 混音實作
│   │   └── workers/
│   │       └── audiobook_worker.py      # 新增: 生成 Worker
│   └── presentation/
│       └── api/
│           └── routes/
│               ├── audiobook_projects.py    # 新增
│               ├── audiobook_characters.py  # 新增
│               └── audiobook_generation.py  # 新增
├── tests/
│   ├── unit/
│   │   ├── test_script_parser.py        # 新增
│   │   └── test_audio_mixer.py          # 新增
│   └── integration/
│       └── test_audiobook_generation.py # 新增
└── alembic/
    └── versions/
        └── xxx_add_audiobook_tables.py  # 新增: migration

frontend/
└── src/
    ├── pages/
    │   ├── AudiobookList.tsx            # 新增: 專案列表
    │   └── AudiobookEditor.tsx          # 新增: 專案編輯器
    ├── components/
    │   ├── ScriptEditor/                # 新增: 劇本編輯器
    │   ├── CharacterPanel/              # 新增: 角色設定面板
    │   ├── GenerationProgress/          # 新增: 生成進度
    │   └── AudioPreview/                # 新增: 音訊預覽
    └── stores/
        └── audiobookStore.ts            # 新增: Zustand store
```

**Structure Decision**: 沿用現有 Web application 結構（backend/ + frontend/），遵循 Clean Architecture 分層。

## Key Technical Decisions

### 1. 劇本解析策略

使用正則表達式解析「角色名：台詞」格式，支援中英文冒號：

```python
import re

def parse_script(content: str) -> list[dict]:
    pattern = r'^([^：:]+)[：:]\s*(.+)$'
    turns = []
    for line in content.strip().split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            turns.append({
                'character': match.group(1).strip(),
                'text': match.group(2).strip()
            })
    return turns
```

### 2. 非同步生成架構

整合 007-async-job-mgmt 的 JobWorker 架構：

```text
[API Request] → [Create Job] → [Queue] → [AudiobookWorker]
                     │                          │
                     ▼                          ▼
              [Return Job ID]            [Process Turns]
                                               │
                                               ▼
                                         [Merge Audio]
                                               │
                                               ▼
                                         [Update Status]
```

### 3. 音訊處理

使用 pydub 進行音訊合併與混音：

- 合併：將所有 ScriptTurn 的音訊按順序連接
- 混音：將背景音樂與旁白疊加，調整音量比例
- 輸出：MP3（預設 192kbps）、WAV（可選）

### 4. 前端狀態管理

使用 Zustand 管理專案編輯狀態：

```typescript
interface AudiobookState {
  project: AudiobookProject | null
  characters: Character[]
  turns: ScriptTurn[]
  generationStatus: JobStatus | null
  // actions
  loadProject: (id: string) => Promise<void>
  updateCharacter: (id: string, data: Partial<Character>) => void
  startGeneration: () => Promise<void>
}
```

## Dependencies on Other Features

| Feature | 依賴內容 | 必要性 |
|---------|---------|--------|
| 008-voai-multi-role-voice-generation | VoiceCache API（聲音篩選） | 必要 |
| 007-async-job-mgmt | JobWorker 架構 | 必要 |
| 005-multi-role-tts | TTS Provider 整合 | 必要 |

## Complexity Tracking

> **無違規需要記錄** - 所有設計符合 Constitution 原則。

## Risk Assessment

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 長篇內容生成時間過長 | 中 | 高 | 平行處理多個 Turn、顯示詳細進度 |
| pydub 處理大檔案記憶體不足 | 低 | 中 | 分段處理、限制單一專案大小 |
| 使用者取消後資源未清理 | 中 | 低 | Job 狀態管理、定期清理 |
