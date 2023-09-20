import ulid
from pydantic import Field
from typing import Optional

from chalicelib.orm.model_common_base import Recordable
from chalicelib.util import Util
from chalicelib.orm.model_agent_config import AgentConfig


class ChatSession(Recordable):
    # Tracking
    client_id: str = Field(description="The ID of the client the ChatSession belongs to")

    # We just take in an agent, but save it like this
    frozen_agent_memory: bytes = Field(description="The frozen agent memory", repr=False)
    frozen_agent_config: str = Field(description="The frozen agent config", repr=False)
    # serialized_agent = JSONAttribute()
    frozen_lead: Optional[str] = Field(default=None, description="The frozen lead", repr=False)
    session_id: str = Field(default_factory=ulid.ULID().to_uuid().__str__, description="The session_id associated with this ChatSession")
    # agent_config: Optional[AgentConfig] = Field(default=None, exclude=True)

    def save(self):
        return self._save(
            table_name=Util.SESSION_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="session_id",
            hash_key_value=self.client_id,
            range_key_value=self.session_id,
        )

    @classmethod
    def get(cls, session_id, client_id) -> Optional["ChatSession"]:
        agent_config = cls._get(
            table_name=Util.SESSION_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="session_id",
            hash_key_value=client_id,
            range_key_value=session_id,
        )
        dynamo_memory_typed_memory = agent_config.get("frozen_agent_memory", None)
        agent_config["frozen_agent_memory"] = bytes(dynamo_memory_typed_memory)  # TODO inelegant
        return cls(**agent_config) if agent_config else None

    def refresh(self):
        session_from_db = ChatSession.get(session_id=self.session_id, client_id=self.client_id)

        for key, value in session_from_db.dict().items():
            setattr(self, key, value)
