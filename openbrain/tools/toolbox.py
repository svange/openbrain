from langchain.tools import BaseTool

from openbrain.tools.callback_handler import CallbackHandler
from openbrain.tools.protocols import OBCallbackHandlerFunctionProtocol
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_lead import Lead
from openbrain.tools.obtool import OBTool

from openbrain.util import get_logger

from openbrain.tools.tool_leadmo_update_contact import OBToolLeadmoUpdateContact
from openbrain.tools.tool_leadmo_stop_conversation import OBToolLeadmoStopConversation
from openbrain.tools.tool_send_lead_to_crm import OBToolSendToCRM

logger = get_logger()


class Toolbox:  # invoker
    """A toolbox for GptAgents."""

    tool_friendly_names: dict[str:OBTool] = {
        "leadmo_update_contact": "OBToolLeadmoUpdateContact",
        "leadmo_stop_conversation": "OBToolLeadmoStopConversation",
        "send_lead_to_crm": "OBToolSendToCRM",
        "tester": "OBToolTester",
    }

    available_tools: dict[str:OBTool] = {}

    tools: list[BaseTool] = []

    def __init__(
        self,
        agent_config: AgentConfig,
        initial_context: dict = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.callback_handler = CallbackHandler(agent_config=agent_config, initial_context=initial_context)
        # Initialize a list for the BaseTool objects and one list each for each langchain callback type
        self._initialize_known_lists()

        # Add tools listed by name in the agent_config to the list of tool, and add the tool's callbacks to the
        # appropriate callback list, creating new lists for callback types if langchain has added new callback types
        # emit a warning to the user to update the list of known callback types

        tools_to_register = [tool_name for tool_name in agent_config.tools]
        if tools_to_register:
            for tool_name in tools_to_register:
                tool_class_name = self.tool_friendly_names.get(tool_name)
                try:
                    obtool = self.available_tools[tool_class_name]
                except KeyError:
                    raise KeyError(f"Tool {tool_class_name} not registered\n Registered tools: {str(self.available_tools)}")

                self.callback_handler.register_ob_tool(obtool, initial_context=initial_context)
                self.register_obtool(obtool)

        else:
            # add all tools
            # self.tools = [obtool.tool for obtool in self.available_tools.values()]
            # add no tools
            self.tools = [self.available_tools['OBToolDoNothing'].tool]




    def _initialize_known_lists(self, *args, **kwargs):
        """Initialize a list for the BaseTool objects and one list each for each langchain callback type."""
        # self.tools: list[BaseTool] = []
        # Setting known langchain handler callbacks for type hinting new callbacks (i.e. on_whatever) added to
        # langchain should be added here for completeness as type hints don't work through setattr
        self.on_llm_start_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_chat_model_start_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_llm_new_token_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_llm_end_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_llm_error_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_chain_start_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_chain_end_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_chain_error_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_tool_start_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_tool_end_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_tool_error_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_text_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_agent_action_callbacks: list[OBCallbackHandlerFunctionProtocol] = []
        self.on_agent_finish_callbacks: list[OBCallbackHandlerFunctionProtocol] = []

    def register_obtool(self, obtool: type[OBTool]):
        if obtool.tool:
            self.tools.append(obtool.tool)


    @classmethod
    def register_available_obtool(cls, tool: type[OBTool]):
        if issubclass(tool, OBTool) and tool != OBTool:
            cls.available_tools[tool.__name__] = tool
        else:
            raise TypeError(f"Tool {tool} is not a subclass of OBTool")

    def get_tools(self):
        return [tool() for tool in self.tools]
