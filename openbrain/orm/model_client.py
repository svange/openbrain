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
    # client_id: str = Field(description="The ID of the client this should match the cognito:username")
    email: str = Field(description="The email of the client")
    # roles: Optional[list[str]] = Field(description="The roles of the client")

    leadmo_api_key: Optional[str] = Field(default=None, description="The API key for the Leadmo API")
    leadmo_location_id: Optional[str] = Field(default=None, description="The location ID for the Leadmo API")
    lls_api_key: Optional[str] = Field(default=None, description="The API key for the LLS API")

    class Meta:
        table_name = config.CLIENT_TABLE_NAME
        region = config.AWS_REGION

    def save(self):
        """Save the client to the database"""
        table_name = config.CLIENT_TABLE_NAME or "client_table"
        return self._save(
            table_name=table_name,
            hash_key_name="email",
            hash_key_value=self.email,
        )

    @classmethod
    def get(cls, email=None, location_id=None) -> TClient:
        """Get a client from the database"""
        if (not email) and (not location_id):
            raise ValueError("Either email or location_id must be provided")

        table_name = config.CLIENT_TABLE_NAME or "client_table"

        if email:
            client = cls._get(
                table_name=table_name,
                hash_key_name="email",
                hash_key_value=email
            )
        elif location_id:
            client = cls._get(
                table_name=table_name,
                hash_key_name="leadmo_location_id",
                hash_key_value=location_id,
                index="LocationIndex"
            )
        else:
            raise ValueError("Either email or location_id must be provided")
        return cls(**client)

    def refresh(self):
        """Update this client with the latest values from the database"""
        client_from_db = Client.get(email=self.email)

        for key, value in client_from_db.dict().items():
            setattr(self, key, value)
