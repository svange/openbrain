from typing import Protocol, Any

from openbrain.orm.model_agent_config import AgentConfig
# from openbrain.orm.model_lead import Lead


class OBCallbackHandlerFunctionProtocol(Protocol):
    """Type hints for our customized langchain callback handler. The OB callback handler adds instance variables to the callback handler class for use with OB tools. The OBTool class has functions that can be used as callbacks. This Protocol provides type hints for those functions."""

    def __call__(self, agent_config: AgentConfig, *args, **kwargs) -> Any:
        ...
