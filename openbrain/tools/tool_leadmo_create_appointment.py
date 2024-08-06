from __future__ import annotations

import datetime
import json
from ast import literal_eval
from typing import Any, Optional

from langchain.tools.base import BaseTool
from leadmo_api.models.appointment_endpoint_params import CreateAppointmentParams
from leadmo_api.v1.client import LeadmoApiV1
from pydantic import BaseModel, Extra, Field

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.tools.models.model_leadmo_appointment import LeadmoAppointmentAdaptor
from openbrain.tools.util_leadmo_tools import get_leadmo_api_key

logger = get_logger()

TOOL_NAME = "leadmo_create_appointment"

# LangChain tool
class LeadmoCreateAppointmentTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = 'allow'
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful when you have negotiated an appointment time with the user and want to book the appointment."""
    args_schema: type[BaseModel] = LeadmoAppointmentAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        context = json.loads(tool_input.get('context'))
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        try:
            # Create an appointment in Lead Momentum

            location_id = context.get("locationId")
            calendar_id = context.get("calendarId")

            # Lead Momentum requests from the workflow come in with location_id's
            if location_id:
                try:
                    api_key = get_leadmo_api_key(location_id)
                except Exception as e:
                    api_key = context.get("api_key")

            if not calendar_id and not api_key:
                response = "System error: Can't get appointment times. Inform the user of other ways to contact us, and apologize for the inconveinence."
                if agent_config.get("record_tool_actions"):
                    OBTool.record_action(tool_name=TOOL_NAME, response=response, latest=True, session_id=session_id,
                                         agent_config=agent_config,
                                         event={"ERROR": "No calendar ID or API key when getting appointment slots."})
                return response


            # Send appointment
            constructed_appointment = context
            constructed_appointment.update(kwargs)

            leadmo_create_appointment_params = CreateAppointmentParams(**constructed_appointment)

            try:
                leadmo_client = LeadmoApiV1(api_key=api_key)
                # start = timer()
                response_from_crm = leadmo_client.create_appointment(
                    **leadmo_create_appointment_params.model_dump())
                # end = timer()
                # elapsed_time = end - start
                # put_metric_data('ExternalApiLatency', elapsed_time, [{'Name': 'ExternalApi', 'Value': "Leadmo"}], namespace=METRICS_NAMESPACE)
            except Exception as e:
                print("Failed to send user info to Lead Momentum.")
                raise

            logger.info(f"response_from_crm: {response_from_crm}")

            return json.dumps(response_from_crm)
        except Exception as e:
            # Tool failed, send an event instead and let the event mesh / dead letter queue handle it.
            event_detail = {
                "context": context,
                "ai_input": kwargs
            }

            event_detail_string = json.dumps(event_detail)
            logger.info(f"event_detail_string: {event_detail_string}")
            response = OBTool.send_event(tool_name=TOOL_NAME, event_detail=event_detail_string)

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

            return response

        # Send event


    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass

def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLeadmoCreateAppointment(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LeadmoCreateAppointmentTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
