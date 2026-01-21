"""ScenarioTemplate Repository Interface.

Feature: 004-interaction-module
T068 [US4]: Abstract repository for scenario template persistence.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from src.domain.entities.scenario_template import ScenarioTemplate


class ScenarioTemplateRepository(ABC):
    """Abstract repository for scenario templates."""

    @abstractmethod
    async def create(self, template: ScenarioTemplate) -> ScenarioTemplate:
        """Create a new scenario template."""
        ...

    @abstractmethod
    async def get_by_id(self, template_id: UUID) -> ScenarioTemplate | None:
        """Get template by ID."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> ScenarioTemplate | None:
        """Get template by name."""
        ...

    @abstractmethod
    async def list_all(self) -> Sequence[ScenarioTemplate]:
        """List all templates."""
        ...

    @abstractmethod
    async def list_by_category(self, category: str) -> Sequence[ScenarioTemplate]:
        """List templates by category."""
        ...

    @abstractmethod
    async def get_defaults(self) -> Sequence[ScenarioTemplate]:
        """Get default templates."""
        ...

    @abstractmethod
    async def update(self, template: ScenarioTemplate) -> ScenarioTemplate:
        """Update an existing template."""
        ...

    @abstractmethod
    async def delete(self, template_id: UUID) -> bool:
        """Delete a template."""
        ...
