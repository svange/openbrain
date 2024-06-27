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
from openbrain.tools.models.model_leadmo_contact_adaptor import LeadmoContactAdaptor

logger = get_logger()

TOOL_NAME = "leadmo_update_contact"


class LeadmoUpdateContactTool(BaseTool, ContextAwareToolMixin):
    name = TOOL_NAME
    description = """Useful when you want to update a user's information in our system, based on learned details from the conversation."""
    args_schema: type[BaseModel] = LeadmoContactAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        logger.debug(f"self.tool_input: {self.tool_input}")
        logger.debut(f"args: {args}")
        logger.debug(f"kwargs: {kwargs}")
        logger.debug(f"dir(self): {dir(self)}")

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
