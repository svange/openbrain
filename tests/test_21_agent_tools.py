import contextlib
import datetime
import importlib
import inspect
import os
import pkgutil
import random
import sys
from decimal import Decimal

import boto3
import pytest
import pytz
import ulid
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
from tests.generator_leadmo_contact import generate_leadmo_contact


@pytest.fixture
def simple_tool_tester_agent_config(default_agent_config):
    profile_name = "tester"
    system_message = "You are being tested for your ability to use tools. Use the tools available to you when appropriate."
    ice_breaker = "Hello, I am a test agent."
    tools = ["input_and_context_tester", "get_current_time", "simple_calculator", "event_mesh_tester", "convert_to_from_utc"]
    record_tool_actions = True
    record_conversations = True

    agent_config = AgentConfig(profile_name=profile_name, system_message=system_message, ice_breaker=ice_breaker, tools=tools, record_tool_actions=record_tool_actions, record_conversations=record_conversations)

    return agent_config

@pytest.fixture
def session_id():
    session_id = 'test-ob-' + ulid.ULID().to_uuid().__str__()[9:-1]
    return session_id


@pytest.fixture
def lls_tool_tester_agent_config(default_agent_config):
    profile_name = "lls_tester"
    system_message = "You are being tested for your ability to use tools. Use the tools available to you when appropriate."
    ice_breaker = "Hello, I am a test agent."
    tools = ["lls_scrub_phone_number"]
    record_tool_actions = True
    record_conversations = True

    agent_config = AgentConfig(profile_name=profile_name, system_message=system_message, ice_breaker=ice_breaker, tools=tools, record_tool_actions=record_tool_actions, record_conversations=record_conversations)

    return agent_config


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
    def test_input_and_context_tester_tool(self, simple_tool_tester_agent_config: AgentConfig, session_id):
        """Test the tester tool."""
        context = {"random_word": "rambutan"}
        agent = GptAgent(agent_config=simple_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Your random word is banana.")
        assert "banana" in response
        assert "rambutan" in response

    @pytest.mark.tools
    def test_get_current_time_tool(self, simple_tool_tester_agent_config, session_id):
        context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Get the current year.")
        assert response is not None
        current_year = datetime.datetime.now().year
        assert str(current_year) in response.casefold()

    @pytest.mark.skip(reason="Known bug")
    @pytest.mark.tools
    def test_convert_to_from_utc(self, simple_tool_tester_agent_config, session_id):
        context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, context=context, session_id=session_id)
        timezone = "US/Pacific"
        pacific_tz = pytz.timezone(timezone)
        pacific_time_now = datetime.datetime.now(pacific_tz)
        pacific_time_hour = pacific_time_now.hour

        utc = pytz.utc
        utc_time_now = datetime.datetime.now(utc)
        utc_time_hour = utc_time_now.hour

        response = agent.handle_user_message(f"Convert {pacific_time_now} (US Pacific) to UTC and respond with only the hour")
        assert response is not None
        assert str(utc_time_hour) in response.casefold()


        agent = GptAgent(agent_config=simple_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message(f"Convert {utc_time_now} from UTC to US Pacific time")

        assert str(pacific_time_hour) in response.casefold()

    @pytest.mark.tools
    def test_event_mesh_tester_tool(self, simple_tool_tester_agent_config, session_id):
        context = generate_leadmo_contact(contact_id='8LDRBvYKbVyhXymqMurF', location_id='HbTkOpUVUXtrMQ5wkwxD')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Send an event to the event mesh and, if succesfull, respond with the word 'success' in your response and the event ID. If sending the event fails, don't use the word 'success' in your response")
        assert response is not None
        assert str('success') in response.casefold()

    @pytest.mark.tools
    def test_simple_calculator_tool(self, simple_tool_tester_agent_config, session_id):
        left_number = Decimal(random.randint(-10000, 10000))
        right_number = Decimal(random.randint(-10000, 10000))
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} + {right_number}.")
        # assert response is not None
        # assert str(left_number + right_number) in response.casefold().replace(',', '')
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} - {right_number}.")
        # assert response is not None
        # result = left_number - right_number
        # assert str(result) in response.casefold().replace(',', '')
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} * {right_number}.")
        # assert response is not None
        # result = left_number * right_number
        # assert str(result) in response.casefold().replace(',', '')
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} / {right_number}.")
        # assert response is not None
        # result = left_number / right_number
        # assert str(result)[:4] in response.casefold().replace(',', '')
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} // {right_number}.")
        # assert response is not None
        # result = left_number // right_number
        # assert str(result) in response.casefold().replace(',', '')
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} % {right_number}.")
        # assert response is not None
        # result = left_number % right_number
        # assert str(result) in response.casefold().replace(',', '')
        #
        # agent = GptAgent(agent_config=simple_tool_tester_agent_config)
        # response = agent.handle_user_message(f"Calculate {left_number} ** {right_number}.")
        # assert response is not None
        # result = left_number ** right_number
        # assert str(result)[:4] in response.casefold().replace(',', '')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, session_id=session_id)
        response = agent.handle_user_message(f"Calculate the square root of {abs(left_number)}.")
        assert response is not None
        result = abs(left_number).sqrt()
        assert str(result)[:4] in response.casefold().replace(',', '')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, session_id=session_id)
        response = agent.handle_user_message(f"Calculate {left_number} cubed.")
        assert response is not None
        result = left_number ** Decimal(3)
        assert str(result) in response.casefold().replace(',', '')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, session_id=session_id)
        response = agent.handle_user_message(f"Calculate the inverse of {left_number}.")
        assert response is not None
        result = Decimal(1) / left_number
        assert str(result)[:4] in response.casefold().replace(',', '')

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, session_id=session_id)
        response = agent.handle_user_message(f"Calculate the negation of {left_number}.")
        assert response is not None
        result = -left_number
        assert str(result) in response.casefold().replace(',', '')

    @pytest.mark.tools
    @pytest.mark.xfail(reason="This fills up the context windows and gets the AI to fail to use tools correctly")
    def test_simple_calculator_tool_overload_context(self, simple_tool_tester_agent_config, session_id):
        left_number = Decimal(random.randint(-10000, 10000))
        right_number = Decimal(random.randint(-10000, 10000))

        agent = GptAgent(agent_config=simple_tool_tester_agent_config, session_id=session_id)
        response = agent.handle_user_message(f"Calculate {left_number} + {right_number}.")
        assert response is not None
        assert str(left_number + right_number) in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} - {right_number}.")
        assert response is not None
        result = left_number - right_number
        assert str(result) in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} * {right_number}.")
        assert response is not None
        result = left_number * right_number
        assert str(result) in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} / {right_number}.")
        assert response is not None
        result = left_number / right_number
        assert str(result)[:4] in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} // {right_number}.")
        assert response is not None
        result = left_number // right_number
        assert str(result) in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} % {right_number}.")
        assert response is not None
        result = left_number % right_number
        assert str(result) in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} ** {right_number}.")
        assert response is not None
        result = left_number ** right_number
        assert str(result)[:4] in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate the square root of {left_number}.")
        assert response is not None
        result = left_number ** Decimal(0.5)
        assert str(result)[:4] in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate {left_number} cubed.")
        assert response is not None
        result = left_number ** Decimal(3)
        assert str(result) in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate the inverse of {left_number}.")
        assert response is not None
        result = Decimal(1) / left_number
        assert str(result)[:4] in response.casefold().replace(',', '')

        response = agent.handle_user_message(f"Calculate the negation of {left_number}.")
        assert response is not None
        result = -left_number
        assert str(result) in response.casefold().replace(',', '')



    @pytest.mark.tools
    @pytest.mark.skip("LLS currently inop")
    def test_lls_scrub_phone_number(self, lls_tool_tester_agent_config, session_id):
        context = {
            "phone": "6194103847",
            "api_key": os.getenv('DEV_LLS_API_KEY')
        }

        agent = GptAgent(agent_config=lls_tool_tester_agent_config, context=context, session_id=session_id)
        response = agent.handle_user_message("Tell me if the phone number 6194103847 is on the 'do-not-call' list. If the tool succeeded, ensure the word 'success' is in your response. If the tool failed, ensure the word 'success' is not in your response, and instead, ensure the word 'fail' is in your response.")
        assert response is not None
        assert "success" in response.casefold()

