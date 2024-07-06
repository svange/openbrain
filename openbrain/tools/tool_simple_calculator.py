from __future__ import annotations

import datetime
import json
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

import pytz
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Field, Extra

from openbrain.orm.model_agent_config import AgentConfig
from openbrain.tools.models.context_aware_tool import ContextAwareToolMixin
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol

logger = get_logger()

TOOL_NAME = "simple_calculator"


class Operator(Enum):
    ADDITION = "+"
    SUBTRACTION = "-"
    MULTIPLICATION = "*"
    DIVISION = "/"
    MODULUS = "%"
    EXPONENTIATION = "**"
    FLOOR_DIVISION = "//"
    SQUARE_ROOT = "sqrt"
    SQUARE = "^2"
    CUBE = "^3"
    INVERSE = "1/x"
    NEGATE = "-x"

    def __str__(self):
        strings = []
        initial_string = "Operator: Description"
        strings.append(initial_string)
        for op in Operator:
            # Get string of the form
            # '+ ADDITION'
            # for each operator
            strings.append(f"{op.value} {op.name}")
        return "\n".join(strings)


class SimpleCalculatorAdaptor(BaseModel):
    """The schema for the tool's input."""
    operation: Operator = Field(description=f"""The operation to perform. One of: {' '.join(["'" + op.value + "'" for op in Operator])}""")
    left_value: Decimal = Field(description="left value of formula.")
    right_value: Optional[Decimal] = Field(default=None, description="right value of formula.")


# LangChain tool
class SimpleCalculatorTool(BaseTool, ContextAwareToolMixin):
    class Config:
        extra = Extra.allow
        populate_by_name = True
    name = TOOL_NAME
    description = """Useful when you need to make simple calculations."""
    args_schema: type[BaseModel] = SimpleCalculatorAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        tool_input = json.loads(self.tool_input)
        agent_config = tool_input.get("agent_config")
        session_id = tool_input.get("session_id")

        operation = kwargs.get("operation")
        left_value = Decimal(kwargs.get("left_value"))

        operation_map = {
            Operator.ADDITION: lambda x, y: x + y,
            Operator.SUBTRACTION: lambda x, y: x - y,
            Operator.MULTIPLICATION: lambda x, y: x * y,
            Operator.DIVISION: lambda x, y: x / y,
            Operator.MODULUS: lambda x, y: x % y,
            Operator.EXPONENTIATION: lambda x, y: x ** y,
            Operator.FLOOR_DIVISION: lambda x, y: x // y,
        }

        if operation in operation_map:
            right_value = Decimal(kwargs.get("right_value"))
            result = operation_map[operation](left_value, right_value)

        else:
            try:
                if operation == Operator.SQUARE_ROOT:
                    result = left_value.sqrt()
                elif operation == Operator.SQUARE:
                    result = left_value ** Decimal(2)
                elif operation == Operator.CUBE:
                    result = left_value ** Decimal(3)
                elif operation == Operator.INVERSE:
                    result = Decimal(1) / left_value
                elif operation == Operator.NEGATE:
                    result = -left_value
                else:
                    raise ValueError(f"Invalid operation {operation}")
            except Exception as e:
                result = f"Error: {e}"

        if agent_config.get("record_tool_actions"):
            OBTool.record_action(event=TOOL_NAME, response=result, latest=True, session_id=session_id)

        return result

    def _arun(self, ticker: str):
        raise NotImplementedError(f"{TOOL_NAME} does not support async")


# on_tool_start
def on_tool_start(agent_config: AgentConfig, input_str: str, **kwargs) -> Any:
    """Function to run during callback handler's on_llm_start event."""
    pass


def on_tool_error(agent_config: AgentConfig = None, agent_input=None, *args, **kwargs) -> Any:
    pass


class OBToolSimpleCalculator(OBTool):
    name: str = TOOL_NAME
    tool: BaseTool = SimpleCalculatorTool
    on_tool_start: OBCallbackHandlerFunctionProtocol = on_tool_start
    on_tool_error: OBCallbackHandlerFunctionProtocol = on_tool_error
