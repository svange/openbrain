from __future__ import annotations

from ast import literal_eval
from typing import Any

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "tester"


# Utility classes and functions


class TesterAdaptor(BaseModel):
    class Config:
        extra = Extra.allow
        populate_by_name = True
        # validate_assignment = True

    random_word_from_conversation: str
    # random_word_from_agent_creation: str



# LangChain tool
class TesterTool(BaseTool):
    name = TOOL_NAME
    description = """Useful when you want prove that you can use tools."""
    args_schema: type[BaseModel] = TesterAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        response = (
            "Successfully ran tool."
        )
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("tester does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    input = literal_eval(input_str)
    context = kwargs.get("context")
    random_word_from_agent_creation = context.get("random_word_from_agent_creation")

    event_detail = TesterAdaptor(
        random_word_from_agent_creation=random_word_from_agent_creation,
        random_word_from_conversation=input.get("random_word_from_conversation")
    )
    response = OBTool.send_event(event_source=TOOL_NAME, event_detail=event_detail.to_json())
    return response



def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    input = literal_eval(agent_input)
    logger.info(f"Input: {input}")
    logger.info(f"Agent Config: {agent_config}")
    logger.info(f"kwargs: {kwargs}")

class OBToolTester(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = TesterTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
