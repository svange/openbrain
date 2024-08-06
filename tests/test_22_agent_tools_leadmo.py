import datetime
import os

import pytest
import ulid

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_agent_config import AgentConfig
from tests.conftest import Secret, logger
from tests.generator_leadmo_contact import generate_leadmo_contact


@pytest.fixture
def leadmo_tool_tester_agent_config():
    LEADMO_TOOL_TESTER_AGENT_SYSTEM_MESSAGE = '''You are testing your ability to use any tools available. When asked to trigger a tool, you will trigger the tool, generating appropriate values for testing, and report the success or failure or the tool. If the tool is succesful, ensure that your response contains the word success. If the tool fails, ensure that your response contains the word fail.'''
    LEADMO_TOOL_TESTER_AGENT_ICEBREAKER = '''Ready to test!'''

    agent_config = AgentConfig()
    agent_config.profile_name = "leadmo_tool_tester"
    agent_config.tools = ["leadmo_update_contact", "leadmo_create_contact", "leadmo_stop_conversation", "leadmo_get_simple_calendar_appointment_slots", "leadmo_create_appointment", "leadmo_get_contact_info_from_context"]
    agent_config.record_tool_actions = True
    agent_config.record_conversations = True

    agent_config.profile_name = 'leadmo_tool_tester'
    agent_config.system_message = LEADMO_TOOL_TESTER_AGENT_SYSTEM_MESSAGE
    agent_config.icebreaker = LEADMO_TOOL_TESTER_AGENT_ICEBREAKER
    agent_config.executor_max_execution_time = 20
    agent_config.executor_max_iterations = 5

    return agent_config


@pytest.fixture
def session_id():
    session_id = 'test-ob-' + ulid.ULID().to_uuid().__str__()[9:-1]
    return session_id


@pytest.fixture(scope="module")
def safe_leadmo_user():
    safe_user = {
        "email": "test@augmentingintegrations.com",
        "phone": "+16197966726",
        "first_name": "Augmenting",
        "last_name": "Integrations",
        "name": "Augmenting Integrations",
        "address1": "123 Fake St.",
        "city": "San Diego",
        "state": "CA",
        "postal_code": "92123",
        "website": "https://augmentingintegrations.com",
        # "timezone": "US/Pacific",
        "dnd": "true",
        "tags": ["test"],
        # custom_field="",
        # source="",
    }
    return safe_user

@pytest.fixture
def leadmo_location_id():
    return os.getenv("LEADMO_LOCATION_ID")

@pytest.fixture
def leadmo_calendar_id():
    return os.getenv("LEADMO_CALENDAR_ID")

@pytest.fixture
def leadmo_api_key():
    return Secret(os.getenv("LEADMO_BEARER_TOKEN"))


class TestAgentTools:
    """Test the GptAgent's tools."""


    @pytest.mark.tools
    def test_get_simple_calendar_appointment_slots_tool(self, leadmo_tool_tester_agent_config, session_id, state, leadmo_calendar_id, safe_leadmo_user, leadmo_location_id, leadmo_api_key):
        context = safe_leadmo_user
        context["locationId"] = leadmo_location_id
        context['calendarId'] = leadmo_calendar_id
        context['api_key'] = leadmo_api_key.value

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, context=context, session_id=session_id)

        # get current_time from library
        current_time = datetime.datetime.now().isoformat()
        response = agent.handle_user_message(f"It is currently {current_time}. What appointment times do I have available in 3 days? If the tool triggerred successfully, ensure the word 'success' is in your response. If the tool fails, ensure the word 'success' is not in your respond, and instead, ensure the word 'fail' is in your response.")
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    def test_leadmo_create_appointment_tool(self, leadmo_tool_tester_agent_config, session_id, state, leadmo_calendar_id, safe_leadmo_user, leadmo_location_id, leadmo_api_key):
        context = safe_leadmo_user
        context["locationId"] = leadmo_location_id
        context['calendarId'] = leadmo_calendar_id
        context['api_key'] = leadmo_api_key.value

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Create an appointment. for tomorrow at 1500 UTC")
        logger.info(response)
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    def test_leadmo_create_contact_tool(self, leadmo_tool_tester_agent_config, session_id, state, leadmo_calendar_id, safe_leadmo_user, leadmo_location_id, leadmo_api_key):
        context = safe_leadmo_user
        context["locationId"] = leadmo_location_id
        context['calendarId'] = leadmo_calendar_id
        context['api_key'] = leadmo_api_key.value

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Create a contact.")
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    def test_leadmo_update_contact_tool(self, leadmo_tool_tester_agent_config, session_id, state, leadmo_calendar_id, safe_leadmo_user, leadmo_location_id, leadmo_api_key):
        context = safe_leadmo_user
        context["locationId"] = leadmo_location_id
        context['calendarId'] = leadmo_calendar_id
        context['api_key'] = leadmo_api_key.value

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Update the contact.")
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    def test_leadmo_stop_conversation_tool(self, leadmo_tool_tester_agent_config, session_id, state, leadmo_calendar_id, safe_leadmo_user, leadmo_location_id, leadmo_api_key):
        context = safe_leadmo_user
        context["locationId"] = leadmo_location_id
        context['calendarId'] = leadmo_calendar_id
        context['api_key'] = leadmo_api_key.value

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Stop the conversation.")
        assert response is not None
        assert "success" in response.casefold()

    @pytest.mark.tools
    def test_get_contact_info_from_context(self, leadmo_tool_tester_agent_config, session_id, state, leadmo_calendar_id, safe_leadmo_user, leadmo_location_id, leadmo_api_key):
        context = safe_leadmo_user
        context["locationId"] = leadmo_location_id
        context['calendarId'] = leadmo_calendar_id
        context['api_key'] = leadmo_api_key.value

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("What's my first name?")
        assert response is not None
        first_name = str.casefold(context['first_name'])
        assert str(first_name) in response.casefold()
