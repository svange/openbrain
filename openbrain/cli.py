from __future__ import annotations

import os

import click
import sys
from cmd import Cmd

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.util import config, get_logger, get_tracer, get_metrics, Defaults


class CliChatBot(Cmd):
    intro = "Welcome to the OpenBrain chat bot. Type help or ? to list commands.\n"
    prompt = "(openbrain)"

    def __init__(self):
        super().__init__()
        self.agent = GptAgent(
            AgentConfig(client_id=Defaults.DEFAULT_PROFILE_NAME.value, profile_name=Defaults.DEFAULT_PROFILE_NAME.value)
        )

    def do_quit(self, arg):
        """Quit the chat bot."""
        print("Quitting.")
        raise SystemExit

    def default(self, arg):
        """Send a message to the agent."""
        response = self.agent.handle_user_message(arg)
        print("Agent: " + response + "\n")


@click.command()
@click.option("--client_id", default=Defaults.DEFAULT_CLIENT_ID.value, help="The client_id to use")
@click.option("--profile_name", default=Defaults.DEFAULT_PROFILE_NAME.value, help="The profile_name to use")
@click.argument("message", default="No message provided")
def cli(client_id, profile_name, message):
    """Send a message to the agent."""
    try:
        agent_config = AgentConfig.get(client_id=client_id, profile_name=profile_name)
    except Exception as e:
        print(e)
        print(f"Could not find agent config {client_id=}, {profile_name=}, exiting.")
        sys.exit(1)
    agent_config = AgentConfig(client_id=client_id, profile_name=profile_name)
    agent = GptAgent(agent_config)
    response = agent.handle_user_message(message)
    print(response)


@click.command()
def cli_env():
    """Print the .env.example file to stdout."""
    with open(".env.example", "r") as f:
        print(f.read())


@click.command()
def cli_chat():
    CliChatBot().cmdloop()
