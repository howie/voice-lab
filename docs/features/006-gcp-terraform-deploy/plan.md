# Implementation Plan: GCP Terraform Deploy

**Branch**: `006-gcp-terraform-deploy` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/006-gcp-terraform-deploy/spec.md`

## Summary

透過 Terraform 將 Voice Lab 完整部署到 GCP，使用成本效益最高的服務組合（Cloud Run + Cloud SQL + Secret Manager），並整合 Google OAuth 2.0 限制特定網域登入。DNS 由 Cloudflare 管理，使用 Proxy 模式提供 SSL 終止。

## Technical Context

**Language/Version**: Terraform 1.6+ (HCL), Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**:
- Terraform Google Provider 5.x
- Cloudflare Provider (DNS 管理)
- GCP Cloud Run, Cloud SQL (PostgreSQL 16), Secret Manager, Cloud Storage
**Storage**:
- Cloud SQL PostgreSQL 16 (應用程式資料)
- Cloud Storage (Terraform state, 音訊檔案)
**Testing**: terraform validate, terraform plan (dry-run), pytest (backend), vitest (frontend)
**Target Platform**: GCP (asia-east1 region)
**Project Type**: Infrastructure as Code (IaC) + Web application deployment
**Performance Goals**:
- 部署時間 < 15 分鐘
- 系統可用後 < 2 分鐘內可存取
- 支援 10+ 並發使用者
**Constraints**:
- 每月閒置成本 < USD $100
- 完整銷毀時間 < 10 分鐘
**Scale/Scope**: 內部測試環境，10-20 位使用者

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ⚠️ N/A | 本功能為基礎設施部署，非應用程式邏輯；將透過 terraform validate/plan 驗證 |
| II. Unified API Abstraction | ✅ Pass | 不涉及新增 TTS/STT 服務 |
| III. Performance Benchmarking | ⚠️ N/A | 基礎設施功能，非效能敏感服務 |
| IV. Documentation First | ✅ Pass | 將建立完整的 quickstart.md 部署文件 |
| V. Clean Architecture | ✅ Pass | Terraform 模組化設計符合分層原則 |

**Gate Result**: ✅ PASS - 可進入 Phase 0

## Project Structure

### Documentation (this feature)

```text
docs/features/006-gcp-terraform-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (Terraform 資源模型)
├── quickstart.md        # Phase 1 output (部署指南)
├── contracts/           # Phase 1 output (Terraform 變數定義)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
terraform/
├── main.tf              # 主要資源定義
├── variables.tf         # 輸入變數
├── outputs.tf           # 輸出值
├── versions.tf          # Provider 版本鎖定
├── terraform.tfvars.example  # 範例配置
├── backend.tf           # GCS remote state 配置
└── modules/
    ├── networking/      # VPC, 防火牆規則
    ├── cloud-run/       # Cloud Run 服務
    ├── cloud-sql/       # Cloud SQL PostgreSQL
    ├── secrets/         # Secret Manager
    ├── storage/         # Cloud Storage buckets
    └── iam/             # IAM 角色與服務帳號

backend/
├── Dockerfile           # 後端容器映像 (需新增)
└── ...existing code...

frontend/
├── Dockerfile           # 前端容器映像 (需新增)
├── nginx.conf           # Nginx 配置 (需新增)
└── ...existing code...
```

**Structure Decision**: 採用 Terraform 模組化設計，將基礎設施分為獨立模組以便維護和重用。後端和前端各需新增 Dockerfile 以支援 Cloud Run 部署。

## Complexity Tracking

> No Constitution violations requiring justification.

| Aspect | Complexity Level | Justification |
|--------|------------------|---------------|
| Terraform modules | Medium | 模組化設計符合可維護性原則，每個模組職責單一 |
| Multi-service deployment | Medium | Cloud Run + Cloud SQL + Secret Manager 是 GCP 標準組合 |
| Cloudflare integration | Low | 僅需 DNS 設定，SSL 由 Cloudflare 處理 |
