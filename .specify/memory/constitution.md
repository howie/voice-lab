<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0
Bump rationale: Initial constitution creation (MAJOR - new governance document)

Modified principles: N/A (initial creation)

Added sections:
- I. Test-Driven Development (TDD)
- II. Unified API Abstraction
- III. Performance Benchmarking
- IV. Documentation First
- V. Clean Architecture
- Technical Standards section
- Development Workflow section
- Governance section

Removed sections: None

Templates requiring updates:
- .specify/templates/plan-template.md ✅ (Constitution Check section compatible)
- .specify/templates/spec-template.md ✅ (User scenarios align with TDD principle)
- .specify/templates/tasks-template.md ✅ (Phase structure supports Clean Architecture)

Follow-up TODOs: None
==================
-->

# Voice Lab Constitution

## Core Principles

### I. Test-Driven Development (TDD)

所有功能開發 **必須** 遵循 TDD 流程：

1. **先寫測試**：在實作任何功能前，必須先撰寫失敗的測試案例
2. **紅燈-綠燈-重構**：嚴格執行 Red-Green-Refactor 循環
3. **測試類型**：
   - Contract tests：驗證 TTS/STT 服務的 API 合約
   - Integration tests：驗證服務整合與端對端流程
   - Unit tests：驗證核心邏輯單元
4. **覆蓋率要求**：核心服務抽象層必須達到 80% 以上測試覆蓋率

**理由**：voice-lab 是測試導向專案，測試各種 TTS/STT 服務的品質與行為，TDD 確保我們的測試基礎設施本身是可靠的。

### II. Unified API Abstraction

所有 TTS/STT 服務 **必須** 透過統一抽象層存取：

1. **統一介面**：所有服務提供者必須實作相同的介面協定
2. **可切換性**：使用者可在不修改應用程式碼的情況下切換服務提供者
3. **協定規範**：
   - TTS：`text_to_speech(text, voice, options) -> AudioResult`
   - STT：`speech_to_text(audio, options) -> TranscriptResult`
4. **錯誤處理**：統一的錯誤類型與回傳格式

**理由**：統一抽象讓我們能公平比較不同服務，並讓使用者輕鬆切換提供者。

### III. Performance Benchmarking

每個 TTS/STT 服務整合 **必須** 包含效能基準測試：

1. **必要指標**：
   - 延遲 (Latency)：首字節時間 (TTFB)、完成時間
   - 準確度：WER (Word Error Rate) 用於 STT，MOS (Mean Opinion Score) 評估用於 TTS
   - 吞吐量：並發請求處理能力
2. **基準格式**：所有效能結果必須以標準化 JSON 格式記錄
3. **可重現性**：基準測試必須可重現，使用固定測試資料集

**理由**：voice-lab 的核心價值在於提供客觀的服務比較，效能數據是關鍵產出。

### IV. Documentation First

每個服務整合 **必須** 先有文件再實作：

1. **必要文件**：
   - 快速開始指南 (Quickstart)
   - API 參考文件
   - 設定與環境變數說明
   - 範例程式碼
2. **文件位置**：`docs/<provider>/` 目錄結構
3. **同步要求**：程式碼變更必須同步更新相關文件
4. **範例驅動**：每個 API 方法至少有一個可執行的範例

**理由**：使用者需要清楚了解如何使用各個服務整合，完整文件降低採用門檻。

### V. Clean Architecture

專案結構 **必須** 遵循分層架構設計：

1. **層級劃分**：
   - `core/`：領域模型與業務邏輯（無外部依賴）
   - `adapters/`：服務提供者實作（實作 core 定義的介面）
   - `cli/`：命令列介面
   - `tests/`：測試程式碼
2. **依賴規則**：依賴方向必須由外向內，內層不得依賴外層
3. **隔離原則**：每個服務提供者的適配器獨立於其他提供者

**理由**：清晰的架構讓專案易於維護、測試和擴展新的服務提供者。

## Technical Standards

### 技術堆疊

- **語言**：Python 3.11+
- **測試框架**：pytest, pytest-asyncio
- **型別檢查**：mypy (strict mode)
- **程式碼風格**：ruff (formatting + linting)
- **套件管理**：uv 或 poetry

### 程式碼品質

- 所有公開 API 必須有完整的型別註解
- 非同步操作優先使用 `asyncio`
- 禁止全域可變狀態
- 設定值透過環境變數或設定檔注入，不硬編碼

### 目錄結構

```text
src/
├── core/           # 領域模型與介面定義
│   ├── models/     # 資料模型
│   └── ports/      # 抽象介面 (protocols)
├── adapters/       # 服務提供者實作
│   ├── openai/
│   ├── google/
│   ├── azure/
│   └── ...
├── cli/            # CLI 入口點
└── utils/          # 共用工具函式

tests/
├── contract/       # 合約測試
├── integration/    # 整合測試
└── unit/           # 單元測試

docs/
├── quickstart.md
└── <provider>/     # 各提供者文件
```

## Development Workflow

### 新服務整合流程

1. **文件先行**：在 `docs/<provider>/` 建立使用文件草稿
2. **定義合約**：在 `tests/contract/` 撰寫合約測試
3. **實作適配器**：在 `src/adapters/<provider>/` 實作
4. **效能測試**：執行並記錄基準測試結果
5. **文件完善**：根據實作更新文件

### 程式碼審查要求

- 所有變更必須通過 CI 檢查（測試、型別檢查、linting）
- 新增服務適配器必須附帶完整測試與文件
- 破壞性變更必須在 PR 描述中明確說明

### 提交訊息格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

類型：feat, fix, docs, test, refactor, perf, chore

## Governance

### 憲章修訂

- 本憲章優先於所有其他開發實踐
- 修訂必須包含：變更說明、理由、遷移計畫（如適用）
- 版本更新遵循語意化版本：
  - MAJOR：移除或重新定義核心原則
  - MINOR：新增原則或實質擴展指引
  - PATCH：澄清、措辭修正、非語意性調整

### 合規審查

- 所有 PR 審查必須驗證是否符合憲章原則
- 複雜度增加必須有合理說明
- 偏離原則需在 PR 中明確記錄並獲得核准

### 執行指引

詳細的開發指引請參考 `docs/quickstart.md` 與各模板文件。

**Version**: 1.0.0 | **Ratified**: 2026-01-16 | **Last Amended**: 2026-01-16
