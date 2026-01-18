# Tasks: Provider API Key Management Interface

**Input**: Design documents from `/docs/features/002-provider-mgmt-interface/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as per Constitution principle I (TDD requirement)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migrations and core entity setup

- [X] T001 Create Alembic migration for Provider table in backend/alembic/versions/xxx_add_provider_table.py
- [X] T002 Create Alembic migration for UserProviderCredential table in backend/alembic/versions/xxx_add_credential_table.py
- [X] T003 Create Alembic migration for AuditLog table in backend/alembic/versions/xxx_add_audit_log_table.py
- [X] T004 Seed Provider reference data (elevenlabs, azure, gemini) in migration
- [X] T005 Run migrations and verify database schema

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create Provider domain entity in backend/src/domain/entities/provider.py
- [X] T007 [P] Create UserProviderCredential domain entity in backend/src/domain/entities/provider_credential.py
- [X] T008 [P] Create AuditLog domain entity in backend/src/domain/entities/audit_log.py
- [X] T009 Add Provider, UserProviderCredential, AuditLog SQLAlchemy models to backend/src/infrastructure/persistence/models.py
- [X] T010 [P] Create ProviderCredentialRepository interface in backend/src/domain/repositories/provider_credential_repository.py
- [X] T011 [P] Create AuditLogRepository interface in backend/src/domain/repositories/audit_log_repository.py
- [X] T012 [P] Implement SQLAlchemy ProviderCredentialRepository in backend/src/infrastructure/persistence/credential_repository.py
- [X] T013 [P] Implement SQLAlchemy AuditLogRepository in backend/src/infrastructure/persistence/audit_log_repository.py
- [X] T014 Create AuditService for logging operations in backend/src/application/services/audit_service.py
- [X] T015 [P] Create BaseProviderValidator abstract class in backend/src/infrastructure/providers/validators/base.py
- [X] T016 [P] Implement ElevenLabsValidator in backend/src/infrastructure/providers/validators/elevenlabs.py
- [X] T017 [P] Implement AzureValidator in backend/src/infrastructure/providers/validators/azure.py
- [X] T018 [P] Implement GeminiValidator in backend/src/infrastructure/providers/validators/gemini.py
- [X] T019 Create ProviderValidatorRegistry in backend/src/infrastructure/providers/validators/__init__.py
- [X] T020 Create API key masking utility in backend/src/domain/utils/masking.py
- [X] T021 [P] Create credential schemas (request/response) in backend/src/presentation/schemas/credential.py
- [X] T022 [P] Create provider schemas in backend/src/presentation/schemas/provider.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Add Provider API Key (Priority: P1) 🎯 MVP

**Goal**: Users can add their own API key for a TTS/STT provider with validation

**Independent Test**: Navigate to provider settings, enter an API key, verify validation and secure storage

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US1] Contract test for POST /credentials in backend/tests/contract/test_add_credential.py
- [X] T024 [P] [US1] Unit test for provider validators in backend/tests/unit/test_provider_validators.py
- [X] T025 [P] [US1] Integration test for credential creation flow in backend/tests/integration/test_credential_crud.py

### Implementation for User Story 1

- [X] T026 [US1] Implement AddProviderCredential use case in backend/src/application/use_cases/add_provider_credential.py
- [X] T027 [US1] Implement ValidateProviderKey use case in backend/src/application/use_cases/validate_provider_key.py
- [X] T028 [US1] Implement POST /credentials endpoint in backend/src/presentation/api/routes/credentials.py
- [X] T029 [US1] Implement GET /providers endpoint in backend/src/presentation/api/routes/credentials.py
- [X] T030 [US1] Add audit logging for credential.created event
- [X] T031 [P] [US1] Create credentialService.ts API client in frontend/src/services/credentialService.ts
- [X] T032 [P] [US1] Create ApiKeyInput component in frontend/src/components/settings/ApiKeyInput.tsx
- [X] T033 [P] [US1] Create ProviderCard component in frontend/src/components/settings/ProviderCard.tsx
- [X] T034 [US1] Create ProviderSettings page with add credential form in frontend/src/routes/settings/ProviderSettings.tsx
- [X] T035 [US1] Add route for /settings/providers in frontend router

**Checkpoint**: User Story 1 complete - users can add and validate API keys

---

## Phase 4: User Story 2 - Select Provider and Model (Priority: P1)

**Goal**: Users can select which provider and model to use for TTS/STT operations

**Independent Test**: Select a provider/model, verify selection persisted and used in operations

### Tests for User Story 2 ⚠️

- [X] T036 [P] [US2] Contract test for GET /credentials/{id}/models in backend/tests/contract/test_list_models.py
- [X] T037 [P] [US2] Contract test for PUT /credentials/{id} (model selection) in backend/tests/contract/test_update_credential.py

### Implementation for User Story 2

- [X] T038 [US2] Implement ListProviderModels use case in backend/src/application/use_cases/list_provider_models.py
- [X] T039 [US2] Implement UpdateProviderCredential use case for model selection in backend/src/application/use_cases/update_provider_credential.py
- [X] T040 [US2] Implement GET /credentials/{id}/models endpoint in backend/src/presentation/api/routes/credentials.py
- [X] T041 [US2] Implement PUT /credentials/{id} endpoint in backend/src/presentation/api/routes/credentials.py
- [X] T042 [US2] Add audit logging for model.selected event
- [X] T043 [US2] Implement TTSProviderFactory with credential injection in backend/src/infrastructure/providers/tts/factory.py
- [X] T044 [US2] Modify BaseTTSProvider to support credential injection in backend/src/infrastructure/providers/tts/base.py
- [X] T045 [P] [US2] Create ModelSelector component in frontend/src/components/settings/ModelSelector.tsx
- [X] T046 [US2] Update ProviderSettings to show available models after key validation
- [X] T047 [US2] Add model selection persistence in frontend state

**Checkpoint**: User Story 2 complete - users can select providers and models

---

## Phase 5: User Story 3 - Manage Multiple Provider Credentials (Priority: P2)

**Goal**: Users can manage credentials for multiple providers with status visibility

**Independent Test**: Add credentials for multiple providers, verify all are accessible with status

### Tests for User Story 3 ⚠️

- [X] T048 [P] [US3] Contract test for GET /credentials (list all) in backend/tests/contract/test_list_credentials.py
- [X] T049 [P] [US3] Integration test for multi-provider management in backend/tests/integration/test_multi_provider.py

### Implementation for User Story 3

- [X] T050 [US3] Implement ListProviderCredentials use case in backend/src/application/use_cases/list_provider_credentials.py
- [X] T051 [US3] Implement GET /credentials endpoint with user filtering in backend/src/presentation/api/routes/credentials.py
- [X] T052 [US3] Add audit logging for credential.viewed event
- [X] T053 [US3] Update ProviderSettings to display all configured providers
- [X] T054 [US3] Add provider status indicators (valid/invalid) to ProviderCard component
- [X] T055 [US3] Implement provider list refresh functionality in frontend

**Checkpoint**: User Story 3 complete - users can manage multiple providers

---

## Phase 6: User Story 4 - Update or Remove API Key (Priority: P2)

**Goal**: Users can update or remove their API keys for security maintenance

**Independent Test**: Update an existing key, verify new key validated; delete a key, verify removed

### Tests for User Story 4 ⚠️

- [X] T056 [P] [US4] Contract test for DELETE /credentials/{id} in backend/tests/contract/test_delete_credential.py
- [X] T057 [P] [US4] Unit test for key update with revalidation in backend/tests/unit/test_credential_update.py

### Implementation for User Story 4

- [X] T058 [US4] Implement DeleteProviderCredential use case in backend/src/application/use_cases/delete_provider_credential.py
- [X] T059 [US4] Extend UpdateProviderCredential for API key rotation in backend/src/application/use_cases/update_provider_credential.py
- [X] T060 [US4] Implement DELETE /credentials/{id} endpoint in backend/src/presentation/api/routes/credentials.py
- [X] T061 [US4] Add audit logging for credential.updated and credential.deleted events
- [X] T062 [US4] Add update/delete actions to ProviderCard component
- [X] T063 [US4] Add confirmation dialog for credential deletion in frontend
- [X] T064 [US4] Implement key rotation UI with revalidation feedback

**Checkpoint**: User Story 4 complete - users can update and delete credentials

---

## Phase 7: User Story 5 - View Provider Status and Quota (Priority: P3)

**Goal**: Users can view connection status and quota information for configured providers

**Independent Test**: View provider status page, verify status and quota display

### Tests for User Story 5 ⚠️

- [X] T065 [P] [US5] Contract test for POST /credentials/{id}/validate in backend/tests/contract/test_validate_credential.py
- [X] T066 [P] [US5] Integration test for status refresh in backend/tests/integration/test_provider_status.py

### Implementation for User Story 5

- [X] T067 [US5] Implement RevalidateCredential use case in backend/src/application/use_cases/revalidate_credential.py
- [X] T068 [US5] Implement POST /credentials/{id}/validate endpoint in backend/src/presentation/api/routes/credentials.py
- [X] T069 [US5] Add quota fetching to provider validators (where supported) in backend/src/infrastructure/providers/validators/
- [X] T070 [US5] Add audit logging for credential.validated event
- [X] T071 [US5] Add status refresh button to ProviderCard
- [X] T072 [US5] Display quota information in provider details view
- [X] T073 [US5] Add error state handling for invalid credentials in UI

**Checkpoint**: User Story 5 complete - users can view status and quota

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T074 [P] Add audit logging for credential.used events in TTS/STT operations
- [X] T075 [P] Unit tests for audit logging service in backend/tests/unit/test_audit_logging.py
- [X] T076 [P] Update API documentation with new endpoints
- [X] T077 Implement fallback to system-level API keys when user credentials unavailable
- [X] T078 Add error handling for network timeouts during validation
- [X] T079 Add rate limit handling for provider API validation
- [X] T080 [P] Frontend tests for ProviderSettings in frontend/tests/ProviderSettings.test.tsx
- [X] T081 Run quickstart.md validation
- [X] T082 Code cleanup and refactoring
- [X] T083 Performance testing for credential operations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 - can proceed in parallel after Foundational
  - US3 and US4 are both P2 - can proceed in parallel after Foundational
  - US5 is P3 - can start after Foundational
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Builds on US1 credential creation but independently testable
- **User Story 3 (P2)**: Can start after Foundational - Extends US1/US2 list view but independently testable
- **User Story 4 (P2)**: Can start after Foundational - Extends US1 CRUD but independently testable
- **User Story 5 (P3)**: Can start after Foundational - Extends validation from US1 but independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Backend before frontend within each story
- Models before services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel
- All tests for a user story marked [P] can run in parallel
- Frontend components marked [P] can run in parallel

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all domain entities in parallel:
Task: "Create Provider domain entity in backend/src/domain/entities/provider.py"
Task: "Create UserProviderCredential domain entity in backend/src/domain/entities/provider_credential.py"
Task: "Create AuditLog domain entity in backend/src/domain/entities/audit_log.py"

# Launch all provider validators in parallel:
Task: "Implement ElevenLabsValidator in backend/src/infrastructure/providers/validators/elevenlabs.py"
Task: "Implement AzureValidator in backend/src/infrastructure/providers/validators/azure.py"
Task: "Implement GeminiValidator in backend/src/infrastructure/providers/validators/gemini.py"
```

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for POST /credentials in backend/tests/contract/test_add_credential.py"
Task: "Unit test for provider validators in backend/tests/unit/test_provider_validators.py"
Task: "Integration test for credential creation flow in backend/tests/integration/test_credential_crud.py"

# Launch frontend components in parallel:
Task: "Create credentialService.ts API client in frontend/src/services/credentialService.ts"
Task: "Create ApiKeyInput component in frontend/src/components/ApiKeyInput.tsx"
Task: "Create ProviderCard component in frontend/src/components/ProviderCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (5 tasks)
2. Complete Phase 2: Foundational (17 tasks) - CRITICAL blocks all stories
3. Complete Phase 3: User Story 1 (13 tasks)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - Users can add and validate API keys!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (model selection)
4. Add User Story 3 → Test independently → Deploy/Demo (multi-provider)
5. Add User Story 4 → Test independently → Deploy/Demo (key rotation)
6. Add User Story 5 → Test independently → Deploy/Demo (status/quota)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (add key)
   - Developer B: User Story 2 (model selection)
3. Then:
   - Developer A: User Story 3 (multi-provider)
   - Developer B: User Story 4 (update/delete)
4. Finally: User Story 5 (status/quota)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per Constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All API keys encrypted at database level (PostgreSQL TDE)
- Audit logging required for all credential operations (FR-012, FR-013)
