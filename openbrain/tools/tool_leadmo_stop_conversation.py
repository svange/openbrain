from __future__ import annotations

import datetime
from ast import literal_eval
from typing import Any, Optional

import boto3
from botocore.exceptions import ParamValidationError
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.obtool import OBTool
from openbrain.agents.exceptions import AgentToolIncompleteLeadError, AgentToolIncompleteContactError
from openbrain.tools.models.model_leadmo_contact import LeadmoContact

from openbrain.util import config, get_logger, Defaults
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "leadmo_stop_conversation"


# Utility classes and functions
class LeadmoStopConversationAdaptor(BaseModel):
    class Config:
        extra = Extra.allow
        populate_by_name = True
        # validate_assignment = True

    # contactId: Optional[str] = Field(default=None, description="The contact's ID in Lead Momentum")
    # locationId: Optional[str] = Field(default=None, description="The agent's location ID in Lead Momentum")
    #



# LangChain tool
class LeadmoStopConversationTool(BaseTool):
    name = TOOL_NAME
    description = """Useful to signal that this conversation should end for one of the following reasons: natural end of conversation, abuse by the user, user responds with '1'."""
    args_schema: type[BaseModel] = LeadmoStopConversationAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        response = (
            "Successfully stopped the conversation in Lead Momentum."
        )
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("This tool does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""

    contact_from_metadata = LeadmoContact(**kwargs)

    location_id = kwargs.get("locationId", None)
    contact_id = kwargs.get("contactId", None)
    session_id = kwargs.get("sessionId", None)

    required_fields = ["contactId", "locationId"]

    # Check if all required fields are present
    for field in required_fields:
        if not getattr(contact_from_metadata, field):
            raise AgentToolIncompleteLeadError(
                f"Required field {field} is missing from the metadata. Perhaps this tool should not be enabled for this profile."
            )
    leadmo_contact = LeadmoContact(location_id=location_id, contact_id=contact_id)

    response = OBTool.send_event(event_source=TOOL_NAME, event_detail=leadmo_contact.to_json())
    return response


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoStopConversation(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoStopConversationTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
