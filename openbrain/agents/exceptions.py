from langchain.tools.base import ToolException

class AgentError(Exception):
    """Raised when the agent fails."""


class AgentToolError(ToolException):
    """Raised when the backend fails."""


class AgentToolIncompleteLeadError(AgentToolError):
    """Raised when the agent tries to connect to an agent on behalf of a lead that is not complete"""


class AgentToolIncompleteContactError(AgentToolError):
    """Raised when the agent tries to update a contact without enough information"""


class AgentToolLeadMomentumError(AgentToolError):
    """Raised when LeadMomentum returns an error"""
    pass
