from __future__ import annotations

from pydantic import BaseModel, Field

from openbrain.orm.model_lead import Lead
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel


class LeadEvent(ORMModel, BaseModel):
    """A wrapper containing everything needed when the Agent uses the CRM tool"""

    lead: Lead = Field(description="The lead associated with this event")
    agent_config: AgentConfig = Field(description="The agent config associated with this event")

    @classmethod
    def get(cls, *args, **kwargs) -> LeadEvent:
        """Get a ChatMessage object from the database"""
        raise NotImplementedError("No DB for LeadEvent objects")

    def save(self):
        """Save the ChatMessage object to the database"""
        raise NotImplementedError("No DB for LeadEvent objects")

    def refresh(self):
        """Update this ChatMessage object with the latest values from the database"""
        raise NotImplementedError("No DB for LeadEvent objects")
