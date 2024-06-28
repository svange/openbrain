from __future__ import annotations

import json
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

def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    input = literal_eval(agent_input)
    logger.debug(f"Input: {input}")
    logger.debug(f"Agent Config: {agent_config}")
    logger.debug(f"kwargs: {kwargs}")


# LangChain tool
class TesterTool(BaseTool):
    class Config:
        extra = Extra.allow

    name = TOOL_NAME
    description = """Useful when you want prove that you can use tools."""
    args_schema: type[BaseModel] = TesterAdaptor
    handle_tool_error = True
    verbose = True
    # callbacks = [on_tool_start, on_tool_error]

    def _run(self, *args, **kwargs) -> str:
        # This seemingly does nothing. All the work is done in the callback handler. This function is here for
        # the metadata.
        initial_context = literal_eval(self.tool_input)
        random_word_from_agent_creation = initial_context.get("random_word_from_agent_creation")
        random_word_from_conversation = kwargs.get("random_word_from_conversation")

        event_detail_dict = {
            "random_word_from_agent_creation": random_word_from_agent_creation,
            "random_word_from_conversation": random_word_from_conversation
        }

        event_detail = json.dumps(event_detail_dict)

        event_response = OBTool.send_event(event_source=TOOL_NAME, event_detail=event_detail)
        # response = (
        #     "Successfully ran tool. Repeat the word to the user."
        # )
        response = f"Respond to the user with the words: {random_word_from_agent_creation} {random_word_from_conversation}"

        return response


    def _arun(self, ticker: str):
        raise NotImplementedError("tester does not support async")

    # def register_context(self, context: dict):
    #     self.initial_context = context


# on_tool_start

class OBToolTester(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = TesterTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
