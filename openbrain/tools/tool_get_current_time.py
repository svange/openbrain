from __future__ import annotations

import datetime
from typing import Any, Optional

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Field

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
    name = TOOL_NAME
    description = """Useful when you need to know the current time."""
    args_schema: type[BaseModel] = TimeRequestAdapter
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        # timezone = kwargs.get("timezone")
        current_time = datetime.datetime.now()
        return current_time.isoformat()

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
