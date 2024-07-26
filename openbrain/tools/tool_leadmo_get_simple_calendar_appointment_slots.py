from __future__ import annotations

import datetime
import json
from typing import Any, Optional

import requests
from dateutil.tz import tz
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

import os
from openbrain.tools.util_leadmo_tools import get_leadmo_api_key
from aws_lambda_powertools import Logger, Tracer
from dateutil import parser


LEADMO_API_V1_GET_APPOINTMENT_SLOTS_URL = 'https://rest.gohighlevel.com/v1/appointments/slots/'

DEFAULT_ORIGIN = os.getenv('DEFAULT_ORIGIN', 'https://localhost:5173')
IDEMPOTENCY_TABLE_NAME = os.getenv('IDEMPOTENCY_TABLE_NAME', 'ObIdempotencyTable-Dev')


# INFRA_TOPIC_NAME = os.getenv('INFRA_TOPIC_NAME')
tracer = Tracer()  # Sets service name from env var
logger = Logger()

TOOL_NAME = "leadmo_get_simple_calendar_appointment_slots"


# Utility classes and functions
class LeadmoAvailableAppointmentSlotsAdaptor(BaseModel):
    """Adaptor class for Lead Momentum get available appointment slots tool."""
    class Config:
        extra = Extra.allow
        populate_by_name = True
        validate_assignment = True

    # locationId: str
    # api_key: str
    startTime: str = Field(..., description="Start time for your query in ISO format. You only want the blocked slots after this time.")
    endTime: str = Field(..., description="End time for your query in ISO format. You only want the blocked slots before this time.")
    timezone: str = Field(..., description="Timezone for the query. If not provided, UTC will be used.")


# LangChain tool
class LeadmoGetSimpleCalendarAppointmentSlotsTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful when you want need to know appointment slots are available for scheduling. The output of this tool is a list of available appointment slots, for you to use in conversation."""
    args_schema: type[BaseModel] = LeadmoAvailableAppointmentSlotsAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        global DEFAULT_ORIGIN
        global IDEMPOTENCY_TABLE_NAME
        global LEADMO_API_V1_GET_APPOINTMENT_SLOTS_URL

        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        location_id = context.get("locationId")
        calendar_id = context.get("calendarId")
        timezone = kwargs.get("timezone", 'UTC')

        # Lead Momentum requests from the workflow come in with location_id's
        if location_id:
            try:
                api_key = get_leadmo_api_key(location_id)
            except Exception as e:
                api_key = context.get("api_key")


        if not calendar_id and not api_key:
            response = "System error: Can't get appointment times. Inform the user of other ways to contact us, and apologize for the inconveinence."
            if agent_config.get("record_tool_actions"):
                OBTool.record_action(event=TOOL_NAME, response=response, latest=True, session_id=session_id, context=context, tool_input=tool_input)
            return response

        standardized_tz = tz.gettz(timezone)
        start_time_iso = kwargs.get("startTime")
        end_time_iso = kwargs.get("endTime")

        # convert to epoch
        start_time = parser.parse(start_time_iso).astimezone(standardized_tz)
        end_time = parser.parse(end_time_iso).astimezone(standardized_tz)

        start_time_epoch = int(start_time.timestamp() * 1000)
        end_time_epoch = int(end_time.timestamp() * 1000)


        headers = {
            "Content-Type": "application/json",
            "Origin": DEFAULT_ORIGIN,
            "Authorization": f'Bearer {api_key}'
        }

        query_params = {
            'calendarId': calendar_id,
            'startDate': str(start_time_epoch),
            'endDate': str(end_time_epoch)
        }
        if timezone:
            query_params['timezone'] = timezone

        query_params_str = '&'.join([f'{k}={v}' for k, v in query_params.items()])

        url = LEADMO_API_V1_GET_APPOINTMENT_SLOTS_URL + '?' + query_params_str

        try:

            api_response = requests.get(url=url, headers=headers)
            response = api_response.json()

        except Exception as e:
            logger.info("Failed to get info from Lead Momentum.")
            raise e

        if agent_config.get("record_tool_actions"):
            wrapped_response = {
                "response": response,
                "context": context,
                "tool_name": TOOL_NAME,
                "tool_input": tool_input,
                "agent_config": agent_config,
                "session_id": session_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            OBTool.record_action(event=TOOL_NAME, response=wrapped_response, latest=True, session_id=session_id, context=context, tool_input=tool_input)

        return response


    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass

def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoGetSimpleCalendarAppointmentSlots(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoGetSimpleCalendarAppointmentSlotsTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
