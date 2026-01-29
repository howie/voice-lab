"""Unit tests for InteractionWebSocketHandler config handling.

Feature: 004-interaction-module
Tests specifically for user_role and ai_role configuration handling.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.infrastructure.websocket.base_handler import MessageType, WebSocketMessage
from src.infrastructure.websocket.interaction_handler import InteractionWebSocketHandler


class TestHandleConfigRoles:
    """Tests for _handle_config method's role handling."""

    @pytest.fixture
    def mock_websocket(self) -> MagicMock:
        """Create a mock WebSocket."""
        ws = MagicMock()
        ws.client_state = MagicMock()
        ws.client_state.name = "CONNECTED"
        ws.send_json = AsyncMock()
        return ws

    @pytest.fixture
    def mock_mode_service(self) -> MagicMock:
        """Create a mock InteractionModeService."""
        service = MagicMock()
        service.mode_name = "realtime"
        service.is_connected = MagicMock(return_value=False)
        service.connect = AsyncMock()
        service.trigger_greeting = AsyncMock()
        return service

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock InteractionRepository."""
        repo = MagicMock()
        repo.create_session = AsyncMock()
        return repo

    @pytest.fixture
    def mock_audio_storage(self) -> MagicMock:
        """Create a mock AudioStorageService."""
        storage = MagicMock()
        storage.ensure_session_dir = AsyncMock()
        return storage

    @pytest.fixture
    def handler(
        self,
        mock_websocket: MagicMock,
        mock_mode_service: MagicMock,
        mock_repository: MagicMock,
        mock_audio_storage: MagicMock,
    ) -> InteractionWebSocketHandler:
        """Create a handler instance with mocked dependencies."""
        return InteractionWebSocketHandler(
            websocket=mock_websocket,
            user_id=uuid4(),
            mode_service=mock_mode_service,
            repository=mock_repository,
            audio_storage=mock_audio_storage,
        )

    @pytest.mark.asyncio
    async def test_handle_config_extracts_custom_roles(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Test that custom user_role and ai_role are correctly extracted from config."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data={
                "config": {"provider": "gemini"},
                "system_prompt": "test prompt",
                "user_role": "小朋友",
                "ai_role": "老師",
                "scenario_context": "",
            },
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - Check that roles are stored in handler
        assert handler._user_role == "小朋友"
        assert handler._ai_role == "老師"

    @pytest.mark.asyncio
    async def test_handle_config_uses_default_roles_when_not_provided(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Test that default roles are used when not provided in config."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data={
                "config": {"provider": "gemini"},
                "system_prompt": "test prompt",
                # No user_role or ai_role provided
            },
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - Check that default roles are used
        assert handler._user_role == "使用者"
        assert handler._ai_role == "AI 助理"

    @pytest.mark.asyncio
    async def test_handle_config_sends_roles_in_response(
        self,
        handler: InteractionWebSocketHandler,
        mock_websocket: MagicMock,
        mock_repository: MagicMock,
    ) -> None:
        """Test that roles are included in the session_started response."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        # Make handler appear connected
        handler._connected = True
        from starlette.websockets import WebSocketState

        mock_websocket.client_state = WebSocketState.CONNECTED

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data={
                "config": {"provider": "gemini"},
                "system_prompt": "test prompt",
                "user_role": "學生",
                "ai_role": "教授",
            },
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - Check the sent message contains correct roles
        mock_websocket.send_json.assert_called()
        sent_payload = mock_websocket.send_json.call_args[0][0]

        assert sent_payload["type"] == "connected"
        assert sent_payload["data"]["status"] == "session_started"
        assert sent_payload["data"]["user_role"] == "學生"
        assert sent_payload["data"]["ai_role"] == "教授"

    @pytest.mark.asyncio
    async def test_handle_config_with_empty_string_roles_uses_defaults(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Test that empty string roles fall back to defaults (empty is falsy)."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data={
                "config": {"provider": "gemini"},
                "system_prompt": "test prompt",
                "user_role": "",  # Empty string - falsy, will use default
                "ai_role": "",  # Empty string - falsy, will use default
            },
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - Empty strings fall back to defaults (using 'or' operator)
        assert handler._user_role == "使用者"
        assert handler._ai_role == "AI 助理"

    @pytest.mark.asyncio
    async def test_handle_config_with_none_roles(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Test that None roles fall back to defaults."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data={
                "config": {"provider": "gemini"},
                "system_prompt": "test prompt",
                "user_role": None,
                "ai_role": None,
            },
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - None should fall back to defaults
        assert handler._user_role == "使用者"
        assert handler._ai_role == "AI 助理"

    @pytest.mark.asyncio
    async def test_handle_config_passes_roles_to_session_entity(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Test that roles are passed to InteractionSession entity."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data={
                "config": {"provider": "gemini"},
                "system_prompt": "test prompt",
                "user_role": "患者",
                "ai_role": "醫生",
            },
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - Check that create_session was called with correct roles
        mock_repository.create_session.assert_called_once()
        created_session = mock_repository.create_session.call_args[0][0]
        assert created_session.user_role == "患者"
        assert created_session.ai_role == "醫生"


class TestHandleConfigDataParsing:
    """Tests for verifying message.data parsing in _handle_config."""

    @pytest.fixture
    def mock_websocket(self) -> MagicMock:
        """Create a mock WebSocket."""
        ws = MagicMock()
        ws.client_state = MagicMock()
        ws.client_state.name = "CONNECTED"
        ws.send_json = AsyncMock()
        return ws

    @pytest.fixture
    def mock_mode_service(self) -> MagicMock:
        """Create a mock InteractionModeService."""
        service = MagicMock()
        service.mode_name = "realtime"
        service.is_connected = MagicMock(return_value=False)
        service.connect = AsyncMock()
        service.trigger_greeting = AsyncMock()
        return service

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock InteractionRepository."""
        repo = MagicMock()
        repo.create_session = AsyncMock()
        return repo

    @pytest.fixture
    def mock_audio_storage(self) -> MagicMock:
        """Create a mock AudioStorageService."""
        storage = MagicMock()
        storage.ensure_session_dir = AsyncMock()
        return storage

    @pytest.fixture
    def handler(
        self,
        mock_websocket: MagicMock,
        mock_mode_service: MagicMock,
        mock_repository: MagicMock,
        mock_audio_storage: MagicMock,
    ) -> InteractionWebSocketHandler:
        """Create a handler instance with mocked dependencies."""
        return InteractionWebSocketHandler(
            websocket=mock_websocket,
            user_id=uuid4(),
            mode_service=mock_mode_service,
            repository=mock_repository,
            audio_storage=mock_audio_storage,
        )

    @pytest.mark.asyncio
    async def test_message_data_structure_is_dict(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Verify that message.data is a dict with expected keys."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        # Simulate the exact data structure that frontend sends
        # Frontend: sendMessage('config', configPayload)
        # This becomes: { type: 'config', data: configPayload }
        # Backend parses: message.data = data.get('data', {})
        frontend_payload = {
            "config": {"provider": "gemini", "voice": "Kore"},
            "system_prompt": "你是老師",
            "user_role": "小朋友",
            "ai_role": "老師",
            "scenario_context": "",
            "barge_in_enabled": True,
            "lightweight_mode": True,
            "auto_greeting": False,
        }

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data=frontend_payload,  # This is what message.data should be
        )

        # Act
        await handler._handle_config(config_message)

        # Assert
        assert handler._user_role == "小朋友"
        assert handler._ai_role == "老師"

    @pytest.mark.asyncio
    async def test_data_get_returns_correct_values(
        self,
        handler: InteractionWebSocketHandler,
        mock_repository: MagicMock,
    ) -> None:
        """Test that data.get() returns the correct values for each key."""
        # Arrange
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_repository.create_session.return_value = mock_session

        test_data = {
            "config": {"provider": "gemini"},
            "system_prompt": "test",
            "user_role": "客戶",
            "ai_role": "客服",
            "scenario_context": "電話客服情境",
            "barge_in_enabled": False,
            "auto_greeting": True,
            "greeting_prompt": "您好，請問有什麼可以幫您？",
        }

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data=test_data,
        )

        # Act
        await handler._handle_config(config_message)

        # Assert - Verify all values are correctly extracted
        assert handler._user_role == "客戶"
        assert handler._ai_role == "客服"
        assert handler._barge_in_enabled is False
