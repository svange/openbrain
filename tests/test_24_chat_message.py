from __future__ import annotations

import json

import pytest

from openbrain.orm.model_chat_message import AgentConfig, ChatMessage


@pytest.fixture
def incoming_chat_message(simple_chat_message):
    outgoing_chat_message = simple_chat_message
    return outgoing_chat_message


class TestChatMessage:
    @pytest.mark.orm_tests
    def test_chat_message(self, incoming_chat_message):
        chat_message = incoming_chat_message
        client_id = chat_message.client_id
        session_id = chat_message.session_id
        reset = chat_message.reset
        agent_config = chat_message.agent_config_overrides
        message = chat_message.message

        # Assert that the client_id is not None
        if chat_message.client_id:
            assert isinstance(chat_message.client_id, str)
            assert chat_message.client_id == client_id

        # Assert that the session_id is not None
        if chat_message.session_id:
            assert isinstance(chat_message.session_id, str)
            assert chat_message.session_id == session_id

        # Assert that the reset is not None
        if chat_message.reset:
            assert isinstance(chat_message.reset, bool)
            assert chat_message.reset == reset

        # Assert that the agent_config is not None
        if chat_message.agent_config_overrides:
            assert isinstance(chat_message.agent_config_overrides, AgentConfig)
            assert chat_message.agent_config_overrides == agent_config

        # Assert that the message is not None
        if chat_message.agent_config:
            assert isinstance(chat_message.message, str)
            assert chat_message.message == message

        # If an AgentConfig is present, assert its profile_name is not None
        if chat_message.agent_config_overrides:
            assert chat_message.client_id is not None

        # Create a copy then assert equality
        serialized_chat_message = chat_message.to_json()

        copied_chat_message = ChatMessage.from_json(serialized_chat_message)

        assert copied_chat_message == chat_message

        # Assert that the copy is not the same object
        assert copied_chat_message is not chat_message

        # Change the copy and confirm inequality
        copied_chat_message.client_id = "Different"
        assert copied_chat_message != chat_message

    @pytest.mark.orm_tests
    def test_serialize_chat_message(self, incoming_chat_message):
        chat_message = incoming_chat_message
        serialized_chat_message = chat_message.to_json()
        assert serialized_chat_message is not None
        assert isinstance(serialized_chat_message, str)
        assert len(serialized_chat_message) > 0

        deserialized_chat_message = ChatMessage(**json.loads(serialized_chat_message))
        assert deserialized_chat_message == chat_message
        assert deserialized_chat_message is not chat_message
        assert deserialized_chat_message.client_id == chat_message.client_id
        assert deserialized_chat_message.message == chat_message.message
        assert deserialized_chat_message.reset == chat_message.reset
