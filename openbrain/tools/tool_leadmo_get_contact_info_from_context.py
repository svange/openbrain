from __future__ import annotations

import json
import re
from typing import Any

from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "leadmo_get_contact_info_from_context"


# Utility classes and functions
class LeadmoGetContactInfoFromContextAdaptor(BaseModel):
    ...


# LangChain tool
class LeadmoGetContactInfoFromContextTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow

    name = TOOL_NAME
    description = """Useful when you need to know the information our Customer Relations Management system has on our customer. The context is intormation about the customer from the CRM."""
    args_schema: type[BaseModel] = LeadmoGetContactInfoFromContextAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = self.tool_input
        context = json.loads(tool_input)

        def camel_to_snake(name):
            name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

        forbidden_keys_pascal_case = [
                "sessionId",
                "contactId",
                "locationId",
                "apiKey",
                "calendarId",
                "appointmentId",
                "medications",
            ]

        forbidden_keys_snake_case = [camel_to_snake(key) for key in forbidden_keys_pascal_case]

        forbidden_keys = forbidden_keys_pascal_case + forbidden_keys_snake_case

        for key in forbidden_keys:
            if key in context:
                del context[key]

        try:
            context_string = json.dumps(context)
        except Exception as e:
            logger.error(f"Failed to convert context to string: {e}")
            context_string = str(context)

        return context_string


    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass

def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoGetContactInfoFromContext(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoGetContactInfoFromContextTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
