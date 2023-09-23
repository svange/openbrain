from __future__ import annotations

import sys
from cmd import Cmd

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_agent_config import AgentConfig


class CliChatBot(Cmd):
    intro = "Welcome to the OpenBrain chat bot. Type help or ? to list commands.\n"
    prompt = "(openbrain)"

    def __init__(self):
        super().__init__()
        self.agent = GptAgent(AgentConfig(client_id="public", profile_name="default"))

    def do_quit(self, arg):
        """Quit the chat bot."""
        print("Quitting.")
        raise SystemExit

    def default(self, arg):
        """Send a message to the agent."""
        response = self.agent.handle_user_message(arg)
        print("Agent: " + response + "\n")


def cli():
    message = sys.argv[1] if len(sys.argv) > 1 else "No message provided"
    agent = GptAgent(AgentConfig(client_id="public", profile_name="default"))
    response = agent.handle_user_message(message)
    print(response)


def cli_chat():
    CliChatBot().cmdloop()
