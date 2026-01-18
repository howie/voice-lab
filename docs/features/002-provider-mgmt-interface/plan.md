# Implementation Plan: Provider API Key Management Interface

**Branch**: `002-provider-mgmt-interface` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/002-provider-mgmt-interface/spec.md`

## Summary

Enable users to manage their own TTS/STT provider API keys at runtime (BYOL model). Users can add, validate, update, and remove API keys for ElevenLabs, Azure, and Gemini providers. Keys are encrypted at database level and validated against provider APIs before acceptance. Full audit trail for all key operations and usage events.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.3+ (Frontend)
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, React 18+
**Storage**: PostgreSQL with TDE (Transparent Data Encryption)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (Docker), Web browser
**Project Type**: Web application (backend + frontend)
**Performance Goals**: API key validation within 10 seconds, key operations within 30 seconds
**Constraints**: Database-level encryption, multi-tenant isolation, full audit trail
**Scale/Scope**: Multi-tenant, extensible provider architecture

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-Driven Development | ✅ PASS | Will write contract tests for provider validation, unit tests for encryption/CRUD |
| II. Unified API Abstraction | ✅ PASS | Extends existing `ITTSProvider` interface with credential injection support |
| III. Performance Benchmarking | ✅ PASS | Key validation latency will be measured and logged |
| IV. Documentation First | ✅ PASS | quickstart.md and API contracts generated in Phase 1 |
| V. Clean Architecture | ✅ PASS | New entities in domain/, adapters in infrastructure/, API in presentation/ |

## Project Structure

### Documentation (this feature)

```text
docs/features/002-provider-mgmt-interface/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── provider-credentials-api.yaml
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── provider_credential.py   # NEW: UserProviderCredential entity
│   │   │   └── audit_log.py             # NEW: AuditLog entity
│   │   └── repositories/
│   │       ├── provider_credential_repository.py  # NEW
│   │       └── audit_log_repository.py            # NEW
│   ├── application/
│   │   ├── interfaces/
│   │   │   └── credential_service.py    # NEW: Credential management port
│   │   └── use_cases/
│   │       ├── add_provider_credential.py      # NEW
│   │       ├── validate_provider_key.py        # NEW
│   │       ├── update_provider_credential.py   # NEW
│   │       ├── delete_provider_credential.py   # NEW
│   │       └── list_provider_credentials.py    # NEW
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   └── models.py                # MODIFY: Add credential & audit models
│   │   └── providers/
│   │       └── tts/
│   │           └── base.py              # MODIFY: Support credential injection
│   └── presentation/
│       └── api/
│           └── routes/
│               └── credentials.py       # NEW: CRUD API endpoints
└── tests/
    ├── contract/
    │   └── test_provider_validation.py  # NEW
    ├── integration/
    │   └── test_credential_crud.py      # NEW
    └── unit/
        └── test_audit_logging.py        # NEW

frontend/
├── src/
│   ├── pages/
│   │   └── ProviderSettings.tsx         # NEW: Provider management UI
│   ├── components/
│   │   ├── ProviderCard.tsx             # NEW
│   │   ├── ApiKeyInput.tsx              # NEW
│   │   └── ModelSelector.tsx            # NEW
│   └── services/
│       └── credentialService.ts         # NEW: API client
└── tests/
    └── ProviderSettings.test.tsx        # NEW
```

**Structure Decision**: Web application pattern (backend + frontend). Follows existing Clean Architecture with domain/application/infrastructure/presentation layers. New entities and use cases added to support credential management.

## Complexity Tracking

No violations to justify. Design follows existing patterns and constitution principles.
