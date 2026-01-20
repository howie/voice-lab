# Quick Start: Multi-Role TTS

本指南說明如何使用多角色 TTS 功能，將多人對話逐字稿轉換為包含不同聲音的音訊檔案。

## 先決條件

1. Voice Lab 應用程式已啟動
2. 至少一個 TTS Provider 的 API 金鑰已設定（透過「API 金鑰」頁面）

## 快速開始

### 步驟 1：進入多角色 TTS 頁面

從左側選單點擊「多角色 TTS」（位於「TTS 測試」下方）。

### 步驟 2：選擇 Provider

從下拉選單選擇 TTS Provider。系統會顯示該 Provider 的多角色支援能力：

| 支援類型 | 說明 |
|---------|------|
| ✅ 原生支援 | 單一請求即可產生多角色音訊（ElevenLabs、Azure、Google Cloud） |
| ⚠️ 分段合併 | 系統會分段產生後自動合併（OpenAI、Cartesia、Deepgram） |

### 步驟 3：輸入對話逐字稿

在輸入區域貼上或輸入對話，支援以下格式：

**格式 1：字母標識**
```
A: 你好，歡迎來到我們的節目！
B: 謝謝邀請，很高興能參加。
A: 今天我們要討論 AI 語音技術的發展...
```

**格式 2：方括號標識**
```
[主持人] 你好，歡迎來到我們的節目！
[來賓] 謝謝邀請，很高興能參加。
[主持人] 今天我們要討論 AI 語音技術的發展...
```

系統會自動解析說話者，並顯示在下方的對應表格中。

### 步驟 4：為每位說話者選擇語音

系統會列出所有偵測到的說話者。為每位說話者從下拉選單中選擇語音：

| 說話者 | 語音 |
|--------|------|
| A / 主持人 | zh-TW-HsiaoChenNeural ▼ |
| B / 來賓 | zh-TW-YunJheNeural ▼ |

### 步驟 5：產生音訊

點擊「產生語音」按鈕。產生完成後，您可以：
- 點擊播放按鈕預覽音訊
- 點擊下載按鈕儲存音訊檔案

## Provider 能力比較

| Provider | 原生多角色 | 最大說話者 | 字元上限 | 進階功能 |
|----------|-----------|-----------|---------|---------|
| ElevenLabs | ✅ | 10 | 5,000 | 打斷、重疊、笑聲 |
| Azure | ✅ | 10 | 10,000 | 情感風格 |
| Google Cloud | ✅ | 6 | 5,000 | - |
| OpenAI | ⚠️ | 6 | 4,096 | 語氣控制 |
| Cartesia | ⚠️ | 6 | 3,000 | - |
| Deepgram | ⚠️ | 6 | 2,000 | - |

## API 使用範例

### 解析對話

```bash
curl -X POST http://localhost:8000/api/v1/tts/multi-role/parse \
  -H "Content-Type: application/json" \
  -d '{
    "dialogue_text": "A: 你好\nB: 嗨\nA: 今天天氣很好"
  }'
```

**回應：**
```json
{
  "turns": [
    {"speaker": "A", "text": "你好", "index": 0},
    {"speaker": "B", "text": "嗨", "index": 1},
    {"speaker": "A", "text": "今天天氣很好", "index": 2}
  ],
  "speakers": ["A", "B"],
  "total_characters": 13,
  "is_valid": true
}
```

### 產生多角色音訊

```bash
curl -X POST http://localhost:8000/api/v1/tts/multi-role/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "azure",
    "dialogue_text": "A: 你好\nB: 嗨",
    "voice_assignments": [
      {"speaker": "A", "voice_id": "zh-TW-HsiaoChenNeural"},
      {"speaker": "B", "voice_id": "zh-TW-YunJheNeural"}
    ],
    "language": "zh-TW",
    "output_format": "mp3"
  }'
```

**回應：**
```json
{
  "audio_content": "//uQxAAAAAANIAAAAAExBTUUz...",
  "content_type": "audio/mpeg",
  "duration_ms": 2500,
  "latency_ms": 1200,
  "provider": "azure",
  "synthesis_mode": "native",
  "storage_path": "storage/azure/abc123.mp3"
}
```

### 取得二進位音訊

```bash
curl -X POST http://localhost:8000/api/v1/tts/multi-role/synthesize/binary \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "azure",
    "dialogue_text": "A: 你好\nB: 嗨",
    "voice_assignments": [
      {"speaker": "A", "voice_id": "zh-TW-HsiaoChenNeural"},
      {"speaker": "B", "voice_id": "zh-TW-YunJheNeural"}
    ]
  }' \
  --output dialogue.mp3
```

## 常見問題

### Q: 為什麼解析失敗？

確保您的對話格式正確：
- 每位說話者標識後需要冒號（`:` 或 `：`）
- 說話者標識可以是單一大寫字母（A-Z）或方括號內的名稱

**正確：**
```
A: 你好
[主持人]: 歡迎
```

**錯誤：**
```
A 你好      （缺少冒號）
主持人: 歡迎 （缺少方括號）
```

### Q: 字元超過上限怎麼辦？

不同 Provider 有不同字元限制。當接近上限時，輸入區域會顯示警告。建議：
1. 縮短對話內容
2. 切換到支援較高上限的 Provider（如 Azure 支援 10,000 字元）
3. 將長對話分成多個較短的段落分別產生

### Q: 分段合併的音訊不自然？

使用不支援原生多角色的 Provider 時，可調整合併參數：
- `gap_ms`：段落間隔（預設 300ms）
- `crossfade_ms`：淡入淡出（預設 50ms）

建議切換到支援原生多角色的 Provider（ElevenLabs、Azure、Google Cloud）以獲得最佳效果。

## 下一步

- 查看 [API 合約](./contracts/multi-role-tts-api.yaml) 了解完整 API 規格
- 查看 [資料模型](./data-model.md) 了解資料結構
- 查看 [研究文件](./research.md) 了解技術決策
