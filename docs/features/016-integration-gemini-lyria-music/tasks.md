# Tasks: Gemini Lyria 音樂生成整合

**Input**: Design documents from `/docs/features/016-integration-gemini-lyria-music/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/lyria-api.yaml, quickstart.md

**Tests**: Included — Constitution mandates TDD for all provider integrations.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, configuration, and adapter skeleton

- [ ] T001 Verify `google-auth>=2.27.0` already in `backend/pyproject.toml` (confirmed present); no `google-auth-httplib2` needed — we use httpx with manual `credentials.token` instead
- [ ] T002 Verify `pydub>=0.25.0` already in `backend/pyproject.toml` (confirmed present) and `ffmpeg` already in `backend/Dockerfile` (confirmed line 40)
- [ ] T003 [P] Add Lyria configuration settings (`lyria_gcp_project_id`, `lyria_gcp_location`, `lyria_model`, `lyria_timeout`) to `backend/src/config.py`
- [ ] T004 [P] Create adapter directory structure: `backend/src/infrastructure/adapters/lyria/__init__.py`
- [ ] T005 Run `cd backend && uv sync` to verify dependency installation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Enum values and factory registration that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Add `LYRIA = "lyria"` to `MusicProvider` enum in `backend/src/domain/entities/music.py`
- [ ] T007 Add `LYRIA = "lyria"` to `MusicProviderEnum` Pydantic schema in `backend/src/presentation/api/schemas/music_schemas.py`
- [ ] T008 [P] Add `"lyria"` to `MusicProvider` union type in `frontend/src/types/music.ts`
- [ ] T009 Create `LyriaVertexAIClient` skeleton (init + health_check only) in `backend/src/infrastructure/adapters/lyria/client.py` with Google Cloud ADC authentication via `google.auth.default()` and httpx AsyncClient
- [ ] T010 Create `LyriaMusicProvider` skeleton implementing `IMusicProvider` (name/display_name properties + NotSupportedError stubs for generate_song/generate_lyrics) in `backend/src/infrastructure/providers/music/lyria_music.py`
- [ ] T011 Register `"lyria"` provider in `MusicProviderFactory.create()` with lazy import in `backend/src/infrastructure/providers/music/factory.py`
- [ ] T012 Add `"lyria"` to `SUPPORTED_PROVIDERS` list in `backend/src/infrastructure/providers/music/factory.py`
- [ ] T012a [P] Add optional `capabilities() -> list[str]` property to `IMusicProvider` interface in `backend/src/application/interfaces/music_provider.py` with default return `["song", "instrumental", "lyrics"]` so existing providers (Mureka, Suno) are unaffected
- [ ] T012b [P] Create Alembic migration to add `provider_metadata` JSONB column (nullable, default `{}`) to `music_generation_jobs` table in `backend/alembic/versions/` — this column stores provider-specific params (negative_prompt, seed, sample_count, batch_id) following the pattern of `JobModel.input_params`
- [ ] T012c [P] Add `provider_metadata: dict[str, Any] | None = None` field to `MusicGenerationJob` dataclass in `backend/src/domain/entities/music.py` and to `MusicGenerationJobModel` in `backend/src/infrastructure/persistence/models.py`

**Checkpoint**: Factory can instantiate LyriaMusicProvider; health_check passes with valid GCP credentials; `provider_metadata` column available for all user stories

---

## Phase 3: User Story 1 — 使用 Lyria 生成器樂 BGM (Priority: P1) 🎯 MVP

**Goal**: End-to-end instrumental BGM generation via Lyria 2 Vertex AI API

**Independent Test**: POST `/api/v1/music/instrumental` with `provider: "lyria"` and English prompt → job completes → downloadable MP3

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for Lyria Vertex AI predict endpoint (mock HTTP response with base64 WAV) in `backend/tests/contract/music/test_lyria_contract.py`
- [ ] T014 [P] [US1] Unit test for `LyriaMusicProvider.generate_instrumental()` returning `MusicSubmitResult` in `backend/tests/unit/music/test_lyria_provider.py`
- [ ] T015 [P] [US1] Unit test for WAV→MP3 conversion utility in `backend/tests/unit/music/test_lyria_provider.py`
- [ ] T016 [P] [US1] Unit test for `LyriaVertexAIClient.generate_instrumental()` building correct Vertex AI request payload in `backend/tests/contract/music/test_lyria_contract.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement `LyriaVertexAIClient.generate_instrumental(prompt, negative_prompt, seed, sample_count)` in `backend/src/infrastructure/adapters/lyria/client.py` — build Vertex AI predict request, send via httpx, parse base64 WAV response into `LyriaGenerationResult` dataclass
- [ ] T018 [US1] Implement WAV→MP3 conversion helper using pydub in `backend/src/infrastructure/adapters/lyria/client.py` (or shared audio util) — decode base64 → WAV bytes → pydub AudioSegment → export MP3
- [ ] T019 [US1] Implement `LyriaMusicProvider.generate_instrumental()` in `backend/src/infrastructure/providers/music/lyria_music.py` — call client, convert WAV→MP3, save to storage, return `MusicSubmitResult` with COMPLETED status
- [ ] T020 [US1] Create `MusicJobWorker` in `backend/src/infrastructure/workers/music_job_worker.py` following `JobWorker` pattern — polling loop calls `repository.acquire_pending_job()`, dispatches to provider via factory, handles submit → poll → download → store flow. **For Lyria**: skip polling (synchronous API, result returned immediately). **For Mureka**: submit → poll `query_task()` every 5s → download MP3. Register worker in `backend/src/main.py` lifespan alongside existing `JobWorker`
- [ ] T021 [US1] Implement `LyriaMusicProvider.query_task()` returning always-COMPLETED result (Lyria 2 is synchronous — result is available immediately after generate) in `backend/src/infrastructure/providers/music/lyria_music.py`
- [ ] T022 [US1] Add Vertex AI error handling: 401 (auth failure), 400 (safety filter), 429 (rate limit), 5xx (server error) with mapped error messages in `backend/src/infrastructure/adapters/lyria/client.py`
- [ ] T022a [US1] Add retry logic (max 3 attempts, exponential backoff 2s/4s/8s) for transient errors (429 rate limit, 5xx server errors) in `LyriaVertexAIClient` via httpx `AsyncHTTPTransport(retries=...)` or manual retry loop in `backend/src/infrastructure/adapters/lyria/client.py` — per FR-016
- [ ] T022b [US1] Add WAV→MP3 fallback: if pydub/ffmpeg conversion fails, store raw WAV and set `result_url` to WAV file as degraded fallback in `backend/src/infrastructure/providers/music/lyria_music.py` — per EC-004
- [ ] T023 [US1] Add English-only prompt validation (reject non-ASCII or detect CJK characters) for Lyria provider in `backend/src/presentation/api/schemas/music_schemas.py` or route-level validation in `backend/src/presentation/api/routes/music.py`
- [ ] T024 [US1] Verify end-to-end: `make check` passes, then manual test with real GCP credentials

**Checkpoint**: Lyria instrumental generation works end-to-end. POST with `provider: "lyria"` → MP3 result downloadable.

---

## Phase 4: User Story 2 — 使用 Negative Prompt 精確控制 (Priority: P1)

**Goal**: Users can specify elements to exclude from generated music via negative_prompt

**Independent Test**: POST `/api/v1/music/instrumental` with `provider: "lyria"` and `negative_prompt` → field passed to Vertex AI → generation succeeds

### Tests for User Story 2

- [ ] T025 [P] [US2] Unit test verifying negative_prompt is included in Vertex AI request payload in `backend/tests/contract/music/test_lyria_contract.py`
- [ ] T026 [P] [US2] Unit test verifying negative_prompt is stored and returned in job response in `backend/tests/unit/music/test_lyria_provider.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Add `negative_prompt` optional field to `InstrumentalRequest` Pydantic schema in `backend/src/presentation/api/schemas/music_schemas.py` (maxLength: 200, nullable, only used when provider=lyria)
- [ ] T028 [US2] Pass `negative_prompt` through service layer to `LyriaMusicProvider.generate_instrumental()` in `backend/src/domain/services/music/service.py` (add parameter to `submit_instrumental` method)
- [ ] T029 [US2] Ensure `negative_prompt` is included in `instances` payload sent to Vertex AI in `backend/src/infrastructure/adapters/lyria/client.py` (already scaffolded in T017, verify)
- [ ] T030 [US2] Store `negative_prompt` in `provider_metadata` JSONB column (created in T012b) as `{"negative_prompt": "..."}` — no additional migration needed. Update `MusicGenerationService.submit_instrumental()` to persist `provider_metadata` in `backend/src/domain/services/music/service.py`
- [ ] T031 [US2] Return `negative_prompt` from `provider_metadata` in `MusicJobResponse` schema in `backend/src/presentation/api/schemas/music_schemas.py`

**Checkpoint**: Negative prompt passed to Vertex AI and visible in job response. Mureka requests ignore this field gracefully.

---

## Phase 5: User Story 3 — Lyria 與 Mureka Provider 切換 (Priority: P1)

**Goal**: Users can freely switch between Lyria and Mureka in the UI, with capability-aware form

**Independent Test**: UI shows provider dropdown; selecting Lyria hides song/lyrics options; selecting Mureka shows full options; history shows provider per job

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for `/api/v1/music/providers` endpoint returning Lyria capabilities in `backend/tests/unit/music/test_lyria_provider.py`

### Implementation for User Story 3

- [ ] T033 [US3] Add `GET /api/v1/music/providers` endpoint returning list of available providers with capabilities per `contracts/lyria-api.yaml` ProviderInfo schema in `backend/src/presentation/api/routes/music.py`
- [ ] T034 [US3] Implement `LyriaMusicProvider.capabilities()` property returning `["instrumental"]` in `backend/src/infrastructure/providers/music/lyria_music.py`
- [ ] T035 [P] [US3] Add provider dropdown component to music generation form showing "Mureka AI" and "Google Lyria" in `frontend/src/components/music/MusicForm.tsx`
- [ ] T036 [US3] Conditionally show/hide form sections based on selected provider capabilities (hide song/lyrics for Lyria) in `frontend/src/components/music/MusicForm.tsx`
- [ ] T037 [P] [US3] Add Lyria provider option to musicService API client in `frontend/src/services/musicApi.ts`
- [ ] T038 [US3] Display provider name in job history list and job detail views in `frontend/src/components/music/MusicJobStatus.tsx`

**Checkpoint**: UI provider switching works. Lyria shows only instrumental form. History shows provider per job.

---

## Phase 6: User Story 4 — 種子值可重現生成 (Priority: P2)

**Goal**: Users can specify seed for reproducible Lyria generation results

**Independent Test**: Same prompt + seed → identical output; seed + sample_count → validation error

### Tests for User Story 4

- [ ] T039 [P] [US4] Unit test verifying seed is included in Vertex AI request `instances` in `backend/tests/contract/music/test_lyria_contract.py`
- [ ] T040 [P] [US4] Unit test verifying seed + sample_count mutual exclusion validation in `backend/tests/unit/music/test_lyria_provider.py`

### Implementation for User Story 4

- [ ] T041 [P] [US4] Add `seed` optional integer field (0–2,147,483,647) to `InstrumentalRequest` schema in `backend/src/presentation/api/schemas/music_schemas.py`
- [ ] T042 [US4] Add `@model_validator` to reject request if both `seed` and `sample_count` are provided in `backend/src/presentation/api/schemas/music_schemas.py`
- [ ] T043 [US4] Pass `seed` through service layer to `LyriaVertexAIClient.generate_instrumental()` in `backend/src/domain/services/music/service.py`
- [ ] T044 [P] [US4] Add seed input field (optional) to Lyria instrumental form in `frontend/src/components/music/MusicForm.tsx`
- [ ] T045 [US4] Frontend validation: disable sample_count when seed is filled and vice versa in `frontend/src/components/music/MusicForm.tsx`

**Checkpoint**: Seed parameter works. Same prompt+seed produces same output. Conflict validation prevents seed+sample_count.

---

## Phase 7: User Story 5 — 批量生成多首變體 (Priority: P2)

**Goal**: Users can generate multiple variants in one request via sample_count

**Independent Test**: POST with sample_count=3 → 3 separate jobs created → 3 different MP3 results

### Tests for User Story 5

- [ ] T046 [P] [US5] Unit test verifying sample_count is included in Vertex AI `parameters` payload in `backend/tests/contract/music/test_lyria_contract.py`
- [ ] T047 [P] [US5] Unit test verifying multiple results from single API call are split into separate jobs in `backend/tests/unit/music/test_lyria_provider.py`

### Implementation for User Story 5

- [ ] T048 [P] [US5] Add `sample_count` optional integer field (1–4) to `InstrumentalRequest` schema in `backend/src/presentation/api/schemas/music_schemas.py`
- [ ] T049 [US5] Handle multi-result response from Vertex AI: when `sample_count > 1`, API returns multiple `predictions` — create one MusicGenerationJob per result in `backend/src/infrastructure/providers/music/lyria_music.py`
- [ ] T050 [US5] Link batch jobs together via `provider_metadata.batch_id` (UUID, stored in JSONB column created in T012b) so UI can group variants — update `MusicGenerationService` in `backend/src/domain/services/music/service.py` and add `GET /api/v1/music/jobs?batch_id={id}` filter in `backend/src/presentation/api/routes/music.py`
- [ ] T051 [P] [US5] Add sample_count selector (1–4) to Lyria instrumental form in `frontend/src/components/music/MusicForm.tsx`
- [ ] T052 [US5] Display batch variants as grouped results in job detail view in `frontend/src/components/music/MusicJobStatus.tsx`

**Checkpoint**: Batch generation works. sample_count=3 produces 3 downloadable variants grouped in UI.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T053 [P] Add `LyriaMusicProvider.health_check()` implementation (test Vertex AI connectivity) in `backend/src/infrastructure/providers/music/lyria_music.py`
- [ ] T053a [P] Log SynthID watermark presence from Vertex AI response metadata in `backend/src/infrastructure/adapters/lyria/client.py` — per FR-012 (verify `predictions[].synthId` field exists in response)
- [ ] T054 [P] Add Lyria-specific logging (request/response timing, model version, audio duration) in `backend/src/infrastructure/adapters/lyria/client.py`
- [ ] T055 [P] Update Terraform config to add Vertex AI IAM role (`roles/aiplatform.user`) to Cloud Run service account in `terraform/` (relevant .tf file)
- [ ] T056 [P] Add `LYRIA_GCP_PROJECT_ID`, `LYRIA_GCP_LOCATION`, `LYRIA_MODEL` environment variables to Cloud Run Terraform config
- [ ] T057 [P] Update `docs/features/016-integration-gemini-lyria-music/quickstart.md` with verified examples after implementation
- [ ] T058 Run `make check` to verify linting, formatting, type checking pass
- [ ] T059 Run `make test` to verify all new tests pass
- [ ] T060 Run quickstart.md validation: execute cURL examples against running server

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001–T005) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T006–T012) — Core MVP
- **US2 (Phase 4)**: Depends on US1 (T017 client implementation)
- **US3 (Phase 5)**: Depends on Foundational only — can run parallel with US1
- **US4 (Phase 6)**: Depends on US1 (T017 client implementation)
- **US5 (Phase 7)**: Depends on US1 (T017 client implementation)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1 (Setup) ──▶ Phase 2 (Foundational)
                         │
                    ┌────┼────────┐
                    ▼    ▼        ▼
                  US1  US3      (wait)
                   │              │
              ┌────┼────┐        │
              ▼    ▼    ▼        │
            US2  US4  US5        │
              │    │    │        │
              └────┴────┴────────┘
                         │
                    ▼ Phase 8 (Polish)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Client/adapter before provider
- Provider before service/route changes
- Backend before frontend
- Story complete before moving to next priority

### Parallel Opportunities

- T001 + T002 can run in parallel (verification only — deps already present)
- T003 + T004 can run in parallel (different files)
- T006 + T007 + T008 can run in parallel (different files: entity, schema, frontend type)
- T012a + T012b + T012c can run in parallel (interface, migration, entity — different files)
- T013 + T014 + T015 + T016 can run in parallel (all test files, write before implementation)
- T027 + T035 + T037 can run in parallel (different files: backend schema, frontend form, frontend service)
- T039 + T040 can run in parallel (test files)
- T046 + T047 can run in parallel (test files)
- T053 + T053a + T054 + T055 + T056 + T057 can run in parallel (independent polish tasks)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together (FIRST — must fail):
Task: "T013 Contract test for Lyria Vertex AI predict endpoint in backend/tests/contract/music/test_lyria_contract.py"
Task: "T014 Unit test for LyriaMusicProvider.generate_instrumental() in backend/tests/unit/music/test_lyria_provider.py"
Task: "T015 Unit test for WAV→MP3 conversion in backend/tests/unit/music/test_lyria_provider.py"
Task: "T016 Unit test for LyriaVertexAIClient request payload in backend/tests/contract/music/test_lyria_contract.py"

# Then implement (sequentially — client before provider before worker):
Task: "T017 Implement LyriaVertexAIClient.generate_instrumental()"
Task: "T018 Implement WAV→MP3 conversion helper"
Task: "T019 Implement LyriaMusicProvider.generate_instrumental()"
Task: "T020 Create MusicJobWorker (new file: music_job_worker.py)"
Task: "T021 Implement LyriaMusicProvider.query_task()"
Task: "T022 Add Vertex AI error handling"
Task: "T022a Add retry logic (FR-016)"
Task: "T022b Add WAV fallback (EC-004)"
Task: "T023 Add English-only prompt validation"
Task: "T024 End-to-end verification"
```

---

## Parallel Example: User Story 3 (can run parallel with US1)

```bash
# US3 only depends on Foundational phase, not on US1:
Task: "T032 Unit test for /api/v1/music/providers endpoint"
Task: "T033 Add GET /api/v1/music/providers endpoint"
Task: "T034 Implement LyriaMusicProvider.capabilities()"

# Frontend tasks (parallel with each other):
Task: "T035 Add provider dropdown to MusicForm.tsx"
Task: "T037 Add Lyria provider to musicApi.ts"

# Then sequential:
Task: "T036 Conditional form sections based on provider"
Task: "T038 Display provider in history views"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational (T006–T012c)
3. Complete Phase 3: User Story 1 (T013–T024, incl. T022a/T022b)
4. **STOP and VALIDATE**: Test Lyria instrumental generation end-to-end
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Lyria instrumental) → Test → Deploy/Demo **(MVP!)**
3. Add US2 (Negative prompt) + US3 (Provider switching) → Test → Deploy/Demo
4. Add US4 (Seed) + US5 (Batch) → Test → Deploy/Demo
5. Polish → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (core Lyria generation)
   - Developer B: US3 (provider switching UI) — independent of US1
3. After US1 done:
   - Developer A: US2 (negative prompt)
   - Developer B: US4 (seed) or US5 (batch)
4. Stories complete and integrate independently

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 67 |
| **Setup tasks** | 5 (T001–T005) |
| **Foundational tasks** | 10 (T006–T012c) |
| **US1 tasks** | 14 (T013–T024, incl. T022a/T022b) |
| **US2 tasks** | 7 (T025–T031) |
| **US3 tasks** | 7 (T032–T038) |
| **US4 tasks** | 7 (T039–T045) |
| **US5 tasks** | 7 (T046–T052) |
| **Polish tasks** | 10 (T053–T060, incl. T053a) |
| **Parallelizable** | 31 tasks marked [P] |
| **MVP scope** | 29 tasks (Setup + Foundational + US1) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Lyria 2 is synchronous API — MusicJobWorker skips polling loop for Lyria (handle in T020)
- WAV→MP3 conversion requires ffmpeg in Docker image (confirmed present in Dockerfile)
- `google-auth` and `pydub` already in `pyproject.toml` — T001/T002 are verification-only
- **Music job worker does NOT exist yet** — T020 creates `MusicJobWorker` (also enables Mureka background processing)
- `provider_metadata` JSONB column (T012b) stores: negative_prompt, seed, sample_count, batch_id — avoids per-field migrations
- File paths verified against codebase: schemas in `schemas/music_schemas.py`, form in `MusicForm.tsx`, API client in `musicApi.ts`

## Analysis Changelog (2026-02-19)

Post-generation gap analysis identified and fixed 7 issues:

| # | Issue | Fix Applied |
|---|---|---|
| G1 | EC-004 WAV→MP3 fallback missing | Added T022b |
| G2 | FR-012 SynthID verification missing | Added T053a |
| G3 | FR-016 Retry logic (max 3) missing | Added T022a |
| G4 | IMusicProvider.capabilities() not in interface | Added T012a |
| G5 | T030 conflicted with data-model.md "no migration" | Resolved via `provider_metadata` JSONB (T012b/T012c) |
| P1 | T007 wrong file path (routes → schemas) | Fixed to `schemas/music_schemas.py` |
| P2 | T035/T036 wrong component name | Fixed to `MusicForm.tsx` |
| R1 | T020 assumed existing music worker | Rewritten: creates `MusicJobWorker` from scratch |
| R7 | T001 listed unnecessary `google-auth-httplib2` | Removed; only `google-auth` needed |
