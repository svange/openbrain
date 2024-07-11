import json
import os
import re
from decimal import Decimal
from io import StringIO
from json import JSONDecodeError

import boto3
import gradio as gr

import openbrain.orm
import openbrain.util
from openbrain.agents.gpt_agent import GptAgent
from openbrain.ob_tuner.functions.util import logger, OB_PROVIDER_API_KEY, CHAT_ENDPOINT, DEFAULT_ORIGIN, INFRA_STACK_NAME, DEFAULT_CLIENT_ID, TOOL_NAMES, aws_profile
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_chat_message import ChatMessage
from openbrain.orm.model_chat_session import ChatSession
from openbrain.util import config, Defaults

def get_aws_cloudwatch_logs(_session_state=None):
    """Get cloudwatch logs for the agent we are interacting with"""
    logger.info("Getting AWS Cloudwatch logs...")
    if not OB_PROVIDER_API_KEY:
        return "Local mode... no API to monitor."
    try:
        cloudwatch = boto3.client("logs")
        target_log_group_name_prefix = f"/aws/lambda/{INFRA_STACK_NAME}-APIHandler"
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
            except JSONDecodeError:
                continue
            except KeyError:
                continue

            message = json.dumps(new_dict, indent=2)

            events_string += message + ",\n"
            counter += 1
            if counter > max_events:
                break

        # remove the last comma
        try:
            events_string = events_string[:-2]
        except Exception:
            events_string = json.dumps({"Idle": "No events found"})
        # formatted_message = '''```python\n''' + events_string + '''\n```'''
        formatted_message = "[\n" + events_string + "\n]"
        return formatted_message
    except Exception as e:
        return json.dumps({"exception": e.__str__()})


def chat(message, chat_history, _profile_name, _session_state, _client_id, _context):
    # Make a POST request to the chat endpoint
    session_id = _session_state["session_id"]
    context_dict = json.loads(_context)
    # context_dict = _context
    chat_message = ChatMessage(
        agent_config=_profile_name, client_id=_client_id, reset=False, message=message, session_id=session_id, **context_dict
    )

    if not OB_PROVIDER_API_KEY:
        logger.info("No API key found, trying to use local mode for agent interactions...")
        try:
            chat_session = ChatSession.get(session_id=session_id, client_id=_client_id)
        except Exception:
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
        original_context = json.loads(_context)
        # original_context = _context
        response_dict.update(original_context)
        new_context = json.dumps(response_dict, indent=4, sort_keys=True)
        _session_state["last_response"] = response

    # session_state["last_response"] = response_message

    chat_history.append([message, response_message])

    # Return the response from the API
    return ["", chat_history, _session_state, new_context]


def reset(_client_id, _profile_name, chat_history, _session_state, _context):
    try:
        context_dict = json.loads(_context)
    except JSONDecodeError:
        context_dict = {"random_word": "dogwater"}
    # context_dict = _context
    chat_message = ChatMessage(client_id=_client_id, reset=True, agent_config=_profile_name, message="Hi", **context_dict)

    chat_message_dump = chat_message.model_dump()
    chat_message_dump.pop("message")

    response = None
    if not OB_PROVIDER_API_KEY:
        logger.info("No API key found, trying to use local mode for agent interactions...")
        # Get a new agent with the specified settings
        agent_config = AgentConfig.get(profile_name=_profile_name, client_id=_client_id)
        gpt_agent = GptAgent(agent_config=agent_config, context=context_dict)

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

    message = "Please wait, fetching new agent..."
    chat_history.append([message, response_message])

    original_context = context_dict
    # original_context = _context

    response_dict.update(context_dict)
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
    _tools,
):
    if _profile_name.strip() == "":
        gr.Error("This agent config must have a name (profile_name).")
        return []

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
        tools=_tools,
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
    supported_tools = TOOL_NAMES

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
        _tools,
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


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJsonEncoder, self).default(obj)


def get_action_events(_events=None, _session_state=None):
    try:
        _session_id = _session_state["session_id"]
    except TypeError:
        return json.dumps({"Idle": "Start a conversation to begin monitoring for events"})
    logger.info("Getting latest action...")

    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(config.ACTION_TABLE_NAME)
        response = table.get_item(Key={"action_id": "latest", "session_id": _session_id})
        ret = response.get("Item", {})
    except KeyError:
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
        cfn = boto3.client("cloudformation")
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


def get_bottom_text(_session_state=None, _client_id=None, _profile_name=None):
    try:
        bucket_name = get_bucket_name()
        _session_id = _session_state.get("session_id").lower()
        dl_url = f"https://{bucket_name}.s3.amazonaws.com/conversations/{_profile_name}/{_client_id}/{_session_id}.json"
        # link_text_md = f"| [Download Session Data]({link_text}) "
        link_text_md = f"| [Download Session Data]({dl_url}) "

        xray_trace_id = _session_state["last_response"].headers["x-amzn-trace-id"]
        xray_trace_id = re.sub(r";.*", "", xray_trace_id.replace("Root=", ""))

        xray_trace_id_md = f"| [X-Ray](https://console.aws.amazon.com/xray/home?region=us-east-1#/traces/{xray_trace_id}) "

    except Exception:
        _session_id = "no-session"
        link_text_md = ""
        xray_trace_id_md = ""

    if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
        orm_mode = "LOCAL"
    else:
        orm_mode = "DYNAMODB"

    # if not _session_id:
    #     _session_id = "no-session"

    api = f"{CHAT_ENDPOINT}" if OB_PROVIDER_API_KEY else "LOCAL"

    infra_stack_name = os.environ["INFRA_STACK_NAME"]
    formatted_text = (
        xray_trace_id_md
        + link_text_md
        + f"| Session: `{_session_id}` | Stack: `{aws_profile}:{infra_stack_name}` | ORM Mode: `{orm_mode}` | API: `{api}` |"
    )
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
    return json.dumps({"Error": "Could not find StringIO Agent log streamer"})


def get_context(
        _location_id,
        _calendar_id,
        _contact_id,
        _context_firstName,
        _context_lastName,
        _context_name,
        _context_dateOfBirth,
        _context_phone,
        _context_email,
        _context_address1,
        _context_city,
        _context_state,
        _context_country,
        _context_postalCode,
        _context_companyName,
        _context_website,
        _context_medications,
        _context_random_word,
):
    context_json = {
        "locationId": _location_id,
        "calendarId": _calendar_id,
        "contactId": _contact_id,
        "firstName": _context_firstName,
        "lastName": _context_lastName,
        "name": _context_name,
        "dateOfBirth": _context_dateOfBirth,
        "phone": _context_phone,
        "email": _context_email,
        "address1": _context_address1,
        "city": _context_city,
        "state": _context_state,
        "country": _context_country,
        "postalCode": _context_postalCode,
        "companyName": _context_companyName,
        "website": _context_website,
        "medications": _context_medications,
        "random_word": _context_random_word,
    }
    ret_dict = {}
    for key in context_json:
        if context_json[key]:
            ret_dict[key] = context_json[key]
    return json.dumps(ret_dict, indent=2)


def save_context(
        _location_id,
        _calendar_id,
        _contact_id,
        _context_firstName,
        _context_lastName,
        _context_name,
        _context_dateOfBirth,
        _context_phone,
        _context_email,
        _context_address1,
        _context_city,
        _context_state,
        _context_country,
        _context_postalCode,
        _context_companyName,
        _context_website,
        _context_medications,
        _context_random_word,
):
    context = get_context(
        _location_id,
        _calendar_id,
        _contact_id,
        _context_firstName,
        _context_lastName,
        _context_name,
        _context_dateOfBirth,
        _context_phone,
        _context_email,
        _context_address1,
        _context_city,
        _context_state,
        _context_country,
        _context_postalCode,
        _context_companyName,
        _context_website,
        _context_medications,
        _context_random_word,
    )
    raise gr.Error("Saving not yet implemented 💥!", duration=5)
