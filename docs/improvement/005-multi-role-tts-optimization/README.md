# 多角色 TTS 效能與體驗優化計畫

## 背景

Feature 005 (Multi-Role TTS) 目前已完成核心功能開發並通過驗證。為了進一步提升系統的可維護性、一致性以及使用者體驗，本計畫提出以下優化方向。

---

## 優化項目總覽

| 項目 | 類別 | 說明 | 優先級 |
|----------|------|------|--------|
| **SDK 整合優化** | 維護性 | ElevenLabs 原生呼叫從 httpx 遷移至 SDK | 🟡 低 (P3) |
| **預設值一致性** | 健壯性 | 建立前後端統一的音訊格式與間隔常數 | 🟠 中 (P2) |
| **解析錯誤視覺化** | 體驗 | 提升對話解析失敗時的錯誤定位能力 | 🔴 高 (P1) |

---

## 詳細優化方案

### 1. ElevenLabs SDK 遷移 (P3)

**現況**:
`synthesize_multi_role.py` 使用 `httpx` 直接呼叫 `https://api.elevenlabs.io/v1/text-to-dialogue`。

**優化建議**:
- 待 ElevenLabs 官方 Python SDK 支援此 Endpoint 後，應將其封裝進 `ElevenLabsProvider` 類別中。
- 移除自定義的 `httpx` 異步呼叫邏輯，保持 Provider 實作風格一致。

---

### 2. 全域預設值與常數管理 (P2)

**現況**:
音訊格式 (`mp3`) 與間隔 (`gap_ms: 300`) 的預設值分別散落在 Python `MergeConfig` 與 TypeScript `multiRoleTTSStore` 中。

**優化建議**:
- **Backend**: 在 `src/domain/entities/multi_role_tts.py` 定義 `DEFAULT_MULTI_ROLE_CONFIG`。
- **Frontend**: 在 `src/config/constants.ts` 定義相關常數。
- 確保雙方在未指定參數時的行為完全一致。

---

### 3. 解析錯誤視覺化與定位 (P1)

**現況**:
當 `dialogue_parser.py` 報錯時，使用者僅能在 `ErrorDisplay` 看到一段文字訊息（如 "Invalid dialogue format"）。

**優化建議**:
- **Parser 升級**: 修改 `parse_dialogue` 回傳發生錯誤的行號或索引。
- **UI 強化**:
    - 在 `DialogueInput` 內標示出錯誤行。
    - 提供「修正建議」按鈕，自動修正常見的標點符號錯誤（如半形冒號改全形）。
    - 即時解析 (Debounced Parsing)：不需要點擊按鈕，在輸入停止 500ms 後自動嘗試解析並更新說話者清單。

---

## 實作細節建議

### 關於解析錯誤視覺化 (P1)

修改 `DialogueTurn` 實體，加入 `raw_line` 資訊：

```python
@dataclass
class DialogueTurn:
    speaker: str
    text: str
    index: int
    line_number: int  # 新增：紀錄原始文字行號
```

前端 `multiRoleTTSStore` 增加 `autoParse` 邏輯：

```typescript
// 當 dialogueText 改變時自動觸發 (需 debounce)
useEffect(() => {
  const timer = setTimeout(() => {
    if (dialogueText.trim()) parseDialogue();
  }, 800);
  return () => clearTimeout(timer);
}, [dialogueText]);
```

---

## 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| 自動解析過於頻繁 | 中 | 低 | 實作適當的 Debounce 時間 (800ms+) |
| SDK 版本不相容 | 低 | 中 | 先在分支測試 SDK 相容性 |

## 預期效果

1. **維護性**: 減少手動處理 HTTP 請求的程式碼量。
2. **一致性**: 避免因預設值不一導致的合成結果差異。
3. **滿意度**: 使用者能更快速地修正輸入格式錯誤，提升對話錄製效率。
