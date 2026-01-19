# STT (Speech-to-Text) Providers Research 2025

> 最後更新：2026-01

本目錄包含針對 2025-2026 年主流語音轉文字 (STT) 供應商的深入研究與評測。

## 📚 詳細研究報告

*   [**Deepgram**](./deepgram.md): 極速、低成本、即時應用首選。
*   [**OpenAI Whisper**](./openai-whisper.md): 開源準確度基準，生態系豐富 (含 Groq)。
*   [**AssemblyAI**](./assemblyai.md): 功能豐富，性價比高，不僅僅是轉錄。
*   [**ElevenLabs Scribe**](./elevenlabs-scribe.md): 頂級準確度，多語言與 GenAI 整合。
*   [**Speechmatics**](./speechmatics.md): 專精困難場景 (兒童語音、重口音)。

---

## ⚡️ 快速比較矩陣

| 供應商 | 最佳用途 | 定價 (Batch/hr) | 即時延遲 (Real-time) | 獨特優勢 |
| :--- | :--- | :--- | :--- | :--- |
| **Deepgram** | **即時語音 AI** | ~$0.26 | **<300ms** (極快) | 速度、成本、Flux 模型 |
| **Whisper (Groq)** | **極致成本效益** | **$0.04** | **<500ms** | 超便宜、開源模型相容 |
| **Whisper (OpenAI)**| **離線高精度** | $0.36 | N/A (僅批次) | 基準準確度 |
| **AssemblyAI** | **內容分析** | $0.15 | ~300ms | 說話者分離、NLP 分析 |
| **ElevenLabs** | **多語言/合規** | $0.40 | ~150ms | 99+ 語言、隱私合規 |
| **Speechmatics** | **特殊場景** | $0.30+ | 較高 | 兒童語音、抗噪 |

---

## 🎯 選型指南

### Q1: 你需要做「即時對話」 (如 AI 客服、語音助理) 嗎？
*   **是** ➡️ 首選 **Deepgram** (Nova-2/Flux)。
    *   *備選*: **Whisper on Groq** (如果你能處理 VAD 和打斷邏輯)。
*   **否** (僅需批次處理) ➡️ 繼續 Q2。

### Q2: 你對「價格」敏感嗎？
*   **非常敏感** ➡️ **Whisper on Groq** ($0.04/hr) 是目前的價格破壞者。
    *   *備選*: **AssemblyAI** ($0.15/hr) 提供了很好的平衡。
*   **還好** ➡️ 繼續 Q3。

### Q3: 你需要「說話者分離 (Diarization)」嗎？
*   **是** ➡️ **Deepgram** 或 **AssemblyAI**。
    *   *注意*: Whisper 原生不支援，需外掛 Pyannote (慢且貴)。
*   **否** ➡️ **OpenAI Whisper (Large-v3)** 提供最佳純文字準確度。

### Q4: 你的音訊有「特殊挑戰」嗎？
*   **兒童/重口音** ➡️ **Speechmatics**。
*   **專有名詞/術語** ➡️ **Deepgram** (Custom Vocab) 或 **AssemblyAI** (Word Boost)。
