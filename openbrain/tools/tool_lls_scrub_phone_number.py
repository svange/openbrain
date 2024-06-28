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
from aws_lambda_powertools import Logger, Tracer

LLS_API_URL = 'https://api.landlinescrubber.com/api/check_number'

DEFAULT_ORIGIN = os.getenv('DEFAULT_ORIGIN', 'https://localhost:5173')
IDEMPOTENCY_TABLE_NAME = os.getenv('IDEMPOTENCY_TABLE_NAME', 'ObIdempotencyTable-Dev')
LEADMO_AGENT_TABLE_NAME = os.getenv("LEADMO_AGENT_TABLE_NAME", "LeadmoAgentTable-Dev")


# INFRA_TOPIC_NAME = os.getenv('INFRA_TOPIC_NAME')
tracer = Tracer()  # Sets service name from env var
logger = Logger()

TOOL_NAME = "lls_scrub_phone_number"


# Utility classes and functions
class LLSAdaptor(BaseModel):
    """Adaptor class for Landline Scrubber tool."""
    phone: str = Field(..., description="Phone number to use for query")


def get_lls_api_key():
    raise NotImplementedError("get_lls_api_key is not implemented yet.")


class LLSScrubberPhoneNumberTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True

    name = TOOL_NAME
    description = """Useful when you want need to know if a phone number is on the 'Do Not Call List', or if you want to know if a phone number is a landline or mobile number."""
    args_schema: type[BaseModel] = LLSAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        global DEFAULT_ORIGIN
        global IDEMPOTENCY_TABLE_NAME
        global LLS_API_URL
        global LEADMO_AGENT_TABLE_NAME

        context = json.loads(self.tool_input)
        phone = kwargs.get("phone", None)
        api_key = context.get("api_key", None)

        try:
            if not api_key:
                api_key = get_lls_api_key()
        except Exception as e:
            logger.error(f"Exception while getting API key: {e}")
            raise e

        headers = {
            "Content-Type": "application/json",
            "Origin": DEFAULT_ORIGIN,
        }

        query_params = {
            'p': phone,
            'k': api_key
        }
        query_params_str = '&'.join([f'{k}={v}' for k, v in query_params.items()])

        url = LLS_API_URL + '?' + query_params_str

        try:

            api_response = requests.get(url=url, headers=headers)
            response = api_response.json()

        except Exception as e:
            logger.info("Failed to get info from Landline Scrubber.")
            raise e

        return response

    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass

def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolLLSScrubPhoneNumberTool(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = LLSScrubberPhoneNumberTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
