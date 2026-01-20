# Research: GCP Terraform Deploy

**Feature**: 006-gcp-terraform-deploy
**Date**: 2026-01-20

## Executive Summary

本研究評估了 Voice Lab 部署到 GCP 的最佳方案，重點在於成本最佳化、Terraform 最佳實踐和 Cloudflare 整合。

---

## 1. GCP 服務選擇：成本最佳化

### Decision: Cloud Run + Cloud SQL (db-f1-micro) + Secret Manager

### Rationale

| 服務 | 選擇 | 月成本估計 | 理由 |
|------|------|-----------|------|
| 運算 | Cloud Run | $0-5 | 按請求計費，閒置時零成本 |
| 資料庫 | Cloud SQL db-f1-micro | ~$10 | 最小可用規格，足夠 10-20 使用者 |
| 機密管理 | Secret Manager | $0 | 免費額度內（6 個 secrets, 10K operations/月）|
| 儲存 | Cloud Storage | ~$0.01 | Terraform state + 音訊檔案 |
| **總計** | | **~$10-15/月** | |

### Alternatives Considered

| 方案 | 月成本估計 | 為何拒絕 |
|------|-----------|----------|
| App Engine | $30-50 | 維持最小運行實例，閒置成本高 |
| GKE | $50-100+ | 需要最少 3 節點叢集，遠超需求 |
| Compute Engine VM | $20-30 | 需要自行管理，24/7 運行成本 |
| Cloud Run + Firestore | ~$10 | Firestore 對現有 PostgreSQL 遷移成本高 |

### Cloud Run 成本最佳化設定

```hcl
# 關鍵設定
min_instances = 0        # 閒置時零成本
cpu = 1                  # 最小 vCPU
memory = "512Mi"         # 最小記憶體
execution_environment = "gen2"  # 更好的定價
```

---

## 2. Terraform 架構設計

### Decision: 模組化設計 + GCS Remote State + VPC Serverless Connector

### Rationale

模組化設計符合 Clean Architecture 原則，每個模組職責單一，便於維護和重用。

### 目錄結構

```text
terraform/
├── main.tf                      # 主入口
├── variables.tf                 # 全域變數
├── outputs.tf                   # 輸出值
├── versions.tf                  # Provider 版本鎖定
├── backend.tf                   # GCS remote state
├── terraform.tfvars.example     # 範例配置
└── modules/
    ├── apis/                    # GCP API 啟用
    │   ├── main.tf
    │   └── variables.tf
    ├── networking/              # VPC + Serverless Connector
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── cloud-sql/               # PostgreSQL 實例
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── secrets/                 # Secret Manager
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── iam/                     # 服務帳號與權限
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── cloud-run/               # Cloud Run 服務
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── storage/                 # Cloud Storage buckets
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### GCS Backend 配置

```hcl
terraform {
  backend "gcs" {
    bucket       = "voice-lab-tf-state"
    prefix       = "terraform/state"
    use_lockfile = true  # Terraform 1.10+ 原生鎖定
  }
}
```

### 必要 GCP APIs

```hcl
required_apis = [
  "run.googleapis.com",              # Cloud Run
  "sqladmin.googleapis.com",         # Cloud SQL
  "secretmanager.googleapis.com",    # Secret Manager
  "compute.googleapis.com",          # VPC/Networking
  "servicenetworking.googleapis.com", # Private Service Access
  "cloudresourcemanager.googleapis.com", # Project 管理
  "iam.googleapis.com",              # IAM
  "artifactregistry.googleapis.com", # Container Registry
]
```

### VPC Serverless Connector 架構

```
Cloud Run → VPC Serverless Connector → Private VPC → Cloud SQL (Private IP)
```

關鍵配置：
- Connector 需要專用 /28 子網段
- Cloud SQL 使用 Private IP（停用 Public IP）
- Cloud Run 設定 `egress = "PRIVATE_RANGES_ONLY"`

---

## 3. Cloudflare 整合

### Decision: Cloudflare DNS Only (灰雲) + Cloud Run Domain Mapping

### Rationale

Cloud Run 的 Domain Mapping 與 Cloudflare Proxy 模式不相容。使用 DNS Only 模式配合 Google 託管憑證是最穩定的配置。

### 配置方案

**方案 A（推薦）: DNS Only + Google 託管憑證**

```hcl
# Cloudflare DNS 記錄
resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = "voice-lab"
  type    = "CNAME"
  value   = "ghs.googleusercontent.com"
  ttl     = 3600
  proxied = false  # 必須為 false
}

# Cloud Run Domain Mapping
resource "google_cloud_run_domain_mapping" "custom" {
  location = var.region
  name     = "voice-lab.heyuai.com.tw"

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.backend.name
  }
}
```

**方案 B（進階）: Cloud Load Balancer + Cloudflare Proxy**

如果需要 Cloudflare 的 DDoS 防護和快取功能：

```
User → Cloudflare (Proxy) → Global Load Balancer → Serverless NEG → Cloud Run
```

這需要額外配置 Google Cloud Load Balancer，增加約 $20/月成本。

### SSL/TLS 配置

1. **Cloudflare SSL/TLS 模式**: Full (不是 Full Strict)
2. **停用 Always Use HTTPS**: 避免重定向迴圈
3. **Google 託管憑證**: 自動簽發和續期（需 15 分鐘至 24 小時）

### Alternatives Considered

| 方案 | 為何拒絕 |
|------|----------|
| Cloudflare Proxy + Cloud Run | 不相容 Domain Mapping，會造成憑證驗證失敗 |
| Cloudflare Origin Certificate | 需要額外配置 Load Balancer，增加成本 |
| 自簽憑證 | 安全性不足，瀏覽器警告 |

---

## 4. Google OAuth 網域限制

### Decision: 應用程式層級實作

### Rationale

Cloud Run 沒有內建的 OAuth 網域限制功能，需在應用程式層級實作。這提供最大的靈活性且無額外成本。

### 實作方式

```python
# backend/src/auth/oauth.py
from google.oauth2.id_token import verify_oauth2_token

ALLOWED_DOMAINS = ["heyuai.com.tw"]  # 從環境變數讀取

async def verify_google_token(token: str) -> dict:
    id_info = verify_oauth2_token(token, Request(), CLIENT_ID)
    email = id_info.get("email", "")
    domain = email.split("@")[-1]

    if domain not in ALLOWED_DOMAINS:
        raise HTTPException(403, f"Domain {domain} not allowed")

    return id_info
```

### 配置流程

1. 在 Google Cloud Console 建立 OAuth 2.0 Client ID
2. 設定 Authorized redirect URIs: `https://voice-lab.heyuai.com.tw/auth/callback`
3. 在 Terraform 變數中配置允許的網域清單
4. 透過 Secret Manager 儲存 OAuth Client ID 和 Secret

---

## 5. Secret 管理策略

### Decision: GCP Secret Manager + 環境變數注入

### 需要管理的 Secrets

| Secret | 用途 |
|--------|------|
| `db-password` | Cloud SQL PostgreSQL 密碼 |
| `oauth-client-id` | Google OAuth Client ID |
| `oauth-client-secret` | Google OAuth Client Secret |
| `openai-api-key` | OpenAI API Key |
| `azure-speech-key` | Azure Speech Services Key |
| `google-tts-credentials` | Google TTS Service Account JSON |
| `elevenlabs-api-key` | ElevenLabs API Key |

### 注入模式

```hcl
resource "google_cloud_run_v2_service" "backend" {
  template {
    containers {
      # 非敏感環境變數
      env {
        name  = "DATABASE_HOST"
        value = module.cloud_sql.private_ip
      }

      # 敏感資料從 Secret Manager 讀取
      env {
        name = "DATABASE_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "db-password"
            version = "latest"
          }
        }
      }
    }
  }
}
```

---

## 6. 容器化策略

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY backend/pyproject.toml backend/uv.lock ./
RUN pip install uv && uv sync --frozen

# 複製程式碼
COPY backend/src ./src
COPY backend/alembic ./alembic
COPY backend/alembic.ini .

# 執行 FastAPI
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Frontend Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 部署架構

```
Artifact Registry
├── voice-lab-backend:latest
└── voice-lab-frontend:latest

Cloud Run Services
├── voice-lab-backend  (api.voice-lab.heyuai.com.tw)
└── voice-lab-frontend (voice-lab.heyuai.com.tw)
```

---

## 7. 資源命名慣例

### Decision: 採用 `{project}-{env}-{resource}` 格式

| 資源類型 | 命名範例 |
|----------|----------|
| GCP Project | `voice-lab-test` |
| Cloud Run Service | `voice-lab-test-backend`, `voice-lab-test-frontend` |
| Cloud SQL Instance | `voice-lab-test-postgres` |
| VPC Network | `voice-lab-test-vpc` |
| Service Account | `voice-lab-test-cloudrun-sa` |
| Secret | `voice-lab-test-db-password` |
| GCS Bucket | `voice-lab-test-tf-state` |

---

## Summary of Decisions

| 領域 | 決定 | 關鍵理由 |
|------|------|----------|
| 運算服務 | Cloud Run | 按請求計費，閒置零成本 |
| 資料庫 | Cloud SQL db-f1-micro | 最低成本可用規格 |
| 機密管理 | Secret Manager | 免費額度內，原生整合 |
| 狀態管理 | GCS + 原生鎖定 | 團隊協作，版本控制 |
| SSL/DNS | Cloudflare DNS Only | 與 Cloud Run Domain Mapping 相容 |
| OAuth | 應用程式層級 | 最大靈活性，無額外成本 |
| 網路 | VPC Serverless Connector | 安全的私有連線 |
| 容器 | Artifact Registry | GCP 原生，與 Cloud Run 整合 |

---

## References

- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Cloud SQL Pricing](https://cloud.google.com/sql/pricing)
- [Terraform GCP Best Practices](https://cloud.google.com/docs/terraform/best-practices-for-terraform)
- [Cloud Run Domain Mapping](https://cloud.google.com/run/docs/mapping-custom-domains)
- [VPC Serverless Access](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)
