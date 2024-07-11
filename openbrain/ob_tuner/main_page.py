import gradio
import requests
import ulid

from openbrain.ob_tuner.functions.util import *
from openbrain.ob_tuner.functions.button_logic import *

import openbrain.orm.model_agent_config
from openbrain.tools import Toolbox

with gr.Blocks(theme="JohnSmith9982/small_and_pretty") as main_block:
    # m = gr.Markdown(f"Welcome to Gradio! {greet(Request)}")
    # gr.Button("Logout", link="/logout")
    username = gr.Textbox("", label="username", visible=False)

    session_state = gr.State(value={"session_id": "", "session": requests.Session(), "agent": None, "last_response": None, "username": ""})
    main_block.load(initialize_username, [session_state], [username, session_state])
    session_apikey = gr.State(value="")

    with gr.Accordion("My Resources") as submit_accordion:
        with gr.Tab("Selected Agent Configuration") as submit_tab:
            with gr.Row() as submit_row:
                with gr.Column(scale=3) as key_text_column:
                    with gr.Row() as key_text_row:

                        client_id = gr.Dropdown(
                            label="Client ID",
                            info="Develop your own AI agents or use a community agent.",
                            choices=[DEFAULT_CLIENT_ID],
                            value=DEFAULT_CLIENT_ID,
                        )
                        initial_profile_names = get_available_profile_names(client_id=client_id.value)
                        profile_name = gr.Dropdown(
                            allow_custom_value=True,
                            label="Profile Name",
                            info="The name of your AgentConfig. Defaults to 'default'",
                            choices=initial_profile_names,
                            value=DEFAULT_PROFILE_NAME,
                        )

                with gr.Column(scale=1) as submit_column:
                    load_agent_profile_button = gr.Button(value="Load", variant="primary")
                    save_agent_profile_button = gr.Button(value="Save", variant="secondary")

        with gr.Tab("User Profile") as user_profile_tab:
            with gr.Column():
                gr.Markdown("Information about you. When the AI agent uses tools, it will do so as you. For this reason, it will need your API keys and other identifying information.")
                with gr.Row():
                    with gr.Accordion("Lead Momentum Integration") as leadmo_box:
                        with gr.Column():
                            leadmo_api_key = gr.Textbox(info="Lead Momentum API Key", label="Lead Momentum API Key", type="password", placeholder="YourLeadMoAPIKey")
                            leadmo_location_id = gr.Textbox(info="Lead Momentum 'Location ID'", label="Lead Momentum Location ID", placeholder="YourLeadMoLocationID")
                    with gr.Accordion("Landline Scrubber Integration") as lls_box:
                        lls_api_key = gr.Textbox(info="Landline Scrubber API Key", label="Landline Scrubber API Key", type="password", placeholder="YourLeadMoAPIKey")
            with gr.Row():
                gr.Button("Save", size="sm", variant="primary")
                gr.Button("reload", size="sm", variant="secondary")

    with gr.Accordion("AI Agent Configuration and Tuning", elem_classes="accordion", visible=is_settings_set(), open=False) as prompts_box:

        with gr.Tab("LLM Parameters") as tuning_tab:
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
                    info="The language model to use for completion",
                )

                with gr.Column() as extra_options_column:
                    record_tool_actions = gr.Checkbox(
                        label="Record Tool Actions", info="Record tool actions (use 'Actions' box)."
                    )
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
            tools = gr.CheckboxGroup(choices=TOOL_NAMES, value=[], label="Tools", info="Select tools to enable for the agent")

            gr.Markdown(
                value="Tool descriptions as presented to the AI. Confusing text here could lead to inconsistent use of tools."
            )
            _tools = Toolbox.discovered_tools
            with gr.Column() as tool_accordion:
                for _tool in _tools:
                    with gr.Tab(_tool.name):
                        gr.Markdown(value=get_tool_description(_tool.name))

            # tool_names = openbrain.orm.model_agent_config.DefaultSettings.AVAILABLE_TOOLS.value

        with gr.Tab("Tool Context") as tool_context_row:
            msg = """# Instructions\n\nWhen your AI uses tools, it may need to leverage information that never came up in the conversation. For example, the AI can't see your appointment times without your calendarId. A workflow in Lead Momentum sends these data with every request. In order a tool, the appropriate context may be present."""
            gr.Markdown(msg)
            with gr.Column():
                with gr.Accordion(label="Lead Momentum", open=False):
                    with gr.Row(equal_height=True):
                        with gr.Column():
                            context_calendarId = gr.Textbox(info="Lead Momentum Calendar ID", label="Calendar ID", placeholder="YourCalendarID")
                            context_contact_id = gr.Textbox(info="Lead Momentum Contact ID", label="Contact ID", placeholder="ContactID")
                            context_firstName = gr.Textbox(info="Contact First Name", label="First Name", placeholder="Deez")
                            context_lastName = gr.Textbox(info="Contact Last Name", label="Last Name", placeholder="Nutzington")
                            context_name = gr.Textbox(info="Contact Name", label="Name", placeholder="Your Mother")
                            context_dateOfBirth = gr.Textbox(info="Contact DoB", label="Date of Birth", placeholder="1970-04-01")
                        with gr.Column():
                            context_phone = gr.Textbox(info="Contact Phone", label="Phone", placeholder="+16198675309")
                            context_email = gr.Textbox(info="Contact Email", label="Email", placeholder="e@my.ass")
                            context_address1 = gr.Textbox(info="Contact Address 1", label="Address 1", placeholder="123 4th St.")
                            context_city = gr.Textbox(info="Contact City", label="City", placeholder="San Diego")
                            context_state = gr.Textbox(info="Contact State", label="State", placeholder="CA")
                        with gr.Column():
                            context_country = gr.Textbox(info="Contact Country", label="Country", placeholder="USA")
                            context_postalCode = gr.Textbox(info="Contact Postal Code", label="Postal Code", placeholder="92108")
                            context_companyName = gr.Textbox(info="Contact Company Name", label="Company Name", placeholder="Augmenting Integrations")
                            context_website = gr.Textbox(info="Contact Website", label="Website", placeholder="openbra.in")
                            context_medications = gr.Textbox(info="Contact Medications", label="Medications", placeholder="vicodin")
                with gr.Accordion(label="OpenBra.in", open=False):
                     context_random_word = gr.Textbox(info="Random word", label="Random Word", placeholder="Rambutan", value="Rambutan")

                context_save_button = gr.Button("Save", variant="secondary")


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

        with gr.Tab("Documentation") as help_tab:
            gr.Markdown(value=get_help_text())

        with gr.Tab("Conversation Analysis") as conversation_analysis_tab:
            gr.Markdown(value="NOT IMPLEMENTED")


    with gr.Accordion("Interact with Agent") as chat_accordian:
        with gr.Row() as chat_row:
            with gr.Column(scale=2) as chat_container:
                with gr.Column(scale=2) as chat_column:
                    chatbot = gr.Chatbot(
                        show_share_button=True,
                        show_copy_button=True,
                        # avatar=(user_avatar_path, ai_avatar_path),
                        likeable=True,
                        # layout="panel",
                        layout="bubble",

                    )

                    msg = gr.Textbox()

            with gr.Column(scale=1) as context_container:
                initial_value_str = json.loads(json.dumps({
                    "random_word": "Rambutan"
                }))

                # context = gr.JSON(
                #     label="Context",
                #     value=initial_value_str
                # )
                context = gr.Textbox(
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

    with gr.Accordion("Debugging", open=False) as debug_box:
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
                # every=3.0,
            )
            refresh_api_logs_button = gr.Button("Refresh", size="sm", variant="secondary")

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

        with gr.Tab("Action Event Logs"):
            # events_str = get_action_events()
            # events = gr.Json(value=events_str, label="Latest action event recorded.")
            events = gr.Json(
                value=get_action_events,
                # every=15.0,
                label="Latest action recorded.",
            )

            refresh_events_button = gr.Button("Refresh", size="sm", variant="secondary")


    user_context_list = [
        leadmo_location_id,
        context_calendarId,
        context_contact_id,
        context_firstName,
        context_lastName,
        context_name,
        context_dateOfBirth,
        context_phone,
        context_email,
        context_address1,
        context_city,
        context_state,
        context_country,
        context_postalCode,
        context_companyName,
        context_website,
        context_medications,
        context_random_word,
    ]

    preferences = [
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
        tools,
        llm_types,
    ]

    # Refresh Buttons
    refresh_bottom_text_button = gr.Markdown(value=get_bottom_text(), rtl=True)
    refresh_api_logs_button.click(get_aws_cloudwatch_logs, inputs=[session_state], outputs=[api_debug_text])
    refresh_agent_logs_button.click(get_gpt_agent_logs, outputs=[agent_debug_text])
    refresh_events_button.click(get_action_events, inputs=[events, session_state], outputs=[events])

    # Save Context Button
    context_save_button.click(save_context, inputs=[*user_context_list])

    # Save Agent Button
    save_agent_profile_button.click(
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
            tools,
        ],
    )

    # Load Agent Button
    load_agent_profile_button.click(load, inputs=[profile_name, client_id], outputs=preferences)

    # Chat Button
    chat_button.click(
        fn=chat,
        inputs=[msg, chatbot, profile_name, session_state, client_id, context],
        outputs=[msg, chatbot, session_state, context],
    )
    chat_button.click(get_aws_cloudwatch_logs, inputs=[session_state], outputs=[agent_debug_text])

    # Chat Reset Button
    reset_agent.click(
        fn=reset,
        inputs=[client_id, profile_name, chatbot, session_state, context],
        outputs=[msg, chatbot, session_state, context],
    )
    # reset_agent.click(get_bottom_text, inputs=[session_state, profile_name, client_id], outputs=[context])
    reset_agent.click(get_aws_cloudwatch_logs, inputs=[session_state], outputs=[agent_debug_text])
    reset_agent.click(get_action_events, inputs=[events, session_state], outputs=[events])

    # On Change Events
    llm_types.change(get_llm_choices, inputs=[llm_types], outputs=[llm])
    client_id.change(update_available_profile_names, inputs=[client_id], outputs=[profile_name])

    username.change(get_session_username, inputs=[session_state], outputs=[client_id])

    # leadmo_location_id.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_calendarId.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_contact_id.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_calendarId.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_firstName.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_lastName.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_name.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_dateOfBirth.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_phone.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_email.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_address1.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_city.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_state.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_country.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_postalCode.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_companyName.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_website.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_medications.change(get_context, inputs=[*user_context_list], outputs=[context])
    # context_random_word.change(get_context, inputs=[*user_context_list], outputs=[context])


if __name__ == "__main__":
    if os.getenv("GRADIO_PORT", False) or os.getenv("GRADIO_HOST", False):
        # gradio_host = os.getenv("GRADIO_HOST", '0.0.0.0')
        # gradio_port = int(os.getenv("GRADIO_PORT", 7861))
        gradio_host = '0.0.0.0'
        gradio_port = 7861
        main_block.launch(
            debug=True,
            share=False,
            server_name=gradio_host,
            server_port=gradio_port,
        )
