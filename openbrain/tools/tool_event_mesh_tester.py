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

TOOL_NAME = "event_mesh_tester"


class EventMeshTesterAdaptor(BaseModel):
    """The schema for the tool's input."""

    trigger_reason: str = Field(
        description="Repeat or describe what, if anything, in the conversation prompted you to send this event to the event mesh."
    )


class EventMeshTesterTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful when you need to send an event to the event mesh for testing."""
    args_schema: type[BaseModel] = EventMeshTesterAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get("context"))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        event_detail = json.dumps({"context": context, "ai_input": kwargs})

        response = OBTool.send_event(event_source=TOOL_NAME, event_detail=event_detail)
        if agent_config.get("record_tool_actions"):
            OBTool.record_action(event=TOOL_NAME, response=response, latest=True, session_id=session_id)

        return response

    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolEventMeshTester(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = EventMeshTesterTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
