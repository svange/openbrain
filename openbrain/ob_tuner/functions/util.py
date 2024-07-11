import datetime
import os
import pathlib
import boto3
import gradio as gr

import openbrain.orm
import openbrain.util
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_common_base import InMemoryDb
from openbrain.util import config, Defaults
from openbrain.tools import Toolbox

import logging

from io import StringIO
INFRA_STACK_NAME = os.environ.get("INFRA_STACK_NAME")
log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.INFO, format="%(levelname)s :: %(message)s")
logger = logging.getLogger("Gradio")

OB_MODE = config.OB_MODE
CHAT_ENDPOINT = os.environ.get("OB_API_URL", "") + "/chat"

DEFAULT_ORIGIN = os.environ.get("DEFAULT_ORIGIN", "https://localhost:5173")
OB_PROVIDER_API_KEY = os.environ.get("GRADIO_OB_PROVIDER_API_KEY", "")
GRADIO_PASSWORD = os.environ.get("GRADIO_PASSWORD", None)
DEFAULT_CLIENT_ID: str = Defaults.DEFAULT_CLIENT_ID.value
DEFAULT_PROFILE_NAME = Defaults.DEFAULT_PROFILE_NAME.value
PORT = int(os.environ.get("GRADIO_PORT", 7860))
logger.info(("-" * 60) + "PROGRAM INITIALIZING" + ("-" * 60))

aws_region = config.AWS_REGION
aws_profile = os.environ.get("AWS_PROFILE", "UNKNOWN")
obfuscated_api_key = OB_PROVIDER_API_KEY[:2] + "*" * (len(OB_PROVIDER_API_KEY) - 4) + OB_PROVIDER_API_KEY[-2:]
obfuscated_password = GRADIO_PASSWORD[:2] + "*" * (len(GRADIO_PASSWORD) - 4) if GRADIO_PASSWORD else None

logger.info(f"AWS_REGION: {aws_region}")
logger.info(f"AWS_PROFILE: {aws_profile}")
logger.info(f"OB_MODE: {OB_MODE}")

logger.info(f"OB_PROVIDER_API_KEY: {obfuscated_api_key}")
logger.info(f"GRADIO_PASSWORD: {obfuscated_password}")

logger.info(f"CHAT_ENDPOINT: {CHAT_ENDPOINT}")
logger.info(f"DEFAULT_ORIGIN: {DEFAULT_ORIGIN}")
logger.info(f"PORT: {PORT}")

logger.info(f"INFRA_STACK_NAME: {config.INFRA_STACK_NAME}")
logger.info(f"SESSION_TABLE_NAME: {config.SESSION_TABLE_NAME}")
logger.info(f"AGENT_CONFIG_TABLE_NAME: {config.AGENT_CONFIG_TABLE_NAME}")
logger.info(f"ACTION_TABLE_NAME: {config    .ACTION_TABLE_NAME}")

logger.info(("-" * 60) + "PROGRAM RUNNING" + ("-" * 60))

print(log_stream.getvalue(), flush=True)


tool_names = [tool.name for tool in Toolbox.discovered_tools if not tool.name.startswith("leadmo_")]
leadmo_tool_names = [tool.name for tool in Toolbox.discovered_tools if tool.name.startswith("leadmo_")]

tool_names.sort()
leadmo_tool_names.sort()
TOOL_NAMES = tool_names + leadmo_tool_names
logger.info(f"Tool names: {TOOL_NAMES}")

if OB_MODE == Defaults.OB_MODE_LOCAL.value:
    pass

def get_debug_text(_debug_text=None) -> str:
    try:
        ret = log_stream.getvalue()
    except Exception as e:
        ret = e.__str__()

    if _debug_text:
        _debug_text = ret

    return ret


def get_aws_xray_trace_summaries(id=None):
    """Get x-ray logs from AWS"""
    client = boto3.client("xray")
    this_year = datetime.datetime.now().year
    this_month = datetime.datetime.now().month
    this_day = datetime.datetime.now().day
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).day

    if id:
        response = client.get_trace_summaries(
            StartTime=datetime.datetime(this_year, this_month, yesterday),
            EndTime=datetime.datetime(this_year, this_month, this_day),
            Sampling=False,
            FilterExpression=f"traceId = {id}",
        )
    else:
        response = client.get_trace_summaries(
            StartTime=datetime.datetime(this_year, this_month, yesterday),
            EndTime=datetime.datetime(this_year, this_month, this_day),
            Sampling=False,
        )

    return response


def is_settings_set():
    return True


def get_tool_description(tool_name):
    for tool in Toolbox.discovered_tools:
        if tool_name == tool.name:
            tool_instance = tool.tool()
            tool_description = tool_instance.description
            fields = tool_instance.args_schema.model_fields
            args_string = ""
            if not fields:
                args_string = "'No args'"
            for field in fields:
                field_str = fields[field].__str__()
                args_string += f"{field}: {field_str}\n"
            tool_description = f"""#### Description
{tool_description}

#### Args
```python
{args_string}
```"""
            return tool_description


def get_available_tool_descriptions():
    tool_descriptions = []

    for tool in Toolbox.discovered_tools:
        tool_name = tool.name
        tool_instance = tool.tool()
        tool_description = tool_instance.description
        fields = tool_instance.args_schema.model_fields
        args_string = ""
        if not fields:
            args_string = "'No args'"
        for field in fields:
            field_str = fields[field].__str__()
            args_string += f"{field}: {field_str}\n"
        tool_description = f"""
## Tool: {tool_name}

#### Description
{tool_description}

#### Args
```python
{args_string}
```
---"""

        tool_descriptions.append(tool_description)

    tool_descriptions_string = "\n".join(tool_descriptions)
    return tool_descriptions_string


def get_available_profile_names(client_id=DEFAULT_CLIENT_ID) -> list:
    logger.info("Getting available profile names...")
    # logger.warning("get_available_profile_names() is not implemented")
    # Get AgentConfig table

    if OB_MODE == Defaults.OB_MODE_LOCAL.value:
        try:
            lst = list(InMemoryDb.instance[config.AGENT_CONFIG_TABLE_NAME][client_id].keys())
            return lst
        except Exception:
            default_config = AgentConfig(client_id=client_id, profile_name=DEFAULT_PROFILE_NAME)
            default_config.save()
            lst = list(InMemoryDb.instance[config.AGENT_CONFIG_TABLE_NAME][client_id].keys())
            return lst
    else:
        table = boto3.resource("dynamodb").Table(config.AGENT_CONFIG_TABLE_NAME)
        # get all items in the table
        try:
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('client_id').eq(client_id)
            )
        except Exception as e:
            logger.error(f"Error getting available profile names: {e}")
            return []

        return response["Items"]


def update_available_profile_names(client_id=DEFAULT_CLIENT_ID):
    available_profiles = get_available_profile_names(client_id)
    available_profile_names = [profile["profile_name"] for profile in available_profiles]
    return gr.Dropdown(choices=available_profile_names, value="")


def get_llm_choices(llm_types=None):
    """Get the available LLM choices based on the selected types"""
    if not llm_types:
        llm_types = ["function"]
    available_llms = []
    known_llm_types = openbrain.orm.model_agent_config.EXECUTOR_MODEL_TYPES
    for llm_type in llm_types:
        if llm_type == "function":
            available_llms += openbrain.orm.model_agent_config.FUNCTION_LANGUAGE_MODELS
        elif llm_type == "chat":
            available_llms += openbrain.orm.model_agent_config.CHAT_LANGUAGE_MODELS
        elif llm_type == "completion":
            available_llms += openbrain.orm.model_agent_config.COMPLETION_LANGUAGE_MODELS
        else:
            logger.error(f"Unknown LLM type: {llm_type}, must be one of {known_llm_types}")
            continue
    return gr.Dropdown(choices=available_llms)


def greet(request: gr.Request):
    try:
        return f"Welcome to Gradio, {request.username}"
    except Exception:
        return "OH NO!"


def initialize_username(request: gr.Request, _session_state):
    username = request.username
    _session_state["username"] = username
    return [username, _session_state]


def get_session_username(_session_state=None):
    _base_choices = [DEFAULT_CLIENT_ID]
    try:
        username = _session_state["username"]
        _choices = [DEFAULT_CLIENT_ID, username]
    except Exception:
        username = "Guest"
        _choices = [DEFAULT_CLIENT_ID, username]
    return gr.Dropdown(choices=_choices, value=username)


def get_help_text() -> str:
    current_dir = pathlib.Path(__file__).parent.parent
    help_text_path = current_dir / "resources" / "help_text.md"
    with open(help_text_path, "r", encoding="utf8") as file:
        # Read line in UTF-8 format
        help_text = file.readlines()
    return ''.join(help_text)


EXAMPLE_CONTEXT = """
{
    "locationId": "HbTkOpUVUXtrMQ5wkwxD",
    "calendarId": "asGgwlPqqu6s17W084uE",
    "contactId": "8LDRBvYKbVyhXymqMurF",
    "random_word_from_agent_creation": "spatula",
    "firstName": "Deez",
    "lastName": "Nutzington",
    "name": "Your mother",
    "dateOfBirth": "1970-04-01",
    "phone": "+16197966726",
    "email": "e@my.ass",
    "address1": "1234 5th St N",
    "city": "San Diego",
    "state": "CA",
    "country": "US",
    "postalCode": "92108",
    "companyName": "Augmenting Integrations",
    "website": "openbra.in",
    "medications": "vicodin"
}
""".strip()
