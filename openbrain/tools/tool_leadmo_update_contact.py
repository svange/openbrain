from __future__ import annotations

import json
from ast import literal_eval
from typing import Any, Optional

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

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
class LeadmoUpdateContactTool(BaseTool, ContextAwareToolMixin):
    name = TOOL_NAME
    description = """Useful when you want to update a user's information in our system, based on learned details from the conversation."""
    args_schema: type[BaseModel] = LeadmoContactAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        context = literal_eval(self.tool_input)
        event_detail = {
            "context": context,
            "ai_input": kwargs
        }

        response = OBTool.send_event(event_source=TOOL_NAME, event_detail=json.dump(event_detail))

        return response


    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass

def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoUpdateContact(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoUpdateContactTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
