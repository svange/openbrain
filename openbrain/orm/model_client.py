from __future__ import annotations

from typing import TypeAlias, Optional

from pydantic import BaseModel, Field, Extra
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel

TClient: TypeAlias = "Client"

class Client(ORMModel, BaseModel):
    """Represents a message sent to the agent"""
    class Config:
        extra = Extra.allow

    # Tracking
    client_id: str = Field(description="The ID of the client this should match the cognito:username")
    email: str = Field(description="The email of the client")
    roles: Optional[list[str]] = Field(description="The roles of the client")

    leadmo_api_key: Optional[list[str]] = Field(description="The API key for the Leadmo API")
    leadmo_location_id: Optional[list[str]] = Field(description="The location ID for the Leadmo API")
    lls_api_key: Optional[list[str]] = Field(description="The API key for the LLS API")

    class Meta:
        table_name = config.CLIENT_TABLE_NAME
        region = config.AWS_REGION

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
    def get(cls, profile_name, client_id) -> TClient:
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
