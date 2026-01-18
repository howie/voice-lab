# Quickstart: Provider API Key Management

本指南說明如何使用 Provider API Key Management 功能來管理您自己的 TTS/STT 服務提供者 API 金鑰。

## 概述

Voice Lab 支援 BYOL (Bring Your Own License) 模式，讓您可以使用自己的 API 金鑰來存取 TTS/STT 服務。支援的提供者包括：

- **ElevenLabs** - 高品質 AI 語音合成
- **Azure Cognitive Services** - Microsoft 語音服務
- **Google Gemini** - Google AI 語音服務

## 前置需求

1. 已登入 Voice Lab 帳號
2. 已取得目標提供者的 API 金鑰

### 取得 API 金鑰

| 提供者 | 取得方式 |
|--------|----------|
| ElevenLabs | [ElevenLabs Console](https://elevenlabs.io/app/settings/api-keys) → Profile → API Key |
| Azure | [Azure Portal](https://portal.azure.com) → Cognitive Services → Keys and Endpoint |
| Gemini | [Google AI Studio](https://aistudio.google.com/app/apikey) → Get API Key |

## 新增 API 金鑰

### 透過 UI

1. 登入 Voice Lab
2. 前往 **Settings** → **Providers**
3. 選擇要設定的提供者
4. 輸入您的 API 金鑰
5. 點擊 **Save & Validate**

系統會自動驗證您的金鑰是否有效。

### 透過 API

```bash
curl -X POST /api/v1/credentials \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "elevenlabs",
    "api_key": "your-api-key-here"
  }'
```

成功回應：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "elevenlabs",
  "provider_display_name": "ElevenLabs",
  "masked_key": "****abc1",
  "is_valid": true,
  "last_validated_at": "2026-01-18T10:30:00Z",
  "created_at": "2026-01-18T10:30:00Z"
}
```

## 選擇語音模型

設定 API 金鑰後，您可以選擇要使用的語音模型：

### 列出可用模型

```bash
curl -X GET /api/v1/credentials/{credentialId}/models \
  -H "Authorization: Bearer <your-token>"
```

### 設定預設模型

```bash
curl -X PUT /api/v1/credentials/{credentialId} \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_model_id": "zh-TW-HsiaoChenNeural"
  }'
```

## 管理金鑰

### 更新 API 金鑰

當您需要輪換金鑰時：

```bash
curl -X PUT /api/v1/credentials/{credentialId} \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "new-api-key-here"
  }'
```

### 重新驗證金鑰

```bash
curl -X POST /api/v1/credentials/{credentialId}/validate \
  -H "Authorization: Bearer <your-token>"
```

### 刪除金鑰

```bash
curl -X DELETE /api/v1/credentials/{credentialId} \
  -H "Authorization: Bearer <your-token>"
```

## 金鑰優先順序

當使用 TTS/STT 服務時，系統會依以下順序選擇 API 金鑰：

1. **使用者金鑰** - 您自己設定的 API 金鑰（優先）
2. **系統金鑰** - 系統管理員設定的共用金鑰（備援）

如果您有設定自己的金鑰，系統會優先使用您的金鑰。

## 安全性

- 所有 API 金鑰都會在儲存前加密
- 金鑰在 UI 和 API 回應中只會顯示最後 4 個字元
- 所有金鑰操作都會記錄在稽核日誌中

## 常見問題

### Q: 驗證失敗怎麼辦？

1. 確認 API 金鑰正確無誤
2. 確認金鑰未過期或被撤銷
3. 確認提供者帳號狀態正常

### Q: 如何知道金鑰是否有效？

在 Provider Settings 頁面可以看到每個金鑰的狀態。綠色表示有效，紅色表示無效。

### Q: 可以設定多個提供者嗎？

可以，您可以同時設定多個提供者的金鑰，並在使用時選擇要使用哪個。

## 下一步

- 查看 [API 文件](./contracts/provider-credentials-api.yaml) 了解完整 API 規格
- 查看 [資料模型](./data-model.md) 了解資料結構
