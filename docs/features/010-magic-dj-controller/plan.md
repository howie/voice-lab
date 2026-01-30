# Implementation Plan: Magic DJ Controller

**Branch**: `010-magic-dj-controller` | **Date**: 2026-01-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/010-magic-dj-controller/spec.md`

## Summary

建立「魔法 DJ 控制台」功能，整合於現有 Voice Lab 前端選單，讓 RD 能像 DJ 一樣操作 4-6 歲兒童語音互動 MVP 測試。核心功能包括：手動強制送出（繞過 VAD）、聲音庫 (Sound Library) 管理與播放、播放清單 (Cue List) 預排流程、Gemini AI 對話整合、思考音效熱鍵、模式切換（預錄/AI）、救場語音機制。本功能為純前端實作，使用 localStorage 儲存聲音庫配置、播放清單和測試 Session 數據，無需後端資料庫。

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
| I. Test-Driven Development | ✅ PASS | 為核心 hooks（useMultiTrackPlayer、useCueList）和 magicDJStore 撰寫單元測試，目標覆蓋率 80%+ |
| II. Unified API Abstraction | ✅ PASS | 複用現有 Gemini adapter，無新增提供者 |
| III. Performance Benchmarking | ✅ PASS | 雖非 TTS/STT 服務整合，但 spec 定義明確延遲指標（SC-001~SC-009），將建立前端延遲基準測試追蹤音檔播放 <100ms、模式切換 <500ms、拖曳回饋 <200ms |
| IV. Documentation First | ✅ PASS | quickstart.md 已建立，含完整操作指南 |
| V. Clean Architecture | ✅ PASS | 遵循現有前端分層結構（components/ hooks/ stores/ types/） |

**結論**: 所有原則通過。Principle III 雖非傳統 TTS/STT 基準測試，但 spec 定義了 9 項可量測延遲指標，納入前端效能追蹤。

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
│   │       ├── ChannelStrip.tsx       # 頻道條（DJ Mixer 風格）
│   │       ├── SoundLibrary.tsx       # 聲音庫面板（左側）
│   │       ├── SoundItem.tsx          # 聲音庫項目（可拖曳）
│   │       ├── CueList.tsx            # 播放清單面板（右側）
│   │       ├── CueItem.tsx            # 播放清單項目
│   │       ├── ModeSwitch.tsx         # 預錄/AI 模式切換
│   │       ├── ForceSubmitButton.tsx  # 強制送出按鈕
│   │       ├── InterruptButton.tsx    # 中斷按鈕
│   │       ├── FillerSoundTrigger.tsx # 思考音效熱鍵
│   │       ├── RescuePanel.tsx        # 救場語音面板
│   │       └── SessionTimer.tsx       # 測試計時器
│   ├── hooks/
│   │   ├── useMultiTrackPlayer.ts     # 新增：多音軌播放 hook
│   │   ├── useCueList.ts              # 新增：播放清單 hook
│   │   ├── useDragAndDrop.ts          # 新增：拖曳功能 hook
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
            ├── useMultiTrackPlayer.test.ts
            ├── useCueList.test.ts
            ├── useDragAndDrop.test.ts
            ├── magicDJStore.test.ts
            └── useSessionStorage.test.ts
```

**Structure Decision**: 遵循現有 frontend/ 結構，新增 `magic-dj` 模組於 components/、hooks/、stores/、routes/ 目錄下。

## Complexity Tracking

> 無 Constitution 違規項目。以下為中等複雜度功能備註：

| 功能 | 複雜度 | 風險 | 緩解措施 |
|------|--------|------|----------|
| Cue List 拖曳（跨區域 + 區內排序） | 中 | 觸控/拖曳體驗在不同瀏覽器表現不一 | 優先以 HTML5 DnD 實作，若不足再引入 @dnd-kit |
| 多頻道同時播放 + priority 規則 | 中 | Voice 頻道 rescue/normal 優先級邏輯錯誤可能導致救場語音被覆蓋 | 單元測試覆蓋所有優先級交互場景 |
| localStorage 大量音檔 base64 儲存 | 低-中 | localStorage 5MB 限制可能不足以儲存多個 TTS 音檔 | 監控使用量，提供匯出/匯入替代方案 |
