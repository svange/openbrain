from __future__ import annotations

from typing import Optional

from pydantic import Field, BaseModel

from chalicelib.orm.model_agent_config import AgentConfig
from chalicelib.orm.model_common_base import Recordable


class ChatMessage(Recordable, BaseModel):
    # Tracking
    client_id: str = Field(description="The ID of the client the AgentConfig belongs to")
    session_id: Optional[str] = Field(default=None, description="DEPRECATED IN FAVOR OF SESSION HEADER/COOKIE - The session_id associated with this message")

    # Behavior
    reset: Optional[bool] = Field(default=False, description="Reset the session with a new agent configuration")
    agent_config_overrides: Optional[AgentConfig] = Field(default=None, description="Override the agent config", repr=False)
    agent_config: Optional[str] = Field(default=None, description="The profile_name of the base agent configuration to apply")
    message: Optional[str] = Field(default=None, description="The message to send to the agent, ignored when resetting the session")

    @classmethod
    def get(cls, *args, **kwargs) -> ChatMessage:
        raise NotImplementedError("No DB for ChatMessage objects")

    def save(self):
        raise NotImplementedError("No DB for ChatMessage objects")

    def refresh(self):
        raise NotImplementedError("No DB for ChatMessage objects")
