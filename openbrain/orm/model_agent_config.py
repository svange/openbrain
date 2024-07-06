import datetime
import os
import random
from enum import Enum
from typing import Optional, TypeAlias

import pytz
import ulid
from pydantic import BaseModel, Field

from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel

from openbrain.util import config, Defaults

TAgentConfig: TypeAlias = "AgentConfig"

EXECUTOR_MODEL_TYPES = [
    "function",
    "chat",
    "completion"]

COMPLETION_LANGUAGE_MODELS = [
    "davinci-002"
    "babbage-002"
]
CHAT_LANGUAGE_MODELS = [
    "gpt-4-32k",
    "text-davinci-003",
    "gpt-3.5-turbo-16k",
]
FUNCTION_LANGUAGE_MODELS = [
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    "gpt-4-turbo-preview",
    "gpt-4-0125-preview",
    "gpt-4-1106-preview",
    "gpt-4",
    "gpt-4-0613",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0613"
]

class DefaultSettings(Enum):
    """Default settings for the agent config"""
    CLIENT_ID = Defaults.DEFAULT_CLIENT_ID.value
    PROFILE_NAME = Defaults.DEFAULT_PROFILE_NAME.value

    ICEBREAKER = """Ahoy! Ready to get started? What's up?"""
    SYSTEM_MESSAGE = "You are a helpful assistant showing off your capabilities as an AI assistant. You speak like a stereotypical reddit user."

    EXECUTOR_TEMP = 0.0
    MAX_EXECUTION_TIME = 45
    MAX_ITERATIONS = 10

    LLM = "gpt-3.5-turbo-0613"
    TOOLS = []

    RECORD_TOOL_ACTIONS: bool = False
    RECORD_CONVERSATIONS: bool = False


class AgentConfig(ORMModel, BaseModel):
    """Represents the values for the tunable parameters of the agent"""
    @staticmethod
    def dynamic_system_message():
        greetings = [
            "Welcome! Ready to explore?",
            "Hello! How can I make your day better?",
            "Hi there! Excited to assist you today."
        ]

        central_time_zone = pytz.timezone("America/Chicago")
        time_of_day = datetime.datetime.now(central_time_zone).hour
        if 5 <= time_of_day < 12:
            time_specific_greeting = "Good morning! Let's start the day with a smile. 😊"
        elif 12 <= time_of_day < 18:
            time_specific_greeting = "Good afternoon! What can I do for you?"
        else:
            time_specific_greeting = "Good evening! Can I help you wind down or gear up for tomorrow?"

        fun_facts = [
            "Did you know? The first AI program was written in 1951.",
            "Fun fact: AI can learn to play video games by itself.",
            "Here's a tip: Break down big tasks into smaller, manageable ones for better productivity.",
            "AI insight: Machine learning models can predict outcomes based on data from the past."
        ]

        return f"{random.choice(greetings)} {time_specific_greeting} {random.choice(fun_facts)}"


    class Meta:
        table_name = config.AGENT_CONFIG_TABLE_NAME
        region = config.AWS_REGION

    # Tracking
    profile_name: str = Field(
        default=DefaultSettings.PROFILE_NAME.value,
        description="The name of the agent config profile",
    )
    client_id: str = Field(
        default=DefaultSettings.CLIENT_ID.value,
        description="The unique id of the client this agent config belongs to",
    )

    executor_id: str = Field(
        default_factory=ulid.ULID().to_uuid().__str__,
        description="A unique identifier for this configuration",
    )

    # Prompts
    system_message: str = Field(
        default=DefaultSettings.SYSTEM_MESSAGE.value,
        repr=False,
        description="The system message to send to the user when they first start chatting with the agent",
    )
    icebreaker: str = Field(
        default=DefaultSettings.ICEBREAKER.value,
        description="The first message to send to the user when they first start chatting with the agent",
    )

    llm: str = Field(
        default=DefaultSettings.LLM.value,
        description="The name of the OpenAI language model to use for the executor",
    )

    executor_max_iterations: int = Field(
        default=DefaultSettings.MAX_ITERATIONS.value,
        description="The maximum number of iterations to run the executor for",
    )
    executor_max_execution_time: int = Field(
        default=DefaultSettings.MAX_EXECUTION_TIME.value,
        description="The maximum number of seconds to run the executor for",
    )
    executor_temp: float = Field(
        default=DefaultSettings.EXECUTOR_TEMP.value,
        description="The temperature to use for the executor",
    )

    # Debugging
    # prompt_layer_tags: str = Field(
    #     default=DefaultSettings.PROMPT_LAYER_TAGS.value,
    #     repr=False,
    #     description="The tags to use for the prompt layer",
    # )

    # # API Keys
    # openai_api_key: Optional[str] = Field(
    #     default=None,
    #     repr=False,
    #     description="OpenAI API key to use with this specific configuration",
    # )
    # promptlayer_api_key: Optional[str] = Field(
    #     default=None,
    #     repr=False,
    #     description="PromptLayer API key to use with this specific configuration",
    # )

    # Integrations
    # outgoing_webhook_url: Optional[str] = Field(
    #     default=DefaultSettings.OUTGOING_WEBHOOK_URL.value,
    #     description="The outgoing webhook url to send leads to",
    # )
    # email_address: Optional[str] = Field(
    #     default=DefaultSettings.EMAIL_ADDRESS.value,
    #     description="The email address associated with this client",
    # )

    tools: Optional[list[str]] = Field(
        # default=[tool: False for tool in DefaultSettings.AVAILABLE_TOOLS.value]
        # default={tool: False for tool in list(DefaultSettings.AVAILABLE_TOOLS.value)},
        default=[],
        description="A list of tool names indicating which tools to enable",
    )
    record_tool_actions: bool = Field(
        default=bool(DefaultSettings.RECORD_TOOL_ACTIONS.value),
        description="If true, records all tool actions in S3 for analysis",
    )
    record_conversations: bool = Field(
        default=bool(DefaultSettings.RECORD_CONVERSATIONS.value),
        description="If true, records all conversations in S3 for analysis. This is not implemented in OpenBrain, "
                    "but should be implemented in your API.",
    )

    def save(self):
        """Save the agent config to the database"""
        return self._save(
            table_name=config.AGENT_CONFIG_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="profile_name",
            hash_key_value=self.client_id,
            range_key_value=self.profile_name,
        )

    @classmethod
    def get(cls, profile_name, client_id) -> TAgentConfig:
        """Get an agent config from the database"""
        agent_config = cls._get(
            table_name=config.AGENT_CONFIG_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="profile_name",
            hash_key_value=client_id,
            range_key_value=profile_name,
        )
        return cls(**agent_config)

    def refresh(self):
        """Update this agent config with the latest values from the database"""
        agent_config_from_db = AgentConfig.get(profile_name=self.profile_name, client_id=self.client_id)

        for key, value in agent_config_from_db.dict().items():
            setattr(self, key, value)
