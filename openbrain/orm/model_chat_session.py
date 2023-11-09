import os
from typing import Optional

import ulid
from pydantic import Field
from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel
from openbrain.util import config


class ChatSession(ORMModel):
    """A chat session with an agent including all necessary state (config, memory, etc)"""

    # Tracking
    client_id: str = Field(description="The ID of the client the ChatSession belongs to")

    # We just take in an agent, but save it like this
    frozen_agent_memory: bytes = Field(description="The frozen agent memory", repr=False)
    frozen_agent_config: str = Field(description="The frozen agent config", repr=False)
    # serialized_agent = JSONAttribute()
    frozen_lead: Optional[str] = Field(default=None, description="The frozen lead", repr=False)
    session_id: str = Field(
        default_factory=ulid.ULID().to_uuid().__str__,
        description="The session_id associated with this ChatSession",
    )

    def save(self):
        """Save the ChatSession object to the database"""
        return self._save(
            table_name=config.SESSION_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="session_id",
            hash_key_value=self.client_id,
            range_key_value=self.session_id,
        )

    @classmethod
    def get(cls, session_id, client_id) -> Optional["ChatSession"]:
        """Get a ChatSession object from the database"""
        agent_config = cls._get(
            table_name=config.SESSION_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="session_id",
            hash_key_value=client_id,
            range_key_value=session_id,
        )
        dynamo_memory_typed_memory = agent_config.get("frozen_agent_memory", None)
        agent_config["frozen_agent_memory"] = bytes(dynamo_memory_typed_memory)  # TODO inelegant
        return cls(**agent_config) if agent_config else None

    def refresh(self):
        """Update this ChatSession object with the latest values from the database"""
        session_from_db = ChatSession.get(session_id=self.session_id, client_id=self.client_id)

        for key, value in session_from_db.dict().items():
            setattr(self, key, value)
