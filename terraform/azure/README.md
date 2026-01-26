# Azure Speech Services Terraform 配置

本 Terraform 配置用於建立 Azure Cognitive Services Speech 資源，提供 TTS（文字轉語音）和 STT（語音轉文字）功能。

## 目錄

- [架構概覽](#架構概覽)
- [前置需求](#前置需求)
- [快速開始](#快速開始)
- [詳細教學](#詳細教學)
- [取得 API Key](#取得-api-key)
- [整合至 Voice Lab](#整合至-voice-lab)
- [進階配置](#進階配置)
- [常見問題](#常見問題)

## 架構概覽

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Cloud                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Resource Group: voice-lab-speech-rg     │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │     Cognitive Services (SpeechServices)     │  │  │
│  │  │                                             │  │  │
│  │  │  ┌─────────────┐    ┌─────────────┐        │  │  │
│  │  │  │    TTS      │    │    STT      │        │  │  │
│  │  │  │ 文字轉語音   │    │  語音轉文字  │        │  │  │
│  │  │  └─────────────┘    └─────────────┘        │  │  │
│  │  │                                             │  │  │
│  │  │  • API Key 認證                             │  │  │
│  │  │  • Managed Identity (選用)                  │  │  │
│  │  │  • 網路存取控制 (選用)                       │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 前置需求

### 1. 安裝 Azure CLI

```bash
# macOS
brew install azure-cli

# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows (PowerShell)
winget install Microsoft.AzureCLI
```

### 2. 安裝 Terraform

```bash
# macOS
brew install terraform

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

### 3. 登入 Azure

```bash
# 登入 Azure 帳號
az login

# 確認目前的訂閱
az account show

# 如有多個訂閱，選擇正確的訂閱
az account list --output table
az account set --subscription "<subscription-id>"
```

## 快速開始

只需要 5 個步驟，即可完成 Azure Speech Services 的建立：

```bash
# 1. 進入 Azure Terraform 目錄
cd terraform/azure

# 2. 複製並編輯配置檔
cp terraform.tfvars.example terraform.tfvars
# 編輯 terraform.tfvars 設定你的值

# 3. 初始化 Terraform
terraform init

# 4. 預覽並部署
terraform plan
terraform apply

# 5. 取得 API Key
az cognitiveservices account keys list \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg \
    --query key1 -o tsv
```

## 詳細教學

### 步驟一：配置變數

編輯 `terraform.tfvars` 檔案：

```hcl
# 資源命名
resource_group_name = "voice-lab-speech-rg"
speech_service_name = "voice-lab-speech"

# 區域選擇（建議選擇離使用者最近的區域）
# 台灣地區建議使用 eastasia（香港）或 japaneast（東京）
location = "eastasia"

# SKU 選擇
# F0 = 免費層（開發測試用，有配額限制）
# S0 = 標準層（生產環境，按量計費）
sku_name = "S0"

# 環境標籤
environment = "dev"

# 其他標籤
tags = {
  Project = "voice-lab"
  Team    = "platform"
}
```

### 步驟二：初始化 Terraform

```bash
cd terraform/azure
terraform init
```

成功輸出：
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/azurerm versions matching "~> 4.0"...
- Installing hashicorp/azurerm v4.x.x...

Terraform has been successfully initialized!
```

### 步驟三：預覽變更

```bash
terraform plan
```

確認將建立以下資源：
- `azurerm_resource_group.speech` - 資源群組
- `azurerm_cognitive_account.speech` - Speech Services 資源

### 步驟四：執行部署

```bash
terraform apply
```

輸入 `yes` 確認部署。部署完成後會顯示：
```
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

speech_endpoint = "https://eastasia.api.cognitive.microsoft.com/"
speech_region = "eastasia"
get_api_keys_command = "az cognitiveservices account keys list --name voice-lab-speech --resource-group voice-lab-speech-rg"
```

## 取得 API Key

**重要**：基於安全考量，API Key 不會透過 Terraform 輸出。請使用 Azure CLI 取得：

### 方法一：取得完整 Key 資訊

```bash
az cognitiveservices account keys list \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg
```

輸出：
```json
{
  "key1": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "key2": "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
}
```

### 方法二：只取得 key1

```bash
az cognitiveservices account keys list \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg \
    --query key1 -o tsv
```

### 方法三：使用 Terraform 輸出的指令

```bash
# 取得指令
terraform output get_key1_command

# 執行指令
$(terraform output -raw get_key1_command)
```

### Key 輪換（安全最佳實踐）

定期輪換 API Key 以提高安全性：

```bash
# 1. 先將應用程式切換到使用 key2
# 2. 重新產生 key1
az cognitiveservices account keys regenerate \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg \
    --key-name key1

# 3. 將應用程式切換回 key1
# 4. 重新產生 key2
az cognitiveservices account keys regenerate \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg \
    --key-name key2
```

## 整合至 Voice Lab

### 本地開發

在 `backend/.env` 中設定：

```bash
# Azure Speech Services
AZURE_SPEECH_KEY=<your-api-key>
AZURE_SPEECH_REGION=eastasia
```

### GCP Cloud Run 部署

已建立的 Key 可以儲存到 GCP Secret Manager，透過主要的 Terraform 配置整合：

```bash
cd terraform  # 回到主 Terraform 目錄

# 在 terraform.tfvars 中設定
azure_speech_key = "<your-api-key>"

# 重新部署
terraform apply
```

### 驗證整合

```bash
# 啟動後端服務
cd backend && uvicorn src.main:app --reload

# 測試 TTS
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界", "provider": "azure", "voice_id": "zh-TW-HsiaoChenNeural"}'
```

## 進階配置

### 網路存取限制

限制只允許特定 IP 存取：

```hcl
# terraform.tfvars
allowed_ip_ranges = [
  "203.0.113.0/24",    # 公司 IP 範圍
  "198.51.100.1"       # CI/CD 伺服器
]
```

### Managed Identity

啟用 Managed Identity 以支援無密碼認證：

```hcl
# terraform.tfvars
enable_managed_identity = true
enable_custom_subdomain = true  # 使用 Managed Identity 必須啟用
```

### 多環境部署

建立不同環境的配置：

```bash
# 開發環境
terraform workspace new dev
terraform apply -var-file="environments/dev.tfvars"

# 生產環境
terraform workspace new prod
terraform apply -var-file="environments/prod.tfvars"
```

## SKU 比較

| 項目 | F0（免費） | S0（標準） |
|------|-----------|-----------|
| 費用 | 免費 | 按量計費 |
| 神經網路 TTS | 500K 字元/月 | 無限制 |
| STT | 5 小時/月 | 無限制 |
| 並行請求 | 1 | 100+ |
| 配額調整 | ❌ | ✅ |
| SLA | ❌ | 99.9% |
| 適用場景 | 開發測試 | 生產環境 |

**注意**：F0 配額用完後會停止服務直到下個月，無法調整。

## 常見問題

### Q: Terraform apply 失敗，顯示 "AuthorizationFailed"

**原因**：Azure 帳號沒有建立資源的權限。

**解決方案**：
```bash
# 確認登入狀態
az account show

# 重新登入
az login

# 確認有 Contributor 或更高權限
az role assignment list --assignee <your-email>
```

### Q: 資源名稱衝突

**原因**：Speech Service 名稱在 Azure 全域必須唯一。

**解決方案**：
```hcl
# 使用更唯一的名稱
speech_service_name = "voice-lab-speech-<your-unique-suffix>"
```

### Q: 如何刪除所有資源？

```bash
terraform destroy
```

### Q: 如何查看目前資源狀態？

```bash
# Terraform 狀態
terraform show

# Azure Portal
az cognitiveservices account show \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg
```

## Terraform 程式碼檢查

本專案使用以下工具確保 Terraform 程式碼品質：

```bash
# 格式化檢查
terraform fmt -check -recursive terraform/azure/

# 格式化（自動修正）
terraform fmt -recursive terraform/azure/

# 驗證配置
terraform validate
```

## 參考資源

- [Azure Speech Service 文件](https://learn.microsoft.com/zh-tw/azure/ai-services/speech-service/)
- [Speech Service 定價](https://azure.microsoft.com/zh-tw/pricing/details/cognitive-services/speech-services/)
- [azurerm_cognitive_account Terraform 文件](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cognitive_account)
- [Azure CLI cognitiveservices 指令](https://learn.microsoft.com/zh-tw/cli/azure/cognitiveservices/account)
