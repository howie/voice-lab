# Implementation Plan: STT Provider Dropdown Selector

**Branch**: `003-stt-testing-module` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/003-stt-testing-module/spec.md`

## Summary

將 STT Provider 選擇器從 card-based grid 改為 dropdown (`<select>`) 元件，並且只顯示使用者已設定有效 API Key 的 Provider，與 TTS ProviderSelector 行為一致。此變更源於 spec FR-003 更新。

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, React 18+, Zustand (state management)
**Storage**: PostgreSQL (transcription history), Local filesystem (uploaded audio)
**Testing**: pytest (Backend), vitest (Frontend)
**Target Platform**: Web application (Linux server + modern browsers)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Batch response within 30s for 1-min audio, Provider list load < 200ms
**Constraints**: Provider dropdown must match TTS selector UX pattern
**Scale/Scope**: 7 STT providers, filtering by user credential status

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | PASS | Frontend component test exists, will update for dropdown |
| II. Unified API Abstraction | PASS | Backend `GET /stt/providers` already returns credential status |
| III. Performance Benchmarking | N/A | UI-only change, no perf benchmark needed |
| IV. Documentation First | PASS | Plan and spec updated before implementation |
| V. Clean Architecture | PASS | Change scoped to presentation layer only |

## Project Structure

### Documentation (this feature)

```text
docs/features/003-stt-testing-module/
├── plan.md              # This file (updated for dropdown change)
├── research.md          # Phase 0 output (existing, minor update)
├── data-model.md        # Phase 1 output (existing, no change needed)
├── quickstart.md        # Phase 1 output (existing, update UI flow)
├── contracts/           # Phase 1 output (existing, update STTProvider schema)
│   └── stt-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/stt.py           # STT domain entities (no change)
│   │   └── services/                 # Business logic (no change)
│   ├── infrastructure/
│   │   └── providers/stt/factory.py  # Provider metadata (no change)
│   └── presentation/
│       └── api/routes/stt.py         # GET /stt/providers (no change)
└── tests/

frontend/
├── src/
│   ├── components/
│   │   ├── tts/ProviderSelector.tsx  # TTS dropdown (reference pattern)
│   │   └── stt/ProviderSelector.tsx  # STT selector (CHANGE: cards → dropdown)
│   ├── stores/sttStore.ts            # Zustand store (minor update: filter logic)
│   ├── services/sttApi.ts            # API calls (no change)
│   └── types/stt.ts                  # TypeScript types (no change)
└── tests/
```

**Structure Decision**: Web application with separate backend/frontend. Changes are scoped to frontend presentation layer, backend already provides the required data.

## Design: Card → Dropdown Migration

### Current State (Card-based)

```
┌─────────────────────────────────────────────┐
│  STT Provider                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  Azure   │ │   GCP    │ │ Whisper  │    │
│  │  已設定   │ │  已設定   │ │  已設定   │    │
│  │ ✓ Child  │ │ ✓ Child  │ │Batch Only│    │
│  └──────────┘ └──────────┘ └──────────┘    │
│  ┌──────────┐ ┌──────────┐                  │
│  │ Deepgram │ │ ElevenLabs│  ← disabled     │
│  │ 尚未設定  │ │ 尚未設定   │  (no API key)  │
│  └──────────┘ └──────────┘                  │
└─────────────────────────────────────────────┘
```

**問題**: 佔用過多空間、與 TTS 選擇器 UX 不一致、顯示無法使用的 Provider 造成混淆。

### Target State (Dropdown)

```
┌─────────────────────────────────────────────┐
│  選擇 Provider                              │
│  ┌───────────────────────────────────────┐  │
│  │ Azure Speech Services            ▼   │  │
│  └───────────────────────────────────────┘  │
│  Microsoft Azure 語音辨識服務                  │
│                                             │
│  ┌─ Provider Limits ───────────────────┐    │
│  │ Max File: 200 MB  │ Max Dur: 10 min │    │
│  │ Formats: mp3, wav │ Child Mode: Yes │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**關鍵行為**:
1. Dropdown 只列出 `has_credentials === true && is_valid === true` 的 Provider
2. 無有效 credential 的 Provider 不出現在選單中（完全隱藏）
3. 選中 Provider 後顯示 description 與 capabilities（保留現有 ProviderCapabilities 元件）
4. 若無任何 Provider 有 credentials，顯示提示「請先至 Provider 管理頁面設定 API Key」

### Data Flow

```
GET /stt/providers
    ↓ returns all providers with has_credentials, is_valid
Frontend store (sttStore.ts)
    ↓ stores all providers in availableProviders
ProviderSelector component
    ↓ filters: availableProviders.filter(p => p.has_credentials && p.is_valid)
    ↓ renders <select> dropdown with only valid providers
    ↓ shows ProviderCapabilities for selected provider
```

### Backend Impact

**無需修改**。`GET /stt/providers` 已回傳 `has_credentials` 和 `is_valid` 欄位。前端負責過濾顯示邏輯。

### Frontend Changes

#### 1. `frontend/src/components/stt/ProviderSelector.tsx`

**完全重寫**：從 card grid 改為 dropdown，參考 TTS `ProviderSelector.tsx` 模式。

核心改動：
- 移除 `ProviderCard` 子元件
- 新增 `<select>` dropdown，只顯示有效 credentials 的 Provider
- 保留 `ProviderCapabilities` 子元件（顯示 limits）
- 新增空狀態：當無可用 Provider 時顯示提示

```typescript
// Pseudocode for new component
const validProviders = availableProviders.filter(
  p => p.has_credentials && p.is_valid
)

if (validProviders.length === 0) {
  return <EmptyState message="請先至 Provider 管理頁面設定 API Key" />
}

return (
  <select>
    {validProviders.map(p => (
      <option key={p.name} value={p.name}>{p.display_name}</option>
    ))}
  </select>
  <ProviderCapabilities provider={selectedProviderInfo} />
)
```

#### 2. `frontend/src/stores/sttStore.ts`

Minor update：確保 `selectedProvider` 預設值為第一個有 valid credentials 的 Provider（而非硬編碼值）。

#### 3. 測試更新

更新 `frontend/src/components/stt/__tests__/ProviderSelector.test.tsx`（如存在）以測試：
- Dropdown 只顯示有 credentials 的 Provider
- 無 Provider 時顯示空狀態提示
- 選擇 Provider 後顯示 capabilities

### API Contract Update

`contracts/stt-api.yaml` 中 `STTProvider` schema 需補上 `has_credentials` 和 `is_valid` 欄位（backend 已實作但 contract 未記錄）。

## Complexity Tracking

無 Constitution 違規，不需要 justification。

此變更範圍小（主要是一個 frontend component 重寫），不增加架構複雜度，反而統一了 TTS/STT 的 UX 模式。
