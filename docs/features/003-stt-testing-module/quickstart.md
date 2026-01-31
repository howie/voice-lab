# STT Testing Module - Quickstart Guide

**Feature Branch**: `003-stt-testing-module`

## Overview

Voice Lab STT 測試模組讓你可以：
- 上傳音檔或使用麥克風錄音進行語音辨識
- 比較 Azure、GCP、OpenAI Whisper 三家 STT Provider
- 計算 WER/CER 準確度指標
- 查看辨識歷史紀錄

---

## Prerequisites

1. **已設定 Provider API Keys** (透過 [Provider Management](/settings/providers))
   - Azure Speech Services subscription key
   - Google Cloud Speech-to-Text service account
   - OpenAI API key (for Whisper)

2. **瀏覽器要求**
   - Chrome 89+, Firefox 85+, Safari 14+, Edge 89+
   - 麥克風權限（用於錄音功能）

---

## Quick Start

### 1. 上傳音檔測試

```bash
# API 呼叫範例
curl -X POST "http://localhost:8000/api/v1/stt/transcribe" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@test_audio.mp3" \
  -F "provider=azure" \
  -F "language=zh-TW"
```

**回應範例**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "azure",
  "transcript": "你好，歡迎使用語音測試平台",
  "confidence": 0.95,
  "latency_ms": 1234,
  "words": [
    {"word": "你好", "start_ms": 0, "end_ms": 500, "confidence": 0.98},
    {"word": "歡迎", "start_ms": 550, "end_ms": 900, "confidence": 0.96}
  ]
}
```

### 2. 計算 WER/CER

```bash
# 帶 ground truth 的辨識請求
curl -X POST "http://localhost:8000/api/v1/stt/transcribe" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@test_audio.mp3" \
  -F "provider=gcp" \
  -F "language=zh-TW" \
  -F "ground_truth=你好，歡迎使用語音測試平台"
```

**回應包含 WER 分析**:
```json
{
  "id": "...",
  "transcript": "你好，歡迎使用語音測試平台",
  "wer_analysis": {
    "error_rate": 0.0,
    "error_type": "CER",
    "insertions": 0,
    "deletions": 0,
    "substitutions": 0,
    "total_reference": 12
  }
}
```

### 3. 多 Provider 比較

```bash
curl -X POST "http://localhost:8000/api/v1/stt/compare" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@test_audio.mp3" \
  -F "providers=azure" \
  -F "providers=gcp" \
  -F "providers=whisper" \
  -F "language=zh-TW" \
  -F "ground_truth=正確的轉錄文字"
```

**比較結果**:
```json
{
  "audio_file_id": "...",
  "comparison_table": [
    {"provider": "azure", "confidence": 0.95, "latency_ms": 1200, "error_rate": 0.05},
    {"provider": "gcp", "confidence": 0.93, "latency_ms": 1100, "error_rate": 0.08},
    {"provider": "whisper", "confidence": 0.97, "latency_ms": 2500, "error_rate": 0.02}
  ]
}
```

---

## Web UI 使用流程

### 基本測試流程

1. 導航到 **STT 測試** 頁面
2. 選擇輸入方式：
   - **上傳檔案**: 支援 MP3, WAV, M4A, FLAC, WEBM
   - **麥克風錄音**: 點擊錄音按鈕開始
3. 從 **Provider 下拉選單** 選擇 STT Provider（僅顯示已設定有效 API Key 的 Provider）
4. 選擇 **語言**
5. （選用）勾選 **兒童語音模式**
6. 點擊 **開始辨識**
7. 查看結果與波形對照

> **注意**: Provider 下拉選單只會顯示已在 [Provider 管理頁面](/settings/providers) 設定有效 API Key 的服務。若選單為空，請先設定至少一組 Provider 的 API Key。

### WER/CER 分析

1. 完成辨識後，展開 **準確度分析** 區塊
2. 輸入 **正確答案 (Ground Truth)**
3. 點擊 **計算 WER/CER**
4. 查看：
   - 錯誤率百分比
   - 插入/刪除/替換錯誤數
   - 對齊視覺化

---

## Provider 特性比較

| 特性 | Azure | GCP | Whisper |
|------|-------|-----|---------|
| 兒童語音優化 | ⚠️ Phrase hints | ✅ Model selection | ❌ |
| Word Timestamps | ✅ | ✅ | ✅ |
| 最大檔案 | 200 MB | 480 MB | 25 MB |
| 繁中支援 | ✅ | ✅ | ✅ |
| 延遲 | 低 | 低 | 中 |
| 準確度 (CJK) | 高 | 高 | 最高 |

---

## 語言代碼

| 語言 | 代碼 | WER/CER |
|------|------|---------|
| 繁體中文 (台灣) | `zh-TW` | CER |
| 簡體中文 | `zh-CN` | CER |
| English (US) | `en-US` | WER |
| 日本語 | `ja-JP` | CER |
| 한국어 | `ko-KR` | CER |

---

## 錯誤處理

### 常見錯誤代碼

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_FORMAT` | 不支援的音檔格式 | 使用 MP3, WAV, M4A, FLAC, WEBM |
| `FILE_TOO_LARGE` | 檔案超過限制 | 依 Provider 限制壓縮或分割 |
| `PROVIDER_ERROR` | Provider API 錯誤 | 檢查 API Key 設定與額度 |
| `QUOTA_EXCEEDED` | API 配額用盡 | 更換 Provider 或等待配額重置 |

### 錯誤回應範例

```json
{
  "error": "FILE_TOO_LARGE",
  "detail": "File size 30MB exceeds Whisper limit of 25MB",
  "code": "FILE_TOO_LARGE"
}
```

---

## 進階用法

### 自動分段處理 (計劃中功能)

> **注意**: 此功能尚在開發中 (T075)。目前系統會在檔案超過限制時返回錯誤。

計劃中:長音檔（超過 Provider 單次限制）將自動分段處理：

```bash
# 上傳 5 分鐘音檔 (計劃中)
curl -X POST ".../stt/transcribe" \
  -F "audio=@long_audio.mp3" \
  -F "provider=azure"

# 系統將自動分段辨識並合併結果 (尚未實作)
```

### 歷史紀錄管理

```bash
# 列出歷史
curl "http://localhost:8000/api/v1/stt/history?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 刪除紀錄
curl -X DELETE "http://localhost:8000/api/v1/stt/history/{id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Next Steps

- [API Reference](./contracts/stt-api.yaml) - 完整 OpenAPI 規格
- [Data Model](./data-model.md) - 資料模型說明
- [Research Notes](./research.md) - Provider 研究筆記
