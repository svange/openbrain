from __future__ import annotations

import json

import pytest
import retry
from langchain.schema import BaseMemory

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_chat_session import ChatSession
from openbrain.orm.model_lead import Lead


@pytest.fixture
def incoming_chat_session(simple_chat_session):
    outgoing_chat_session = simple_chat_session
    return outgoing_chat_session


@pytest.mark.orm_tests
def test_chat_session(incoming_chat_session):
    chat_session = incoming_chat_session

    # Assert that the client_id is not None
    assert chat_session.client_id is not None

    # Assert that the session_id is not None
    assert chat_session.session_id is not None

    # Create a copy then assert equality
    copied_chat_session = ChatSession(**chat_session.to_dict())
    assert copied_chat_session == chat_session

    # Assert that the copy is not the same object
    assert copied_chat_session is not chat_session

    # Change the copy and confirm inequality
    copied_chat_session.client_id = "Different"
    assert copied_chat_session != chat_session


@pytest.mark.orm_tests
def test_chat_session_save_retrieve(incoming_chat_session):
    save_response = incoming_chat_session.save()
    assert (
            save_response is not None
    )  # Add more robust checks based on your DynamoDB response structure

    # 2. Retrieve the saved AgentConfig from DynamoDB
    retrieved_chat_session = ChatSession.get(
        session_id=incoming_chat_session.session_id, client_id=incoming_chat_session.client_id
    )
    assert retrieved_chat_session is not None

    for key, value in incoming_chat_session.to_dict().items():
        original_value = value
        retrieved_value = getattr(retrieved_chat_session, key)
        assert original_value == retrieved_value

        original_type = type(original_value)
        retrieved_type = type(retrieved_value)
        assert original_type == retrieved_type

    # 4. Use == to assert equality between the original and retrieved AgentConfigs
    assert incoming_chat_session == retrieved_chat_session
    assert incoming_chat_session is not retrieved_chat_session


@pytest.mark.orm_tests
@retry.retry(delay=1, tries=2)
def test_chat_session_session_id(incoming_chat_session: ChatSession):
    """Test that the session_id is generated as a uuid"""
    # Assert that the session_id is a uuid
    assert incoming_chat_session.session_id is not None
    assert isinstance(incoming_chat_session.session_id, str)
    assert len(incoming_chat_session.session_id) > 0

    # Save the chat session, then retrieve it into a new instance, and assert that the session_id is the same
    incoming_chat_session.save()
    retrieved_chat_session = ChatSession.get(
        session_id=incoming_chat_session.session_id, client_id=incoming_chat_session.client_id
    )
    assert incoming_chat_session.session_id == retrieved_chat_session.session_id


@pytest.mark.orm_tests
def test_get_agent_from_chat_session(incoming_chat_session):
    incoming_chat_session.save()

    retrieved_chat_session = ChatSession.get(
        session_id=incoming_chat_session.session_id, client_id=incoming_chat_session.client_id
    )
    assert retrieved_chat_session is not None
    assert isinstance(retrieved_chat_session, ChatSession)
    assert isinstance(retrieved_chat_session.frozen_agent_memory, bytes)
    assert isinstance(retrieved_chat_session.frozen_agent_config, str)
    assert isinstance(retrieved_chat_session.frozen_lead, str)
    assert isinstance(retrieved_chat_session.client_id, str)
    assert isinstance(retrieved_chat_session.session_id, str)

    client_id = retrieved_chat_session.client_id
    session_id = retrieved_chat_session.session_id
    agent_state = {
        "frozen_agent_memory": retrieved_chat_session.frozen_agent_memory,
        "frozen_agent_config": retrieved_chat_session.frozen_agent_config,
        "frozen_lead": retrieved_chat_session.frozen_lead,
    }
    agent = GptAgent.deserialize(state=agent_state)
    frozen_lead = json.loads(retrieved_chat_session.frozen_lead)
    lead = Lead(**frozen_lead)

    assert agent is not None
    assert isinstance(agent, GptAgent)
    # assert isinstance(agent.agent_config, AgentConfig)
    assert agent.agent_config.__class__ == agent.agent_config.__class__
    assert isinstance(agent.working_memory, BaseMemory)
    assert isinstance(lead, Lead)
    assert isinstance(client_id, str)
    assert isinstance(session_id, str)

    assert retrieved_chat_session.client_id == client_id
    assert retrieved_chat_session.session_id == session_id

    assert retrieved_chat_session.session_id == incoming_chat_session.session_id
    assert retrieved_chat_session.client_id == incoming_chat_session.client_id
    assert retrieved_chat_session.frozen_agent_memory == incoming_chat_session.frozen_agent_memory
    assert retrieved_chat_session.frozen_agent_config == incoming_chat_session.frozen_agent_config
    assert retrieved_chat_session.frozen_lead == incoming_chat_session.frozen_lead
    assert retrieved_chat_session == incoming_chat_session

#
# def test_chat_session(unique_agent_config: AgentConfig, unique_lead: Lead) -> None:
#     """Test that we can use the agent with a chat session"""
#     # client_id: str
#     #
#     # # We just take in an agent, but save it like this
#     # frozen_agent_memory: bytes
#     # frozen_agent_config: str
#     # # serialized_agent = JSONAttribute()
#     # frozen_lead: Optional[str] = None
#     # session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
#
#     agent_config = unique_agent_config
#     lead = unique_lead
#
#     agent = GptAgent(agent_config)
#     frozen_agent_memory = agent.serialize()["frozen_agent_memory"]
#     frozen_agent_config = agent.serialize()["frozen_agent_config"]
#     frozen_lead = lead.to_json()
#
#     chat_session = ChatSession(
#         client_id="test_chat_session",
#         frozen_agent_memory=frozen_agent_memory,
#         frozen_agent_config=frozen_agent_config,
#         frozen_lead=frozen_lead,
#     )
#
#     assert chat_session.client_id is not None
