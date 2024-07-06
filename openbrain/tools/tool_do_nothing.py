from __future__ import annotations

import json
from typing import Any, Optional

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Field, Extra

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "do_nothing"


# Utility classes and functions
class DoNothingAdapter(BaseModel):
    """The schema for the tool's input."""
    input: Optional[str] = Field(default="", description="indicates nothing")


# LangChain tool
class DoNothingTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True
    name = TOOL_NAME
    description = """Does nothing."""
    args_schema: type[BaseModel] = DoNothingAdapter
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        if agent_config.get("record_tool_actions"):
            try:
                context_str = json.dumps(context)
            except:
                context_str = json.dumps({
                    "error": "Could not convert context to json",
                })
            OBTool.record_action(event=TOOL_NAME, response=context_str, latest=True, session_id=session_id)

        return "successfully did nothing"

    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolDoNothing(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = DoNothingTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
