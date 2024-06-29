from __future__ import annotations

import datetime
import json
import pickle
from json import JSONDecodeError

import langchain.prompts
import openai
from langchain import LLMChain
from langchain.agents import AgentExecutor, AgentType, ConversationalChatAgent, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import OutputParserException, SystemMessage

from openbrain.agents.exceptions import (
    AgentError,
)
from openbrain.orm.model_agent_config import AgentConfig
# from openbrain.orm.model_lead import Lead
from openbrain.tools.toolbox import Toolbox
from openbrain.util import get_logger

# from openbrain.tools.tool_callback_handler import CallbackHandler


logger = get_logger()


class GptAgent:
    working_memory: BaseChatMemory

    def __init__(self, agent_config: AgentConfig, memory: BaseChatMemory = None, initial_context: dict = None, **kwargs):
        # Initialize the agent config
        self.initial_context = initial_context or {}
        # self.lead = lead
        self.agent_config = agent_config
        self.client_id = agent_config.client_id
        self.session_id = agent_config.session_id

        # Initialize the agent
        self.toolbox = Toolbox(agent_config=self.agent_config, initial_context=initial_context, **kwargs)

        self.tools = self.toolbox.get_tools()
        # self.tools = [ConnectWithAgentTool()]

        self._rw_memory: ConversationBufferMemory
        # self.callbacks: List[BaseCallbackHandler] = [CallbackHandler(lead=self.lead)]
        # self.shared_memory: ReadOnlySharedMemory
        try:
            self.agent = self._get_new_agent(
                memory=memory,
            )
        except Exception as e:
            raise AgentError(e)
        # self.filter_chain = self.get_new_filter_chain()
        # self.sensor_chain = self.get_new_censor_chain()

        # self._snapshot_state()  # ensure that the memory is saved after every message
        logger.debug("Initialized agent with id: " + self.agent_config.executor_id)

    def _get_new_agent(self, memory: BaseChatMemory = None) -> AgentExecutor:
        # Get attributes from the preferences dict
        # Set up API keys

        # Model name
        model_name = self.agent_config.executor_chat_model

        # Model Temperature
        model_temp = self.agent_config.executor_temp

        # Executor Max Iterations
        max_iterations = self.agent_config.executor_max_iterations

        # Executor Max Execution Time
        max_execution_time = self.agent_config.executor_max_execution_time

        # System Message
        system_message = self.agent_config.system_message

        openai.api_key = self.agent_config.openai_api_key

        llm = ChatOpenAI(
            temperature=model_temp,
            model_name=model_name,
        )

        # Memory
        self._rw_memory = memory

        # Tools
        tools = self.tools

        # Function agents are special, so we build them differently # TODO: Time to make a class...
        initial_message = f"Hi, this conversation is starting on {datetime.datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}, and may span several days."

        # if self.initial_context:
        #     readable_list = [k + ": " + v for k, v in self.initial_context.items()]
        #     initial_message = "To begin, here is some information about me: " + ", ".join(readable_list)

        if self.agent_config.executor_model_type == "function":
            if memory is None:
                memory = ConversationBufferMemory(memory_key="memory", return_messages=True)
                memory.save_context({"input": initial_message}, {"output": self.agent_config.icebreaker})

            system_message = SystemMessage(content=system_message)

            agent_kwargs = {
                "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
                "system_message": system_message,
            }

            agent_executor = initialize_agent(
                tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                agent_kwargs=agent_kwargs,
                memory=memory,
                handle_parsing_errors=True,
                max_iterations=max_iterations,
                max_execution_time=max_execution_time,
                # callbacks=self.callbacks,
            )
        else:
            if memory is None:
                memory = ConversationSummaryBufferMemory(memory_key="chat_history", return_messages=True, llm=llm)
            prompt = langchain.agents.ConversationalChatAgent.create_prompt(
                tools=tools,
                system_message=system_message,
            )
            llm_chain = LLMChain(
                llm=llm,
                prompt=prompt,
                verbose=False,
            )
            agent = ConversationalChatAgent(
                llm_chain=llm_chain,
                tools=tools,
                max_execution_time=max_execution_time,
            )
            agent_executor = langchain.agents.AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=tools,
                memory=memory,
                max_iterations=max_iterations,
                max_execution_time=max_execution_time,
                verbose=True,
            )

        self.working_memory = memory
        return agent_executor

    @classmethod
    def deserialize(cls, state: dict[str, str | bytes], context: dict = None) -> GptAgent:
        """Reconstructs an agent from a serialized agent memory and initial config."""
        frozen_memory = state["frozen_agent_memory"]
        frozen_agent_config = state["frozen_agent_config"]
        # frozen_lead = state["frozen_lead"]

        thawed_agent_config = json.loads(frozen_agent_config)
        # thawed_lead = Lead.from_json(frozen_lead)
        agent_memory = pickle.loads(frozen_memory)

        initial_config = AgentConfig(**thawed_agent_config)

        if context:
            agent = GptAgent(agent_config=initial_config, memory=agent_memory, initial_context=context)
        else:
            agent = GptAgent(agent_config=initial_config, memory=agent_memory)
        return agent

    def serialize(self) -> dict[str, str | bytes]:
        """Returns a serializable state of the agent, which can be used to reconstruct the agent."""
        memory_snapshot: bytes = pickle.dumps(self.working_memory)  # SERIALIZING DONE HERE

        agent_state = {
            "frozen_agent_memory": memory_snapshot,
            "frozen_agent_config": self.agent_config.to_json(),
            # "frozen_lead": None if self.lead.to_json is None else self.lead.to_json(),
        }
        return agent_state

    def handle_user_message(self, user_message: str, **kwargs) -> str:
        """Send message to agent"""

        logger.debug(f"{kwargs=}")


        try:
            response_message = self.agent.run(user_message, callbacks=[self.toolbox.callback_handler])

        except JSONDecodeError as e:
            logger.error(str(e))
            ai_message = e.doc
            self._rw_memory.chat_memory.add_user_message(user_message)
            self._rw_memory.chat_memory.add_ai_message(ai_message)
            response_message = ai_message
        except OutputParserException as e:
            logger.error("OutputParserException: " + str(e))
            ai_message = e.args[0].strip("Could not parse LLM output: ")
            self._rw_memory.chat_memory.add_user_message(user_message)
            self._rw_memory.chat_memory.add_ai_message(ai_message)
            response_message = ai_message
        except Exception as e:
            logger.error("Exception: " + str(e))
            raise

        # ensure that the state is saved after every message
        # self._snapshot_state()  # ensure that the memory is saved after every message
        return response_message


if __name__ == "__main__":
    pass
