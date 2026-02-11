# Cloud Run Keep-Warm 策略：解決冷啟動導致的 Network Error

## 問題描述

TTS 頁面偶爾出現「網路連線問題」(Network Error)，根因分析發現主要來自 Cloud Run 冷啟動：

- Backend `min_instance_count = 0`，實例閒置後被回收
- 使用者請求到達時，Cloud Run 需要重新啟動容器（冷啟動 3-10 秒）
- 前端 Axios 在等待期間 timeout → 拋出 `ERR_NETWORK` → 顯示「網路連線問題」

### 錯誤觸發路徑

```
Cloud Run 冷啟動 (3-10s)
  → Axios 請求超時 / 無回應
  → error.message = "Network Error" (code: ERR_NETWORK)
  → multiRoleTTSStore.ts catch block 設定 error state
  → ErrorDisplay.tsx 匹配 /network|ERR_NETWORK/i
  → 顯示「網路連線問題 - 無法連接到伺服器」
```

## 方案比較

### 方案 A：Cloud Scheduler Ping（已實作）

每 5 分鐘透過 Cloud Scheduler 對 Cloud Run health endpoint 發送 HTTP GET，保持實例 warm。

**架構：**
```
Cloud Scheduler (每 5 分鐘)
  → HTTP GET → Cloud Run /api/v1/health
  → 實例保持 warm，避免冷啟動
```

**費用：**
| 項目 | 計算 | 月費 (USD) |
|---|---|---|
| Cloud Scheduler | 3 個免費 job | $0.00 |
| Cloud Run 請求 | 8,640 次/月（200 萬次免費額度內） | $0.00 |
| Cloud Run CPU/Memory | health check ~10ms | ≈ $0.01 |
| **合計** | | **≈ $0.01/月** |

**優點：**
- 極低成本
- 實作簡單
- 適合開發/Staging 環境

**缺點：**
- 不保證 100% warm（GCP 可能在 ping 之間回收實例）
- 高負載期間仍可能出現冷啟動
- Cloud Run idle timeout ~15 分鐘，5 分鐘間隔應足夠但不絕對

### 方案 B：Min Instances = 1（生產推薦）

設定 `min_instance_count = 1`，GCP 保證至少一個實例永遠運行。

**費用：**
| 項目 | 計算 | 月費 (USD) |
|---|---|---|
| CPU (idle) | 1 vCPU × 730 hr × $0.00000250/vCPU-s | ≈ $6.57 |
| Memory (idle) | 512MB × 730 hr × $0.00000025/GiB-s | ≈ $0.34 |
| **合計** | | **≈ $6.91/月** |

**優點：**
- 100% 保證無冷啟動
- 配置最簡單（改一個數字）

**缺點：**
- 持續計費，即使無流量

### 建議策略

| 環境 | 策略 | 月費 |
|---|---|---|
| **Production** | `min_instance_count = 1`（未來升級） | ~$7/月 |
| **Staging** | Cloud Scheduler ping 每 5 分鐘 | ~$0.01/月 |
| **Dev** | 不處理，接受冷啟動 | $0 |

## 實作內容

### 新增 Terraform 資源

1. **`terraform/modules/apis/main.tf`**
   - 啟用 `cloudscheduler.googleapis.com` API

2. **`terraform/modules/cloud-run/main.tf`**
   - 新增 `google_cloud_scheduler_job.keep_warm_backend` — 每 5 分鐘 ping backend
   - 新增 `google_cloud_scheduler_job.keep_warm_frontend` — 每 5 分鐘 ping frontend
   - 透過 `var.enable_keep_warm` 控制是否啟用
   - Scheduler 使用 `allUsers` 已有的 public invoker 權限（無需額外 Service Account）

3. **`terraform/modules/cloud-run/variables.tf`**
   - 新增 `enable_keep_warm` 變數（預設 `false`）

4. **`terraform/variables.tf`** / **`terraform/main.tf`**
   - 透傳 `enable_keep_warm` 到 cloud-run module

### 啟用方式

在 `terraform.tfvars` 中：

```hcl
# 啟用 Cloud Scheduler keep-warm（適合 staging 環境）
enable_keep_warm = true
```

## 相關檔案

- `frontend/src/components/multi-role-tts/ErrorDisplay.tsx` — 錯誤分類與顯示
- `frontend/src/stores/multiRoleTTSStore.ts` — TTS 錯誤處理
- `backend/src/presentation/api/routes/health.py` — Health endpoint
- `terraform/modules/cloud-run/main.tf` — Cloud Run 與 Scheduler 配置
