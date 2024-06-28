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
from openbrain.tools.models.model_leadmo_appointment import LeadmoAppointmentAdaptor

logger = get_logger()

TOOL_NAME = "leadmo_create_appointment"

# LangChain tool
class LeadmoCreateAppointmentTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful when you have negotiated an appointment time with the user and want to book the appointment."""
    args_schema: type[BaseModel] = LeadmoAppointmentAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = self.tool_input
        context = json.loads(tool_input)

        event_detail = {
            "context": context,
            "ai_input": kwargs
        }

        event_detail_string = json.dumps(event_detail)
        logger.info(f"event_detail_string: {event_detail_string}")

        response = OBTool.send_event(event_source=TOOL_NAME, event_detail=event_detail_string)

        return response


    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass

def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoCreateAppointment(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoCreateAppointmentTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
