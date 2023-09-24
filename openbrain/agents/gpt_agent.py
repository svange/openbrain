from __future__ import annotations

import json
import pickle
from ast import literal_eval
from json import JSONDecodeError
from typing import Any

import boto3
import langchain.prompts
import openai
import promptlayer
import requests
from langchain import LLMChain
from langchain.agents import AgentExecutor, AgentType, ConversationalChatAgent, initialize_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI, PromptLayerChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import OutputParserException, SystemMessage
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Extra, Field

from openbrain.agents.exceptions import AgentError, AgentToolIncompleteLeadError, AgentToolLeadMomentumError
from openbrain.orm.model_agent_config import AgentConfig
from openbrain.orm.model_lead import Lead
from openbrain.util import Util

logger = Util.logger


class CallbackHandler(BaseCallbackHandler):
    """Base callback handler that can be used to handle callbacks from langchain."""

    def __init__(self, lead: Lead, agent: GptAgent):
        super().__init__()
        self.lead = lead
        self.agent = agent

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        """Run when tool starts running."""
        if serialized["name"] == "connect_with_agent":
            lead_from_db = self.lead
            agent = self.agent
            url = agent.agent_config.outgoing_webhook_url
            lead_info_from_conversation = literal_eval(input_str)
            for key, new_value in lead_info_from_conversation.items():
                try:
                    old_value = getattr(lead_from_db, key)
                except NameError:
                    old_value = None

                if old_value == new_value:
                    logger.warning(
                        f"Ambiguous property for lead, arbitrarily replacing with new value.\n{old_value=}\n{new_value=}"
                    )

                setattr(lead_from_db, key, new_value)

            if not lead_from_db.email_address and not lead_from_db.phone_number:
                raise AgentToolIncompleteLeadError(
                    "No email or phone number provided, ask the user for an email address or phone " "number and try again."
                )
            lead_from_db.sent_by_agent = True
            lead_from_db.save()
            send_business_sns(f"New lead sent: {lead_from_db=}")
            send_lead_event(lead_from_db)

            send_lead_to_lead_momentum(lead_from_db, outgoing_webhook_url=url)

            return lead_from_db

    def on_tool_error(self, error: Exception | KeyboardInterrupt, **kwargs: Any) -> Any:
        """Run when tool errors."""
        self.lead.refresh()
        self.lead.status = "ERROR"
        self.lead.save()


class GptAgent:
    working_memory: BaseChatMemory

    def __init__(self, agent_config: AgentConfig, memory=None, lead=None):
        # Initialize the agent config
        self.lead = lead
        self.agent_config = agent_config
        self.client_id = agent_config.client_id
        self.session_id = agent_config.session_id

        # Initialize the agent
        self.tools = [ConnectWithAgentTool()]
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
        logger.info("Initialized agent with id: " + self.agent_config.executor_id)

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

        # Prompt layer tags
        prompt_layer_tags = ["executor", model_name, self.agent_config.executor_id]
        if self.agent_config.prompt_layer_tags != "":
            prompt_layer_tags += self.agent_config.prompt_layer_tags.split(",")

        openai.api_key = self.agent_config.openai_api_key

        try:
            # Prompt layer enabled
            if self.agent_config.promptlayer_api_key:
                langchain.debug = True
                promptlayer.api_key = self.agent_config.promptlayer_api_key
                llm = PromptLayerChatOpenAI(
                    pl_tags=prompt_layer_tags,
                    model_name=model_name,
                    temperature=model_temp,
                    verbose=True,
                )
            else:
                llm = ChatOpenAI(
                    temperature=model_temp,
                    model_name=model_name,
                )
        except Exception:
            logger.critical("Error Creating PromptLayer LLM, trying non-promptlayer LLM")
            logger.info(f"{self.agent_config.__dict__}")
            llm = ChatOpenAI(
                temperature=model_temp,
                model_name=model_name,
            )

        # Memory
        self._rw_memory = memory

        # Tools
        tools = self.tools

        # Function agents are special, so we build them differently # TODO: Time to make a class...
        if self.agent_config.executor_model_type == "function":
            if memory is None:
                memory = ConversationBufferMemory(memory_key="memory", return_messages=True)
                memory.save_context({"input": "Hi!"}, {"output": self.agent_config.icebreaker})

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
            tools = tools
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
    def deserialize(cls, state: dict[str, str | bytes]) -> GptAgent:
        """Reconstructs an agent from a serialized agent memory and initial config."""
        frozen_memory = state["frozen_agent_memory"]
        frozen_agent_config = state["frozen_agent_config"]
        frozen_lead = state["frozen_lead"]

        thawed_agent_config = json.loads(frozen_agent_config)
        thawed_lead = Lead.from_json(frozen_lead)
        agent_memory = pickle.loads(frozen_memory)

        initial_config = AgentConfig(**thawed_agent_config)
        agent = GptAgent(agent_config=initial_config, memory=agent_memory, lead=thawed_lead)
        return agent

    def serialize(self) -> dict[str, str | bytes]:
        """Returns a serializable state of the agent, which can be used to reconstruct the agent."""
        memory_snapshot: bytes = pickle.dumps(self.working_memory)  # SERIALIZING DONE HERE

        agent_state = {
            "frozen_agent_memory": memory_snapshot,
            "frozen_agent_config": self.agent_config.to_json(),
            "frozen_lead": self.lead.to_json(),
        }
        return agent_state

    def handle_user_message(self, user_message: str) -> str:
        """Send message to agent, update lead based on conversation fragment, return LLM response and updated lead"""

        try:
            response_message = self.agent.run(user_message, callbacks=[CallbackHandler(lead=self.lead, agent=self)])

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


def send_lead_event(lead_adaptor):
    """Send lead event to event bus."""
    logger.info(f"Sending lead event to event bus: {lead_adaptor.__dict__}")
    event_bus_friendly_name = Util.EVENT_BUS_FRIENDLY_NAME
    event_bus_client = boto3.client("events")
    event_bus_client.put_events(
        Entries=[
            {
                "EventBusName": event_bus_friendly_name,
                "DetailType": "Lead",
                "Detail": json.dumps(lead_adaptor.__dict__),
            }
        ]
    )
    # Don't forget the exception that also does this


def send_business_sns(message: str) -> None:
    """Send message event to sns Business topic."""
    logger.info(f"Sending event to sns Business topic: {message}")
    sns = boto3.client("sns")
    sns.publish(
        TopicArn=Util.SNS_BUSINESS_TOPIC_ARN,
        Message=message,
        Subject="GptAgent tool used",
        MessageStructure="string",
    )
    # Don't forget the exception that also does this


def send_lead_to_lead_momentum(lead: Lead, outgoing_webhook_url=None) -> None:
    payload = lead.to_dict()

    try:
        response = requests.post(outgoing_webhook_url, json=payload)
        if response.status_code != 200:
            logger.error(f"Error sending lead to Lead Momentum: {response.status_code}")
            logger.error(response.text)
            raise AgentToolLeadMomentumError("Error sending lead to Lead Momentum (1)")
    except Exception as e:
        logger.exception(e)
        raise AgentToolLeadMomentumError("Error sending lead to Lead Momentum (2)")


class LeadAdaptor(BaseModel):
    class Config:
        extra = Extra.allow
        populate_by_name = True
        # validate_assignment = True

    # first_name: Optional[str] = Field(default=None)
    # middle_name: Optional[str] = Field(default=None)
    # last_name: Optional[str] = Field(default=None)
    full_name: str | None = Field(default=None)
    current_medications: list[str] | None = Field(default=None)
    date_of_birth: str | None = Field(default=None)
    email_address: str | None = Field(default=None)
    phone_number: str | None = Field(default=None)
    state_of_residence: str | None = Field(default=None)


class ConnectWithAgentTool(BaseTool):
    name = "connect_with_agent"
    description = """Useful when you want to get the user in touch with a human agent."""
    args_schema: type[BaseModel] = LeadAdaptor
    handle_tool_error = True
    verbose = True

    def _run(self, *args, **kwargs) -> str:
        response = (
            "Successfully connected with agent! continue to be a helpful, and friendly assistant focused on "
            "answering health insurance questions!"
        )
        return response

    def _arun(self, ticker: str):
        raise NotImplementedError("connect_with_agent does not support async")


# class ToolBox:
#     def __init__(self):
#         # self.tools = [ToolBox.send_all_required_data_to_brokerage, ToolBox.query_docs]
#         # self.tools = [ToolBox.do_nothing]
#         self.tools: list = [ToolBox.connect_with_agent]
#         self.function_agent_tools = [format_tool_to_openai_function(_tool) for _tool in self.tools]
#
# @staticmethod @tool def connect_with_agent(user_info: str) -> str: """useful if and only if ALL required user
# information is known. Takes a JSON object with user's information. If any optional user information is not known,
# do not lie, guess, or hallucinate; instead provide an empty string as its value. EXAMPLE INPUTS: {{"full_name":
# "John Doe", "date_of_birth": "01/01/1970", "current_medications": "", "state_of_residence": "CA", "email_address":
# "", "phone_number": "6194206969"}} AND {{"full_name": "Mary Jane Doe", "date_of_birth": "04/01/2001",
# "current_medications": "Tylenol", "state_of_residence": "CA", "email_address": "maryjane@example.com",
# "phone_number": ""}}"""
#
#         try:
#             user_info = json.loads(user_info)
#             full_name = user_info["full_name"]
#         except JSONDecodeError as e:
#             logger.error("Error decoding JSON object in connect_with_agent full_name")
#             logger.error(e)
#             return "I should ask the user for their full name now"
#
#         try:
#             date_of_birth = user_info["date_of_birth"]
#         except JSONDecodeError as e:
#             logger.error("Error decoding JSON object in connect_with_agent date_of_birth")
#             logger.error(e)
#             return "I should ask the user for their date of birth now"
#
#         try:
#             current_medications = user_info["current_medications"]
#         except JSONDecodeError as e:
#             logger.error("Error decoding JSON object in connect_with_agent current_medications")
#             logger.error(e)
#             return "I should ask the user for their current medications now"
#
#         try:
#             state_of_residence = user_info["state_of_residence"]
#         except JSONDecodeError as e:
#             logger.error("Error decoding JSON object in connect_with_agent state_of_residence")
#             logger.error(e)
#             return "I should ask the user for their state of residence now"
#
#         try:
#             email_address = user_info["email_address"]
#         except JSONDecodeError as e:
#             logger.error("Error decoding JSON object in connect_with_agent email_address")
#             logger.error(e)
#             return "I should ask the user for their email address now"
#
#         try:
#             phone_number = user_info["phone_number"]
#         except JSONDecodeError as e:
#             logger.error("Error decoding JSON object in connect_with_agent phone_number")
#             logger.error(e)
#             return "I should ask the user for their phone number now"
#
# response = "I no longer need to ask the user any personal questions, but I will continue to be a helpful,
# and friendly assistant!"
#
# ToolBox.send_lead( f"LEAD ALERT: {full_name} ({date_of_birth}) has requested to speak with an agent. Their phone
# number is {phone_number} and their email address is {email_address}. They are currently taking {
# current_medications} and live in {state_of_residence}." )
#
#         return response
#
#     @staticmethod
#     @tool
#     def request_full_name(full_name: str) -> str:
#         """
#         useful for when the user hasn't provided their full name yet
#         """
#         return f"I will respond by asking for full name."
#
#     @staticmethod
#     @tool
#     def request_date_of_birth(date_of_birth: str) -> str:
#         """
#         useful for when the user hasn't provided their date of birth yet
#         """
#         return f"I will respond by asking for date of birth."
#
#     @staticmethod
#     @tool
#     def request_email(email_address: str) -> str:
#         """
#         useful for when the user hasn't provided their email yet
#         """
#         return f"I will respond by asking for email."
#
#     @staticmethod
#     @tool
#     def request_phone_number(phone_number: str) -> str:
#         """
#         useful for when the user hasn't provided their phone number yet
#         """
#         return f"I will respond by asking for phone number."
#
#     @staticmethod
#     @tool
#     def request_current_medications(current_medications: str) -> str:
#         """
#         useful for when the user hasn't provided their list of medications yet
#         """
#         return f"I will respond by asking for list of medications."
#
#     @staticmethod
#     @tool
#     def request_state_of_residence(state_of_residence: str) -> str:
#         """
#         useful for when the user hasn't provided their state of residence yet
#         """
#         return f"I will respond by asking for state of residence."
#
#     @staticmethod
#     @tool
#     def do_nothing(ignored: str) -> str:
#         """useful when no other tool is useful"""
#         return "I should continue the conversation"
#
# @staticmethod @tool def no_tools_available(ignored: str) -> str: """never useful, don't bother with this,
# just  respond with a Final Answer.""" return "I'm sorry, I don't know how to do that yet. I'm still learning. I'll
# let my human friends know that you asked me to do that. They'll teach me how to do it soon!"
#
#     @staticmethod
#     def send_lead(message: str) -> None:
#         sns = boto3.client("sns")
#         sns.publish(
#             TopicArn=Util.SNS_BUSINESS_TOPIC_ARN,
#             Message=message,
#             Subject="HealthGPT",
#             MessageStructure="string",
#         )


if __name__ == "__main__":
    pass
