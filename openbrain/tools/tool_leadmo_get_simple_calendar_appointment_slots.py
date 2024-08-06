from __future__ import annotations

import json
import os
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from langchain.tools.base import BaseTool
from leadmo_api.util import iso_to_epoch
from leadmo_api.v1.client import LeadmoApiV1
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.tools.util_leadmo_tools import get_leadmo_api_key

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
        extra = 'allow'
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
        extra = 'allow'
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
        try:

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
                    OBTool.record_action(tool_name=TOOL_NAME, response=response, latest=True, session_id=session_id, agent_config=agent_config, event={"ERROR": "No calendar ID or API key when getting appointment slots."})
                return response

            start_time_iso = kwargs.get("startTime")
            end_time_iso = kwargs.get("endTime")

            leadmo_client = LeadmoApiV1(api_key=api_key)
            try:
                response = leadmo_client.get_available_appointment_slots(
                    calendar_id=calendar_id,
                    start_date=start_time_iso,
                    end_date=end_time_iso,
                    timezone=timezone,
                )
            except Exception as e:
                logger.info("Failed to get info from Lead Momentum.")
                raise e

            info_to_return = {}
            for event in list(response.items()):
                date = event[0]
                slots = event[1].get('slots')
                slots_for_this_date = []
                for slot in slots:
                    slots_for_this_date.append(slot)

                info_to_return[date] = slots_for_this_date

            if agent_config.get("record_tool_actions"):
                event = {
                    'context': context,
                    'ai_input': kwargs
                }
                OBTool.record_action(
                    tool_name=TOOL_NAME,
                    event=event,
                    response=response,
                    session_id=session_id,
                    latest=True,
                    agent_config=agent_config
                )

            return json.dumps(info_to_return)

        except Exception as e:
            logger.error(f"Error in {TOOL_NAME}: {e}")
            raise

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
