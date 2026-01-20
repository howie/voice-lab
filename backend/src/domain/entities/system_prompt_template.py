"""SystemPromptTemplate entity.

T011: Represents a system prompt template for AI configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class SystemPromptTemplate:
    """A reusable system prompt template."""

    name: str
    description: str
    prompt_content: str
    category: str
    id: UUID = field(default_factory=uuid4)
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        prompt_content: str | None = None,
        category: str | None = None,
    ) -> None:
        """Update template fields."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if prompt_content is not None:
            self.prompt_content = prompt_content
        if category is not None:
            self.category = category
        self.updated_at = datetime.utcnow()
