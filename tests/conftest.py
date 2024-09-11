from __future__ import annotations

import boto3
import os
import pathlib
import pprint
import random
import string
from dataclasses import dataclass

import pytest
import ulid

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_chat_message import ChatMessage
from openbrain.orm.model_chat_session import ChatSession
# from openbrain.orm.model_lead import Lead
from tests.generator_agent_configs import generate_agent_config
from tests.generator_chat_messages import generate_chat_message
from tests.generator_chat_sessions import generate_chat_session
from tests.generator_clients import generate_client
from loguru import logger

# from tests.generator_leads import generate_lead

# load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PROMPTLAYER_API_KEY = os.environ.get("PROMPTLAYER_API_KEY")
DEV_OB_PROVIDER_API_KEY = os.environ.get("DEV_OB_PROVIDER_API_KEY")
PROD_OB_PROVIDER_API_KEY = os.environ.get("PROD_OB_PROVIDER_API_KEY")
STAGE = os.environ.get("STAGE", "dev")
# DEV_API_URL = os.environ.get("DEV_API_URL")
# PROD_API_URL = os.environ.get("PROD_API_URL")

# we'll reuse objects in dynamodb
pytest.CLIENT_ID = "test_client_id"
pytest.SESSION_ID = str(ulid.ULID().to_uuid())
pp = pprint.PrettyPrinter(indent=4, sort_dicts=True)

tests_dir = pathlib.Path(__file__).parent.absolute()
test_resources_dir = tests_dir / "resources" / "examples"

NUMBER_OF_SAMPLES = 2


class Secret:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "Secret(********)"

    def __str___(self):
        return "*******"


@pytest.fixture(scope="module")
def state():
    return {}


@pytest.fixture
def lambda_event():
    return {"test": "event"}


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()


@pytest.fixture
def headers():
    return {"x-api-key": DEV_OB_PROVIDER_API_KEY, "Content-Type": "application/json"}


@pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
def clean_agent_configs(request):
    return (generate_agent_config() for _ in range(request.param))


@pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
def dirty_agent_config(request):
    return (generate_agent_config(try_to_break_shit=True) for _ in range(request.param))


@pytest.fixture(scope="module")
def default_agent_config():
    return AgentConfig()


# @pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
# def clean_leads(request):
#     return (generate_lead() for _ in range(request.param))
#
#
# @pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
# def dirty_leads(request):
#     return (generate_lead(try_to_break_shit=True) for _ in range(request.param))

#
# @pytest.fixture(scope="module")
# def default_lead():
#     return Lead(client_id="lead_test_fixture")
#
#
# @pytest.fixture(scope="module")
# def simple_lead():
#     return Lead(
#         client_id="simple_lead_test_fixture",
#         session_id=str(ulid.ULID().to_uuid()),
#         full_name="Buck Futter",
#         state_of_residence="FL",
#         email_address="test@test.test",
#         phone="3134581546",
#         med_list=["aspirin", "motrin"],
#     )


@pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
def clean_chat_message(request):
    return (generate_chat_message() for _ in range(request.param))


@pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
def dirty_chat_message(request):
    return (generate_chat_message(try_to_break_shit=True) for _ in range(request.param))


@pytest.fixture(scope="module")
def default_chat_message():
    return ChatMessage()


@pytest.fixture(scope="module")
def simple_chat_message():
    message = "This is a simple test message, say something really stupid."
    chat_message = ChatMessage(message=message, client_id="public")
    return chat_message

@pytest.fixture(scope="module")
def simple_client():
    client = generate_client()
    return client

@pytest.fixture
def simple_chat_session(default_agent_config):
    # Randomly select 4 alphanumeric characters
    r_client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

    client_id = f"t_{r_client_id}"
    agent_config = default_agent_config
    # lead = simple_lead
    gpt_agent = GptAgent(agent_config=agent_config)
    agent_response = gpt_agent.handle_user_message("Hello!")
    assert agent_response is not None

    frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
    frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]
    # frozen_lead = gpt_agent.serialize()["frozen_lead"]

    chat_session = ChatSession(
        client_id=client_id,
        frozen_agent_memory=frozen_agent_memory,
        frozen_agent_config=frozen_agent_config,
        # frozen_lead=frozen_lead,
    )
    # Randomly select a test_case to create a unique ChatSession
    return chat_session


@pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
def clean_chat_session(request):
    return (generate_chat_session() for _ in range(request.param))


@pytest.fixture(scope="module", params=range(NUMBER_OF_SAMPLES))
def dirty_chat_session(request):
    return (generate_chat_session(try_to_break_shit=True) for _ in range(request.param))
