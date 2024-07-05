from __future__ import annotations

import json
from typing import Any

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.tools.models.model_leadmo_contact import LeadmoContactAdaptor

logger = get_logger()

TOOL_NAME = "leadmo_update_contact"


class LeadmoUpdateContactTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful when you want to update a user's information in our system, based on learned details from the conversation."""
    args_schema: type[BaseModel] = LeadmoContactAdaptor
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

        response = OBTool.send_event(event_source=TOOL_NAME, event_detail=event_detail_string)

        if agent_config.get("record_tool_actions"):
            OBTool.record_action(event=TOOL_NAME, response=response, latest=True, session_id=session_id)


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
