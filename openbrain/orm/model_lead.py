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


class Lead(ORMModel):
    """Internal ORM representing Lead."""

    # Tracking
    client_id: str
    session_id: Optional[str] = Field(default=None, description="The session_id associated with this lead")
    # Lead
    first_name: Optional[str] = Field(default=None, description="The first name of the lead")
    middle_name: Optional[str] = Field(default=None, description="The middle name of the lead")
    last_name: Optional[str] = Field(default=None, description="The last name of the lead")
    full_name: Optional[str] = Field(default=None, description="The full name of the lead")
    date_of_birth: Optional[str] = Field(default=None, description="The date of birth of the lead")
    state_of_residence: Optional[str] = Field(default=None, description="The state of residence of the lead")
    email_address: Optional[str] = Field(default=None, description="The email address of the lead")
    phone_number: Optional[str] = Field(default=None, description="The phone number of the lead")
    current_medications: Optional[list[str]] = Field(default=None, description="The current medications of the lead")
    lead_id: str = Field(
        default_factory=ulid.ULID().to_uuid().__str__,
        description="A unique id associated with this lead",
    )
    status: Optional[str] = Field(default=None, description="Human readable status of the lead")
    send_error: Optional[bool] = Field(default=False, description="True if the the lead attempted to send, but failed")
    sent_by_agent: Optional[bool] = False

    def save(self):
        """Save the Lead object to the database"""
        return self._save(
            table_name=config.LEAD_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="lead_id",
            hash_key_value=self.client_id,
            range_key_value=self.lead_id,
        )

    @classmethod
    def get(cls, lead_id, client_id):
        """Get a Lead object from the database"""
        lead = cls._get(
            table_name=config.LEAD_TABLE_NAME,
            hash_key_name="client_id",
            range_key_name="lead_id",
            hash_key_value=client_id,
            range_key_value=lead_id,
        )
        return cls(**lead)

    def refresh(self):
        """Update this Lead object with the latest values from the database"""
        lead = Lead.get(lead_id=self.lead_id, client_id=self.client_id)

        for key, value in lead.dict().items():
            setattr(self, key, value)
