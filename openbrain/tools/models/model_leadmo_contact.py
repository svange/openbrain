from pydantic import BaseModel, Field
from typing import Optional

class LeadmoContact(BaseModel):
    """Internal ORM representing LeadmoContact."""

    contactId: Optional[str] = Field(default=None, description="The contact's id")
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
    sessionId: Optional[str] = Field(default=None, description="The session_id associated with this contact")
