"""Credentials API Routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.audit_service import AuditService
from src.application.use_cases.add_provider_credential import (
    AddCredentialInput,
    AddProviderCredentialUseCase,
    CredentialAlreadyExistsError,
    ProviderNotFoundError,
    ValidationFailedError,
)
from src.application.use_cases.validate_provider_key import (
    CredentialNotFoundError,
    UnauthorizedError,
    ValidateKeyInput,
    ValidateProviderKeyUseCase,
)
from src.config import get_settings
from src.domain.utils.masking import mask_api_key
from src.infrastructure.persistence.audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)
from src.infrastructure.persistence.credential_repository import (
    SQLAlchemyProviderCredentialRepository,
    SQLAlchemyProviderRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.providers.validators import ProviderValidatorRegistry
from src.presentation.schemas.credential import (
    AddCredentialRequest,
    CredentialListResponse,
    CredentialResponse,
    CredentialSummary,
    UpdateCredentialRequest,
    ValidationResult,
)
from src.presentation.schemas.provider import (
    Provider,
    ProviderListResponse,
    ProviderModel,
    ProviderModelsResponse,
)

router = APIRouter(prefix="/credentials", tags=["Credentials"])
providers_router = APIRouter(prefix="/credentials/providers", tags=["Providers"])


# Development user ID for DISABLE_AUTH mode
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# Dependency to get current user ID
# In production, this would come from JWT token validation
async def get_current_user_id(request: Request) -> uuid.UUID:
    """Get the current user ID from the request.

    This is a placeholder - in production this would validate JWT token
    and extract user_id from it.
    """
    settings = get_settings()

    # Development mode: return dev user ID
    if settings.disable_auth:
        return DEV_USER_ID

    # For now, check if there's a user_id in request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        # For development/testing, allow a header-based user ID
        user_id_header = request.headers.get("X-User-Id")
        if user_id_header:
            try:
                return uuid.UUID(user_id_header)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID format",
                ) from e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id


def _get_provider_display_name(provider_id: str) -> str:
    """Get display name for a provider."""
    display_names = {
        "elevenlabs": "ElevenLabs",
        "azure": "Azure Cognitive Services",
        "gemini": "Google Gemini",
    }
    return display_names.get(provider_id, provider_id.title())


# ============== Credentials Endpoints ==============


@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialListResponse:
    """List all provider credentials for the current user."""
    repo = SQLAlchemyProviderCredentialRepository(session)
    credentials = await repo.list_by_user(user_id)

    return CredentialListResponse(
        credentials=[
            CredentialSummary(
                id=cred.id,
                provider=cred.provider,
                provider_display_name=_get_provider_display_name(cred.provider),
                masked_key=mask_api_key(cred.api_key),
                is_valid=cred.is_valid,
                selected_model_id=cred.selected_model_id,
                last_validated_at=cred.last_validated_at,
                created_at=cred.created_at,
            )
            for cred in credentials
        ]
    )


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def add_credential(
    request_data: AddCredentialRequest,
    request: Request,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialResponse:
    """Add a new provider credential.

    The API key will be validated against the provider's API before being stored.
    """
    credential_repo = SQLAlchemyProviderCredentialRepository(session)
    provider_repo = SQLAlchemyProviderRepository(session)
    audit_repo = SQLAlchemyAuditLogRepository(session)
    audit_service = AuditService(audit_repo)

    use_case = AddProviderCredentialUseCase(
        credential_repository=credential_repo,
        provider_repository=provider_repo,
        audit_service=audit_service,
    )

    try:
        result = await use_case.execute(
            AddCredentialInput(
                user_id=user_id,
                provider=request_data.provider,
                api_key=request_data.api_key,
                selected_model_id=request_data.selected_model_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
        )
        await session.commit()

        cred = result.credential
        return CredentialResponse(
            id=cred.id,
            provider=cred.provider,
            provider_display_name=_get_provider_display_name(cred.provider),
            masked_key=mask_api_key(cred.api_key),
            is_valid=cred.is_valid,
            selected_model_id=cred.selected_model_id,
            last_validated_at=cred.last_validated_at,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
        )
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except CredentialAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Credential already exists for this provider",
        ) from e
    except ValidationFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_failed", "message": str(e)},
        ) from e


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialResponse:
    """Get details of a specific credential."""
    repo = SQLAlchemyProviderCredentialRepository(session)
    cred = await repo.get_by_id(credential_id)

    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    if cred.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credential",
        )

    return CredentialResponse(
        id=cred.id,
        provider=cred.provider,
        provider_display_name=_get_provider_display_name(cred.provider),
        masked_key=mask_api_key(cred.api_key),
        is_valid=cred.is_valid,
        selected_model_id=cred.selected_model_id,
        last_validated_at=cred.last_validated_at,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: uuid.UUID,
    request_data: UpdateCredentialRequest,
    request: Request,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialResponse:
    """Update a credential (API key and/or selected model)."""
    repo = SQLAlchemyProviderCredentialRepository(session)
    audit_repo = SQLAlchemyAuditLogRepository(session)
    audit_service = AuditService(audit_repo)

    cred = await repo.get_by_id(credential_id)

    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    if cred.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credential",
        )

    # Update API key if provided
    if request_data.api_key:
        # Validate new key
        validator = ProviderValidatorRegistry.get_validator(cred.provider)
        validation_result = await validator.validate(request_data.api_key)

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "validation_failed",
                    "message": validation_result.error_message,
                },
            )

        cred.update_api_key(request_data.api_key)
        cred.mark_valid()

    # Update model selection if provided
    if request_data.selected_model_id is not None:
        cred.select_model(request_data.selected_model_id)

        await audit_service.log_model_selected(
            user_id=user_id,
            credential_id=cred.id,
            provider=cred.provider,
            model_id=request_data.selected_model_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )

    await repo.update(cred)

    # Log update
    await audit_service.log_credential_updated(
        user_id=user_id,
        credential_id=cred.id,
        provider=cred.provider,
        details={"key_updated": request_data.api_key is not None},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    await session.commit()

    return CredentialResponse(
        id=cred.id,
        provider=cred.provider,
        provider_display_name=_get_provider_display_name(cred.provider),
        masked_key=mask_api_key(cred.api_key),
        is_valid=cred.is_valid,
        selected_model_id=cred.selected_model_id,
        last_validated_at=cred.last_validated_at,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: uuid.UUID,
    request: Request,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a credential."""
    repo = SQLAlchemyProviderCredentialRepository(session)
    audit_repo = SQLAlchemyAuditLogRepository(session)
    audit_service = AuditService(audit_repo)

    cred = await repo.get_by_id(credential_id)

    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    if cred.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credential",
        )

    # Log deletion before deleting
    await audit_service.log_credential_deleted(
        user_id=user_id,
        credential_id=cred.id,
        provider=cred.provider,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    await repo.delete(credential_id)
    await session.commit()


@router.post("/{credential_id}/validate", response_model=ValidationResult)
async def validate_credential(
    credential_id: uuid.UUID,
    request: Request,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ValidationResult:
    """Re-validate an existing credential."""
    credential_repo = SQLAlchemyProviderCredentialRepository(session)
    audit_repo = SQLAlchemyAuditLogRepository(session)
    audit_service = AuditService(audit_repo)

    use_case = ValidateProviderKeyUseCase(
        credential_repository=credential_repo,
        audit_service=audit_service,
    )

    try:
        result = await use_case.execute(
            ValidateKeyInput(
                user_id=user_id,
                credential_id=credential_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
        )
        await session.commit()

        quota_info = None
        if result.quota_info:
            from src.presentation.schemas.credential import QuotaInfo

            quota_info = QuotaInfo(
                character_count=result.quota_info.get("character_count"),
                character_limit=result.quota_info.get("character_limit"),
                remaining_characters=result.quota_info.get("remaining_characters"),
                tier=result.quota_info.get("tier"),
            )

        return ValidationResult(
            is_valid=result.is_valid,
            validated_at=result.validated_at,
            error_message=result.error_message,
            quota_info=quota_info,
        )
    except CredentialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        ) from e
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credential",
        ) from e


@router.get("/{credential_id}/models", response_model=ProviderModelsResponse)
async def list_credential_models(
    credential_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    language: str | None = None,
) -> ProviderModelsResponse:
    """List available models for a credential's provider."""
    repo = SQLAlchemyProviderCredentialRepository(session)
    cred = await repo.get_by_id(credential_id)

    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    if cred.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this credential",
        )

    validator = ProviderValidatorRegistry.get_validator(cred.provider)
    models_data = await validator.get_available_models(cred.api_key)

    # Filter by language if specified
    if language:
        models_data = [m for m in models_data if m.get("language", "").startswith(language)]

    return ProviderModelsResponse(
        models=[
            ProviderModel(
                id=m.get("id", ""),
                name=m.get("name", ""),
                language=m.get("language", ""),
                gender=m.get("gender"),
                description=m.get("description"),
            )
            for m in models_data
        ]
    )


# ============== Providers Endpoints ==============


@providers_router.get("", response_model=ProviderListResponse)
async def list_providers(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProviderListResponse:
    """List all supported TTS/STT providers."""
    repo = SQLAlchemyProviderRepository(session)
    providers = await repo.list_all(active_only=True)

    return ProviderListResponse(
        providers=[
            Provider(
                id=p.id,
                name=p.name,
                display_name=p.display_name,
                type=p.type,
                is_active=p.is_active,
            )
            for p in providers
        ]
    )


@providers_router.get("/{provider_id}", response_model=Provider)
async def get_provider(
    provider_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Provider:
    """Get details of a specific provider."""
    repo = SQLAlchemyProviderRepository(session)
    provider = await repo.get_by_id(provider_id)

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    return Provider(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        type=provider.type,
        is_active=provider.is_active,
    )
