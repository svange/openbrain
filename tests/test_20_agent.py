from __future__ import annotations

import os

import pytest
import retry
from langchain.schema import BaseMemory

import app
from chalicelib.gpt_agent import GptAgent
from chalicelib.orm.model_agent_config import AgentConfig
from chalicelib.orm.model_chat_message import ChatMessage
from chalicelib.orm.model_lead import Lead


@pytest.fixture
def incoming_agent_config(default_agent_config):
    outgoing_agent_config = default_agent_config
    return outgoing_agent_config


@pytest.fixture
def incoming_lead(simple_lead):
    outgoing_lead = simple_lead
    return outgoing_lead


class TestAgent:
    @retry.retry(delay=1, tries=5)
    @pytest.mark.integration_tests
    def test_gpt_agent_creation(self, incoming_agent_config: AgentConfig, incoming_lead: Lead):
        gpt_agent = GptAgent(incoming_agent_config)
        assert True

        response = gpt_agent.handle_user_message("Hello")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        # assert isinstance(type(returned_lead), type(unique_lead)) # TODO, types coming in wrong

    @retry.retry(delay=1, tries=2)
    @pytest.mark.integration_tests
    def test_serialize_deserialize_agent(
            self, incoming_agent_config: AgentConfig, incoming_lead: Lead
    ):
        # unique_agent_config = agent_config_fixture
        gpt_agent = GptAgent(agent_config=incoming_agent_config, lead=incoming_lead)
        response_message = gpt_agent.handle_user_message(
            "I see 25 blue birds!"
        )

        serialized_agent = gpt_agent.serialize()
        assert serialized_agent is not None
        assert serialized_agent["frozen_agent_memory"] is not None
        assert serialized_agent["frozen_agent_config"] is not None
        assert len(serialized_agent) > 0
        assert isinstance(serialized_agent, dict)
        assert isinstance(serialized_agent["frozen_agent_memory"], bytes)
        assert isinstance(serialized_agent["frozen_agent_config"], str)

        # deserialize the agent
        deserialized_agent = GptAgent.deserialize(serialized_agent)
        assert deserialized_agent is not None
        assert deserialized_agent.agent_config is not None
        assert deserialized_agent.working_memory is not None

        assert isinstance(deserialized_agent, GptAgent)
        assert isinstance(deserialized_agent.agent_config, AgentConfig)
        assert isinstance(deserialized_agent.working_memory, BaseMemory)

        # chat with the agent
        response_message = deserialized_agent.handle_user_message(
            user_message="How many birds did I tell you I saw?"
        )
        assert response_message is not None
        assert len(response_message) > 0
        assert isinstance(response_message, str)
        assert (
                "25" in response_message
                or "twenty-five" in response_message
                or "twenty five" in response_message
                or "DISCONNECTED" in response_message
        )

    @pytest.mark.integration_tests
    def test_reset_session(self, lambda_context, lambda_event) -> None:
        """Reset the session."""
        agent_config = AgentConfig()
        client_id = "test_reset_session"
        reset = True

        chat_message = ChatMessage(
            client_id=client_id,
            reset=reset,
            agent_config_overrides=agent_config,
        )

        response = app.reset_session(
            client_id=chat_message.client_id,
            processed_overrides=chat_message.agent_config_overrides,
        )
        response_message = response["message"]
        session_id = response["session_id"]

        # Assert the response is correct
        assert response_message is not None
        assert isinstance(response_message, str)
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert response_message == chat_message.agent_config_overrides.icebreaker
        # TODO test the icebreaker and other attributes
        # TODO test the session cookie
        self.session_id = session_id
        self.client_id = client_id

    @pytest.mark.integration_tests
    def test_process_user_message(self, lambda_context, lambda_event,
                                  message="Output only the string 'test passed' and nothing else"
                                  ):
        self.test_reset_session(lambda_context, lambda_event)
        session_id = self.session_id
        client_id = self.client_id
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert client_id is not None
        assert isinstance(client_id, str)
        assert len(client_id) > 0

        reset = False
        chat_message = ChatMessage(
            client_id=client_id,
            message=message,
            session_id=session_id,
            reset=reset,
        )

        response = app.process_user_message(
            session_id=chat_message.session_id,
            client_id=chat_message.client_id,
            message=chat_message.message,
        )

        response_message = response["message"]
        session_id = response["session_id"]

        # Assert the response is correct
        assert response_message is not None
        assert isinstance(response_message, str)
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        assert (
            response_message == "DISCONNECTED"
            if os.environ.get("stage") == "local"
            else response_message == "test passed"
        )

    @pytest.mark.integration_tests
    def test_introduction(self, lambda_context, lambda_event,
                          message: str = "Hello, my name is Buck Futter and my favorite food is sliced oranges!"
                          ):
        self.test_reset_session(lambda_context, lambda_event)
        session_id = self.session_id
        client_id = self.client_id

        response = app.process_user_message(
            session_id=session_id,
            client_id=client_id,
            message=message,
        )

        response_message = response["message"]
        session_id = response["session_id"]

        # Assert the response is correct
        assert response_message is not None
        assert isinstance(response_message, str)
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # assert response_message == "DISCONNECTED" if os.environ.get('stage') == 'local' else response_message == "test passed"
        # TODO test the session cookie
        # TODO test for the overlay functionality.

    @pytest.mark.integration_tests
    def test_1_memory(self, lambda_context, lambda_event, message: str = "What's my name?"):
        self.test_introduction(lambda_context, lambda_event)
        session_id = self.session_id
        client_id = self.client_id

        chat_message = ChatMessage(
            client_id=client_id,
            message=message,
            session_id=session_id,
            reset=False,
        )

        response = app.process_user_message(
            session_id=chat_message.session_id,
            client_id=chat_message.client_id,
            message=chat_message.message,
        )

        response_message = response["message"]
        session_id = response["session_id"]

        # Assert the response is correct
        assert response_message is not None
        assert isinstance(response_message, str)
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        if os.environ.get("stage") == "local":
            assert response_message == "DISCONNECTED"
        else:
            assert "futter".casefold() in response_message.casefold()
        # TODO test the session cookie
        # TODO test for the overlay functionality.

    @pytest.mark.integration_tests
    def test_2_message_memory(self, lambda_context, lambda_event, message: str = "What's my favorite food?"):
        self.test_1_memory(lambda_context, lambda_event)
        session_id = self.session_id
        client_id = self.client_id

        chat_message = ChatMessage(
            client_id=client_id,
            message=message,
            session_id=session_id,
            reset=False,
        )

        response = app.process_user_message(
            session_id=chat_message.session_id,
            client_id=chat_message.client_id,
            message=chat_message.message,
        )

        response_message = response["message"]
        session_id = response["session_id"]

        # Assert the response is correct
        assert response_message is not None
        assert isinstance(response_message, str)
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        if os.environ.get("stage") == "local":
            assert response_message == "DISCONNECTED"
        else:
            assert "orange" in response_message

        # TODO test the session cookie
        # TODO test for the overlay functionality.
