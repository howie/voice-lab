"""ScenarioTemplate entity.

Feature: 004-interaction-module
T011/US4: Represents a scenario template with role and context configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ScenarioTemplate:
    """A scenario template with user/AI roles and context."""

    name: str
    description: str
    user_role: str
    ai_role: str
    scenario_context: str
    category: str
    id: UUID = field(default_factory=uuid4)
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        user_role: str | None = None,
        ai_role: str | None = None,
        scenario_context: str | None = None,
        category: str | None = None,
    ) -> None:
        """Update template fields."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if user_role is not None:
            self.user_role = user_role
        if ai_role is not None:
            self.ai_role = ai_role
        if scenario_context is not None:
            self.scenario_context = scenario_context
        if category is not None:
            self.category = category
        self.updated_at = datetime.utcnow()

    def generate_system_prompt(self) -> str:
        """Generate system prompt from ai_role and scenario_context."""
        return f"你是{self.ai_role}。{self.scenario_context}"
