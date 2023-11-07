from __future__ import annotations

import os

from pydantic import BaseModel, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel


class ChatMessage(ORMModel, BaseModel):
    """Represents a message sent to the agent"""

    # Tracking
    client_id: str = Field(description="The ID of the client the AgentConfig belongs to")
    session_id: str | None = Field(
        default=None,
        description="DEPRECATED IN FAVOR OF SESSION HEADER/COOKIE - The session_id associated with this message",
    )

    # Behavior
    reset: bool | None = Field(default=False, description="Reset the session with a new agent configuration")
    agent_config_overrides: AgentConfig | None = Field(default=None, description="Override the agent config", repr=False)
    agent_config: str | None = Field(
        default=None,
        description="The profile_name of the base agent configuration to apply",
    )
    message: str | None = Field(
        default=None,
        description="The message to send to the agent, ignored when resetting the session",
    )

    @classmethod
    def get(cls, *args, **kwargs) -> ChatMessage:
        """Get a ChatMessage object from the database"""
        raise NotImplementedError("No DB for ChatMessage objects")

    def save(self):
        """Save the ChatMessage object to the database"""
        raise NotImplementedError("No DB for ChatMessage objects")

    def refresh(self):
        """Update this ChatMessage object with the latest values from the database"""
        raise NotImplementedError("No DB for ChatMessage objects")
