import os

import gradio as gr

from openbrain.ob_tuner.functions.util import INFRA_STACK_NAME as GRADIO_INFRA_STACK_NAME

WELCOME_MESSAGE = f"""
# {GRADIO_INFRA_STACK_NAME} AI Workshop

## Introduction
Welcome to the {GRADIO_INFRA_STACK_NAME} AI Workshop! Build and tune AI agents with ease using this interactive interface. Create AI profiles by choosing it's language model, tools, and other configurations. Interact with the agent through a chat interface and manage the agent's behavior. Once you're happy with what you have, save the bot to your account. You can now interact with this bot using the {GRADIO_INFRA_STACK_NAME} (see the signup link above). Use your {GRADIO_INFRA_STACK_NAME} API key, along with your saved AI profile to make programatic calls to {GRADIO_INFRA_STACK_NAME}.

## Main Features
- Create agent configuration profiles with custom values for:
    - LLM Type - supported types include
        - function
        - chat
        - completion
    - Tools - List of tools the agent can use. To see tool descriptions, navigate to the Tools tab
    - System Message - Message to display when the agent is first started.
    - Icebreaker - Message to display when the agent is first started.
    - LLM - name of the LLM to use (e.g. gpt-3, gpt-4o, etc.)
    - Temperature - Higher values result in spicier agents with less reliable tool use.
    - Max Execution Time - Maximum time allowed for agent to execute a tool.
    - Max Iterations - Maximum number of iterations allowed for agent to execute a tool.
    - Record Chat - Record chat messages for this agent for later analysis.
    - Record Tool Actions - Record tool actions for this agent for later analysis.
- Save and load named agent configuration profiles to/from your account.
- Interact with your named agents, or community (shared) named agents.
- Interact with {GRADIO_INFRA_STACK_NAME} with context to simulate the AI interacting with the Lead Momentum SMS Workflow.
"""

with gr.Blocks() as landing_page:
    # Read the README file content
    gr.Button("Login", link="/login", variant="primary")
    gr.Button("Signup", link="/signup", variant="secondary")

    with gr.Accordion("Welcome!"):
        with gr.Tab(f"Welcome to {GRADIO_INFRA_STACK_NAME}"):
            gr.Markdown(WELCOME_MESSAGE)

        with gr.Tab("Technical Information"):
            with open("README.md", "r") as file:
                readme_content = file.read()
            gr.Markdown(readme_content)
