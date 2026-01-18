# Data Model: Provider API Key Management Interface

**Feature**: 002-provider-mgmt-interface
**Date**: 2026-01-18

## Entity Relationship Diagram

```
┌──────────────────┐       ┌─────────────────────────────┐
│      User        │       │    UserProviderCredential   │
├──────────────────┤       ├─────────────────────────────┤
│ id (PK)          │──────<│ id (PK)                     │
│ google_id        │       │ user_id (FK)                │
│ email            │       │ provider                    │
│ name             │       │ api_key (encrypted)         │
│ picture_url      │       │ selected_model_id           │
│ created_at       │       │ is_valid                    │
│ last_login_at    │       │ last_validated_at           │
└──────────────────┘       │ created_at                  │
                           │ updated_at                  │
                           └─────────────────────────────┘
                                       │
                                       │
                           ┌───────────┴───────────┐
                           │                       │
                           ▼                       ▼
              ┌─────────────────────┐  ┌─────────────────────┐
              │     AuditLog        │  │      Provider       │
              ├─────────────────────┤  ├─────────────────────┤
              │ id (PK)             │  │ id (PK)             │
              │ user_id (FK)        │  │ name                │
              │ event_type          │  │ display_name        │
              │ provider            │  │ type (tts/stt/both) │
              │ resource_id         │  │ supported_models    │
              │ timestamp           │  │ is_active           │
              │ details (JSON)      │  │ created_at          │
              │ outcome             │  └─────────────────────┘
              │ ip_address          │
              │ user_agent          │
              └─────────────────────┘
```

## Entities

### 1. UserProviderCredential

Stores encrypted API keys for TTS/STT providers, scoped to individual users.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| user_id | UUID | FK(users.id), NOT NULL, INDEX | Owner of the credential |
| provider | VARCHAR(50) | NOT NULL, INDEX | Provider identifier (elevenlabs, azure, gemini) |
| api_key | TEXT | NOT NULL, ENCRYPTED | Encrypted API key (PostgreSQL TDE) |
| selected_model_id | VARCHAR(128) | NULL | Currently selected model for this provider |
| is_valid | BOOLEAN | NOT NULL, DEFAULT true | Last validation result |
| last_validated_at | TIMESTAMP WITH TZ | NULL | When key was last validated |
| created_at | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now(), ON UPDATE | Last update timestamp |

**Constraints**:
- UNIQUE(user_id, provider) - One credential per provider per user
- api_key length validation per provider requirements

**Indexes**:
- idx_credentials_user_id (user_id)
- idx_credentials_provider (provider)
- idx_credentials_user_provider (user_id, provider) - for lookup

### 2. AuditLog

Records all security-relevant events for compliance and debugging.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| user_id | UUID | FK(users.id), NOT NULL, INDEX | User who performed action |
| event_type | VARCHAR(50) | NOT NULL, INDEX | Event type (see Event Types) |
| provider | VARCHAR(50) | NULL | Related provider (if applicable) |
| resource_id | UUID | NULL | Related resource ID (credential ID) |
| timestamp | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now(), INDEX | When event occurred |
| details | JSONB | NULL | Event-specific metadata |
| outcome | VARCHAR(20) | NOT NULL | success, failure, error |
| ip_address | VARCHAR(45) | NULL | Client IP (IPv4/IPv6) |
| user_agent | VARCHAR(512) | NULL | Client user agent |

**Event Types**:
- `credential.created` - New API key added
- `credential.updated` - API key rotated/updated
- `credential.deleted` - API key removed
- `credential.validated` - Key validation performed
- `credential.validation_failed` - Key validation failed
- `credential.used` - Key used for provider call
- `credential.viewed` - Credential details viewed (masked)
- `model.selected` - Model selection changed

**Indexes**:
- idx_audit_user_id (user_id)
- idx_audit_event_type (event_type)
- idx_audit_timestamp (timestamp)
- idx_audit_provider (provider)

### 3. Provider (Reference Data)

Static reference table for supported providers. Can be seeded via migration.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(50) | PK | Provider identifier (elevenlabs, azure, gemini) |
| name | VARCHAR(100) | NOT NULL | Display name |
| display_name | VARCHAR(100) | NOT NULL | Human-friendly name |
| type | VARCHAR(20)[] | NOT NULL | Supported types: tts, stt, or both |
| supported_models | JSONB | NULL | Available models with metadata |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Whether provider is enabled |
| created_at | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now() | Creation timestamp |

**Seed Data**:
```json
[
  {
    "id": "elevenlabs",
    "name": "elevenlabs",
    "display_name": "ElevenLabs",
    "type": ["tts"],
    "is_active": true
  },
  {
    "id": "azure",
    "name": "azure",
    "display_name": "Azure Cognitive Services",
    "type": ["tts", "stt"],
    "is_active": true
  },
  {
    "id": "gemini",
    "name": "gemini",
    "display_name": "Google Gemini",
    "type": ["tts", "stt"],
    "is_active": true
  }
]
```

## State Transitions

### UserProviderCredential States

```
                    ┌─────────────┐
                    │   (none)    │
                    └──────┬──────┘
                           │ add_credential
                           ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   invalid   │◄────│   pending   │────►│    valid    │
│ is_valid=F  │     │  validation │     │ is_valid=T  │
└──────┬──────┘     └─────────────┘     └──────┬──────┘
       │                   ▲                    │
       │                   │                    │
       │ retry_validation  │ update_credential  │ revalidate
       └───────────────────┴────────────────────┘
                           │
                           │ delete_credential
                           ▼
                    ┌─────────────┐
                    │  (deleted)  │
                    └─────────────┘
```

## Validation Rules

### UserProviderCredential

1. **user_id**: Must reference existing user
2. **provider**: Must be one of supported providers (elevenlabs, azure, gemini)
3. **api_key**:
   - Not empty
   - Max length varies by provider:
     - ElevenLabs: 32 characters
     - Azure: 32 characters
     - Gemini: 39 characters (API key format)
4. **selected_model_id**: Must be valid model for the provider (validated on save)

### AuditLog

1. **event_type**: Must be one of defined event types
2. **outcome**: Must be one of: success, failure, error
3. **details**: Valid JSON if provided

## Data Lifecycle

### Retention Policy

- **UserProviderCredential**: Retained until user deletes or account is closed
- **AuditLog**: Retained for 2 years (configurable), then archived or purged

### Cascade Rules

- On User deletion: Soft-delete associated UserProviderCredentials
- On UserProviderCredential deletion: Create audit log entry, hard delete credential

## Migration Notes

1. Create `providers` table and seed reference data
2. Create `user_provider_credentials` table with encryption
3. Create `audit_logs` table with partitioning by month (optional for scale)
4. Add foreign key indexes for performance
