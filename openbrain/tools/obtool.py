import datetime
import json
from decimal import Decimal
from typing import Any

import boto3
import ulid
from botocore.exceptions import ParamValidationError
from langchain.tools import BaseTool
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.util import logger, Defaults, config

INFRA_STACK_NAME = config.INFRA_STACK_NAME

class OBTool:
    """
    A tool for GptAgents. Tools consist of the main langchain extended BaseTool and any callbacks needed to supplement
    """
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

    def __init__(self, context: dict = None, *args, **kwargs):
        self.context = context or {}

    @classmethod
    def record_action(cls, tool_name, event, response, agent_config, session_id="no-session", latest=False) -> Any:
        """
        Record an action in the DynamoDB table. Used for testing/debugging/observability.
        :param agent_config: the agent_config that triggered the action.
        :param tool_name: Name of the tool being triggered
        :param event: The event that triggered the action. Usually the tool name.
        :param response: The response from the tool. For example, the answer to a calculation or the response object of an API call.
        :param latest: If True, also record the action as the latest action for the session.
        :param session_id: The session ID. If not provided, defaults to "no-session".
        :param context: The context of the action. For example, the input to a calculation or the request object of an API call.
        :param ai_input: The input to the tool. For example, the input to a calculation or the request object of an API call.
        :return:
        """
        # response = str(response)
        logger.info(f"Recording action for session {session_id}: {event=}, {response=}")

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(config.ACTION_TABLE_NAME)

        item = json.loads(json.dumps({
            "tool_name": tool_name,
            "action_id": ulid.ULID().to_uuid().__str__(),
            "session_id": session_id,
            "event": event,
            "response": response,
            "agent_config": agent_config,
        }), parse_float=Decimal)

        action_response = table.put_item(
            Item=item
        )

        if latest:
            try:
                table.put_item(
                    Item=item
                )
            except Exception as e:
                logger.error(f"Error recording latest action: {e}")
                pass

        return action_response


    @classmethod
    def send_event(cls, event_detail: str, tool_name: str) -> Any:
        """
        Send a tool event to the Event Bus.
        :param event_detail: contains the event details including the context and ai_input
        :param tool_name: name of the tool, used to construct an event source
        :return:
        """
        logger.info(f"Sending event: {event_detail}")

        # Send event to eventbus
        event_bus_friendly_name = config.EVENTBUS_NAME
        event_bus_client = boto3.client("events")

        response = None
        entries = [
            {
                "EventBusName": event_bus_friendly_name,
                "Source": tool_name,
                "DetailType": config.OB_TOOL_EVENT_DETAIL_TYPE,
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
        # try:
        #     cls.record_action(event=entries, response=response)
        # except Exception as e:
        #     logger.error(f"Error recording action: {e}")

        # try:
        #     cls.record_action(event=entries, response=response, latest=True)
        # except Exception as e:
        #     logger.error(f"Error recording latest action: {e}")

        return response
