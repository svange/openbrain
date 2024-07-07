import datetime
import json
import os
import re
from decimal import Decimal
from json import JSONDecodeError

import boto3
import gradio as gr
import requests
from dotenv import load_dotenv

load_dotenv()

## IMPORTANT: This is a local environment variable that is used to determine the stack name for the infrastructure.
## Must be set before importing openbrain

os.environ["INFRA_STACK_NAME"] = os.environ.get("GRADIO_INFRA_STACK_NAME", "LOCAL")
INFRA_STACK_NAME = os.environ.get("INFRA_STACK_NAME")


from openbrain.tools import Toolbox
import openbrain.orm.model_agent_config
from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_chat_message import ChatMessage
from openbrain.orm.model_chat_session import ChatSession
from openbrain.util import config, Defaults
import logging

from io import StringIO

log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.INFO, format='%(levelname)s :: %(message)s')
logger = logging.getLogger("Gradio")

EXAMPLE_CONTEXT = '''
{
    "locationId": "HbTkOpUVUXtrMQ5wkwxD",
    "calendarId": "asGgwlPqqu6s17W084uE",
    "contactId": "8LDRBvYKbVyhXymqMurF",
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
'''.strip()

HELP_TEXT = """# 🚀 Agent Configurations
## 📲 Loading an Agent's Settings
Choose an agent by selecting a `profile_name` and a `client_id`. The agent's settings will be loaded into the form. You can then modify the settings and save them. You can also reset the agent to its initial state. This will load the agent's configuration into Gradio for inspection and modification.

## 💽 Saving an Agent's Settings
Once all required agent fields are filled out, click the **Save** button to save the agent's settings. The settings will be saved to the DynamoDB database. You can then load the agent's settings at a later time.

> ⚠️ **Do not modify AgentConfigs in the public or leadmo client_id's, they may be overwritten by devops pipelines.**

# 🌍 Context
Some tools require some information from the incoming API call. You can send a contact's personal information like `firstName`, `lastName`, `dob`, etc. in your request (for LeadMomentum, see the custom webhook message). This information is the context for the conversation.

The context section below simulates the leadmo workflow by calling the leadmo API with the values seen here, and then replacing values such as `contactId` with the returned values. Be aware that the default customerId certainly doesn't exist in the leadmo database, so tools such as `leadmo_update_contact` will fail until a contact is created (maybe by using the `leadmo_create_contact` tool).

# 📆 Events
Events either gather information or perform an action. Action events are replayable, best-effort, ephemeral functions. Tools that perform an action, such as updating a Lead Momentum contact create action events. Events are stored in a DynamoDB table and can be retrieved for debugging purposes. You can see if your event triggered using the Action Events tab.

# 🔧 Available Tools
Tools are functions that can be called by the agent. They can be used to gather information or perform an action. Tools are defined in the `openbrain/tools` directory. You can see the available tools and their descriptions in the Available Tools tab.

# 🤖 Debugging Agents
The Agent Debugging tab shows the cloudwatch logs from the agent. If you encounter any issues, you can copy the logs and send them to the Sam for debugging.

# 🐛 Debugging Gradio Interface
The Debug tab shows the logs from the program. If you encounter any issues, you can copy the logs and send them to the Sam for debugging."""

OB_MODE = config.OB_MODE
CHAT_ENDPOINT = os.environ.get("OB_API_URL", "") + "/chat"

DEFAULT_ORIGIN = os.environ.get("DEFAULT_ORIGIN", "https://localhost:5173")
OB_PROVIDER_API_KEY = os.environ.get("GRADIO_OB_PROVIDER_API_KEY", "")
GRADIO_PASSWORD = os.environ.get("GRADIO_PASSWORD", None)
DEFAULT_CLIENT_ID = Defaults.DEFAULT_CLIENT_ID.value
DEFAULT_PROFILE_NAME = Defaults.DEFAULT_PROFILE_NAME.value
PORT = int(os.environ.get("GRADIO_PORT", 7860))

if OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import InMemoryDb

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

def get_debug_text(_debug_text = None) -> str:
    try:
        ret = log_stream.getvalue()
    except Exception as e:
        ret = e.__str__()

    if _debug_text:
        _debug_text = ret

    return ret


def get_aws_cloudwatch_logs(_session_state=None):
    """Get cloudwatch logs for the agent we are interacting with"""
    logger.info("Getting AWS Cloudwatch logs...")
    if not OB_PROVIDER_API_KEY:
        return "Local mode... no API to monitor."
    try:
        cloudwatch = boto3.client("logs")
        target_log_group_name_prefix = f'/aws/lambda/{INFRA_STACK_NAME}-APIHandler'
        # get list of log groups and find the one with GRADIO_INFRA_STACK_NAME's value in it's name
        log_groups = cloudwatch.describe_log_groups(logGroupNamePrefix=target_log_group_name_prefix)

        logger.info(f"Found {len(log_groups['logGroups'])} log groups.")
        target_log_group = log_groups["logGroups"][0]["logGroupName"]
        logger.info(f"Target log group: {target_log_group}")

        if not target_log_group:
            return "No log group found"

        # get the log streams for the log group
        log_streams = cloudwatch.describe_log_streams(logGroupName=target_log_group, orderBy="LastEventTime", descending=True)

        # get the latest log stream
        latest_log_stream = log_streams["logStreams"][0]["logStreamName"]

        # get the log events
        log_events = cloudwatch.get_log_events(logGroupName=target_log_group, logStreamName=latest_log_stream)

        events_string = ""
        # match_prefix = '{"level":"'

        # target_xray_trace_id = _session_state['last_response'].headers['x-amzn-trace-id']
        # target_xray_trace_id = re.sub(r';.*', '', target_xray_trace_id.replace("Root=", ""))
        max_events = 10
        counter = 0
        for event in log_events["events"]:
            message = event["message"]
            # if target_xray_trace_id in message:
            try:
                message_dict = json.loads(message, parse_float=Decimal)

                new_dict = {
                    "level": message_dict.get("level", None),
                    "location": message_dict.get("location", None),
                    "message": message_dict.get("message", None),
                    "timestamp": message_dict.get("timestamp", None),
                    "function_name": message_dict.get("function_name", None),
                    "request_path": message_dict.get("request_path", None),
                    "xray_trace_id": message_dict.get("xray_trace_id", None),
                }
            except JSONDecodeError as e:
                continue
            except KeyError as e:
                continue

            message = json.dumps(new_dict, indent=2)

            events_string += message + ",\n"
            counter += 1
            if counter > max_events:
                break

        # remove the last comma
        try:
            events_string = events_string[:-2]
        except Exception as e:
            events_string = json.dumps({
                "Idle": "No events found"
            })
        # formatted_message = '''```python\n''' + events_string + '''\n```'''
        formatted_message = '[\n' + events_string + '\n]'
        return formatted_message
    except Exception as e:
        return json.dumps({
            "exception": e.__str__()
        })


def get_aws_xray_trace_summaries(id=None):
    '''Get x-ray logs from AWS'''
    client = boto3.client('xray')
    this_year = datetime.datetime.now().year
    this_month = datetime.datetime.now().month
    this_day = datetime.datetime.now().day
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).day

    if id:
        response = client.get_trace_summaries(
            StartTime=datetime.datetime(this_year, this_month, yesterday),
            EndTime=datetime.datetime(this_year, this_month, this_day),
            Sampling=False,
            FilterExpression=f"traceId = {id}"
        )
    else:
        response = client.get_trace_summaries(
            StartTime=datetime.datetime(this_year, this_month, yesterday),
            EndTime=datetime.datetime(this_year, this_month, this_day),
            Sampling=False,
        )

    return response

def chat(message, chat_history, _profile_name, _session_state, _client_id, _context):
    # Make a POST request to the chat endpoint
    session_id = _session_state["session_id"]
    # context_dict = json.loads(_context)
    context_dict = _context
    chat_message = ChatMessage(agent_config=_profile_name, client_id=_client_id, reset=False, message=message,
                               session_id=session_id, **context_dict)

    if not OB_PROVIDER_API_KEY:
        logger.info("No API key found, trying to use local mode for agent interactions...")
        try:
            chat_session = ChatSession.get(session_id=session_id, client_id=_client_id)
        except Exception as e:
            logger.info("No chat session found, resetting instead...")
            return reset(_client_id, _profile_name, chat_history, _session_state, _context)


        agent_state = {
            "frozen_agent_memory": chat_session.frozen_agent_memory,
            "frozen_agent_config": chat_session.frozen_agent_config,
        }
        gpt_agent = GptAgent.deserialize(state=agent_state, context=_context)

        response_message = gpt_agent.handle_user_message(message)

        frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
        frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]

        chat_session = ChatSession(
            session_id=session_id,
            client_id=_client_id,
            frozen_agent_memory=frozen_agent_memory,
            frozen_agent_config=frozen_agent_config,
        )
        chat_session.save()
        new_context = _context

    else:
        session = _session_state["session"]
        session.headers.update(
            {
                "x-api-key": OB_PROVIDER_API_KEY,
                "origin": DEFAULT_ORIGIN,
            }
        )
        chat_message_dump = chat_message.model_dump()
        chat_message_dump["session_id"] = session_id

        response = session.post(CHAT_ENDPOINT, json=chat_message_dump)
        logger.info(f"Response: {response.json()}")
        response_message = response.json()["message"]
        _session_state["session"] = session

        response_dict = response.json()
        response_dict.pop("message")
        response_dict.pop("session_id")
        # original_context = json.loads(_context)
        original_context = _context
        response_dict.update(original_context)
        new_context = json.dumps(response_dict, indent=4, sort_keys=True)
        _session_state["last_response"] = response

    # session_state["last_response"] = response_message

    chat_history.append([message, response_message])

    # Return the response from the API
    return ["", chat_history, _session_state, new_context]


def reset(
        _client_id,
        _profile_name,
        chat_history,
        _session_state,
        _context
):
    # context_dict = json.loads(_context)
    context_dict = _context
    chat_message = ChatMessage(
        client_id=_client_id,
        reset=True,
        agent_config=_profile_name,
        message="Hi",
        **context_dict
    )

    chat_message_dump = chat_message.model_dump()
    chat_message_dump.pop("message")

    response = None
    if not OB_PROVIDER_API_KEY:
        logger.info("No API key found, trying to use local mode for agent interactions...")
        # Get a new agent with the specified settings
        agent_config = AgentConfig.get(profile_name=_profile_name, client_id=_client_id)
        gpt_agent = GptAgent(agent_config=agent_config, context=_context)

        frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
        frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]
        chat_session = ChatSession(
            client_id=_client_id,
            frozen_agent_memory=frozen_agent_memory,
            frozen_agent_config=frozen_agent_config,
        )
        session_id = chat_session.session_id
        _session_state["session_id"] = session_id
        chat_session.save()
        response_message = gpt_agent.agent_config.icebreaker
        response_dict = {}
    else:
        # Make a POST request to the reset endpoint
        session = _session_state["session"]
        headers = {
            "x-api-key": OB_PROVIDER_API_KEY,
            "origin": DEFAULT_ORIGIN,
        }
        session.headers.update(headers)
        response = session.post(url=CHAT_ENDPOINT, json=chat_message_dump)
        logger.info(f"Response: {response.json()}")
        session_id = response.cookies["Session"]
        _session_state["session_id"] = session_id
        _session_state["session"] = session
        _session_state["last_response"] = response
        response_message = response.json()["message"]
        response_dict = response.json()
        response_dict.pop("message")
        response_dict.pop("session_id")

    message = f"Please wait, fetching new agent..."
    chat_history.append([message, response_message])

    # original_context = json.loads(_context)
    original_context = _context

    response_dict.update(original_context)
    new_context = json.dumps(response_dict, indent=4)

    # Return the response from the API
    return ["", chat_history, _session_state, new_context]


def save(
        _icebreaker,
        # _chat_model,
        _system_message,
        _llm,
        # _prompt_layer_tags,
        _max_iterations,
        _max_execution_time,
        _executor_temp,
        _profile_name,
        # _executor_model_type,
        # _openai_api_key,
        # _promptlayer_api_key,
        _client_id,
        # _outgoing_webhook_url,
        _record_tool_actions,
        _record_conversations,

        tools
):
    if _profile_name.strip() == "":
        gr.Error("Personalization key can't be blank.")
        return []

    if not _client_id:
        client_id = DEFAULT_CLIENT_ID.value
    else:
        client_id = _client_id

    agent_config = AgentConfig(
        icebreaker=str(_icebreaker),
        # executor_chat_model=str(_chat_model),
        system_message=str(_system_message),
        llm=str(_llm),
        # prompt_layer_tags=str(_prompt_layer_tags),
        executor_max_iterations=str(_max_iterations),
        executor_max_execution_time=str(_max_execution_time),
        executor_temp=str(_executor_temp),
        profile_name=str(_profile_name),
        # executor_model_type=str(_executor_model_type),
        # openai_api_key=str(_openai_api_key),
        # promptlayer_api_key=str(_promptlayer_api_key),
        client_id=str(_client_id),
        # outgoing_webhook_url=str(_outgoing_webhook_url),
        record_tool_actions=str(_record_tool_actions),
        record_conversations=str(_record_conversations),
        tools=tools,
    )

    # Upload the preferences to the DynamoDB database
    agent_config.save()
    logger.info(f"AgentConfig saved: {agent_config.to_json()}")

    # Return a success message
    return "Preferences saved successfully."


def load(_profile_name: str, _client_id: str):
    if _profile_name.strip() == "":
        raise gr.Error("client_id can't be blank.")
    # Upload the preferences to the DynamoDB database
    if not _client_id:
        _client_id = DEFAULT_CLIENT_ID
    try:
        retrieved_agent_config = AgentConfig.get(profile_name=_profile_name, client_id=_client_id)
        logger.info(f"AgentConfig retrieved: {retrieved_agent_config.to_json()}")
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {e}"

    _tools = retrieved_agent_config.tools
    supported_tools = openbrain.tools.Toolbox.discovered_tools

    for _tool in _tools:
        if _tool not in supported_tools:
            _tools.remove(_tool)

    _agent_config = [
        str(retrieved_agent_config.icebreaker),
        # str(retrieved_agent_config.executor_chat_model),
        str(retrieved_agent_config.system_message),
        str(retrieved_agent_config.llm),
        # str(retrieved_agent_config.prompt_layer_tags),
        str(retrieved_agent_config.executor_max_iterations),
        str(retrieved_agent_config.executor_max_execution_time),
        str(retrieved_agent_config.executor_temp),
        str(retrieved_agent_config.profile_name),
        # str(retrieved_agent_config.executor_model_type),
        # str(retrieved_agent_config.openai_api_key),
        # str(retrieved_agent_config.promptlayer_api_key),
        str(retrieved_agent_config.client_id),
        # str(retrieved_agent_config.outgoing_webhook_url),
        bool(retrieved_agent_config.record_tool_actions),
        bool(retrieved_agent_config.record_conversations),
        _tools
    ]
    llm_name = retrieved_agent_config.llm
    if llm_name in openbrain.orm.model_agent_config.FUNCTION_LANGUAGE_MODELS:
        llm_type = "function"
    elif llm_name in openbrain.orm.model_agent_config.CHAT_LANGUAGE_MODELS:
        llm_type = "chat"
    elif llm_name in openbrain.orm.model_agent_config.COMPLETION_LANGUAGE_MODELS:
        llm_type = "completion"

    else:
        raise ValueError(f"Language model {llm_name} not found in any of the language model lists")

    ret = [*_agent_config, llm_type]
    # Return a success message
    return ret


def is_settings_set():
    return True


def auth(username, password):
    if username in ["admin"]:
        if password == GRADIO_PASSWORD:
            return True
    return False


class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJsonEncoder, self).default(obj)


def get_action_events(_events=None, _session_state=None):
    try:
        _session_id = _session_state["session_id"]
        if not _session_id:
            raise AssertionError("Session started, but session_is blank")
    except TypeError as e:
        return json.dumps({
            "Idle": "Working..."
        })
    except AssertionError as e:
        return json.dumps({
            "Idle": f"Start a conversation to begin monitoring for events"
        })
    logger.info("Getting latest action...")

    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(config.ACTION_TABLE_NAME)
        response = table.get_item(Key={"action_id": "latest", "session_id": _session_id})
        ret = response.get("Item", {})
    except KeyError as e:
        ret = json.dumps({"exception": "Event not found for this session, perhaps one wasn't sent yet in this conversation"})
    except Exception as e:
        ret = json.dumps({"exception": e.__str__()})

    if _events:
        _events = ret
    return json.dumps(ret, cls=CustomJsonEncoder, indent=4, sort_keys=True)

def get_bucket_name():
    try:
        infra_stack_name = config.INFRA_STACK_NAME
        # Get tablename from outputs of INFRA_STACK
        cfn = boto3.client('cloudformation')
        response = cfn.describe_stacks(StackName=infra_stack_name)
        outputs = response["Stacks"][0]["Outputs"]
        for output in outputs:
            if output["OutputKey"] == "ObBucketName":
                bucket = output["OutputValue"]
                break
        else:
            raise Exception("Bucket name not found in outputs")
        return bucket
    except Exception as e:
        raise e

def get_tool_description(tool_name):
    for tool in Toolbox.discovered_tools:
        if tool_name == tool.name:

            tool_instance = tool.tool()
            tool_description = tool_instance.description
            fields = tool_instance.args_schema.model_fields
            args_string = ''
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
        args_string = ''
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

def get_available_profile_names() -> list:
    logger.info("Getting available profile names...")
    # logger.warning("get_available_profile_names() is not implemented")
    # Get AgentConfig table

    if OB_MODE == Defaults.OB_MODE_LOCAL.value:
        try:
            lst = list(InMemoryDb.instance[config.AGENT_CONFIG_TABLE_NAME][DEFAULT_CLIENT_ID].keys())
            return lst
        except Exception:
            default_config = AgentConfig(client_id=DEFAULT_CLIENT_ID, profile_name=DEFAULT_PROFILE_NAME)
            default_config.save()
            lst = list(InMemoryDb.instance[config.AGENT_CONFIG_TABLE_NAME][DEFAULT_CLIENT_ID].keys())
            return lst
    else:
        table = boto3.resource("dynamodb").Table(config.AGENT_CONFIG_TABLE_NAME)
        # get all items in the table
        response = table.scan()
        # return the profile names with client_id == 'public'
        return [item["profile_name"] for item in response["Items"] if item["client_id"] == DEFAULT_CLIENT_ID]


def get_bottom_text(_session_state=None, _client_id=None, _profile_name=None):
    try:
        bucket_name = get_bucket_name()
        _session_id = _session_state.get("session_id").lower()
        dl_url = f"https://{bucket_name}.s3.amazonaws.com/conversations/{_profile_name}/{_client_id}/{_session_id}.json"
        # link_text_md = f"| [Download Session Data]({link_text}) "
        link_text_md = f"| [Download Session Data]({dl_url}) "

        xray_trace_id = _session_state['last_response'].headers['x-amzn-trace-id']
        xray_trace_id = re.sub(r';.*', '', xray_trace_id.replace("Root=", ""))

        xray_trace_id_md = f"| [X-Ray](https://console.aws.amazon.com/xray/home?region=us-east-1#/traces/{xray_trace_id}) "

    except Exception as e:
        _session_id = "no-session"
        link_text_md = ''
        xray_trace_id_md = ''

    if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
        orm_mode = "LOCAL"
    else:
        orm_mode = "DYNAMODB"

    # if not _session_id:
    #     _session_id = "no-session"


    api = f"{CHAT_ENDPOINT}" if OB_PROVIDER_API_KEY else "LOCAL"

    infra_stack_name = os.environ["INFRA_STACK_NAME"]
    formatted_text = xray_trace_id_md + link_text_md + f"| Session: `{_session_id}` | Stack: `{aws_profile}:{infra_stack_name}` | ORM Mode: `{orm_mode}` | API: `{api}` |"
    return formatted_text


def get_gpt_agent_logs():

    # Get the StringIO handler from this logger

    # api = f"{CHAT_ENDPOINT}" if OB_PROVIDER_API_KEY else "LOCAL"
    agent_logger = openbrain.util.get_logger()

    # def get_logger() -> Logger:
    #     _logger = Logger(service=f"{__name__}")
    #     log_stream = StringIO()
    #     string_handler = logging.StreamHandler(log_stream)
    #     _logger.addHandler(string_handler)
    #     # logging.basicConfig(stream=log_stream, level=logging.INFO, format='%(levelname)s :: %(message)s')
    #     # boto3.set_stream_logger()
    #     # boto3.set_stream_logger("botocore")
    #     return _logger

    for stream in agent_logger.handlers:
        if isinstance(stream.stream, StringIO):
            return stream.stream.getvalue().replace("\\n", "\n")
    return json.dumps({
        "Error": "Could not find StringIO Agent log streamer"
    })


def get_llm_choices(llm_types=None):
    """Get the available LLM choices based on the selected types"""
    if not llm_types:
        llm_types = ['function']
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
    return gr.Dropdown.update(choices=available_llms)


with gr.Blocks(theme="JohnSmith9982/small_and_pretty") as main_block:
    session_state = gr.State(value={"session_id": "", "session": requests.Session(), "agent": None})
    session_apikey = gr.State(value="")
    with gr.Accordion("Help and information", elem_classes="accordion", visible=is_settings_set(), open=False) as help_box:
        with gr.Tab("Debugging Tools and Help") as help_tab:
            gr.Markdown(value=HELP_TEXT)

        with gr.Tab("Gradio logs") as debug_tab:
            debug_text = gr.Textbox(
                label="Debug",
                info="Debugging information",
                show_label=False,
                lines=20,
                value=get_debug_text,
                interactive=False,
                autoscroll=True,
                show_copy_button=True,
                every=1.0,
            )
            # refresh_button = gr.Button("Refresh", variant="secondary")
            # refresh_button.click(get_debug_text, inputs=[debug_text], outputs=[debug_text])

        with gr.Tab("API Logs") as agent_debug_tab:
            api_debug_text = gr.TextArea(
                label="Debug",
                # info="Debugging information",
                show_label=False,
                lines=20,
                value=get_aws_cloudwatch_logs,
                interactive=False,
                autoscroll=True,
                show_copy_button=True,
                every=3.0,
            )
            refresh_api_logs_button = gr.Button("Refresh", size="sm", variant="secondary")
            refresh_api_logs_button.click(get_aws_cloudwatch_logs, inputs=[session_state], outputs=[api_debug_text])

        with gr.Tab("Agent Logs") as agent_logs:
            agent_debug_text = gr.Textbox(
                value=get_gpt_agent_logs,
                label="Debug",
                info="GptAgent logs",
                show_label=False,
                lines=20,
                interactive=False,
                autoscroll=True,
                show_copy_button=True,
                every=3.0,
            )
            refresh_agent_logs_button = gr.Button("Refresh", size="sm", variant="secondary")
            refresh_agent_logs_button.click(get_gpt_agent_logs, outputs=[agent_debug_text])


        with gr.Tab("Actions"):
            # events_str = get_action_events()
            # events = gr.Json(value=events_str, label="Latest action event recorded.")
            events = gr.Json(value=get_action_events,
                             # every=15.0,
                             label="Latest action recorded.")

            refresh_events_button = gr.Button("Refresh", size="sm", variant="secondary")
            refresh_events_button.click(get_action_events, inputs=[events, session_state], outputs=[events])

    with gr.Accordion("Configuration and Tuning", elem_classes="accordion", visible=is_settings_set(), open=False) as prompts_box:

        with gr.Tab("LLM Parameters") as tuninig_tab:
            gr.Markdown(
                "Changes to these settings are used to set up a conversation using the Reset button and will not "
                "be reflected until the next 'Reset'"
            )

            with gr.Row() as preferences_row1:
                options = openbrain.orm.model_agent_config.EXECUTOR_MODEL_TYPES
                default_llm_types = ["function"]
                llm_types = gr.CheckboxGroup(
                    choices=options,
                    label="LLM Types",
                    info="List only the types of agents you are interested in.",
                    value=default_llm_types,
                )
                original_choices = openbrain.orm.model_agent_config.FUNCTION_LANGUAGE_MODELS
                # original_value = openbrain.orm.model_agent_config.FUNCTION_LANGUAGE_MODELS[0]
                llm = gr.Dropdown(
                    choices=original_choices,
                    # value=original_value,
                    label="LLM",
                    info="The language model to use for completion"
                )
                llm_types.change(get_llm_choices, inputs=[llm_types], outputs=[llm])

                with gr.Column() as extra_options_column:
                    record_tool_actions = gr.Checkbox(label="Record Tool Actions", info="Record tool actions (use 'Actions' box).")
                    record_conversations = gr.Checkbox(label="Record Conversations", info="Record conversations.")

                # executor_completion_model = gr.Dropdown( choices=["text-davinci-003", "text-davinci-002",
                # "text-curie-001", "text-babbage-001", "text-ada-001"], label="Executor Completion Model",
                # info="This is the model used when Executor Model Type is set to 'completion'" )

            with gr.Row() as preferences_row2:

                executor_temp = gr.Slider(
                    minimum=0,
                    maximum=2,
                    label="Temperature",
                    step=0.1,
                    info="Higher temperature for 'spicy' agents.",
                )
                max_execution_time = gr.Slider(
                    minimum=0,
                    maximum=30,
                    label="Max Execution Time",
                    step=0.5,
                    info="Maximum agent response time before termination.",
                )
                max_iterations = gr.Number(
                    label="Max Iterations",
                    info="Number of steps an agent can take for a response before termination.",
                )

        with gr.Tab("Tools") as preferences_row3:

            tool_names = [tool.name for tool in Toolbox.discovered_tools]
            tool_names.sort()
            tools = gr.CheckboxGroup(tool_names, label="Tools", info="Select tools to enable for the agent")

            gr.Markdown(value="Tool descriptions as presented to the AI. Confusing text here could lead to inconsistent use of tools.")
            _tools = Toolbox.discovered_tools
            with gr.Column() as tool_accordion:
                for _tool in _tools:
                    with gr.Tab(_tool.name):
                        gr.Markdown(value=get_tool_description(_tool.name))


            # tool_names = openbrain.orm.model_agent_config.DefaultSettings.AVAILABLE_TOOLS.value

        with gr.Tab("System Message") as long_text_row1:
            system_message = gr.TextArea(
                lines=10,
                label="System Message",
                placeholder="Enter your system message here",
                info="The System Message. This message is a part of every context with "
                     "ChatGPT, and is therefore the most influential, and expensive place to "
                     "add text",
                show_label=False,
            )

        with gr.Tab("Icebreaker") as long_text_row2:
            icebreaker = gr.TextArea(
                lines=10,
                label="Icebreaker",
                placeholder="Enter your icebreaker here",
                show_label=False,
                info="The first message to be sent to the user.",
            )

    with gr.Accordion("Save and Load") as submit_accordion:
        with gr.Row() as submit_row:
            with gr.Column(scale=3) as key_text_column:
                with gr.Row() as key_text_row:
                    client_id = gr.Textbox(
                        label="Client ID",
                        info="Your client ID. Defaults to 'public'.",
                        type="text",
                    )
                    client_id.value = DEFAULT_CLIENT_ID

                    profile_name = gr.Dropdown(
                        allow_custom_value=True,
                        label="Profile Name",
                        info="The name of your AgentConfig. Defaults to 'default'",
                        choices=get_available_profile_names(),
                    )
                    profile_name.value = DEFAULT_PROFILE_NAME

            with gr.Column(scale=1) as submit_column:
                load_button = gr.Button(value="Load", variant="primary")
                save_button = gr.Button(value="Save", variant="secondary")
                preferences = [
                    icebreaker,
                    # chat_model,
                    system_message,
                    llm,
                    # prompt_layer_tags,
                    max_iterations,
                    max_execution_time,
                    executor_temp,
                    profile_name,
                    # executor_model_type,
                    # executor_completion_model,
                    # openai_api_key,
                    # promptlayer_api_key,
                    client_id,
                    # outgoing_webhook_url,
                    record_tool_actions,
                    record_conversations,
                    tools,
                    llm_types
                ]

                load_button.click(load, inputs=[profile_name, client_id], outputs=preferences)

                save_button.click(
                    save,
                    inputs=[
                        icebreaker,
                        system_message,
                        llm,
                        max_iterations,
                        max_execution_time,
                        executor_temp,
                        profile_name,
                        client_id,
                        record_tool_actions,
                        record_conversations,
                        tools
                    ],
                )

    with gr.Accordion("Interact with Agent") as chat_accordian:
        with gr.Row() as chat_row:
            with gr.Column(scale=2) as chat_container:
                with gr.Column(scale=2) as chat_column:
                    chatbot = gr.Chatbot()

                    msg = gr.Textbox()

            with gr.Column(scale=1) as context_container:


                with gr.Accordion("Context", open=True) as context_accordian:



                    # leadmo_location_id = gr.Textbox(label="leadmo_location_id")
                    # leadmo_contact_id = gr.Textbox(label="leadmo_contact_id")
                    # leadmo_calendar_id = gr.Textbox(label="leadmo_calendar_id")
                    #
                    # context_firstName = gr.Textbox(label="firstName")
                    # context_lastName = gr.Textbox(label="lastName")
                    # context_name = gr.Textbox(label="name")
                    # context_dateOfBirth = gr.Textbox(label="dateOfBirth")
                    # context_phone = gr.Textbox(label="phone")
                    # context_email = gr.Textbox(label="email")
                    # context_address1 = gr.Textbox(label="address1")
                    # context_city = gr.Textbox(label="city")
                    # context_state = gr.Textbox(label="state")
                    # context_country = gr.Textbox(label="country")
                    # context_postalCode = gr.Textbox(label="postalCode")
                    # context_companyName = gr.Textbox(label="companyName")
                    # context_website = gr.Textbox(label="website")
                    # context_medications = gr.Textbox(label="medications")


                    context = gr.JSON(
                        label="Context",
                        info="Additional context for tools",
                        show_label=False,
                        show_copy_button=True,
                        lines=4,
                        value=EXAMPLE_CONTEXT,
                    )

                chat_button = gr.Button("Chat", variant="primary")
                reset_agent = gr.Button("Reset", variant="secondary")

                msg.submit(
                    chat,
                    [msg, chatbot, profile_name, session_state, client_id, context],
                    [msg, chatbot, session_state, context],
                )

                chat_button.click(
                    fn=chat,
                    inputs=[msg, chatbot, profile_name, session_state, client_id, context],
                    outputs=[msg, chatbot, session_state, context],
                )

                reset_agent.click(
                    fn=reset,
                    inputs=[
                        client_id,
                        profile_name,
                        chatbot,
                        session_state,
                        context
                    ],
                    outputs=[msg, chatbot, session_state, context],
                )


    bottom_text = gr.Markdown(
        value=get_bottom_text(),
        rtl=True
    )

    # Refresh bottom text
    reset_agent.click(
        get_bottom_text,
        inputs=[session_state, profile_name, client_id],
        outputs=[bottom_text]
    )

    # Refresh agent debug text
    reset_agent.click(
        get_aws_cloudwatch_logs,
        inputs=[session_state],
        outputs=[agent_debug_text]
    )

    chat_button.click(
        get_aws_cloudwatch_logs,
        inputs=[session_state],
        outputs=[agent_debug_text]
    )

    # Refresh Action events
    reset_agent.click(
        get_action_events,
        inputs=[events, session_state],
        outputs=[events]
    )





# key = f"conversations/{session_id}.json"
        # s3 = boto3.client('s3')
        # s3.download_file(bucket_name, key, f"{session_id}.json")



def main():
    if GRADIO_PASSWORD:
        main_block.queue(max_size=20).launch(
            debug=True,
            share=False,
            server_name="0.0.0.0",
            server_port=PORT,
            auth=auth,
            auth_message="Please login to continue",
        )
    else:
        main_block.queue(max_size=20).launch(
            debug=True,
            share=False,
            server_name="0.0.0.0",
            server_port=PORT,
        )


if "__main__" == __name__:
    main()
