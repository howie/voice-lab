# Feature Specification: Provider API Key Management Interface

**Feature Branch**: `002-provider-mgmt-interface`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "目前的設計是各 tts stt provider API key 是系統一啟動就當 config 輸入，在這個 feature 改變成為可以 onfly runtime 讓使用者輸入自己的 API Key，並且加密儲存在 db 裏，所以使用者可以 BYOL, 輸入自己 elevenlab, azure, gemini ...等 API Key and model選擇，而且當輸入完，系統會先驗證是否有正確運作"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Provider API Key (Priority: P1)

As a user, I want to add my own API key for a TTS/STT provider (e.g., ElevenLabs, Azure, Gemini) so that I can use my own account and quota for voice services.

**Why this priority**: This is the core functionality - without the ability to add API keys, no other features can work. This enables the BYOL (Bring Your Own License) model.

**Independent Test**: Can be fully tested by navigating to provider settings, entering an API key, and verifying it gets saved securely. Delivers immediate value as users can start using their own provider accounts.

**Acceptance Scenarios**:

1. **Given** I am on the provider management page, **When** I select a provider (e.g., ElevenLabs) and enter my API key, **Then** the system validates the key and displays a success message if valid
2. **Given** I have entered an invalid API key, **When** I submit the form, **Then** the system displays a clear error message indicating the key is invalid
3. **Given** I have successfully added an API key, **When** I check the database, **Then** the API key is stored in encrypted form (not plaintext)

---

### User Story 2 - Select Provider and Model (Priority: P1)

As a user, I want to select which provider and model to use for TTS/STT operations so that I can choose the voice quality and style that best fits my needs.

**Why this priority**: Equally critical as adding keys - users need to specify which provider and model to use for the service to function properly.

**Independent Test**: Can be tested by selecting a provider and model from available options, then verifying the selection is persisted and used for subsequent operations.

**Acceptance Scenarios**:

1. **Given** I have added valid API keys for multiple providers, **When** I access the provider settings, **Then** I can see all available providers and their models
2. **Given** I am viewing provider options, **When** I select a specific provider and model, **Then** my selection is saved and becomes the active configuration
3. **Given** I have selected a provider/model, **When** I perform a TTS/STT operation, **Then** the system uses my selected provider and model

---

### User Story 3 - Manage Multiple Provider Credentials (Priority: P2)

As a user, I want to manage multiple provider credentials so that I can switch between different providers or have backup options.

**Why this priority**: Provides flexibility and redundancy, but not essential for basic functionality.

**Independent Test**: Can be tested by adding credentials for multiple providers and verifying they are all stored and accessible.

**Acceptance Scenarios**:

1. **Given** I have no saved providers, **When** I add credentials for ElevenLabs, Azure, and Gemini, **Then** all three are saved and visible in my provider list
2. **Given** I have multiple saved providers, **When** I view my provider settings, **Then** I can see status (valid/invalid) for each provider
3. **Given** I have multiple saved providers, **When** I delete one provider's credentials, **Then** only that provider is removed and others remain intact

---

### User Story 4 - Update or Remove API Key (Priority: P2)

As a user, I want to update or remove my API keys so that I can rotate keys for security or remove providers I no longer use.

**Why this priority**: Important for security and maintenance but not blocking core functionality.

**Independent Test**: Can be tested by updating an existing key and verifying the new key is used, or removing a key and verifying it's deleted.

**Acceptance Scenarios**:

1. **Given** I have a saved API key for ElevenLabs, **When** I enter a new API key and save, **Then** the old key is replaced and the new key is validated
2. **Given** I have a saved API key, **When** I choose to remove it, **Then** the key is deleted from the system and I see confirmation
3. **Given** I have removed a provider's key, **When** I try to use that provider for TTS/STT, **Then** the system prompts me to add credentials

---

### User Story 5 - View Provider Status and Quota (Priority: P3)

As a user, I want to see the status and remaining quota of my configured providers so that I can monitor usage and avoid service interruptions.

**Why this priority**: Nice-to-have feature that improves user experience but is not essential for core functionality.

**Independent Test**: Can be tested by viewing provider status page and verifying it displays current status and quota information.

**Acceptance Scenarios**:

1. **Given** I have configured providers, **When** I view the provider management page, **Then** I can see the connection status (connected/error) for each provider
2. **Given** a provider offers quota information via API, **When** I view that provider's details, **Then** I can see my remaining quota or usage statistics

---

### Edge Cases

- What happens when a previously valid API key becomes invalid (e.g., expired, revoked)?
  - System should detect on next use and notify user, prompting for new credentials
- How does system handle network timeout during API key validation?
  - System should show appropriate error and allow retry
- What happens when user tries to use a provider with no configured API key?
  - System should redirect to provider setup or show clear message
- How does system handle provider API rate limiting during validation?
  - System should recognize rate limit errors and advise user to wait before retrying

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to add API keys for supported TTS/STT providers (ElevenLabs, Azure, Gemini)
- **FR-002**: System MUST encrypt all API keys before storing them in the database
- **FR-003**: System MUST validate API keys against the provider's API before accepting them
- **FR-004**: System MUST display available models for each provider after successful key validation
- **FR-005**: System MUST allow users to select a default provider and model for TTS/STT operations
- **FR-006**: System MUST allow users to update existing API keys
- **FR-007**: System MUST allow users to remove API keys from the system
- **FR-008**: System MUST display clear error messages when API key validation fails
- **FR-009**: System MUST never display stored API keys in plaintext (show masked version only)
- **FR-010**: System MUST continue to support system-level API keys from configuration as fallback
- **FR-011**: User-provided API keys MUST take precedence over system-level configuration
- **FR-012**: System MUST maintain full audit trail for all API key operations (create, read, update, delete)
- **FR-013**: System MUST log all API key usage events (provider calls made using user credentials)
- **FR-014**: System architecture MUST support adding new providers without requiring major structural changes

### Key Entities

- **Provider**: Represents a TTS/STT service provider (e.g., ElevenLabs, Azure, Gemini) with its name, type (TTS/STT/both), and supported models; designed for extensibility to add new providers without major changes
- **UserProviderCredential**: Stores user's encrypted API key for a specific provider, including validation status and last validated timestamp; scoped to individual user (multi-tenant isolation)
- **ProviderModel**: Represents available models for each provider, including model ID, display name, and capabilities
- **AuditLog**: Records all API key operations and usage events, including user, action type, timestamp, provider, and outcome

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add and validate a new API key within 30 seconds (excluding network latency)
- **SC-002**: 100% of stored API keys are encrypted at rest (no plaintext storage)
- **SC-003**: API key validation provides clear success/failure feedback within 10 seconds
- **SC-004**: Users can switch between providers and models with immediate effect
- **SC-005**: 95% of users successfully configure their first provider on first attempt
- **SC-006**: System gracefully handles provider API failures without data loss or crashes

## Clarifications

### Session 2026-01-18

- Q: Multi-tenancy model? → A: Multi-tenant (每位使用者各自管理 API keys)，未來可擴展支援 Team-based 共享
- Q: Security audit logging? → A: Full audit trail (完整稽核軌跡，包含所有存取和使用紀錄)
- Q: API Key encryption approach? → A: Database-level encryption (資料庫層級加密，如 PostgreSQL TDE)
- Q: User authentication dependency? → A: Existing auth (認證機制已存在，本 feature 直接使用)
- Q: Provider extensibility? → A: Extensible design (可擴展架構，未來可新增 provider 無需大幅修改)

## Assumptions

- User authentication mechanism already exists; this feature leverages existing auth for user identification
- Users have valid API keys from their respective provider accounts
- Providers offer public APIs for key validation (at minimum, a simple authenticated request that confirms key validity)
- System uses database-level encryption (e.g., PostgreSQL TDE) for API key storage; encryption is transparent to application layer
- Network connectivity is available for API key validation
- Multi-tenant architecture: each user manages their own API keys independently; future extension to Team-based sharing is anticipated
