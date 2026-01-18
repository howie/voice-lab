"""SQLAlchemy implementation of Provider Credential Repository."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.provider import Provider
from src.domain.entities.provider_credential import UserProviderCredential
from src.domain.repositories.provider_credential_repository import (
    IProviderCredentialRepository,
    IProviderRepository,
)
from src.infrastructure.persistence.models import (
    ProviderModel,
    UserProviderCredentialModel,
)


class SQLAlchemyProviderCredentialRepository(IProviderCredentialRepository):
    """SQLAlchemy implementation of the provider credential repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, credential: UserProviderCredential) -> UserProviderCredential:
        """Save a provider credential."""
        model = UserProviderCredentialModel(
            id=credential.id,
            user_id=credential.user_id,
            provider=credential.provider,
            api_key=credential.api_key,
            selected_model_id=credential.selected_model_id,
            is_valid=credential.is_valid,
            last_validated_at=credential.last_validated_at,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return credential

    async def get_by_id(self, credential_id: uuid.UUID) -> UserProviderCredential | None:
        """Get a credential by ID."""
        stmt = select(UserProviderCredentialModel).where(
            UserProviderCredentialModel.id == credential_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_and_provider(
        self, user_id: uuid.UUID, provider: str
    ) -> UserProviderCredential | None:
        """Get a credential by user ID and provider."""
        stmt = select(UserProviderCredentialModel).where(
            UserProviderCredentialModel.user_id == user_id,
            UserProviderCredentialModel.provider == provider,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(self, user_id: uuid.UUID) -> list[UserProviderCredential]:
        """List all credentials for a user."""
        stmt = (
            select(UserProviderCredentialModel)
            .where(UserProviderCredentialModel.user_id == user_id)
            .order_by(UserProviderCredentialModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update(self, credential: UserProviderCredential) -> UserProviderCredential:
        """Update an existing credential."""
        stmt = select(UserProviderCredentialModel).where(
            UserProviderCredentialModel.id == credential.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Credential {credential.id} not found")

        model.api_key = credential.api_key
        model.selected_model_id = credential.selected_model_id
        model.is_valid = credential.is_valid
        model.last_validated_at = credential.last_validated_at
        model.updated_at = datetime.utcnow()

        await self._session.flush()
        return credential

    async def delete(self, credential_id: uuid.UUID) -> bool:
        """Delete a credential."""
        stmt = select(UserProviderCredentialModel).where(
            UserProviderCredentialModel.id == credential_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def exists(self, user_id: uuid.UUID, provider: str) -> bool:
        """Check if a credential exists for user and provider."""
        stmt = select(UserProviderCredentialModel.id).where(
            UserProviderCredentialModel.user_id == user_id,
            UserProviderCredentialModel.provider == provider,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_entity(model: UserProviderCredentialModel) -> UserProviderCredential:
        """Convert SQLAlchemy model to domain entity."""
        return UserProviderCredential(
            id=model.id,
            user_id=model.user_id,
            provider=model.provider,
            api_key=model.api_key,
            selected_model_id=model.selected_model_id,
            is_valid=model.is_valid,
            last_validated_at=model.last_validated_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyProviderRepository(IProviderRepository):
    """SQLAlchemy implementation of the provider repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, provider_id: str) -> Provider | None:
        """Get a provider by ID."""
        stmt = select(ProviderModel).where(ProviderModel.id == provider_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, active_only: bool = True) -> list[Provider]:
        """List all providers."""
        stmt = select(ProviderModel)
        if active_only:
            stmt = stmt.where(ProviderModel.is_active == True)  # noqa: E712
        stmt = stmt.order_by(ProviderModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def list_by_type(self, provider_type: str) -> list[Provider]:
        """List providers by type."""
        stmt = (
            select(ProviderModel)
            .where(
                ProviderModel.is_active == True,  # noqa: E712
                ProviderModel.type.contains([provider_type]),
            )
            .order_by(ProviderModel.id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    @staticmethod
    def _to_entity(model: ProviderModel) -> Provider:
        """Convert SQLAlchemy model to domain entity."""
        return Provider(
            id=model.id,
            name=model.name,
            display_name=model.display_name,
            type=model.type,
            is_active=model.is_active,
            supported_models=model.supported_models,
            created_at=model.created_at,
        )
