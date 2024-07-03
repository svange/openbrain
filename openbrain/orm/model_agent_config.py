import os
from enum import Enum
from typing import Optional, TypeAlias

import ulid
from pydantic import BaseModel, Field

from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel

from openbrain.util import config, Defaults

TAgentConfig: TypeAlias = "AgentConfig"


class DefaultSettings(Enum):
    """Default settings for the agent config"""

    # Tools
    AVAILABLE_TOOLS = [
                        "get_current_time",
                        "tester",
                        "leadmo_update_contact",
                        "leadmo_stop_conversation",
                        "leadmo_get_simple_calendar_appointment_slots",
                        "leadmo_create_appointment",
                        "leadmo_create_contact",
                        "lls_scrub_phone_number",
                        "leadmo_get_contact_info_from_context"
                       ]

    TOOLS = []

    # Default Settings
    EMAIL_ADDRESS = "example@email.com"
    PROFILE_NAME = Defaults.DEFAULT_PROFILE_NAME.value
    EXECUTOR_MODEL_TYPE = "function"
    EXECUTOR_TEMP = 0.0
    MAX_EXECUTION_TIME = 10
    MAX_ITERATIONS = 3
    ENABLE_PROMPT_LAYER = False
    EXECUTOR_CHAT_MODEL = "gpt-3.5-turbo-0613"
    EXECUTOR_COMPLETION_MODEL = "text-davinci-003"
    PROMPT_LAYER_TAGS = ""
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    PROMPTLAYER_API_KEY = os.environ.get("PROMPTLAYER_API_KEY", "")
    CLIENT_ID = Defaults.DEFAULT_CLIENT_ID.value

    # Main Templates
    ICEBREAKER = """Hi! Can I get help you get in touch with an agent?"""
    CHAT_SALES_AGENT_SYSTEM_MESSAGE = """You are a highly skilled Software Developer with a keen eye for design
    patterns. You always think about your suggestions step-by-step in order to come up with the best answer. You
    criticize your own work and suggestions made to you. Your only loyalty is to the code. You are a Software
    Developer and you are here to help."""
    OUTGOING_WEBHOOK_URL = "default_outgoing_webhook_url"

    EXECUTOR_MODEL_TYPES = ["function", "chat", "completion"]
    EXECUTOR_COMPLETION_MODELS = [
        "gpt-4–0613",
        "gpt-3.5-turbo-0613",
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
    ]
    EXECUTOR_CHAT_MODELS = [
        "gpt-4–0613",
        "gpt-3.5-turbo-0613",
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "text-davinci-003",
        "gpt-3.5-turbo-16k",
    ]


class AgentConfig(ORMModel, BaseModel):
    """Represents the values for the tunable parameters of the agent"""

    class Meta:
        table_name = config.AGENT_CONFIG_TABLE_NAME
        region = config.AWS_REGION

    # Tools
    # @staticmethod
    # def available_tools():
    #     """Return a list of available tools"""
    #     return DefaultSettings.AVAILABLE_TOOLS.value

    def get_enabled_tool_names(self):
        """Return a list of enabled tool names"""
        return [tool for tool, enabled in self.tools.items() if enabled]


    # Tracking
    profile_name: str = Field(
        default=DefaultSettings.PROFILE_NAME.value,
        description="The name of the agent config profile",
    )
    client_id: str = Field(
        default=DefaultSettings.CLIENT_ID.value,
        description="The unique id of the client this agent config belongs to",
    )
    session_id: Optional[str] = Field(
        default=None,
        repr=False,
        description="The session_id this agent config belongs is being used in",
    )

    executor_id: str = Field(
        default_factory=ulid.ULID().to_uuid().__str__,
        description="A unique identifier for this configuration",
    )

    # Prompts
    system_message: str = Field(
        default=DefaultSettings.CHAT_SALES_AGENT_SYSTEM_MESSAGE.value,
        repr=False,
        description="The system message to send to the user when they first start chatting with the agent",
    )
    icebreaker: str = Field(
        default=DefaultSettings.ICEBREAKER.value,
        description="The first message to send to the user when they first start chatting with the agent",
    )

    # Tuning
    executor_model_type: str = Field(
        default=DefaultSettings.EXECUTOR_MODEL_TYPE.value,
        description="The type of model to use for the executor",
    )
    executor_chat_model: str = Field(
        default=DefaultSettings.EXECUTOR_CHAT_MODEL.value,
        description="The chat model to use for the executor",
    )
    executor_completion_model: str = Field(
        default=DefaultSettings.EXECUTOR_CHAT_MODEL.value,
        description="The completion model to use for the executor",
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
    prompt_layer_tags: str = Field(
        default=DefaultSettings.PROMPT_LAYER_TAGS.value,
        repr=False,
        description="The tags to use for the prompt layer",
    )

    # API Keys
    openai_api_key: Optional[str] = Field(
        default=None,
        repr=False,
        description="OpenAI API key to use with this specific configuration",
    )
    promptlayer_api_key: Optional[str] = Field(
        default=None,
        repr=False,
        description="PromptLayer API key to use with this specific configuration",
    )

    # Integrations
    outgoing_webhook_url: Optional[str] = Field(
        default=DefaultSettings.OUTGOING_WEBHOOK_URL.value,
        description="The outgoing webhook url to send leads to",
    )
    email_address: Optional[str] = Field(
        default=DefaultSettings.EMAIL_ADDRESS.value,
        description="The email address associated with this client",
    )

    tools: Optional[list[str]] = Field(
        # default=[tool: False for tool in DefaultSettings.AVAILABLE_TOOLS.value]
        # default={tool: False for tool in list(DefaultSettings.AVAILABLE_TOOLS.value)},
        default=[],
        description="A list of tool names indicating which tools to enable",
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
