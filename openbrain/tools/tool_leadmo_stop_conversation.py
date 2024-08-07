from __future__ import annotations

import datetime
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
        extra = 'allow'
        populate_by_name = True
        # validate_assignment = True

    reason: str = Field(default=None, description="The reason for ending the conversation")


# LangChain tool
class LeadmoStopConversationTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = 'allow'
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful to signal that this conversation should end for one of the following reasons: natural end of conversation, abuse by the user, user responds with '1'."""
    args_schema: type[BaseModel] = LeadmoStopConversationAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        event_detail = {
            "context": context,
            "ai_input": kwargs
        }

        event_detail_string = json.dumps(event_detail)
        logger.info(f"event_detail_string: {event_detail_string}")

        response = OBTool.send_event(tool_name=TOOL_NAME, event_detail=event_detail_string)

        event = {
            'context': context,
            'ai_input': kwargs
        }
        OBTool.record_action(
            tool_name=TOOL_NAME,
            event=event,
            response=response,
            session_id=session_id,
            latest=True,
            agent_config=agent_config
        )

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
