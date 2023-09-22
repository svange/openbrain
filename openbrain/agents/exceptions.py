from langchain.tools.base import ToolException

from openbrain.util import Util

logger = Util.logger
metrics = Util.metrics
tracer = Util.tracer


class AgentError(Exception):
    """Raised when the agent fails."""


class AgentToolError(ToolException):
    """Raised when the backend fails."""


class AgentToolIncompleteLeadError(AgentToolError):
    """Raised when the agent tries to connect to an agent on behalf of a lead that is not complete"""


class AgentToolLeadMomentumError(AgentToolError):
    """Raised when LeadMomentum returns an error"""

    event_bus_name = Util.EVENT_BUS_FRIENDLY_NAME
    event_source = Util.PROJECT
    event_bridge_client = Util.BOTO_SESSION.client("events")
    event = {
        "Source": event_source,
        "DetailType": __name__,
        "EventBusName": event_bus_name,
        "Detail": "{}",
    }

    # TODO: Send to dead letter queue
