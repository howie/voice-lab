# Quickstart: Magic DJ AI Prompt Templates

**Feature**: 015-magic-dj-ai-prompts
**Date**: 2026-02-04

## 概述

Magic DJ AI Prompt Templates 讓 RD 在 AI 對話模式中，透過預建的 prompt 按鈕即時控制 Gemini AI 的行為。例如當小孩問奇怪問題時，按下「裝傻」按鈕，AI 就會裝傻不回答。

## 前置需求

- 現有 Magic DJ Controller 功能已部署（010-magic-dj-controller）
- Gemini API Key 已設定
- 瀏覽器支援 Web Audio API（Chrome/Edge）

## AI 對話模式佈局

切換到 AI 對話模式後，介面分為四欄：

| 欄位 | 功能 | 操作方式 |
|------|------|----------|
| Prompt Templates | AI 行為控制按鈕 | 點擊按鈕 → 送出隱藏 prompt 給 AI |
| Story Prompts | 故事情節引導 | 選擇預設模板或輸入自訂文字 |
| 音效 (SFX) | 串場音效 | 點擊播放（可與 AI 同時播放） |
| 音樂 (Music) | 背景音樂 | 點擊播放（可與 AI 同時播放） |

頂部常駐 AI 控制列：麥克風 toggle、連線狀態、中斷按鈕、強制送出。

## 基本操作

### 1. 啟動 AI 對話模式

1. 開啟 Magic DJ 頁面
2. 點擊右上角「AI 對話」模式切換
3. 等待 Gemini WebSocket 連線（綠色狀態指示燈）
4. 點擊「開始 Session」

### 2. 使用 Prompt Template

1. 在第一欄找到想要的 prompt template（如「裝傻」）
2. 點擊按鈕 → 按鈕會短暫閃爍表示已送出
3. AI 會根據隱藏的 prompt 調整回應行為
4. 可在 AI 講話中或對話間隙隨時點擊

### 3. 使用 Story Prompt

**預設模板**:
1. 在第二欄找到故事模板（如「魔法森林」）
2. 點擊模板 → 完整故事指令送出給 AI
3. AI 會自然地轉換到新故事場景

**自訂輸入**:
1. 在第二欄底部的文字輸入框輸入任何指令
2. 按 Enter 或點擊送出按鈕
3. 輸入的文字會作為 text_input 送給 AI

### 4. 搭配音效和音樂

- AI 講話時，可以同時播放音效和背景音樂
- 三者使用獨立頻道，互不干擾
- 使用音量滑桿調整各頻道音量

## 預設 Prompt Templates

| 名稱 | 用途 | 快捷鍵 |
|------|------|--------|
| 裝傻 | 小孩問奇怪問題時，讓 AI 裝傻岔開話題 | `1` |
| 轉移話題 | 對話卡住時，讓 AI 轉到新話題 | `2` |
| 鼓勵 | 小孩完成任務時，讓 AI 熱情讚美 | `3` |
| 等一下 | 需要時間時，讓 AI 請小孩等待 | `4` |
| 結束故事 | 準備結束時，讓 AI 收尾故事 | `5` |
| 回到主題 | 小孩分心時，讓 AI 引導回來 | `6` |
| 簡短回答 | AI 話太多時，讓 AI 簡短回覆 | `7` |
| 多問問題 | 想讓小孩多說話時，讓 AI 多提問 | `8` |

## 自訂 Prompt Template

1. 在 Prompt Template 面板底部點擊「+ 新增」
2. 填寫：
   - **名稱**: 按鈕顯示文字（2-4 字）
   - **Prompt 內容**: 送給 AI 的隱藏指令（最多 500 字）
   - **顏色**: 選擇按鈕顏色
3. 儲存 → 新按鈕出現在面板中

編輯/刪除：長按或右鍵任一 template 按鈕。

## 技術架構

```
RD 點擊按鈕
     ↓
sendMessage('text_input', { text: template.prompt })
     ↓
Backend WebSocket Handler
     ↓
GeminiRealtimeService.send_text(prompt)
     ↓
Gemini V2V WebSocket
     ↓
AI 調整回應行為
```

## 故障排除

| 問題 | 解決方案 |
|------|----------|
| 按鈕顯示灰色無法點擊 | 確認 Gemini WebSocket 已連線（綠色指示燈） |
| AI 沒有按照 prompt 行動 | 嘗試編輯 prompt 內容，使用更明確的指令 |
| 音效/音樂與 AI 衝突 | 調整各頻道音量，確保 AI 語音不被蓋過 |
| Prompt template 消失 | 檢查 localStorage，嘗試匯入 preset 檔案 |
