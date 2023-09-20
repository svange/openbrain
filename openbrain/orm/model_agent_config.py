import os
from enum import Enum
from typing import Optional, TypeAlias

import ulid
from pydantic import Field, BaseModel

from chalicelib.orm.model_common_base import Recordable
from chalicelib.util import Util

TAgentConfig: TypeAlias = "AgentConfig"


class DefaultSettings(Enum):
    # Default Settings
    EMAIL_ADDRESS = "admin@woxomhealth.com"
    PROFILE_NAME = "default"
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
    CLIENT_ID = "public"

    # Main Templates
    ICEBREAKER = """Hi! Can I get help you get in touch with an agent?"""
    CHAT_SALES_AGENT_SYSTEM_MESSAGE = """You are a helpful assistant tasked with assisting users in contacting health insurance agents after gathering some necessary information. Your main objective is to gather the user's full name, date of birth, medications, state of residence, email, and optionally a phone number while engaging them in conversation. You will ask for the user's information one item at a time. Once all of this information is gathered, you may get the user in touch with an agent.
    """

    # AGENCY_KEY = "default_agency_key"
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


class AgentConfig(Recordable, BaseModel):
    class Meta:
        table_name = Util.AGENT_CONFIG_TABLE_NAME
        region = Util.AWS_REGION

    # Tracking

    profile_name: str = Field(default=DefaultSettings.PROFILE_NAME.value,
                              description="The name of the agent config profile")
    client_id: str = Field(default=DefaultSettings.CLIENT_ID.value,
                           description="The unique id of the client this agent config belongs to")
    session_id: Optional[str] = Field(default=None, repr=False,
                                      description="The session_id this agent config belongs is being used in")

    executor_id: str = Field(default_factory=ulid.ULID().to_uuid().__str__,
                             description="A unique identifier for this configuration")

    # Prompts
    system_message: str = Field(default=DefaultSettings.CHAT_SALES_AGENT_SYSTEM_MESSAGE.value, repr=False,
                                description="The system message to send to the user when they first start chatting with the agent")
    icebreaker: str = Field(default=DefaultSettings.ICEBREAKER.value,
                            description="The first message to send to the user when they first start chatting with the agent")

    # Tuning
    executor_model_type: str = Field(default=DefaultSettings.EXECUTOR_MODEL_TYPE.value,
                                     description="The type of model to use for the executor")
    executor_chat_model: str = Field(default=DefaultSettings.EXECUTOR_CHAT_MODEL.value,
                                     description="The chat model to use for the executor")
    executor_completion_model: str = Field(default=DefaultSettings.EXECUTOR_CHAT_MODEL.value,
                                           description="The completion model to use for the executor")
    executor_max_iterations: int = Field(default=DefaultSettings.MAX_ITERATIONS.value,
                                         description="The maximum number of iterations to run the executor for")
    executor_max_execution_time: int = Field(default=DefaultSettings.MAX_EXECUTION_TIME.value,
                                             description="The maximum number of seconds to run the executor for")
    executor_temp: float = Field(default=DefaultSettings.EXECUTOR_TEMP.value,
                                 description="The temperature to use for the executor")

    # Debugging
    prompt_layer_tags: str = Field(default=DefaultSettings.PROMPT_LAYER_TAGS.value, repr=False,
                                   description="The tags to use for the prompt layer")

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, repr=False, description="OpenAI API key to use with this specific configuration")
    promptlayer_api_key: Optional[str] = Field(default=None, repr=False, description="PromptLayer API key to use with this specific configuration")

    # Integrations
    outgoing_webhook_url: Optional[str] = Field(default=DefaultSettings.OUTGOING_WEBHOOK_URL.value,
                                                description="The outgoing webhook url to send leads to")
    email_address: Optional[str] = Field(default=DefaultSettings.EMAIL_ADDRESS.value,
                                         description="The email address associated with this client")

    def save(self):
        return self._save(
            table_name=Util.AGENT_CONFIG_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="profile_name",
            hash_key_value=self.client_id,
            range_key_value=self.profile_name,
        )

    @classmethod
    def get(cls, profile_name, client_id) -> TAgentConfig:
        agent_config = cls._get(
            table_name=Util.AGENT_CONFIG_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="profile_name",
            hash_key_value=client_id,
            range_key_value=profile_name,
        )

        return cls(**agent_config)

    def refresh(self):
        agent_config_from_db = AgentConfig.get(
            profile_name=self.profile_name, client_id=self.client_id
        )

        for key, value in agent_config_from_db.dict().items():
            setattr(self, key, value)

    # def to_json(self) -> str:
    #     obj_dict = self.dict()
    #     return json.dumps(obj_dict)
    #
    # @classmethod
    # def from_json(cls, serialized_agent_config: str) -> AgentConfig:
    #     json_dict = json.loads(serialized_agent_config)
    #     agent_config = cls(**json_dict)
    #     return agent_config

    # def to_dict(self) -> dict:
    #     return self.dict()
    #
    # @classmethod
    # def from_dict(cls, agent_config_dict: dict) -> AgentConfig:
    #     return cls(**agent_config_dict)

    # def __post_init__(self):
    #     for f in fields(self):
    #         if f.type in [int, Optional[int]]:
    #             if isinstance(getattr(self, f.name), str):
    #                 dec = Decimal(getattr(self, f.name))
    #                 self.name = int(dec)
    #             if isinstance(getattr(self, f.name), Decimal):
    #                 self.name = int(self.name)
