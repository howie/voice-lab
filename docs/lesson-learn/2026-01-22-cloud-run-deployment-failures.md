# Cloud Run 部署失敗排查經驗

**日期**: 2026-01-22
**問題**: Terraform apply 時 Cloud Run 容器啟動探測失敗

## 錯誤訊息

```
Error: Error waiting for Updating Service: Error code 9, message: Revision 'voice-lab-backend-00011-5ht' is not ready and cannot serve traffic. The user-provided container failed the configured startup probe checks.
```

## 問題一：資料庫連線配置不匹配

### 症狀
日誌顯示 `ConnectionRefusedError: [Errno 111] Connection refused`，應用程式在啟動時無法連接資料庫。

### 根本原因
- `database.py` 期望 `DATABASE_URL` 環境變數
- Terraform 設定的是分開的變數：`DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
- 當 `DATABASE_URL` 未設定時，會使用預設值 `localhost`，在 Cloud Run 中必定失敗

### 解決方案
修改 `backend/src/infrastructure/persistence/database.py`，新增函數自動組合 URL：

```python
def get_database_url() -> str:
    """Build database URL from environment variables.

    Supports both:
    - Direct DATABASE_URL
    - Separate DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
    """
    # First check for direct DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from separate components (used in Cloud Run)
    host = os.getenv("DATABASE_HOST", "localhost")
    name = os.getenv("DATABASE_NAME", "voicelab")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "postgres")
    port = os.getenv("DATABASE_PORT", "5432")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
```

---

## 問題二：Docker 映像架構不匹配

### 症狀
日誌顯示：
```
terminated: Application failed to start: failed to load /app/.venv/bin/uvicorn: exec format error
```

### 根本原因
- 在 Mac ARM64 (M1/M2) 上建置的 Docker 映像是 `arm64` 架構
- Cloud Run 需要的是 `linux/amd64` 架構
- 架構不匹配導致執行檔無法運行

### 解決方案
使用 `docker buildx` 並指定 `--platform linux/amd64`：

```bash
# 錯誤做法（會使用本機架構）
docker build -f backend/Dockerfile -t image:tag .

# 正確做法（指定 amd64 架構）
docker buildx build --platform linux/amd64 -f backend/Dockerfile -t image:tag --push .
```

---

## 診斷技巧

### 1. 查看 Cloud Run 日誌
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=<revision-name>" \
  --project=<project-id> \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"
```

### 2. 檢查完整日誌（包含 jsonPayload）
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=<revision-name>" \
  --project=<project-id> \
  --limit=30 \
  --format=json | jq -r '.[].textPayload // .[].jsonPayload // "empty"'
```

### 3. 檢查 Cloud Run 環境變數
```bash
gcloud run services describe <service-name> \
  --project=<project-id> \
  --region=<region> \
  --format="yaml(spec.template.spec.containers[0].env)"
```

### 4. 檢查 Cloud SQL 狀態
```bash
gcloud sql instances list --project=<project-id> --format="table(name,state,ipAddresses)"
```

### 5. 檢查 VPC Connector 狀態
```bash
gcloud compute networks vpc-access connectors list \
  --project=<project-id> \
  --region=<region> \
  --format="table(name,state,network)"
```

---

## 預防措施

### 1. 建立部署腳本
在專案中加入標準化的部署腳本：

```bash
#!/bin/bash
# deploy-backend.sh

PROJECT_ID="heyu-voice-lab"
REGION="asia-east1"
IMAGE="asia-east1-docker.pkg.dev/${PROJECT_ID}/voice-lab/backend:latest"

# 使用正確的平台建置
docker buildx build \
  --platform linux/amd64 \
  -f backend/Dockerfile \
  -t ${IMAGE} \
  --push .

# 部署到 Cloud Run
gcloud run deploy voice-lab-backend \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --image=${IMAGE} \
  --quiet
```

### 2. 環境變數設計原則
- 支援多種設定方式（完整 URL 或分開的變數）
- 提供合理的本地開發預設值
- 在文件中清楚說明支援的環境變數

### 3. 啟動時的錯誤處理
- 非關鍵服務（如 JobWorker）的初始化失敗不應阻塞應用程式啟動
- 健康檢查端點應該簡單且不依賴外部服務

---

## 相關檔案

- `backend/src/infrastructure/persistence/database.py` - 資料庫連線配置
- `backend/src/infrastructure/workers/job_worker.py` - 背景工作者啟動邏輯
- `terraform/modules/cloud-run/main.tf` - Cloud Run 服務配置
- `backend/Dockerfile` - Docker 建置配置
