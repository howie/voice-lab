# 2026 Voice AI 技術堆疊總覽

> 最後更新：2026-01

## 架構層級

```
┌──────────────────────────────────────────────────────────────┐
│  傳輸層: WebRTC (現在) → MoQ (未來)                           │
├──────────────────────────────────────────────────────────────┤
│  STT: Deepgram / Gladia / Qwen3-ASR-Flash                    │
├──────────────────────────────────────────────────────────────┤
│  LLM: Gemini 3 Flash (🏆推薦) / Groq+Llama4 / GPT-4o         │
├──────────────────────────────────────────────────────────────┤
│  TTS: Cartesia / ElevenLabs / Deepgram                       │
├──────────────────────────────────────────────────────────────┤
│  框架: Pipecat / LiveKit                                     │
└──────────────────────────────────────────────────────────────┘
```

## 文件索引

| 文件 | 說明 |
|------|------|
| [01-transport-layer.md](./01-transport-layer.md) | 傳輸層技術 (WebRTC, MoQ) |
| [02-stt.md](./02-stt.md) | 語音轉文字 (STT) 服務比較 |
| [03-llm.md](./03-llm.md) | 大型語言模型選擇 |
| [04-tts.md](./04-tts.md) | 文字轉語音 (TTS) 服務比較 |
| [05-frameworks.md](./05-frameworks.md) | Voice AI 框架 |

## 選型考量因素

### 延遲預算 (End-to-End)

理想的對話式 AI 延遲目標：**< 500ms**

| 階段 | 目標延遲 |
|------|----------|
| 傳輸 (雙向) | < 50ms |
| STT | < 100ms |
| LLM (TTFT) | < 150ms |
| TTS (TTFB) | < 100ms |
| Buffer | ~100ms |

### 成本結構

- **STT**: 按音訊時長計費 ($/min)
- **LLM**: 按 token 計費 ($/1M tokens)
- **TTS**: 按字元計費 ($/1M chars)
- **傳輸**: 按頻寬計費

### 品質指標

- **STT**: WER (Word Error Rate)
- **LLM**: 回應品質、一致性
- **TTS**: MOS (Mean Opinion Score)、自然度

## 快速推薦

### 開發/原型階段
- 框架：Pipecat (簡單) 或 LiveKit (完整)
- STT：Deepgram
- LLM：Gemini 3 Flash 🆕 或 GPT-4o-mini
- TTS：Cartesia

### 生產環境 - 注重延遲 🏆
- 框架：LiveKit
- STT：Deepgram
- LLM：**Gemini 3 Flash** ⚡ (2026 首選)
- TTS：Cartesia

### 生產環境 - 注重品質
- 框架：LiveKit
- STT：Deepgram / Gladia
- LLM：Gemini 3 Pro 🆕 或 GPT-4o
- TTS：ElevenLabs

### 生產環境 - 注重成本
- 框架：Pipecat (self-hosted)
- STT：Qwen3-ASR-Flash (self-hosted)
- LLM：Llama 4 + Groq 或 Gemini 2.0 Flash
- TTS：Deepgram

## 更新日誌

| 日期 | 變更 |
|------|------|
| 2026-01 | 🆕 新增 Gemini 3 Flash/Pro 至 LLM 推薦 |
| 2025-01 | 新增 Google Gemini 2.0 系列 |
| 2025-01 | 初始版本 |
