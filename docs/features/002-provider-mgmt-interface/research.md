# Research: Provider API Key Management Interface

**Feature**: 002-provider-mgmt-interface
**Date**: 2026-01-18

## Research Topics

### 1. Provider API Key Validation Methods

**Decision**: Use provider-specific lightweight API calls to validate keys

**Rationale**:
- Each provider has different API structures and authentication methods
- A simple authenticated request (e.g., list voices) confirms key validity without consuming quota
- Provides immediate feedback to users

**Implementation per Provider**:

| Provider | Validation Endpoint | Method |
|----------|-------------------|--------|
| ElevenLabs | `GET /v1/user` | Returns user info if valid |
| Azure Speech | `GET /cognitiveservices/voices/list` | Returns voices if valid |
| Google Cloud TTS | `voices.list()` | Returns voices if valid |

**Alternatives Considered**:
- Dry-run synthesis: Too expensive, consumes quota
- Token introspection: Not all providers support this

### 2. PostgreSQL Transparent Data Encryption (TDE)

**Decision**: Use PostgreSQL TDE for at-rest encryption of API keys

**Rationale**:
- Encryption is transparent to application layer
- No code changes needed for encrypt/decrypt
- Industry-standard approach for sensitive data storage
- Meets compliance requirements

**Implementation Notes**:
- PostgreSQL 16+ supports TDE natively
- For older versions, use pgcrypto extension or column-level encryption
- Connection should use SSL/TLS for data in transit

**Alternatives Considered**:
- Application-level encryption (cryptography lib): More complex key management
- Per-user derived keys: Over-engineering for current requirements

### 3. Multi-tenant Credential Isolation

**Decision**: User ID foreign key with row-level filtering

**Rationale**:
- Leverages existing User model from auth system
- Simple and effective isolation
- Follows existing patterns in SynthesisLog

**Implementation**:
```python
class UserProviderCredential(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
```

**Alternatives Considered**:
- Schema-per-tenant: Overkill for current scale
- Separate databases: Too complex for credential storage

### 4. Audit Logging Strategy

**Decision**: Dedicated AuditLog table with structured event types

**Rationale**:
- Full traceability for compliance
- Can be queried and analyzed independently
- Supports both key operations and usage events

**Event Types**:
- `credential.created` - New API key added
- `credential.updated` - API key rotated
- `credential.deleted` - API key removed
- `credential.validated` - Key validation performed
- `credential.used` - Key used for provider call

**Log Entry Structure**:
```python
class AuditLog(Base):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    provider: str
    timestamp: datetime
    details: dict  # JSON field for event-specific data
    outcome: str   # success/failure
    ip_address: str | None
```

**Alternatives Considered**:
- Append-only file logging: Harder to query
- Event sourcing: Over-engineering for audit requirements

### 5. Extensible Provider Architecture

**Decision**: Provider registry with abstract base class

**Rationale**:
- Existing `BaseTTSProvider` already provides extensibility pattern
- New providers implement common interface
- Registration at startup or via configuration

**Implementation Pattern**:
```python
# Provider registry
SUPPORTED_PROVIDERS = {
    "elevenlabs": {
        "name": "ElevenLabs",
        "type": ["tts"],
        "validator_class": ElevenLabsValidator,
    },
    "azure": {
        "name": "Azure Cognitive Services",
        "type": ["tts", "stt"],
        "validator_class": AzureValidator,
    },
    "gemini": {
        "name": "Google Gemini",
        "type": ["tts", "stt"],
        "validator_class": GeminiValidator,
    },
}
```

**Adding New Provider**:
1. Create validator class extending `BaseProviderValidator`
2. Register in `SUPPORTED_PROVIDERS`
3. No core code changes required

### 6. Credential Injection into Existing Providers

**Decision**: Factory pattern with credential override

**Rationale**:
- Existing providers use environment variables for keys
- Need to support both system-level and user-level credentials
- User credentials take precedence (FR-011)

**Implementation**:
```python
class TTSProviderFactory:
    @staticmethod
    async def create(
        provider_name: str,
        user_id: uuid.UUID | None = None,
        credential_repo: CredentialRepository | None = None
    ) -> ITTSProvider:
        # Check for user credential first
        if user_id and credential_repo:
            user_cred = await credential_repo.get_by_user_and_provider(
                user_id, provider_name
            )
            if user_cred:
                return _create_with_credential(provider_name, user_cred.api_key)

        # Fall back to system configuration
        return _create_from_config(provider_name)
```

### 7. API Key Masking for Display

**Decision**: Show only last 4 characters

**Rationale**:
- Sufficient for user identification
- Prevents exposure in logs or UI
- Industry standard practice

**Implementation**:
```python
def mask_api_key(key: str) -> str:
    if len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"
```

### 8. Model Selection Storage

**Decision**: Store selected model as part of UserProviderCredential

**Rationale**:
- Model selection is provider-specific
- One selected model per provider per user
- Can be updated independently of API key

**Schema Addition**:
```python
class UserProviderCredential(Base):
    # ... existing fields
    selected_model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
```

## Summary

All research topics resolved. No blocking clarifications remaining. Ready for Phase 1 design.
