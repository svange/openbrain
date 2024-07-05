from __future__ import annotations

import datetime
import json
from typing import Any, Optional

import pytz
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Field, Extra

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "get_current_time"


# Utility classes and functions
class TimeRequestAdapter(BaseModel):
    """The schema for the tool's input."""
    timezone: Optional[str] = Field(default="UTC", description="The timezone for your query.")


# LangChain tool
class GetCurrentTimeTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True
    name = TOOL_NAME
    description = """Useful when you need to know the current time."""
    args_schema: type[BaseModel] = TimeRequestAdapter
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        timezone = tool_input.get("timezone", "UTC")
        tz = pytz.timezone(timezone)

        current_time = datetime.datetime.now().astimezone(tz).__str__()

        if agent_config.get("record_tool_actions"):
            logger.info("About to call OBTool.record_action")
            OBTool.record_action(event=TOOL_NAME, response=current_time, latest=True, session_id=session_id)
        else:
            logger.info("Not calling OBTool.record_action")

        return current_time

    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolGetCurrentTime(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = GetCurrentTimeTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
