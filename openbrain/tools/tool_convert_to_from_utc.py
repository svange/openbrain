from __future__ import annotations

import datetime
import json
from typing import Any

import pytz
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Field, Extra

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "convert_to_from_utc"


# Utility classes and functions
class ConvertToFromUtcTimeAdaptor(BaseModel):
    """The schema for the tool's input."""
    time: str = Field(description="The time for your query in ISO format. Include the date for best results.")
    timezone: str = Field(description="Convert to or from this timezone. Use pytz notation, example 'America/New_York', 'America/Los_Angeles.")
    to_utc: bool = Field(description="If true, converts the time to UTC. If false, converts from UTC to the provided timezone.")


# LangChain tool
class ConvertToFromUtcTimeTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = 'allow'
        populate_by_name = True
    name = TOOL_NAME
    description = """Useful when you need to convert time and date values to or from UTC."""
    args_schema: type[BaseModel] = ConvertToFromUtcTimeAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        time = kwargs.get('time')
        timezone = kwargs.get('timezone')
        to_utc = kwargs.get('to_utc')

        tz = pytz.timezone(timezone)

        if to_utc:
            converted_time = datetime.datetime.fromisoformat(time).astimezone(pytz.utc).__str__()
        else:
            converted_time = datetime.datetime.fromisoformat(time).astimezone(tz).__str__()


        if agent_config.get("record_tool_actions"):
            logger.info("About to call OBTool.record_action")
            wrapped_response = {
                "response": converted_time,
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
        else:
            logger.info("RECORD_ACTION: Not calling OBTool.record_action")

        return converted_time

    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolConvertToFromUtc(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = ConvertToFromUtcTimeTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
