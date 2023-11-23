import logging
import os

import boto3
import gradio as gr
import requests
from dotenv import load_dotenv

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_chat_message import ChatMessage
from openbrain.orm.model_chat_session import ChatSession
from openbrain.orm.model_lead import Lead
from openbrain.util import config, Defaults


load_dotenv()

OB_MODE = config.OB_MODE
CHAT_ENDPOINT = os.environ.get("OB_API_URL", "") + "/chat"

DEFAULT_ORIGIN = os.environ.get("DEFAULT_ORIGIN", "https://localhost:5173")
OB_PROVIDER_API_KEY = os.environ.get("OB_PROVIDER_API_KEY", "")


DEFAULT_CLIENT_ID = Defaults.DEFAULT_CLIENT_ID.value
DEFAULT_PROFILE_NAME = Defaults.DEFAULT_PROFILE_NAME.value
PORT = int(os.environ.get("GRADIO_PORT", 7861))

if OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import InMemoryDb

logging.basicConfig(filename="app.log", encoding="utf-8", level=logging.DEBUG)


def chat(message, chat_history, _profile_name, session_state, _client_id):
    # Make a POST request to the chat endpoint

    session_id = session_state["session_id"]

    chat_message = ChatMessage(client_id=_client_id, reset=False, message=message, session_id=session_id)

    response_message = None
    if OB_MODE == Defaults.OB_MODE_LOCAL.value:
        chat_session = ChatSession.get(session_id=session_id, client_id=_client_id)
        agent_state = {
            "frozen_agent_memory": chat_session.frozen_agent_memory,
            "frozen_agent_config": chat_session.frozen_agent_config,
            "frozen_lead": chat_session.frozen_lead,
        }
        gpt_agent = GptAgent.deserialize(state=agent_state)

        response_message = gpt_agent.handle_user_message(message)

        frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
        frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]
        frozen_lead = gpt_agent.serialize()["frozen_lead"]

        chat_session = ChatSession(
            session_id=session_id,
            client_id=_client_id,
            frozen_agent_memory=frozen_agent_memory,
            frozen_agent_config=frozen_agent_config,
            frozen_lead=frozen_lead,
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
        response = session.post(CHAT_ENDPOINT, json=chat_message.to_json())
        response_message = response.json()["message"]
        session_state["session"] = session
    session_state["last_response"] = response_message

    chat_history.append([message, response_message])

    # Return the response from the API
    return ["", chat_history, session_state]


def reset(
    _icebreaker,
    _chat_model,
    _system_message,
    _prompt_layer_tags,
    _max_iterations,
    _max_execution_time,
    _executor_temp,
    _profile_name,
    _executor_model_type,
    _openai_api_key,
    _promptlayer_api_key,
    _client_id,
    _outgoing_webhook_url,
    _message,
    chat_history,
    session_state,
):
    chat_message = ChatMessage(
        client_id=_client_id,
        reset=True,
        message="no message",
        agent_config=_profile_name,
    )

    response = None
    if OB_MODE == Defaults.OB_MODE_LOCAL.value:
        # Get a new agent with the specified settings
        agent_config = AgentConfig.get(profile_name=_profile_name, client_id=_client_id)
        lead = Lead(client_id=_client_id)
        gpt_agent = GptAgent(agent_config=agent_config, lead=lead)

        frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
        frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]
        frozen_lead = gpt_agent.serialize()["frozen_lead"]

        chat_session = ChatSession(
            client_id=_client_id,
            frozen_agent_memory=frozen_agent_memory,
            frozen_agent_config=frozen_agent_config,
            frozen_lead=frozen_lead,
        )
        session_id = chat_session.session_id
        session_state["session_id"] = session_id
        chat_session.save()
        response_message = gpt_agent.agent_config.icebreaker
    else:
        # Make a POST request to the reset endpoint
        session = session_state["session"]
        session.headers.update(
            {
                "x-api-key": OB_PROVIDER_API_KEY,
                "origin": DEFAULT_ORIGIN,
             }
        )
        response = session.post(CHAT_ENDPOINT, json=chat_message.to_json())
        session_id = response.cookies["Session"]
        session_state["session_id"] = session_id
        session_state["session"] = session
        session_state["last_response"] = response
        response_message = response.json()["message"]
    message = f"Please wait, fetching new agent..."
    chat_history.append([message, response_message])

    # Return the response from the API
    return ["", chat_history, session_state]


def save(
    _icebreaker,
    _chat_model,
    _system_message,
    _prompt_layer_tags,
    _max_iterations,
    _max_execution_time,
    _executor_temp,
    _profile_name,
    _executor_model_type,
    _openai_api_key,
    _promptlayer_api_key,
    client_id,
    outgoing_webhook_url,
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
        prompt_layer_tags=str(_prompt_layer_tags),
        executor_max_iterations=str(_max_iterations),
        executor_max_execution_time=str(_max_execution_time),
        executor_temp=str(_executor_temp),
        profile_name=str(_profile_name),
        executor_model_type=str(_executor_model_type),
        openai_api_key=str(_openai_api_key),
        promptlayer_api_key=str(_promptlayer_api_key),
        client_id=str(client_id),
        outgoing_webhook_url=str(outgoing_webhook_url),
    )

    # Upload the preferences to the DynamoDB database
    agent_config.save()

    # Return a success message
    return "Preferences saved successfully."


def load(_profile_name: str, _client_id: str):
    if _profile_name.strip() == "":
        raise gr.Error("client_id can't be blank.")
    # Upload the preferences to the DynamoDB database
    if not _client_id:
        _client_id = DEFAULT_CLIENT_ID
    retrieved_agent_config = AgentConfig.get(profile_name=_profile_name, client_id=_client_id)

    _agent_config = [
        str(retrieved_agent_config.icebreaker),
        str(retrieved_agent_config.executor_chat_model),
        str(retrieved_agent_config.system_message),
        str(retrieved_agent_config.prompt_layer_tags),
        str(retrieved_agent_config.executor_max_iterations),
        str(retrieved_agent_config.executor_max_execution_time),
        str(retrieved_agent_config.executor_temp),
        str(retrieved_agent_config.profile_name),
        str(retrieved_agent_config.executor_model_type),
        str(retrieved_agent_config.openai_api_key),
        str(retrieved_agent_config.promptlayer_api_key),
        str(retrieved_agent_config.client_id),
        str(retrieved_agent_config.outgoing_webhook_url),
    ]

    # Return a success message
    return _agent_config


def is_settings_set():
    return True


def auth(username, password):
    if username in ["sam", "mike", "adam"]:
        if password == "BieberFever!":
            return True
    return False


def get_available_profile_names() -> list:
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
    with gr.Accordion("Tuning", elem_classes="accordion", visible=is_settings_set()) as prompts_box:
        gr.Markdown(
            "Changes to these settings are used to set up a conversation using the Reset button and will not "
            "be reflected until the next 'Reset'"
        )

        with gr.Tab("LLM Tuning") as tuninig_tab:
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
                prompt_layer_tags = gr.Textbox(
                    label="Prompt Layer Tags",
                    info="A comma separated string containing the tags to be used in the " "prompt layer.",
                )
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
            promptlayer_api_key = gr.Textbox(
                label="Prompt Layer API Key",
                info="The API key for Prompt Layer's API",
                type="password",
            )

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
            with gr.Column(scale=4) as key_text_column:
                client_id = gr.Textbox(
                    label="Client ID",
                    info="Your client ID. If left blank, defaults to 'public'.",
                    type="text",
                )
                client_id.value = DEFAULT_CLIENT_ID
                profile_name = gr.Dropdown(
                    allow_custom_value=True,
                    label="Profile Name",
                    info="Enter a unique string to save your preferences. This will " "allow you to load your preferences later.",
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
                    prompt_layer_tags,
                    max_iterations,
                    max_execution_time,
                    executor_temp,
                    profile_name,
                    executor_model_type,
                    # executor_completion_model,
                    openai_api_key,
                    promptlayer_api_key,
                    client_id,
                    outgoing_webhook_url,
                ]

                load_button.click(load, inputs=[profile_name, client_id], outputs=preferences)

                save_button.click(
                    save,
                    inputs=[
                        icebreaker,
                        chat_model,
                        system_message,
                        prompt_layer_tags,
                        max_iterations,
                        max_execution_time,
                        executor_temp,
                        profile_name,
                        executor_model_type,
                        openai_api_key,
                        promptlayer_api_key,
                        client_id,
                        outgoing_webhook_url,
                    ],
                )

    chatbot = gr.Chatbot()

    with gr.Row() as chat_row:
        with gr.Column(scale=4) as chat_column:
            msg = gr.Textbox()
        with gr.Column(scale=1) as chat_button_column:
            chat_button = gr.Button("Chat", variant="primary")
            reset_agent = gr.Button("Reset", variant="secondary")

            msg.submit(
                chat,
                [msg, chatbot, profile_name, session_state, client_id],
                [msg, chatbot, session_state],
            )

            chat_button.click(
                fn=chat,
                inputs=[msg, chatbot, profile_name, session_state, client_id],
                outputs=[msg, chatbot, session_state],
            )

            reset_agent.click(
                fn=reset,
                inputs=[
                    icebreaker,
                    chat_model,
                    system_message,
                    prompt_layer_tags,
                    max_iterations,
                    max_execution_time,
                    executor_temp,
                    profile_name,
                    executor_model_type,
                    openai_api_key,
                    promptlayer_api_key,
                    client_id,
                    outgoing_webhook_url,
                    msg,
                    chatbot,
                    session_state,
                ],
                outputs=[msg, chatbot, session_state],
            )


def main():
    # auth = gr.auth(username="admin", password="admin")'
    # main_block.launch(auth=auth, auth_message="Please login to continue", share=False, debug=True,
    #                   server_name="0.0.0.0", server_port=7861, show_tips=True, )
    # reset the public default profile
    # agent_config = AgentConfig(client_id=DEFAULT_CLIENT_ID, profile_name=DEFAULT_PROFILE_NAME)
    # agent_config.save()
    main_block.launch(
        debug=True,
        share=False,
        server_name="0.0.0.0",
        server_port=PORT,
        show_tips=True,
        auth=auth,
        auth_message="Please login to continue",
    )


if "__main__" == __name__:
    main()
