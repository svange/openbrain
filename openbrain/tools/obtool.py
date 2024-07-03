import datetime
from typing import Any

import boto3
import ulid
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
    def record_action(cls, event, response, latest=False):

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(config.ACTION_TABLE_NAME)

        item = {
            "action_id": ulid.ULID().to_uuid().__str__(),
            "event": event,
            "response": response,
        }

        action_response = table.put_item(
            Item=item
        )

        if latest:
            try:
                table.put_item(
                    Item={
                        "action_id": "latest",
                        "event": event,
                        "response": response,
                    }
                )
            except Exception as e:
                logger.error(f"Error recording latest action: {e}")
                pass

        return action_response


    @classmethod
    def send_event(cls, event_detail: str, event_source: str = Defaults.OB_TOOL_EVENT_SOURCE.value) -> Any:
        """Send an event to eventbus."""
        logger.info(f"Sending event: {event_detail}")

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
        logger.info(f"{entries=}")
        try:
            response = event_bus_client.put_events(Entries=entries)
            logger.info(response["Entries"])
        except ParamValidationError as e:
            if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
                logger.info(f"{e=}")
                logger.info(f"LOCAL_MODE: Can't send to CRM in local mode.")
            else:
                raise e
        try:
            cls.record_action(event=entries, response=response)
        except Exception as e:
            logger.error(f"Error recording action: {e}")

        try:
            cls.record_action(event=entries, response=response, latest=True)
        except Exception as e:
            logger.error(f"Error recording latest action: {e}")

        return response
