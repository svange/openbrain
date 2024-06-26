from __future__ import annotations

import json
from ast import literal_eval
from typing import Any

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "leadmo_stop_conversation"


# Utility classes and functions
class LeadmoStopConversationAdaptor(BaseModel):
    class Config:
        extra = Extra.allow
        populate_by_name = True
        # validate_assignment = True

    reason: str = Field(default=None, description="The reason for ending the conversation")


# LangChain tool
class LeadmoStopConversationTool(BaseTool, ContextAwareToolMixin):
    name = TOOL_NAME
    description = """Useful to signal that this conversation should end for one of the following reasons: natural end of conversation, abuse by the user, user responds with '1'."""
    args_schema: type[BaseModel] = LeadmoStopConversationAdaptor
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


class OBToolLeadmoStopConversation(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoStopConversationTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
