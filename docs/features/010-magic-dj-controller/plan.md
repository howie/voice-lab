# Implementation Plan: Magic DJ Controller

**Branch**: `010-magic-dj-controller` | **Date**: 2026-01-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/010-magic-dj-controller/spec.md`

## Summary

建立「魔法 DJ 控制台」功能，整合於現有 Voice Lab 前端選單，讓 RD 能像 DJ 一樣操作 4-6 歲兒童語音互動 MVP 測試。核心功能包括：手動強制送出（繞過 VAD）、預錄音檔播放、Gemini AI 對話整合、思考音效熱鍵、救場語音機制。本功能為純前端實作，使用 localStorage 儲存測試數據，無需後端資料庫。

## Technical Context

**Language/Version**: TypeScript 5.3+, React 18.2+
**Primary Dependencies**:
- Zustand 4.5+ (狀態管理)
- React Router DOM 6.21+ (路由)
- Radix UI (UI 元件)
- Tailwind CSS 3.4+ (樣式)
- 現有 useAudioPlayback hook (音訊播放)
- 現有 useWebSocket hook (Gemini 通訊)

**Storage**: localStorage（Session 紀錄）、JSON/CSV 檔案匯出
**Testing**: Vitest 1.2+, Testing Library
**Target Platform**: Web (Chrome/Edge，需支援 Web Audio API)
**Project Type**: Web application (整合於現有 frontend/)
**Performance Goals**:
- 音檔播放延遲 < 100ms
- 模式切換 < 500ms
- 支援同時播放多音軌

**Constraints**:
- 純前端實作，無新增後端 API
- 整合現有 Voice Lab 選單和路由系統
- 複用現有的音訊播放和 WebSocket 基礎設施

**Scale/Scope**: 單一 RD 操作，支援 20-25 分鐘測試流程

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ✅ PASS | 將為新元件和 hooks 撰寫單元測試 |
| II. Unified API Abstraction | ✅ PASS | 複用現有 Gemini adapter，無新增提供者 |
| III. Performance Benchmarking | ⚠️ N/A | 非 TTS/STT 服務整合，但會追蹤延遲指標 |
| IV. Documentation First | ✅ PASS | 將建立 quickstart.md 和使用說明 |
| V. Clean Architecture | ✅ PASS | 遵循現有前端分層結構 |

**結論**: 所有適用原則通過。此功能為前端 UI 模組，主要複用現有基礎設施。

## Project Structure

### Documentation (this feature)

```text
docs/features/010-magic-dj-controller/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # N/A (純前端，無新 API)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── magic-dj/              # 新增：Magic DJ 元件
│   │       ├── DJControlPanel.tsx     # 主控制台面板
│   │       ├── TrackPlayer.tsx        # 音軌播放器
│   │       ├── TrackList.tsx          # 音軌列表
│   │       ├── ModeSwitch.tsx         # 預錄/AI 模式切換
│   │       ├── ForceSubmitButton.tsx  # 強制送出按鈕
│   │       ├── InterruptButton.tsx    # 中斷按鈕
│   │       ├── FillerSoundTrigger.tsx # 思考音效熱鍵
│   │       ├── RescuePanel.tsx        # 救場語音面板
│   │       └── SessionTimer.tsx       # 測試計時器
│   ├── hooks/
│   │   ├── useMultiTrackPlayer.ts     # 新增：多音軌播放 hook
│   │   └── useSessionStorage.ts       # 新增：Session 資料持久化 hook
│   ├── stores/
│   │   └── magicDJStore.ts            # 新增：Magic DJ 狀態
│   ├── routes/
│   │   └── magic-dj/
│   │       └── MagicDJPage.tsx        # 新增：Magic DJ 頁面
│   └── types/
│       └── magic-dj.ts                # 新增：類型定義
└── tests/
    └── unit/
        └── magic-dj/                  # 新增：單元測試
            └── useMultiTrackPlayer.test.ts
```

**Structure Decision**: 遵循現有 frontend/ 結構，新增 `magic-dj` 模組於 components/、hooks/、stores/、routes/ 目錄下。

## Complexity Tracking

> 無違規項目，不需填寫。
