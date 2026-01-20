# Tasks: GCP Terraform Deploy

**Input**: Design documents from `/docs/features/006-gcp-terraform-deploy/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 本功能為基礎設施部署，使用 `terraform validate` 和 `terraform plan` 進行驗證，而非傳統單元測試。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

本專案採用以下結構：
- **Terraform**: `terraform/` 目錄
- **Backend**: `backend/` 目錄
- **Frontend**: `frontend/` 目錄

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 建立 Terraform 專案基本結構和必要配置

- [x] T001 Create terraform directory structure at `terraform/`
- [x] T002 [P] Create Terraform version constraints in `terraform/versions.tf`
- [x] T003 [P] Create main variables definition in `terraform/variables.tf` (copy from contracts/variables.tf)
- [x] T004 [P] Create outputs definition in `terraform/outputs.tf` (copy from contracts/outputs.tf)
- [x] T005 [P] Create example configuration in `terraform/terraform.tfvars.example` (copy from contracts/)
- [x] T006 Create GCS backend configuration in `terraform/backend.tf`
- [x] T007 [P] Add terraform/ directory to .gitignore (*.tfvars, .terraform/, *.tfstate*)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有 User Story 都需要的核心 Terraform 模組

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### APIs Module

- [x] T008 Create APIs module structure at `terraform/modules/apis/`
- [x] T009 [P] Implement GCP API enablement in `terraform/modules/apis/main.tf`
- [x] T010 [P] Create APIs module variables in `terraform/modules/apis/variables.tf`
- [x] T011 [P] Create APIs module outputs in `terraform/modules/apis/outputs.tf`

### IAM Module

- [x] T012 Create IAM module structure at `terraform/modules/iam/`
- [x] T013 [P] Implement service account creation in `terraform/modules/iam/main.tf`
- [x] T014 [P] Create IAM module variables in `terraform/modules/iam/variables.tf`
- [x] T015 [P] Create IAM module outputs in `terraform/modules/iam/outputs.tf`

### Networking Module

- [x] T016 Create networking module structure at `terraform/modules/networking/`
- [x] T017 Implement VPC and Serverless Connector in `terraform/modules/networking/main.tf`
- [x] T018 [P] Create networking module variables in `terraform/modules/networking/variables.tf`
- [x] T019 [P] Create networking module outputs in `terraform/modules/networking/outputs.tf`

### Storage Module

- [x] T020 Create storage module structure at `terraform/modules/storage/`
- [x] T021 [P] Implement Cloud Storage buckets in `terraform/modules/storage/main.tf`
- [x] T022 [P] Create storage module variables in `terraform/modules/storage/variables.tf`
- [x] T023 [P] Create storage module outputs in `terraform/modules/storage/outputs.tf`

### Container Images (Prerequisites for Cloud Run)

- [x] T024 Create Backend Dockerfile at `backend/Dockerfile`
- [x] T025 [P] Create Frontend Dockerfile at `frontend/Dockerfile`
- [x] T026 [P] Create Nginx configuration for frontend at `frontend/nginx.conf`

### Main Terraform Configuration

- [x] T027 Create main entry point in `terraform/main.tf` with module calls (APIs, IAM, Networking, Storage)
- [ ] T028 Run `terraform init` and `terraform validate` to verify foundational modules

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 部署 Voice Lab 到 GCP (Priority: P1) 🎯 MVP

**Goal**: 透過 `terraform apply` 完整部署 Voice Lab 到 GCP

**Independent Test**: 執行 `terraform apply` 後，可存取部署的應用程式 URL

### Secrets Module

- [x] T029 [US1] Create secrets module structure at `terraform/modules/secrets/`
- [x] T030 [P] [US1] Implement Secret Manager secrets in `terraform/modules/secrets/main.tf`
- [x] T031 [P] [US1] Create secrets module variables in `terraform/modules/secrets/variables.tf`
- [x] T032 [P] [US1] Create secrets module outputs in `terraform/modules/secrets/outputs.tf`

### Cloud SQL Module

- [x] T033 [US1] Create cloud-sql module structure at `terraform/modules/cloud-sql/`
- [x] T034 [US1] Implement Cloud SQL PostgreSQL instance in `terraform/modules/cloud-sql/main.tf`
- [x] T035 [P] [US1] Create cloud-sql module variables in `terraform/modules/cloud-sql/variables.tf`
- [x] T036 [P] [US1] Create cloud-sql module outputs in `terraform/modules/cloud-sql/outputs.tf`

### Cloud Run Module

- [x] T037 [US1] Create cloud-run module structure at `terraform/modules/cloud-run/`
- [x] T038 [US1] Implement Cloud Run backend service in `terraform/modules/cloud-run/main.tf`
- [x] T039 [US1] Implement Cloud Run frontend service in `terraform/modules/cloud-run/main.tf`
- [x] T040 [P] [US1] Create cloud-run module variables in `terraform/modules/cloud-run/variables.tf`
- [x] T041 [P] [US1] Create cloud-run module outputs in `terraform/modules/cloud-run/outputs.tf`

### Artifact Registry Module

- [x] T042 [US1] Create artifact-registry module at `terraform/modules/artifact-registry/`
- [x] T043 [P] [US1] Implement Artifact Registry repository in `terraform/modules/artifact-registry/main.tf`
- [x] T044 [P] [US1] Create artifact-registry module variables and outputs

### Integration

- [x] T045 [US1] Update `terraform/main.tf` to include all US1 modules (secrets, cloud-sql, cloud-run, artifact-registry)
- [x] T046 [US1] Configure module dependencies and cross-references in `terraform/main.tf`
- [ ] T047 [US1] Run `terraform validate` to verify all configurations
- [ ] T048 [US1] Run `terraform plan` to preview deployment (dry-run verification)

**Checkpoint**: User Story 1 complete - `terraform apply` should successfully deploy all services

---

## Phase 4: User Story 2 - 限定特定網域登入 (Priority: P1)

**Goal**: 實作 Google OAuth 網域限制功能

**Independent Test**: 使用允許網域帳號可登入，其他網域被拒絕

### Backend OAuth Implementation

- [x] T049 [US2] Create OAuth configuration module at `backend/src/auth/oauth_config.py` (existing in middleware/auth.py)
- [x] T050 [US2] Implement Google OAuth token verification in `backend/src/auth/google_oauth.py` (existing in middleware/auth.py)
- [x] T051 [US2] Implement domain validation logic in `backend/src/infrastructure/auth/domain_validator.py`
- [x] T052 [US2] Create OAuth callback endpoint in `backend/src/presentation/api/routes/auth.py` (updated with domain validation)
- [x] T053 [US2] Add ALLOWED_DOMAINS environment variable handling in `backend/src/config.py`

### Frontend OAuth Integration

- [ ] T054 [P] [US2] Install @react-oauth/google package in `frontend/package.json`
- [ ] T055 [US2] Create Google login button component in `frontend/src/components/auth/GoogleLoginButton.tsx`
- [ ] T056 [US2] Implement OAuth callback handler in `frontend/src/pages/auth/Callback.tsx`
- [ ] T057 [US2] Add domain rejection error display in `frontend/src/components/auth/DomainError.tsx`
- [ ] T058 [US2] Update environment configuration for OAuth in `frontend/src/config/env.ts`

### Terraform Integration

- [x] T059 [US2] Update Cloud Run backend environment variables in `terraform/modules/cloud-run/main.tf` for OAuth secrets
- [x] T060 [US2] Add OAuth-related secrets to `terraform/modules/secrets/main.tf`
- [x] T061 [US2] Update `terraform/variables.tf` with allowed_domains variable validation

**Checkpoint**: User Story 2 complete - OAuth login with domain restriction is functional

---

## Phase 5: User Story 3 - 成本最佳化配置 (Priority: P2)

**Goal**: 確保部署配置符合成本最佳化目標

**Independent Test**: 透過 GCP Console 或 `gcloud` 指令驗證資源使用最小配置

### Cost Optimization Tasks

- [x] T062 [US3] Configure Cloud Run min_instances=0 in `terraform/modules/cloud-run/main.tf`
- [x] T063 [US3] Configure Cloud SQL db-f1-micro tier in `terraform/modules/cloud-sql/main.tf`
- [x] T064 [P] [US3] Add cost-related variable validations in `terraform/variables.tf`
- [x] T065 [P] [US3] Document cost implications in `terraform/terraform.tfvars.example` comments
- [x] T066 [US3] Configure VPC connector minimum throughput (200 Mbps) in `terraform/modules/networking/main.tf`

### Budget Monitoring (Optional)

- [ ] T067 [P] [US3] Create budget module at `terraform/modules/budget/` (optional)
- [ ] T068 [US3] Implement GCP budget alert in `terraform/modules/budget/main.tf` (optional)

**Checkpoint**: User Story 3 complete - deployment uses minimum cost configuration

---

## Phase 6: User Story 4 - 快速銷毀測試環境 (Priority: P2)

**Goal**: 確保 `terraform destroy` 可以完整移除所有資源

**Independent Test**: 執行 `terraform destroy` 後，GCP Console 中無相關資源

### Destroy Safety Tasks

- [x] T069 [US4] Configure deletion_protection=false for test environment in `terraform/modules/cloud-sql/main.tf`
- [x] T070 [US4] Ensure all resources have proper lifecycle configuration in all modules
- [x] T071 [P] [US4] Add force_destroy=true to Cloud Storage buckets in `terraform/modules/storage/main.tf`
- [ ] T072 [US4] Verify no external dependencies prevent clean destroy

### Documentation

- [x] T073 [P] [US4] Document destroy process in `docs/features/006-gcp-terraform-deploy/quickstart.md`
- [x] T074 [US4] Add destroy warnings and data backup instructions

**Checkpoint**: User Story 4 complete - `terraform destroy` cleanly removes all resources

---

## Phase 7: User Story 5 - 環境配置管理 (Priority: P3)

**Goal**: 透過變數檔靈活配置環境參數

**Independent Test**: 修改 tfvars 並重新部署，驗證變更生效

### Configuration Flexibility Tasks

- [x] T075 [US5] Ensure all configurable values are exposed as variables in `terraform/variables.tf`
- [x] T076 [P] [US5] Add variable descriptions and defaults in `terraform/variables.tf`
- [ ] T077 [US5] Create production-ready terraform.tfvars.prod.example in `terraform/`
- [x] T078 [P] [US5] Add validation rules for all input variables in `terraform/variables.tf`
- [x] T079 [US5] Update quickstart.md with configuration options documentation

**Checkpoint**: User Story 5 complete - all key parameters are configurable via tfvars

---

## Phase 8: Cloudflare DNS Integration

**Purpose**: 設定自訂網域 DNS

- [x] T080 Create Cloudflare DNS provider configuration in `terraform/main.tf` (integrated)
- [x] T081 [P] Implement Cloudflare DNS records in `terraform/main.tf`
- [x] T082 Document manual Cloudflare setup in `docs/features/006-gcp-terraform-deploy/quickstart.md`
- [x] T083 Add Cloudflare variables to `terraform/variables.tf`

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: 最終驗證和文件完善

- [ ] T084 [P] Update main README.md with GCP deployment instructions
- [ ] T085 [P] Update CLAUDE.md with Terraform-specific guidance
- [ ] T086 Final `terraform validate` and `terraform plan` verification
- [ ] T087 Test complete deployment workflow (init → plan → apply)
- [ ] T088 Test complete destroy workflow (destroy → verify cleanup)
- [ ] T089 [P] Add troubleshooting section to quickstart.md
- [ ] T090 Code review and cleanup of all Terraform modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core deployment
- **User Story 2 (Phase 4)**: Depends on US1 (needs deployed backend for OAuth)
- **User Story 3 (Phase 5)**: Can run in parallel with US2 after US1
- **User Story 4 (Phase 6)**: Depends on US1 (needs deployed resources to test destroy)
- **User Story 5 (Phase 7)**: Can run in parallel with US3/US4 after US1
- **Cloudflare (Phase 8)**: Depends on US1 (needs Cloud Run URLs)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

```
                    ┌─────────────────┐
                    │  Setup (Phase 1) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Foundational    │
                    │   (Phase 2)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ User Story 1    │ 🎯 MVP
                    │ (Deploy to GCP) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│ User Story 2  │   │ User Story 3  │   │ User Story 4  │
│ (OAuth Auth)  │   │ (Cost Opt)    │   │ (Destroy)     │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            │
                   ┌────────▼────────┐
                   │ User Story 5    │
                   │ (Config Mgmt)   │
                   └─────────────────┘
```

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004, T005, T007 can run in parallel

**Phase 2 (Foundational)**:
- T009, T010, T011 can run in parallel (APIs module)
- T013, T014, T015 can run in parallel (IAM module)
- T018, T019 can run in parallel (Networking module)
- T021, T022, T023 can run in parallel (Storage module)
- T024, T025, T026 can run in parallel (Dockerfiles)

**Phase 3 (US1)**:
- T030, T031, T032 can run in parallel (Secrets module)
- T035, T036 can run in parallel (Cloud SQL module)
- T040, T041 can run in parallel (Cloud Run module)

**Phase 4 (US2)**:
- T054 can run in parallel with backend OAuth tasks

---

## Parallel Example: Foundational Phase

```bash
# Launch all module structure creation together:
Task: "Create APIs module structure at terraform/modules/apis/"
Task: "Create IAM module structure at terraform/modules/iam/"
Task: "Create networking module structure at terraform/modules/networking/"
Task: "Create storage module structure at terraform/modules/storage/"

# Launch all Dockerfile creation together:
Task: "Create Backend Dockerfile at backend/Dockerfile"
Task: "Create Frontend Dockerfile at frontend/Dockerfile"
Task: "Create Nginx configuration for frontend at frontend/nginx.conf"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `terraform apply` and verify deployment
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test `terraform apply` → **MVP Ready!**
3. Add User Story 2 → Test OAuth login → Enhanced security
4. Add User Story 3 + 4 → Verify cost/destroy → Production ready
5. Add User Story 5 → Better DX → Full feature complete

### Estimated Time

| Phase | Estimated Tasks | Notes |
|-------|-----------------|-------|
| Phase 1 (Setup) | 7 tasks | ~30 minutes |
| Phase 2 (Foundational) | 21 tasks | ~2 hours |
| Phase 3 (US1 - Deploy) | 20 tasks | ~2-3 hours |
| Phase 4 (US2 - OAuth) | 13 tasks | ~2 hours |
| Phase 5 (US3 - Cost) | 7 tasks | ~30 minutes |
| Phase 6 (US4 - Destroy) | 6 tasks | ~30 minutes |
| Phase 7 (US5 - Config) | 5 tasks | ~30 minutes |
| Phase 8 (Cloudflare) | 4 tasks | ~30 minutes |
| Phase 9 (Polish) | 7 tasks | ~1 hour |
| **Total** | **90 tasks** | **~10-12 hours** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Run `terraform validate` frequently during development
- Run `terraform plan` before any `terraform apply`
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **MVP**: Complete US1 for minimum viable deployment
