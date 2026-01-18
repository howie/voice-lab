"""Shared test fixtures and utilities."""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.main import app
from src.presentation.api.routes import credentials as credentials_module


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Create a mock database session."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@asynccontextmanager
async def override_dependencies(
    user_id: uuid.UUID,
    session: MagicMock,
    credential_repo: AsyncMock | None = None,
    provider_repo: AsyncMock | None = None,
    audit_repo: AsyncMock | None = None,
) -> AsyncGenerator[None, None]:
    """Context manager to override FastAPI dependencies for testing.

    Args:
        user_id: The user ID to return from get_current_user_id
        session: The mock database session
        credential_repo: Optional mock credential repository
        provider_repo: Optional mock provider repository
        audit_repo: Optional mock audit log repository
    """

    async def override_get_current_user_id() -> uuid.UUID:
        return user_id

    async def override_get_db_session() -> Any:
        return session

    # Set overrides
    app.dependency_overrides[credentials_module.get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[credentials_module.get_db_session] = override_get_db_session

    try:
        yield
    finally:
        # Clear all overrides
        app.dependency_overrides.clear()
