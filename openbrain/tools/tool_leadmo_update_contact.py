from __future__ import annotations

from ast import literal_eval
from typing import Any, Optional

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.obtool import OBTool
from openbrain.agents.exceptions import AgentToolIncompleteLeadError, AgentToolIncompleteContactError
from openbrain.tools.models.model_leadmo_contact import LeadmoContact

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "leadmo_update_contact"


# Utility classes and functions
class LeadmoContactAdaptor(BaseModel):
    class Config:
        extra = Extra.allow
        populate_by_name = True
        # validate_assignment = True

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

    # custom fields
    current_medications: Optional[list[str]] = Field(default=None, description="The contact's current medications")


# LangChain tool
class LeadmoUpdateContactTool(BaseTool):
    name = TOOL_NAME
    description = """Useful when you want to update a user's information based on new infromation from the conversation."""
    args_schema: type[BaseModel] = LeadmoContactAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        response = (
            "Successfully updated the contact in Lead Momentum."
        )
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("connect_with_agent does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""

    leadmo_contact_fields = LeadmoContact.model_fields.keys()
    required_fields = ["contactId", "phone"]
    contact_from_metadata = LeadmoContact(**kwargs)

    # Check if all required fields are present
    for field in required_fields:
        if not getattr(contact_from_metadata, field):
            raise AgentToolIncompleteLeadError(
                f"Required field {field} is missing from the metadata. Perhaps this tool should not be enabled for this profile."
            )

    contact_info_from_conversation = literal_eval(input_str)

    leadmo_contact_from_conversation = LeadmoContactAdaptor(**contact_info_from_conversation)

    constructed_contact_dict = {}
    for key, value in contact_from_metadata.dict().items():
        # If the conversation yielded updated information, use that, otherwise use the information from the CRM
        if leadmo_contact_from_conversation[key]:
            constructed_contact_dict[key] = leadmo_contact_from_conversation[key]
        else:
            constructed_contact_dict[key] = value

    constructed_leadmo_contact = LeadmoContact(**constructed_contact_dict)

    if not constructed_leadmo_contact.phone:
        raise AgentToolIncompleteContactError(
            "No email address is known for this user, ask the user for an email address and try again."
        )

    if not constructed_leadmo_contact.contactId:
        raise AgentToolIncompleteContactError(
            "Error updating information, notify an agent."
        )

    response = OBTool.send_event(event_source=TOOL_NAME, event_detail=constructed_leadmo_contact.to_json())

    return response


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoUpdateContact(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoUpdateContactTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
