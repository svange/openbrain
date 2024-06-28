import contextlib
import datetime
# import datetime
import importlib
import inspect
import os
import pkgutil
import sys
from ast import literal_eval

import boto3
import pytest
from langchain.callbacks.base import BaseCallbackHandler

# import openbrain.tools.tool_send_lead_to_crm
from openbrain.agents.gpt_agent import GptAgent
# from openbrain.tools.models.event_lead import LeadEvent
from openbrain.orm.model_agent_config import AgentConfig
# from openbrain.orm.model_lead import Lead
from openbrain.tools.callback_handler import CallbackHandler
# from openbrain.tools.tool_send_lead_to_crm import send_event
from openbrain.tools.toolbox import Toolbox
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
# from openbrain.util import config, Defaults
from tests.generator_leadmo_contact import generate_leadmo_contact, generate_ai_leadmo_contact


@pytest.fixture
def tester_agent_config(default_agent_config):
    profile_name = "tester"
    system_message = "You are being tested for your ability to use tools. Use the tools available to you when appropriate."
    ice_breaker = "Hello, I am a test agent."
    tools = ["tester", "get_current_time"]

    agent_config = AgentConfig(profile_name=profile_name, system_message=system_message, ice_breaker=ice_breaker, tools=tools)

    return agent_config


@pytest.fixture
def lls_tool_tester_agent_config(default_agent_config):
    profile_name = "lls_tester"
    system_message = "You are being tested for your ability to use tools. Use the tools available to you when appropriate."
    ice_breaker = "Hello, I am a test agent."
    tools = ["lls_scrub_phone_number"]

    agent_config = AgentConfig(profile_name=profile_name, system_message=system_message, ice_breaker=ice_breaker, tools=tools)

    return agent_config


@pytest.fixture
def leadmo_tool_tester_agent_config():
    LEADMO_TOOL_TESTER_AGENT_SYSTEM_MESSAGE = '''You are testing your ability to use any tools available. When asked to trigger a tool, you will trigger the tool, generating appropriate values for testing, and report the success or failure or the tool. If the tool is succesful, ensure that your response contains the word success. If the tool fails, ensure that your response contains the word fail.'''
    LEADMO_TOOL_TESTER_AGENT_ICEBREAKER = '''Ready to test!'''

    agent_config = AgentConfig()
    agent_config.profile_name = "leadmo_tool_tester"
    agent_config.tools = ["leadmo_update_contact", "leadmo_create_contact", "leadmo_stop_conversation", "leadmo_get_simple_calendar_appointment_slots", "leadmo_create_appointment"]

    agent_config.profile_name = 'leadmo_tool_tester'
    agent_config.system_message = LEADMO_TOOL_TESTER_AGENT_SYSTEM_MESSAGE
    agent_config.icebreaker = LEADMO_TOOL_TESTER_AGENT_ICEBREAKER
    agent_config.executor_max_execution_time = 20
    agent_config.executor_max_iterations = 5

    return agent_config

@pytest.fixture
def event_bridge_client():
    client = boto3.client("events")
    return client


@pytest.fixture
def incoming_agent_config(default_agent_config):
    outgoing_agent_config = default_agent_config
    return outgoing_agent_config


@pytest.fixture
def incoming_lead(simple_lead):
    outgoing_lead = simple_lead
    return outgoing_lead


class TestAgentTools:
    """Test the GptAgent's tools."""

    @pytest.mark.tools
    def test_callback_handler_up_to_date(self):
        """Test that the callback handler protocol is up to date with langchain. If this test fails, find the langchain handler documentation, and add any missing functions to the protocol."""
        ob_callback_handler = CallbackHandler
        ob_callback_handler_functions = [
            func for func in dir(ob_callback_handler) if func.startswith("on_")
        ]

        lc_callback_handler = BaseCallbackHandler
        lc_callback_handler_functions = [
            func for func in dir(lc_callback_handler) if func.startswith("on_")
        ]

        funcs_missing_in_openbrain_callback_handler = []
        funcs_missing_in_langchain_callback_handler = []
        for function in lc_callback_handler_functions:
            if function not in ob_callback_handler_functions:
                funcs_missing_in_openbrain_callback_handler.append(function)

        for function in ob_callback_handler_functions:
            if function not in lc_callback_handler_functions:
                funcs_missing_in_langchain_callback_handler.append(function)

        assert len(funcs_missing_in_openbrain_callback_handler) == 0
        assert len(funcs_missing_in_langchain_callback_handler) == 0

    @pytest.mark.tools
    def test_protocol_up_to_date(self):
        """Test to ensure updates to the openbrain handler are always reflected in the protocol. If this test fails, find the missing parameters from the openbrain handler's class definition,and add any  missing parameters."""
        protocol_func = OBCallbackHandlerFunctionProtocol.__call__
        handler_func = CallbackHandler.__init__
        protocol_params = list(inspect.signature(protocol_func).parameters)
        handler_params = list(inspect.signature(handler_func).parameters)

        params_missing_in_protocol = []
        params_missing_in_handler = []
        for param in handler_params:
            if param not in protocol_params:
                params_missing_in_protocol.append(param)

        for param in protocol_params:
            if param not in handler_params:
                params_missing_in_handler.append(param)

        assert len(params_missing_in_protocol) == 0
        assert len(params_missing_in_handler) == 0

    @pytest.mark.tools
    def test_tools_are_registered(self):
        """Test that the tools are registered."""
        ob_modules = sys.modules["openbrain.tools"]
        # Dynamically import all submodules

        package = sys.modules[ob_modules.__package__]
        submodules = {
            name: importlib.import_module(ob_modules.__package__ + "." + name)
            for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)
        }

        # submodules = import_submodules(ob_modules.__package__)
        for submodule in submodules.values():
            for obj in inspect.getmembers(submodule):  # inspect.getmembers(submodule))
                # Broken down for troubleshooting
                with contextlib.suppress(KeyError, TypeError):
                    identified_class = obj[1]
                    Toolbox.register_available_obtool(identified_class)

        assert len(Toolbox.available_tools) > 0
        for tool_name, tool in Toolbox.available_tools.items():
            assert tool_name is not None
            assert tool is not None

    @pytest.mark.tools
    def test_tester_tool(self, tester_agent_config: AgentConfig):
        """Test the tester tool."""
        initial_context = {"random_word_from_agent_creation": "rambutan"}
        agent = GptAgent(agent_config=tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Your random word is banana.")
        assert "banana" in response
        assert "rambutan" in response

    @pytest.mark.tools
    def test_leadmo_create_contact_tool(self, leadmo_tool_tester_agent_config):
        initial_context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Create a contact.")
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    def test_leadmo_update_contact_tool(self, leadmo_tool_tester_agent_config):
        initial_context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Update the contact.")
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    def test_get_current_time_tool(self, tester_agent_config):
        initial_context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Get the current time.")
        assert response is not None
        current_year = datetime.datetime.now().year
        assert str(current_year) in response.casefold()


    @pytest.mark.tools
    def test_leadmo_create_appointment_tool(self, leadmo_tool_tester_agent_config):
        initial_context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Create an appointment.")
        assert response is not None
        assert "success" in response.casefold()

    @pytest.mark.tools
    def test_leadmo_stop_conversation_tool(self, leadmo_tool_tester_agent_config):
        initial_context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Stop the conversation.")
        assert response is not None
        assert "success" in response.casefold()


    @pytest.mark.tools
    @pytest.mark.skip
    def test_get_simple_calendar_appointment_slots_tool(self, leadmo_tool_tester_agent_config):
        initial_context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')
        initial_context['api_key'] = os.getenv('DEV_LEADMO_BEARER_TOKEN')
        initial_context['calendarId'] = 'asGgwlPqqu6s17W084uE'

        agent = GptAgent(agent_config=leadmo_tool_tester_agent_config, initial_context=initial_context)

        # get current_time from library
        current_time = datetime.datetime.now().isoformat()
        response = agent.handle_user_message(f"It is currently {current_time}. What appointment times do I have available in 3 days? If the tool triggerred successfully, ensure the word 'success' is in your response. If the tool fails, ensure the word 'success' is not in your respond, and instead, ensure the word 'fail' is in your response.")
        assert response is not None
        assert "success" in response.casefold()

    @pytest.mark.tools
    @pytest.mark.skip
    def test_lls_scrub_phone_number(self, lls_tool_tester_agent_config):
        initial_context = {
            "phone": "6194103847",
            "api_key": os.getenv('DEV_LLS_API_KEY')
        }

        agent = GptAgent(agent_config=lls_tool_tester_agent_config, initial_context=initial_context)
        response = agent.handle_user_message("Tell me if the phone number 6194103847 is on the 'do-not-call' list. If the tool succeeded, ensure the word 'success' is in your response. If the tool failed, ensure the word 'success' is not in your response, and instead, ensure the word 'fail' is in your response.")
        assert response is not None
        assert "success" in response.casefold()


    # @pytest.mark.tools
    # @pytest.mark.expected_failure
    # @pytest.mark.skip
    # def test_agent_send_to_crm_tool(
    #     self,
    #     incoming_agent_config: AgentConfig,
    #     incoming_lead: Lead,
    #     message="My name is Chad Geepeeti, my DOB is April 1, 1975. I live in Mississippi, and I currently take vicodin and tylonol. My phone number is 619-465-7894 and my email is e@my.ass. Please get me in touch with an agent immediately.",
    # ):
    #     """Send an event to the lead event stream by getting the agent to invoke the function."""
    #     openbrain.tools.tool_send_lead_to_crm.fake_event_bus = {}
    #     results_container = {}
    #
    #     def simple_mock(
    #         lead_event: LeadEvent, results_container: dict = results_container, *args, **kwargs
    #     ):
    #         event_bus_friendly_name = config.EVENTBUS_NAME
    #         event = [
    #             {
    #                 "EventBusName": event_bus_friendly_name,
    #                 "Source": Defaults.OB_TOOL_EVENT_SOURCE.value,
    #                 "DetailType": Defaults.OB_TOOL_EVENT_DETAIL_TYPE.value,
    #                 "Detail": lead_event.to_json(),
    #                 "Time": datetime.datetime.now().isoformat(),
    #             }
    #         ]
    #
    #         results_container["lead_event"] = lead_event
    #         results_container["event"] = event
    #         results_container["kwargs"] = kwargs
    #         return lead_event
    #
    #     openbrain.tools.tool_send_lead_to_crm.send_event = (
    #         simple_mock  # First mock ever... pretty fuckin powerful...
    #     )
    #     agent = GptAgent(agent_config=incoming_agent_config, lead=incoming_lead)
    #     # agent.tools[0]._run = simple_mock
    #
    #     response = agent.handle_user_message(message)
    #
    #     assert results_container is not None
    #     for key, value in results_container.items():
    #         assert key is not None
    #         assert value is not None
    #
    #     assert response is not None
    #     # TODO assert that response is a success messge
    #
    #     lead_event = results_container["lead_event"]
    #     assert lead_event is not None
    #     assert isinstance(lead_event, LeadEvent)
    #     assert lead_event.lead is not None
    #     assert lead_event.agent_config is not None
    #
    #     lead_from_lead_event = lead_event.lead
    #     for key, val in incoming_lead.to_dict().items():
    #         assert getattr(lead_from_lead_event, key) == val
