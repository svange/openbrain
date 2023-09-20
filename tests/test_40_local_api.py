from __future__ import annotations

import os

import pytest
import retry
from chalice import Chalice
from pytest_chalice.handlers import RequestHandler


from chalicelib.orm.model_agent_config import AgentConfig
from chalicelib.orm.model_chat_message import ChatMessage

# load_dotenv()
DEV_API_URL = "" if os.getenv("stage") == "local" else os.getenv("DEV_API_URL")

EP_INDEX = DEV_API_URL + "/"
EP_AUTHZ = DEV_API_URL + "/authz"
EP_CHAT = DEV_API_URL + "/chat"
EP_INSPECT_CM = DEV_API_URL + "/inspect/chat_message"


@pytest.fixture
def incoming_agent_config(default_agent_config):
    outgoing_agent_config = default_agent_config
    return outgoing_agent_config  # Change this to default, clean, dirty fixture to expand/constrict the scope of the test


@pytest.fixture
def incoming_chat_message(simple_chat_message: ChatMessage) -> ChatMessage:
    outgoing_chat_message = simple_chat_message
    return outgoing_chat_message  # Change this to default, clean, dirty fixture to expand/constrict the scope of the test


class TestApi:
    """Test the API endpoints."""

    def test_index(self, client: RequestHandler, headers):
        response = client.get(EP_INDEX)
        assert response.values['json'] == {"status": "ready"}

    def test_auth(self, client: RequestHandler, headers):
        response = client.get(EP_AUTHZ, headers=headers)

        assert response.status_code == 200
        assert response.values['json'] == {
            "message": "Successfully authenticated with your API key",
            "status": "ready",
        }

    def test_inspect_chat_message(
            self, client: RequestHandler, headers: dict, incoming_chat_message: ChatMessage
    ):
        """Test the /inspect/chat_message endpoint."""

        # Prepare a sample JSON request body
        response = client.post(path=EP_INSPECT_CM, headers=headers, body=incoming_chat_message.to_json())

        # Assert the response is correct
        assert response.status_code == 200

    # The following tests call eachother in sequence. Their states are independent, but they share code.
    @pytest.mark.redundant
    def test_reset(self, client: RequestHandler, headers: dict, incoming_chat_message: ChatMessage) -> None:
        client_id = incoming_chat_message.client_id

        incoming_chat_message.reset = True
        incoming_chat_message.agent_config = "default"
        chat_message = incoming_chat_message

        if isinstance(chat_message.agent_config_overrides, dict):
            agent_config: AgentConfig = AgentConfig(**chat_message.agent_config_overrides)
        elif isinstance(chat_message.agent_config_overrides, AgentConfig):
            agent_config: AgentConfig = chat_message.agent_config_overrides
        else:
            agent_config: AgentConfig = AgentConfig()

        icebreaker = agent_config.icebreaker

        response = client.post(
            EP_CHAT, headers=headers, body=chat_message.to_json()
        )  # self.call_chat()

        self.response_message = response.values['json']["message"]
        self.session_id = response.values['json']["session_id"]

        # Assert the response is correct
        assert response.status_code == 200
        assert self.response_message is not None
        assert isinstance(self.response_message, str)
        assert self.session_id is not None
        assert isinstance(self.session_id, str)
        assert len(self.session_id) > 0
        assert isinstance(response.values['json']["session_id"], str)
        assert self.response_message == icebreaker
        # TODO test the icebreaker and other attributes
        # TODO test the session cookie

    @pytest.mark.redundant
    def test_introduction(
            self,
            client: RequestHandler,
            headers: dict,
            incoming_chat_message: ChatMessage,
            message: str = "Hello, my name is Buck Futter and my favorite food is sliced oranges!",
    ) -> None:
        """Send a simple introductory message to the bot."""
        reset = True  # true if this is the first message in a conversation
        client_id = incoming_chat_message.client_id
        headers = headers
        agent_config = incoming_chat_message.agent_config_overrides

        chat_message = ChatMessage(
            client_id=client_id,
            reset=reset,
            agent_config_overrides=agent_config,
        )

        self.test_reset(
            client=client,
            headers=headers,
            incoming_chat_message=chat_message,
        )
        chat_message = ChatMessage(
            client_id=client_id,
            reset=False,
            message=message,
            session_id=self.session_id,
            agent_config_overrides=agent_config,
        )

        response = client.post(
            EP_CHAT, headers=headers, body=chat_message.to_json()
        )

        # Assert the response is correct
        assert response.status_code == 200
        assert response.values['json']["message"] is not None
        assert isinstance(response.values['json']["message"], str)
        assert response.values['json']["session_id"] is not None
        assert isinstance(response.values['json']["session_id"], str)
        assert len(response.values['json']["session_id"]) > 0
        last_response_message = response.values['json']["message"]

    @pytest.mark.redundant
    @retry.retry(delay=1, tries=2)
    def test_recall_name(
            self,
            client: RequestHandler,
            headers: dict,
            incoming_chat_message: ChatMessage,
            message: str = "What's my name?",
    ):
        """Message to the bot: What's my name?"""
        client_id = incoming_chat_message.client_id
        headers = headers
        agent_config = incoming_chat_message.agent_config_overrides

        self.test_introduction(
            client=client,
            headers=headers,
            incoming_chat_message=incoming_chat_message,
        )

        reset = False

        chat_message = ChatMessage(
            client_id=client_id,
            reset=reset,
            message=message,
            session_id=self.session_id,
            agent_config_overrides=agent_config,
        )

        response = client.post(
            EP_CHAT, headers=headers, body=chat_message.to_json()
        )

        # Assert the response is correct
        assert response.status_code == 200
        assert response.values['json']["message"] is not None
        assert isinstance(response.values['json']["message"], str)
        assert response.values['json']["session_id"] is not None
        assert isinstance(response.values['json']["session_id"], str)
        assert len(response.values['json']["session_id"]) > 0

        # Assert the response is correct
        assert (
                "futter".casefold() in response.values['json']["message"].casefold()
                or "disconnected".casefold() in response.values['json']["message"].casefold()
        )
        last_response_message = response.values['json']["message"]

    @retry.retry(delay=1, tries=2)
    def test_recall_food(
            self,
            client: RequestHandler,
            headers: dict,
            incoming_chat_message: ChatMessage,
            message="What's my favorite food?",
    ):
        """Message to the bot to test memory"""

        client_id = incoming_chat_message.client_id
        headers = headers

        self.test_introduction(
            client=client,
            headers=headers,
            incoming_chat_message=incoming_chat_message,
        )

        reset = False

        chat_message = ChatMessage(
            client_id=client_id,
            reset=reset,
            message=message,
            session_id=self.session_id,
        )

        response = client.post(
            EP_CHAT, headers=headers, body=chat_message.to_json()
        )
        # Assert the response is correct
        assert response.status_code == 200
        assert response.values['json']["message"] is not None
        assert isinstance(response.values['json']["message"], str)
        assert response.values['json']["session_id"] is not None
        assert isinstance(response.values['json']["session_id"], str)
        assert len(response.values['json']["session_id"]) > 0

        # Assert the response is correct
        assert (
                "orange".casefold() in response.values['json']["message"].casefold()
                or "disconnected".casefold() in response.values['json']["message"].casefold()
        )
        self.last_response_message = response.values['json']["message"]

    # New conversation, try to get the agent to trigger the tool
    def test_call_agent(
            self,
            client: RequestHandler,
            headers: dict,
            incoming_chat_message: ChatMessage,
            message="My name is Chad Geepeeti, my DOB is 1, 1975. I live in Mississippi, and I currently take vicodin and tylonol. My phone number is 619-465-7894 and my email is e@my.ass. Please get me in touch with an agent immediately.",
    ):
        """Message to the bot to test one shot tool use"""
        reset = True  # true if this is the first message in a conversation
        client_id = incoming_chat_message.client_id
        headers = headers
        agent_config = incoming_chat_message.agent_config_overrides

        chat_message = ChatMessage(
            client_id=client_id,
            reset=reset,
            agent_config_overrides=agent_config,
        )

        self.test_reset(
            client=client,
            headers=headers,
            incoming_chat_message=chat_message,
        )

        reset = False

        chat_message = ChatMessage(
            client_id=client_id,
            reset=reset,
            message=message,
            session_id=self.session_id,
            agent_config_overrides=agent_config,
        )

        response = client.post(
            EP_CHAT, headers=headers, body=chat_message.to_json()
        )

        # Assert the response is correct
        assert response.status_code == 200
        assert response.values['json']["message"] is not None
        assert isinstance(response.values['json']["message"], str)
        assert response.values['json']["session_id"] is not None
        assert isinstance(response.values['json']["session_id"], str)
        assert len(response.values['json']["session_id"]) > 0
        last_response_message = response.values['json']["message"]

    # def test_call_agent_with_confirmation(
    #         self, app: RequestHandler, headers: dict, incoming_chat_message: ChatMessage,
    #         message="... yes, please call the fucking agent."
    # ):
    #     """Message to the bot to test tool use."""
    #     """Message to the bot to test one shot tool use"""
    #     self.reset = True  # true if this is the first message in a conversation
    #     self.client = client
    #     self.headers = headers
    #
    #     self.test_reset(client=client, headers=headers, incoming_chat_message=incoming_chat_message)
    #
    #     self.reset = False
    #
    #     self.chat_message = ChatMessage(
    #         client_id=self.client_id,
    #         reset=self.reset,
    #         message=message,
    #         session_id=self.session_id,
    #         agent_config_overrides=self.agent_config,
    #     )
    #
    #     self.response = client.post(
    #         EP_CHAT, headers=self.headers, body=self.chat_message.to_json()
    #     )
    #
    #     # Assert the response is correct
    #     assert self.response.status_code == 200
    #     assert self.response.values['json']["message"] is not None
    #     assert isinstance(self.response.values['json']["message"], str)
    #     assert self.response.values['json']["session_id"] is not None
    #     assert isinstance(self.response.values['json']["session_id"], str)
    #     assert len(self.response.values['json']["session_id"]) > 0
    #     self.last_response_message = self.response.values['json']["message"]
