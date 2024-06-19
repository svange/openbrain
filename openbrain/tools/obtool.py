import datetime
from typing import Any

import boto3
from botocore.exceptions import ParamValidationError
from langchain.tools import BaseTool
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.util import logger, Defaults, config


class OBTool:
    """A tool for GptAgents. Tools consist of the main langchain extended BaseTool and any callbacks needed to supplement"""

    on_llm_start: OBCallbackHandlerFunctionProtocol
    on_chat_model_start: OBCallbackHandlerFunctionProtocol
    on_llm_new_token: OBCallbackHandlerFunctionProtocol
    on_llm_end: OBCallbackHandlerFunctionProtocol
    on_llm_error: OBCallbackHandlerFunctionProtocol
    on_chain_start: OBCallbackHandlerFunctionProtocol
    on_chain_end: OBCallbackHandlerFunctionProtocol
    on_chain_error: OBCallbackHandlerFunctionProtocol
    on_tool_start: OBCallbackHandlerFunctionProtocol
    on_tool_end: OBCallbackHandlerFunctionProtocol
    on_tool_error: OBCallbackHandlerFunctionProtocol
    on_text: OBCallbackHandlerFunctionProtocol
    on_agent_action: OBCallbackHandlerFunctionProtocol
    on_agent_finish: OBCallbackHandlerFunctionProtocol
    tool: BaseTool

    def __init__(self, initial_context: dict = None, *args, **kwargs):
        self.initial_context = initial_context or {}

    @classmethod
    def send_event(cls, event_detail: str, event_source: str = Defaults.OB_TOOL_EVENT_SOURCE.value) -> Any:
        """Send an event to eventbus."""
        logger.debug(f"Sending lead to Lead Momentum: {event_detail}")

        # Send event to eventbus
        event_bus_friendly_name = config.EVENTBUS_NAME
        event_bus_client = boto3.client("events")
        response = None
        entries = [
            {
                "EventBusName": event_bus_friendly_name,
                "Source": event_source,
                "DetailType": Defaults.OB_TOOL_EVENT_DETAIL_TYPE.value,
                "Detail": event_detail,
                "Time": datetime.datetime.now().isoformat(),
            }
        ]
        try:
            response = event_bus_client.put_events(Entries=entries)
            print(response["Entries"])
        except ParamValidationError:
            if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
                print(f"LOCAL_MODE: Can't send to CRM in local mode.")
            else:
                raise

        return response

    # def register_context(self, context: dict):
    #     self.context = context
    #     return self.context
