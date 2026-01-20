# Voice Lab GCP Deployment Quickstart

本指南說明如何將 Voice Lab 部署到 Google Cloud Platform。

---

## Prerequisites

在開始之前，請確保已完成以下準備工作：

### 1. 安裝必要工具

```bash
# Terraform CLI (1.6+)
brew install terraform  # macOS
# 或參考 https://developer.hashicorp.com/terraform/install

# Google Cloud SDK
brew install google-cloud-sdk  # macOS
# 或參考 https://cloud.google.com/sdk/docs/install

# Docker (用於建置容器映像)
brew install docker  # macOS
```

### 2. GCP 專案設定

1. 建立或選擇一個 GCP 專案
2. 啟用計費功能
3. 取得專案 ID（記下來，後續會用到）

### 3. Google OAuth 設定

1. 前往 [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. 點擊「Create Credentials」→「OAuth client ID」
3. 選擇「Web application」
4. 設定：
   - Name: `Voice Lab`
   - Authorized redirect URIs:
     - `https://voice-lab.heyuai.com.tw/auth/callback`（替換為你的網域）
     - `https://api.voice-lab.heyuai.com.tw/auth/callback`
5. 記下 Client ID 和 Client Secret

### 4. Cloudflare 設定（如果使用自訂網域）

1. 前往 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 選擇你的網域
3. 取得 Zone ID（在 Overview 頁面右側）
4. 建立 API Token：
   - My Profile → API Tokens → Create Token
   - 使用 「Edit zone DNS」 模板
   - 限制到你的網域

---

## Quick Deploy (5 分鐘)

### Step 1: 驗證 GCP 身份

```bash
# 登入 GCP
gcloud auth login

# 設定專案
gcloud config set project YOUR_PROJECT_ID

# 建立應用程式預設憑證
gcloud auth application-default login
```

### Step 2: 建立 Terraform State Bucket

```bash
# 建立 bucket（名稱必須全域唯一）
gcloud storage buckets create gs://voice-lab-tf-state-YOUR_PROJECT_ID \
  --location=asia \
  --uniform-bucket-level-access

# 啟用版本控制
gcloud storage buckets update gs://voice-lab-tf-state-YOUR_PROJECT_ID \
  --versioning
```

### Step 3: 配置 Terraform

```bash
# 進入 terraform 目錄
cd terraform

# 複製範例配置檔
cp terraform.tfvars.example terraform.tfvars
```

編輯 `terraform.tfvars`，填入必要的值：

```hcl
# 必填
project_id          = "your-gcp-project-id"
oauth_client_id     = "your-client-id.apps.googleusercontent.com"
oauth_client_secret = "your-client-secret"
allowed_domains     = ["heyuai.com.tw"]

# 選填（如果使用自訂網域）
custom_domain        = "voice-lab.heyuai.com.tw"
cloudflare_api_token = "your-cloudflare-token"
cloudflare_zone_id   = "your-zone-id"
```

### Step 4: 初始化 Terraform

```bash
# 初始化（會下載 providers）
terraform init \
  -backend-config="bucket=voice-lab-tf-state-YOUR_PROJECT_ID" \
  -backend-config="prefix=terraform/state"
```

### Step 5: 建置容器映像

```bash
# 回到專案根目錄
cd ..

# 建置並推送 Backend 映像
docker build -t asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/backend:latest -f backend/Dockerfile .
docker push asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/backend:latest

# 建置並推送 Frontend 映像
docker build -t asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/frontend:latest -f frontend/Dockerfile .
docker push asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/frontend:latest
```

### Step 6: 部署

```bash
cd terraform

# 預覽變更
terraform plan

# 執行部署
terraform apply
```

輸入 `yes` 確認部署。部署通常需要 10-15 分鐘。

### Step 7: 設定 DNS（如果使用自訂網域）

如果沒有使用 Cloudflare Provider 自動設定，手動在 Cloudflare 新增 DNS 記錄：

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | voice-lab | ghs.googleusercontent.com | Off (DNS only) |
| CNAME | api.voice-lab | ghs.googleusercontent.com | Off (DNS only) |

等待 DNS 傳播（最多 24 小時，通常 15 分鐘內）。

### Step 8: 驗證部署

```bash
# 查看輸出值
terraform output

# 存取應用程式
open $(terraform output -raw frontend_url)
```

---

## 成本控制

### 閒置時的預估成本

| 服務 | 閒置成本 | 說明 |
|------|----------|------|
| Cloud Run | $0 | min_instances=0 時不收費 |
| Cloud SQL | ~$10/月 | db-f1-micro 最低規格 |
| Secret Manager | $0 | 免費額度內 |
| Cloud Storage | ~$0.01/月 | 小量儲存 |
| **總計** | **~$10-15/月** | |

### 進一步降低成本

1. **停止 Cloud SQL**（不使用時）：
   ```bash
   gcloud sql instances patch voice-lab-postgres --activation-policy=NEVER
   ```

2. **重新啟動 Cloud SQL**：
   ```bash
   gcloud sql instances patch voice-lab-postgres --activation-policy=ALWAYS
   ```

3. **完全銷毀環境**（不使用時）：
   ```bash
   terraform destroy
   ```

---

## 常見操作

### 更新應用程式

```bash
# 重新建置映像
docker build -t asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/backend:latest -f backend/Dockerfile .
docker push asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/backend:latest

# 觸發 Cloud Run 重新部署
gcloud run services update voice-lab-backend --region=asia-east1 --image=asia-east1-docker.pkg.dev/YOUR_PROJECT_ID/voice-lab/backend:latest
```

### 查看日誌

```bash
# Backend 日誌
gcloud run services logs read voice-lab-backend --region=asia-east1

# Frontend 日誌
gcloud run services logs read voice-lab-frontend --region=asia-east1
```

### 連接資料庫

```bash
# 使用 Cloud SQL Proxy
gcloud sql connect voice-lab-postgres --user=voicelab --database=voicelab
```

### 新增允許的網域

1. 編輯 `terraform.tfvars`：
   ```hcl
   allowed_domains = ["heyuai.com.tw", "new-domain.com"]
   ```

2. 重新部署：
   ```bash
   terraform apply
   ```

---

## 故障排除

### 部署失敗：API 未啟用

```bash
# 手動啟用必要的 APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable servicenetworking.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 部署失敗：配額不足

前往 [GCP Quotas](https://console.cloud.google.com/iam-admin/quotas) 申請提高配額。

### Domain Mapping 失敗

1. 確認 Cloudflare DNS 設定為 DNS only（灰雲）
2. 確認 CNAME 指向 `ghs.googleusercontent.com`
3. 等待 15-60 分鐘讓 SSL 憑證簽發

### Cloud Run 無法連接 Cloud SQL

1. 確認 VPC Serverless Connector 已建立
2. 確認 Cloud SQL 使用 Private IP
3. 確認服務帳號有 `roles/cloudsql.client` 權限

### OAuth 登入失敗

1. 確認 Authorized redirect URIs 設定正確
2. 確認 OAuth Client ID 和 Secret 已正確設定在 Secret Manager
3. 檢查 `allowed_domains` 設定

---

## 環境銷毀

當不再需要測試環境時，完全銷毀所有資源：

```bash
# 銷毀所有 Terraform 管理的資源
terraform destroy

# 確認輸入 "yes"
```

**注意**：這會刪除所有資料！如需保留資料，請先手動匯出。

---

## 下一步

- 配置 CI/CD 自動化部署
- 設定監控和告警
- 配置自動縮放規則
- 建立備份策略
