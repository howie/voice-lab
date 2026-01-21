"""ScenarioTemplate Repository SQLAlchemy Implementation.

Feature: 004-interaction-module
T069 [US4]: SQLAlchemy implementation of ScenarioTemplateRepository.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.scenario_template import ScenarioTemplate
from src.domain.repositories.scenario_template_repository import (
    ScenarioTemplateRepository,
)
from src.infrastructure.persistence.models import ScenarioTemplateModel


class SQLAlchemyScenarioTemplateRepository(ScenarioTemplateRepository):
    """SQLAlchemy implementation of ScenarioTemplateRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_entity(self, model: ScenarioTemplateModel) -> ScenarioTemplate:
        """Convert SQLAlchemy model to domain entity."""
        return ScenarioTemplate(
            id=model.id,
            name=model.name,
            description=model.description,
            user_role=model.user_role,
            ai_role=model.ai_role,
            scenario_context=model.scenario_context,
            category=model.category,
            is_default=model.is_default,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: ScenarioTemplate) -> ScenarioTemplateModel:
        """Convert domain entity to SQLAlchemy model."""
        return ScenarioTemplateModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            user_role=entity.user_role,
            ai_role=entity.ai_role,
            scenario_context=entity.scenario_context,
            category=entity.category,
            is_default=entity.is_default,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, template: ScenarioTemplate) -> ScenarioTemplate:
        """Create a new scenario template."""
        model = self._entity_to_model(template)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def get_by_id(self, template_id: UUID) -> ScenarioTemplate | None:
        """Get template by ID."""
        stmt = select(ScenarioTemplateModel).where(ScenarioTemplateModel.id == template_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_name(self, name: str) -> ScenarioTemplate | None:
        """Get template by name."""
        stmt = select(ScenarioTemplateModel).where(ScenarioTemplateModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def list_all(self) -> Sequence[ScenarioTemplate]:
        """List all templates."""
        stmt = select(ScenarioTemplateModel).order_by(ScenarioTemplateModel.name)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_by_category(self, category: str) -> Sequence[ScenarioTemplate]:
        """List templates by category."""
        stmt = (
            select(ScenarioTemplateModel)
            .where(ScenarioTemplateModel.category == category)
            .order_by(ScenarioTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def get_defaults(self) -> Sequence[ScenarioTemplate]:
        """Get default templates."""
        stmt = (
            select(ScenarioTemplateModel)
            .where(ScenarioTemplateModel.is_default.is_(True))
            .order_by(ScenarioTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def update(self, template: ScenarioTemplate) -> ScenarioTemplate:
        """Update an existing template."""
        stmt = select(ScenarioTemplateModel).where(ScenarioTemplateModel.id == template.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Template with id {template.id} not found")

        model.name = template.name
        model.description = template.description
        model.user_role = template.user_role
        model.ai_role = template.ai_role
        model.scenario_context = template.scenario_context
        model.category = template.category
        model.is_default = template.is_default

        await self._session.flush()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def delete(self, template_id: UUID) -> bool:
        """Delete a template."""
        stmt = select(ScenarioTemplateModel).where(ScenarioTemplateModel.id == template_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True
