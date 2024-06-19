from __future__ import annotations

from typing import Any

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin

logger = get_logger()

TOOL_NAME = "do_nothing"


# Utility classes and functions


class DoNothingAdaptor(BaseModel):
    class Config:
        extra = Extra.allow
        populate_by_name = True
        # validate_assignment = True


# LangChain tool
class DoNothingTool(BaseTool, ContextAwareToolMixin):
    name = TOOL_NAME
    description = """Never useful."""
    args_schema: type[BaseModel] = DoNothingAdaptor
    handle_tool_error = True
    verbose = True


    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        response = (
            "Successfully did nothing."
        )
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("do_nothing does not support async")


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
