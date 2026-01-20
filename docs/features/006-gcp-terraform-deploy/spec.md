# Feature Specification: GCP Terraform Deploy

**Feature Branch**: `006-gcp-terraform-deploy`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "deploy 到 GCP 研究最省錢的方式把這個 voice lab 透過 terraform 部署到 GCP 方便 internal 測試，在 config 限定登入只能使用某個 domain 如 heyuai.com.tw 的 gmail 登入"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 部署 Voice Lab 到 GCP (Priority: P1)

作為開發團隊成員，我想要透過簡單的 Terraform 指令將 Voice Lab 完整部署到 GCP，以便團隊可以在雲端環境進行整合測試。

**Why this priority**: 這是核心功能，沒有部署就無法進行任何測試。必須先有運行中的環境，其他功能才有意義。

**Independent Test**: 可透過執行 `terraform apply` 並驗證所有服務是否正常運行來獨立測試。成功後團隊成員可以存取應用程式 URL。

**Acceptance Scenarios**:

1. **Given** 已設定好 GCP 專案和 Terraform 環境，**When** 執行 `terraform apply`，**Then** 所有 Voice Lab 服務成功部署並可存取
2. **Given** 部署完成，**When** 存取應用程式 URL，**Then** 顯示 Voice Lab 登入頁面
3. **Given** 部署過程中發生錯誤，**When** 檢視 Terraform 輸出，**Then** 顯示清楚的錯誤訊息說明問題所在

---

### User Story 2 - 限定特定網域登入 (Priority: P1)

作為管理員，我想要限制只有特定網域（如 heyuai.com.tw）的 Gmail/Google Workspace 帳號才能登入系統，以確保只有內部人員可以存取測試環境。

**Why this priority**: 安全性是關鍵需求，與部署同等重要。沒有登入限制，測試環境可能被未授權人員存取。

**Independent Test**: 可透過嘗試使用不同網域的帳號登入來測試，確認只有允許的網域可以成功登入。

**Acceptance Scenarios**:

1. **Given** 系統已配置允許 heyuai.com.tw 網域，**When** 使用 @heyuai.com.tw 帳號登入，**Then** 登入成功並可存取系統
2. **Given** 系統已配置允許 heyuai.com.tw 網域，**When** 使用其他網域（如 @gmail.com）帳號嘗試登入，**Then** 登入被拒絕並顯示友善的錯誤訊息
3. **Given** 管理員需要更改允許的網域，**When** 修改 Terraform 配置中的網域設定，**Then** 重新部署後新的網域限制生效

---

### User Story 3 - 成本最佳化配置 (Priority: P2)

作為專案管理員，我想要以最低成本運行測試環境，以便在有限預算內持續進行測試。

**Why this priority**: 雖然成本控制重要，但前提是系統需要先能運行。這是部署成功後的最佳化項目。

**Independent Test**: 可透過 GCP 成本計算器或實際運行一週後檢視帳單來驗證成本是否符合預期。

**Acceptance Scenarios**:

1. **Given** 使用推薦的最低成本配置，**When** 系統持續運行 30 天，**Then** 每月成本在可接受範圍內（具體金額視服務規模而定）
2. **Given** 系統處於閒置狀態，**When** 沒有使用者活動，**Then** 不產生額外的計算費用（僅基礎費用）
3. **Given** 有測試活動進行中，**When** 資源使用量增加，**Then** 系統自動縮放但不超過設定的上限

---

### User Story 4 - 快速銷毀測試環境 (Priority: P2)

作為開發團隊成員，我想要能夠快速銷毀整個測試環境，以便在不使用時避免不必要的費用。

**Why this priority**: 為了進一步控制成本，需要能夠在不使用時完全移除資源。

**Independent Test**: 執行 `terraform destroy` 並確認所有資源已被移除，GCP Console 中不再顯示相關資源。

**Acceptance Scenarios**:

1. **Given** 測試環境正在運行，**When** 執行 `terraform destroy`，**Then** 所有相關 GCP 資源被完全移除
2. **Given** 環境已銷毀，**When** 檢視 GCP Console，**Then** 不存在任何與此部署相關的資源（除了必要的持久性資源如 Terraform state）
3. **Given** 環境已銷毀，**When** 再次執行 `terraform apply`，**Then** 環境可以完整重建

---

### User Story 5 - 環境配置管理 (Priority: P3)

作為開發團隊成員，我想要能夠透過配置檔管理不同的環境設定（如允許的登入網域、機器規格等），以便靈活調整測試環境。

**Why this priority**: 提供更好的使用體驗，但基本功能可以在沒有這個的情況下運作。

**Independent Test**: 修改配置檔中的參數並重新部署，驗證變更是否正確套用。

**Acceptance Scenarios**:

1. **Given** 需要變更允許的登入網域，**When** 修改 Terraform 變數檔中的網域設定，**Then** 重新部署後新設定生效
2. **Given** 需要調整機器規格，**When** 修改配置中的資源大小參數，**Then** 重新部署後使用新的資源規格

---

### Edge Cases

- 當 GCP 配額不足時會發生什麼？系統應顯示清楚的錯誤訊息說明需要申請更多配額
- 當 Terraform state 損壞時如何恢復？應有文件說明恢復步驟
- 當部署過程中斷時如何處理？Terraform 應能安全地處理部分部署狀態
- 當允許的網域沒有任何使用者存在時會發生什麼？系統應正常運作但無人可登入
- 當 Google OAuth 服務暫時不可用時？應顯示適當的錯誤頁面引導使用者稍後重試
- 當需要保留測試資料時？使用者應在執行 `terraform destroy` 前手動匯出所需資料，因為銷毀操作會完全刪除所有資料

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 提供 Terraform 配置檔以部署完整的 Voice Lab 到 GCP
- **FR-002**: 系統 MUST 整合 Google OAuth 2.0 作為唯一的身份驗證方式
- **FR-003**: 系統 MUST 支援配置多個允許登入的 Google Workspace/Gmail 網域（以清單形式配置）
- **FR-004**: 系統 MUST 拒絕非允許網域的登入嘗試並顯示友善的錯誤訊息
- **FR-005**: 系統 MUST 使用 GCP 的成本效益服務來運行（如 Cloud Run 而非 GKE）
- **FR-006**: 系統 MUST 支援透過 Terraform 變數檔配置環境參數
- **FR-007**: 系統 MUST 能透過 `terraform destroy` 完整移除所有已部署資源
- **FR-008**: 系統 MUST 在 Terraform 配置中包含必要的 GCP API 啟用
- **FR-009**: 系統 MUST 提供清楚的部署文件說明前置需求和步驟
- **FR-010**: 系統 MUST 使用 GCP 託管的資料庫服務以降低維運負擔
- **FR-011**: 系統 MUST 使用 GCP Secret Manager 儲存所有敏感資料（API keys、資料庫密碼等），應用程式執行時動態讀取
- **FR-012**: 系統 MUST 透過 Cloudflare Proxy 模式提供 HTTPS 連線，GCP 端配置 Cloudflare Origin Certificate

### Key Entities

- **Terraform State**: 紀錄已部署資源的狀態，用於追蹤和管理基礎設施變更
- **OAuth Client**: Google OAuth 2.0 客戶端配置，用於身份驗證
- **Allowed Domains**: 允許登入的網域清單配置
- **Environment Variables**: 應用程式運行所需的環境變數配置
- **Secret Manager Secrets**: 儲存於 GCP Secret Manager 的敏感資料，包含 API keys、資料庫密碼等

## Assumptions

- 使用者已有 GCP 帳號並有建立專案的權限
- 使用者已在本地安裝 Terraform CLI
- 使用者已安裝並配置 gcloud CLI
- 目標網域（如 heyuai.com.tw）是有效的 Google Workspace 或 Gmail 網域
- 網域 DNS 由 Cloudflare 管理，將使用 Cloudflare Proxy 模式進行流量代理
- Voice Lab 的所有現有功能模組都需要一起部署（001-005 功能）
- Terraform state 將儲存在 GCS 遠端 backend 並啟用狀態鎖定機制以支援團隊協作

## Clarifications

### Session 2026-01-20

- Q: Terraform State 儲存策略？ → A: GCS 遠端 backend 搭配狀態鎖定
- Q: 敏感資料與 API Keys 管理方式？ → A: GCP Secret Manager 儲存，應用程式執行時讀取
- Q: 環境銷毀時的資料保留策略？ → A: 完全刪除所有資料（乾淨銷毀）
- Q: HTTPS/SSL 憑證配置方式？ → A: Cloudflare Proxy 模式 + Cloudflare 提供 SSL，GCP 端用 Origin Certificate
- Q: 允許登入的網域數量？ → A: 支援多網域清單配置

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 從零開始，執行 `terraform apply` 在 15 分鐘內完成完整部署
- **SC-002**: 100% 的非允許網域登入嘗試被正確拒絕
- **SC-003**: 部署後系統在 2 分鐘內可供使用者存取
- **SC-004**: `terraform destroy` 在 10 分鐘內完成並移除所有資源
- **SC-005**: 閒置狀態下的每月運行成本低於 USD $100（基礎配置）
- **SC-006**: 部署文件足夠清楚，讓新團隊成員在 30 分鐘內完成首次部署
- **SC-007**: 系統支援同時至少 10 位內部使用者進行測試
