import json
import os
from decimal import Decimal
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
    "medications": "vicodin",
    "calendarId": "asGgwlPqqu6s17W084uE",
    "contactId": "8LDRBvYKbVyhXymqMurF",
    "locationId": "HbTkOpUVUXtrMQ5wkwxD"
}
'''.strip()

HELP_TEXT = """# Agent Configurations
## Loading an Agent's Settings
Choose an agent by selecting a profile_name and a client_id. The agent's settings will be loaded into the form. You can then modify the settings and save them. You can also reset the agent to its initial state. This will load the agent's configuration into Gradio for inspection and modification.

## Saving an Agent's Settings
Once all required agent fields are filled out, click the Save button to save the agent's settings. The settings will be saved to the DynamoDB database. You can then load the agent's settings at a later time.

> :warning: ** Do not modify AgentConfigs in the public or leadmo client_id's, they may be overwritten by devops pipelines.**

# Context
Some tools require some information from the incoming API call. You can send a contact's personal information like 'firstName', 'lastName', 'dob', etc. in the your request (for LeadMomentum, see the custom webhook message). This information is the context for the conversation.

# Events
Events either gather information or perform an action. Action events are replayable, best-effort, ephemeral functions. Tools that perform an action, such as updating a Lead Momentum contact create action events. Events are stored in a DynamoDB table and can be retrieved for debugging purposes. You can see if your event triggered using the Action Events tab.

# Debugging
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


def chat(message, chat_history, _profile_name, session_state, _client_id, _context):
    # Make a POST request to the chat endpoint
    session_id = session_state["session_id"]
    context_dict = json.loads(_context)
    chat_message = ChatMessage(agent_config=_profile_name, client_id=_client_id, reset=False, message=message,
                               session_id=session_id, **context_dict)

    new_context = None

    response_message = None
    if not OB_PROVIDER_API_KEY:
        logger.info("No API key found, trying to use local mode for agent interactions...")
        chat_session = ChatSession.get(session_id=session_id, client_id=_client_id)
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

    else:
        session = session_state["session"]
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
        session_state["session"] = session

        response_dict = response.json()
        response_dict.pop("message")
        response_dict.pop("session_id")
        original_context = json.loads(_context)
        response_dict.update(original_context)
        new_context = json.dumps(response_dict, indent=4, sort_keys=True)

    session_state["last_response"] = response_message

    chat_history.append([message, response_message])

    # Return the response from the API
    return ["", chat_history, session_state, new_context]


def reset(
        _client_id,
        _profile_name,
        chat_history,
        session_state,
        _context
):
    context_dict = json.loads(_context)
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
        gpt_agent = GptAgent(agent_config=agent_config, initial_context=_context)

        frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
        frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]
        chat_session = ChatSession(
            client_id=_client_id,
            frozen_agent_memory=frozen_agent_memory,
            frozen_agent_config=frozen_agent_config,
        )
        session_id = chat_session.session_id
        session_state["session_id"] = session_id
        chat_session.save()
        response_message = gpt_agent.agent_config.icebreaker
        response_dict = {}
    else:
        # Make a POST request to the reset endpoint
        session = session_state["session"]
        headers = {
            "x-api-key": OB_PROVIDER_API_KEY,
            "origin": DEFAULT_ORIGIN,
        }
        session.headers.update(headers)
        response = session.post(url=CHAT_ENDPOINT, json=chat_message_dump)
        logger.info(f"Response: {response.json()}")
        session_id = response.cookies["Session"]
        session_state["session_id"] = session_id
        session_state["session"] = session
        session_state["last_response"] = response
        response_message = response.json()["message"]
        response_dict = response.json()
        response_dict.pop("message")
        response_dict.pop("session_id")

    message = f"Please wait, fetching new agent..."
    chat_history.append([message, response_message])

    original_context = json.loads(_context)

    response_dict.update(original_context)
    new_context = json.dumps(response_dict, indent=4, sort_keys=True)

    # Return the response from the API
    return ["", chat_history, session_state, new_context]


def save(
        _icebreaker,
        _chat_model,
        _system_message,
        # _prompt_layer_tags,
        _max_iterations,
        _max_execution_time,
        _executor_temp,
        _profile_name,
        _executor_model_type,
        _openai_api_key,
        # _promptlayer_api_key,
        client_id,
        outgoing_webhook_url,
        tools
):
    if _profile_name.strip() == "":
        gr.Error("Personalization key can't be blank.")
        return []

    if not client_id:
        client_id = DEFAULT_CLIENT_ID.value

    agent_config = AgentConfig(
        icebreaker=str(_icebreaker),
        executor_chat_model=str(_chat_model),
        system_message=str(_system_message),
        # prompt_layer_tags=str(_prompt_layer_tags),
        executor_max_iterations=str(_max_iterations),
        executor_max_execution_time=str(_max_execution_time),
        executor_temp=str(_executor_temp),
        profile_name=str(_profile_name),
        executor_model_type=str(_executor_model_type),
        openai_api_key=str(_openai_api_key),
        # promptlayer_api_key=str(_promptlayer_api_key),
        client_id=str(client_id),
        outgoing_webhook_url=str(outgoing_webhook_url),
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
    _agent_config = [
        str(retrieved_agent_config.icebreaker),
        str(retrieved_agent_config.executor_chat_model),
        str(retrieved_agent_config.system_message),
        # str(retrieved_agent_config.prompt_layer_tags),
        str(retrieved_agent_config.executor_max_iterations),
        str(retrieved_agent_config.executor_max_execution_time),
        str(retrieved_agent_config.executor_temp),
        str(retrieved_agent_config.profile_name),
        str(retrieved_agent_config.executor_model_type),
        str(retrieved_agent_config.openai_api_key),
        # str(retrieved_agent_config.promptlayer_api_key),
        str(retrieved_agent_config.client_id),
        str(retrieved_agent_config.outgoing_webhook_url),
        _tools
    ]

    # Return a success message
    return _agent_config


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


def get_action_events(_events=None):
    logger.info("Getting latest action...")
    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(config.ACTION_TABLE_NAME)
        response = table.get_item(Key={"action_id": "latest"})
        ret = response.get("Item", {})
    except Exception as e:
        ret = json.dumps({"exception": e.__str__()})

    if _events:
        _events = ret
    return json.dumps(ret, cls=CustomJsonEncoder, indent=4, sort_keys=True)

def get_available_tool_descriptions():
    tool_descriptions = []

    for tool in Toolbox.discovered_tools:
        tool_name = tool.name
        tool_instance = tool.tool()
        tool_description = tool_instance.description
        fields = tool_instance.args_schema.model_fields
        # args_string = json.dumps(fields, indent=2, cls=CustomJsonEncoder, sort_keys=True)
        # args_string = fields.__str__()
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


with gr.Blocks(theme="JohnSmith9982/small_and_pretty") as main_block:
    session_state = gr.State(value={"session_id": "", "session": requests.Session(), "agent": None})
    session_apikey = gr.State(value="")
    with gr.Accordion("Help and information", elem_classes="accordion", visible=is_settings_set(), open=False) as help_box:
        with gr.Tab("Help and Information") as help_tab:
            gr.Markdown(value=HELP_TEXT)

        with gr.Tab("Available Tools") as tools_tab:
            gr.Markdown(value=get_available_tool_descriptions())

        with gr.Tab("Gradio Debugging") as debug_tab:
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
    with gr.Accordion("Configuration and Tuning", elem_classes="accordion", visible=is_settings_set(), open=False) as prompts_box:

        with gr.Tab("LLM Tuning") as tuninig_tab:
            gr.Markdown(
                "Changes to these settings are used to set up a conversation using the Reset button and will not "
                "be reflected until the next 'Reset'"
            )
            with gr.Row() as preferences_row1:
                max_iterations = gr.Number(
                    label="Max Iterations",
                    info="The number of steps the executor can take before the conversation is terminated with an "
                         "error message.",
                )
                max_execution_time = gr.Slider(
                    minimum=0,
                    maximum=30,
                    label="Max Execution Time",
                    step=0.5,
                    info="The maximum amount of time the executor can take before the "
                         "conversation is terminated with an error message.",
                )
                executor_temp = gr.Slider(
                    minimum=0,
                    maximum=2,
                    label="ExecutorLLM Temp",
                    step=0.1,
                    info="Higher temperatures will result in more random responses.",
                )

            with gr.Row() as preferences_row2:
                # prompt_layer_tags = gr.Textbox(
                #     label="Prompt Layer Tags",
                #     info="A comma separated string containing the tags to be used in the " "prompt layer.",
                # )
                executor_model_type = gr.Dropdown(
                    choices=[
                        "chat",
                        # 'completion',
                        "function",
                    ],
                    label="Chat Model Type",
                    info="Function models are special OpenAI fine-tuned versions of chat models GPT-3.5 and GPT-4.",
                )

                chat_model = gr.Dropdown(
                    choices=[
                        "gpt-4–0613",
                        "gpt-3.5-turbo-0613",
                        "gpt-4",
                        "gpt-4-32k",
                        "gpt-3.5-turbo",
                    ],
                    label="Executor Chat Model",
                    info="Choose gpt-4–0613 or gpt-3.5-turbo-0613 for 'function' models.",
                )

                # executor_completion_model = gr.Dropdown( choices=["text-davinci-003", "text-davinci-002",
                # "text-curie-001", "text-babbage-001", "text-ada-001"], label="Executor Completion Model",
                # info="This is the model used when Executor Model Type is set to 'completion'" )

            with gr.Row() as preferences_row3:
                tool_names = openbrain.orm.model_agent_config.DefaultSettings.AVAILABLE_TOOLS.value
                tool_names.sort()
                tools = gr.CheckboxGroup(tool_names, label="Tools", info="Select tools to enable for the agent")

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

        with gr.Tab("API Keys and contact info") as api_keys_tab:
            outgoing_webhook_url = gr.Textbox(
                label="Outgoing Webhook URL",
                info="LeadMomentum webhook URL",
                type="text",
            )

            openai_api_key = gr.Textbox(
                label="OpenAI API Key",
                info="The API key for OpenAI's API",
                type="password",
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
                    chat_model,
                    system_message,
                    # prompt_layer_tags,
                    max_iterations,
                    max_execution_time,
                    executor_temp,
                    profile_name,
                    executor_model_type,
                    # executor_completion_model,
                    openai_api_key,
                    # promptlayer_api_key,
                    client_id,
                    outgoing_webhook_url,
                    tools
                ]

                load_button.click(load, inputs=[profile_name, client_id], outputs=preferences)

                save_button.click(
                    save,
                    inputs=[
                        icebreaker,
                        chat_model,
                        system_message,
                        # prompt_layer_tags,
                        max_iterations,
                        max_execution_time,
                        executor_temp,
                        profile_name,
                        executor_model_type,
                        openai_api_key,
                        # promptlayer_api_key,
                        client_id,
                        outgoing_webhook_url,
                        tools
                    ],
                )

    with gr.Accordion("Chat") as chat_accordian:
        with gr.Row() as chat_row:
            with gr.Column(scale=2) as chat_container:
                with gr.Accordion("Chat") as chat_box_accordian:
                    with gr.Column(scale=2) as chat_column:
                        chatbot = gr.Chatbot()

                        msg = gr.Textbox()

            with gr.Column(scale=1) as context_container:

                with gr.Tab("Context"):
                    with gr.Accordion("Context", open=True) as context_accordian:
                        context = gr.Textbox(
                            label="Context",
                            info="Additional context for tools",
                            show_label=False,
                            show_copy_button=True,
                            lines=4,
                            value=EXAMPLE_CONTEXT,
                        )
                with gr.Tab("Actions"):
                    with gr.Accordion("Action Events") as events_accordian:
                        # events_str = get_action_events()
                        # events = gr.Json(value=events_str, label="Latest action event recorded.")
                        events = gr.Json(value=get_action_events, every=15.0, label="Latest action event recorded.")
                        refresh_events_button = gr.Button("Refresh", size="sm", variant="secondary")
                        refresh_events_button.click(get_action_events, inputs=[events], outputs=[events])

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


def main():
    if GRADIO_PASSWORD:
        main_block.launch(
            debug=True,
            share=False,
            server_name="0.0.0.0",
            server_port=PORT,
            auth=auth,
            auth_message="Please login to continue",
        )
    else:
        main_block.launch(
            debug=True,
            share=False,
            server_name="0.0.0.0",
            server_port=PORT,
        )


if "__main__" == __name__:
    main()
