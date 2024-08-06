from __future__ import annotations

import datetime
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

TOOL_NAME = "input_and_context_tester"


# Utility classes and functions


class TesterAdaptor(BaseModel):
    class Config:
        extra = 'allow'
        populate_by_name = True
        # validate_assignment = True

    random_word_from_conversation: str
    # random_word: str

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
        extra = 'allow'

    name = TOOL_NAME
    description = """Useful when you want prove that you can use tools."""
    args_schema: type[BaseModel] = TesterAdaptor
    handle_tool_error = True
    verbose = True
    # callbacks = [on_tool_start, on_tool_error]

    def _run(self, *args, **kwargs) -> str:

        logger.info(f"Running {TOOL_NAME} tool")
        logger.debug(f"self.tool_input: {self.tool_input}")
        logger.debug(f"Kwargs: {kwargs}")

        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")
        random_word_from_conversation = kwargs.get("random_word_from_conversation")

        try:
            random_word = context.get("random_word")
        except AttributeError as e:
            double_unwrapped_context = json.loads(context)
            random_word = double_unwrapped_context.get("random_word")

        # event_detail_dict = {
        #     "random_word": random_word,
        #     "random_word_from_conversation": random_word_from_conversation
        # }

        # event_detail = json.dumps(event_detail_dict)

        # event_response = OBTool.send_event(event_source=TOOL_NAME, event_detail=event_detail)
        # response = (
        #     "Successfully ran tool. Repeat the word to the user."
        # )
        response = f"Respond to the user with the words: {random_word} {random_word_from_conversation}"

        if agent_config.get("record_tool_actions"):
            wrapped_response = {
                "response": response,
                "timestamp": datetime.datetime.now().isoformat()
            }
            event = {
                'context': context,
                'ai_input': kwargs
            }
            OBTool.record_action(
                tool_name=TOOL_NAME,
                event=event,
                response=wrapped_response,
                session_id=session_id,
                latest=True,
                agent_config=agent_config
            )
        return response


    def _arun(self, ticker: str):
        raise NotImplementedError("tester does not support async")

    # def register_context(self, context: dict):
    #     self.context = context


# on_tool_start

class OBToolTester(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = TesterTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
