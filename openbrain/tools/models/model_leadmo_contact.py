from typing import Optional

from pydantic import Field
from openbrain.util import config, Defaults

if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    from openbrain.orm.model_common_base import Ephemeral as ORMModel
else:
    from openbrain.orm.model_common_base import Recordable as ORMModel
from openbrain.util import config


class LeadmoContact(ORMModel):
    """Internal ORM representing LeadmoContact."""

    # Lead Momentum API fields
    contactId: str = Field(default=None, description="The contact's id")
    locationId: str = Field(default=None, description="The agent's location ID in Lead Momentum")

    firstName: Optional[str] = Field(default=None, description="The contact's first name")
    lastName: Optional[str] = Field(default=None, description="The contact's last name")
    name: Optional[str] = Field(default=None, description="The contact's full name")
    dateOfBirth: Optional[str] = Field(default=None, description="The contact's date of birth")
    phone: Optional[str] = Field(default=None, description="The contact's phone number")
    email: Optional[str] = Field(default=None, description="The contact's email address")
    address1: Optional[str] = Field(default=None, description="The contact's address line 1")
    city: Optional[str] = Field(default=None, description="The contact's city")
    state: Optional[str] = Field(default=None, description="The contact's state")
    country: Optional[str] = Field(default=None, description="The contact's country")
    postalCode: Optional[str] = Field(default=None, description="The contact's postal code")
    companyName: Optional[str] = Field(default=None, description="The contact's company name")
    website: Optional[str] = Field(default=None, description="The contact's website")
    tags: Optional[list[str]] = Field(default=None, description="The contact's tags")
    customFields: Optional[dict[str, str]] = Field(default=None, description="The contact's custom fields")

    # Woxom Fields
    sessionId: str = Field(default=None, description="The session_id associated with this contact")

    def save(self):
        """Save the Lead object to the database"""
        return self._save(
            table_name=config.LEADMO_CONTACT_TABLE_NAME,
            hash_key_name="contactId",
            hash_key_value=self.contactId,
        )

    @classmethod
    def get(cls, sessionId, contactId):
        """Get a Lead object from the database"""
        lead = cls._get(
            table_name=config.LEADMO_CONTACT_TABLE_NAME,
            hash_key_name="contactId",
            hash_key_value=contactId,
        )
        return cls(**lead)

    def refresh(self):
        """Update this Lead object with the latest values from the database"""
        lead = LeadmoContact.get(contactId=self.contactId)

        for key, value in lead.dict().items():
            setattr(self, key, value)
