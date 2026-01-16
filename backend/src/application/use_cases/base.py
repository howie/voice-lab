"""Base Use Case class."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


class UseCase(ABC, Generic[InputType, OutputType]):
    """Abstract base class for use cases.

    Use cases represent application-specific business rules.
    They orchestrate the flow of data and coordinate entities.
    """

    @abstractmethod
    async def execute(self, input_data: InputType) -> OutputType:
        """Execute the use case.

        Args:
            input_data: Input data for the use case

        Returns:
            Output data from the use case
        """
        pass
