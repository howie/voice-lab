# Testing Documentation

本目錄包含 voice-lab 專案的測試案例文檔（Test Cases）。

## 目錄結構

```
docs/testing/
├── README.md                           # 本說明文件
├── TC-004-gemini-transcript-display.md # Feature 004 Gemini 轉錄顯示測試案例
└── ...                                 # 其他功能測試案例
```

## 命名規範

測試案例文件命名格式：`TC-{feature-number}-{feature-name}.md`

例如：
- `TC-001-pipecat-tts-server.md`
- `TC-002-provider-mgmt-interface.md`
- `TC-004-gemini-transcript-display.md`

## 文件結構

每個測試案例文件應包含：

1. **Overview** - 功能概述
2. **Test Environment** - 測試環境需求
3. **Test Cases** - 詳細測試案例
   - Priority (P1/P2/P3)
   - Type (UI/Functional/E2E/Integration/Performance)
   - Preconditions
   - Steps
   - Expected Results
   - Pass Criteria
4. **Test Matrix** - 組合測試矩陣（如適用）
5. **Regression Tests** - 回歸測試項目
6. **Sign-off** - 簽核狀態

## 優先級定義

| Priority | 說明 | 測試時機 |
|----------|------|----------|
| P1 | 核心功能，必須通過 | 每次提交前 |
| P2 | 重要功能，應該通過 | 功能完成時 |
| P3 | 次要功能，選擇性測試 | 正式發布前 |

## 測試類型

| Type | 說明 |
|------|------|
| UI | 使用者介面測試 |
| Functional | 功能測試 |
| E2E | 端對端測試 |
| Integration | 整合測試 |
| Performance | 效能測試 |
| Error Handling | 錯誤處理測試 |

## 與自動化測試的關係

- 本目錄的測試案例為**手動測試指南**
- 自動化單元測試位於 `backend/tests/` 和 `frontend/src/**/__tests__/`
- 部分測試案例可轉換為自動化 E2E 測試（使用 Playwright）

## 測試報告

測試完成後，在對應的測試案例文件中：
1. 勾選 Pass Criteria 的 checkbox
2. 更新 Sign-off 區塊
3. 如有問題，在文件末尾新增 Issues 區塊記錄

---

## 現有測試案例

| 文件 | 功能 | 狀態 |
|------|------|------|
| [TC-004-gemini-transcript-display.md](./TC-004-gemini-transcript-display.md) | Gemini V2V 轉錄顯示 | Ready for Testing |
