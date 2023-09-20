from __future__ import annotations

import logging
import os

import pytest
import requests

from chalicelib.orm.model_chat_message import ChatMessage

# load_dotenv()
DEV_API_URL = os.getenv("DEV_API_URL") + ""
PROD_API_URL = os.getenv("PROD_API_URL") + ""
API_URL = PROD_API_URL if os.getenv("stage") == "prod" else DEV_API_URL
if not API_URL:
    raise ValueError("Must run with stage dev or prod in env.")

EP_INDEX_SUFFIX = "/"
AUTHZ_SUFFIX = "/authz"
CHAT_SUFFIX = "/chat"
EP_INSPECT_CM_SUFFIX = "/inspect/chat_message"

STAGE = os.getenv("stage", None)

DEV_WOXOM_API_KEY = os.getenv("DEV_WOXOM_API_KEY")
PROD_WOXOM_API_KEY = os.getenv("PROD_WOXOM_API_KEY")

URLS = [PROD_API_URL, DEV_API_URL]
# URLS = [DEV_API_URL]

# if STAGE == "prod" or STAGE is None:
#     URLS.append(PROD_API_URL)
#
# if STAGE == "dev" or STAGE is None:
#     URLS.append(DEV_API_URL)


@pytest.fixture
def session() -> requests.Session:
    with requests.Session() as session:
        yield session


@pytest.mark.parametrize("base_url", URLS)
class TestApi:
    """Test the API endpoints."""

    @pytest.fixture
    def index_url(self, base_url):
        return base_url + EP_INDEX_SUFFIX

    @pytest.fixture
    def authz_url(self, base_url):
        return base_url + AUTHZ_SUFFIX

    @pytest.fixture
    def chat_url(self, base_url):
        return base_url + CHAT_SUFFIX

    @pytest.fixture
    def stage_specific_headers(self, base_url):
        if base_url == PROD_API_URL:
            return {
                "x-api-key": PROD_WOXOM_API_KEY,
                "Content-Type": "application/json",
            }
        else:
            return {
                "x-api-key": DEV_WOXOM_API_KEY,
                "Content-Type": "application/json",
            }

    @pytest.fixture
    def inspect_chat_message_url(self, base_url):
        return base_url + EP_INSPECT_CM_SUFFIX

    @pytest.mark.remote_tests
    def test_index(self, session, stage_specific_headers, index_url):
        response = session.get(index_url)
        assert response.json() == {"status": "ready"}

    @pytest.mark.remote_tests
    def test_auth(self, session, stage_specific_headers, authz_url):
        response = session.get(authz_url, headers=stage_specific_headers)

        assert response.status_code == 200
        assert response.json() == {
            "message": "Successfully authenticated with your API key",
            "status": "ready",
        }

    @pytest.fixture
    def incoming_chat_message(self, simple_chat_message) -> ChatMessage:
        outgoing_chat_message = simple_chat_message
        return outgoing_chat_message

    @pytest.mark.remote_tests
    def test_inspect_chat_message(
        self,
        session: requests.Session,
        stage_specific_headers: dict,
        incoming_chat_message: ChatMessage,
        inspect_chat_message_url: str,
    ):
        """Test the /inspect/chat_message endpoint."""
        chat_message = incoming_chat_message
        self.headers = stage_specific_headers
        self.chat_message = chat_message

        # Prepare a sample JSON request body

        self.response = session.post(
            inspect_chat_message_url,
            headers=self.headers,
            json=self.chat_message.to_json(),
        )

        # Assert the response is correct
        assert self.response.status_code == 200

        response_body = self.response.json()
        assert response_body["incoming_message"] is not None
        assert isinstance(response_body["incoming_message"], str)
        assert response_body["incoming_message"] == self.chat_message.message
        assert response_body["incoming_client_id"] is not None
        assert isinstance(response_body["incoming_client_id"], str)
        assert response_body["incoming_client_id"] == self.chat_message.client_id
        assert response_body["incoming_reset"] is not None
        # You can further customize your assertions based on the expected behavior of this endpoint.

    # The following tests call eachother in sequence. Their states are independent, but they share code.
    @pytest.mark.remote_tests
    def test_reset(
        self,
        session: requests.Session,
        stage_specific_headers: dict,
        chat_url: str,
        incoming_chat_message: ChatMessage,
        agent_config_profile_name: str = "default",
    ) -> None:
        chat_message = incoming_chat_message
        self.headers = stage_specific_headers
        self.client_id = chat_message.client_id

        new_chat_message = ChatMessage(
            client_id=self.client_id,
            reset=True,
            message="don't panic",  # TODO, agent_config=simple_chat_message.agent_config
            agent_config=agent_config_profile_name,
        )
        self.chat_message = new_chat_message

        logging.debug(f"{chat_url=} | {self.headers=}")
        logging.debug(f"chat_message: {self.chat_message}")

        self.response = session.post(
            chat_url, headers=self.headers, json=self.chat_message.to_json()
        )  # self.call_chat()

        self.response_message = self.response.json()["message"]
        self.session_id = self.response.json()["session_id"]

        # Assert the response is correct
        assert self.response.status_code == 200
        assert self.response_message is not None
        assert isinstance(self.response_message, str)
        assert self.session_id is not None
        assert isinstance(self.session_id, str)
        assert len(self.session_id) > 0
        assert isinstance(self.response.json()["session_id"], str)
        # return self.session_id
        # TODO test the icebreaker and other attributes
        # TODO test the session cookie

    @pytest.mark.remote_tests
    def test_introduction(
        self,
        session: requests.Session,
        stage_specific_headers: dict,
        chat_url,
        incoming_chat_message: ChatMessage,
        message: str = "Hello, my name is Buck Futter and my favorite food is sliced oranges!",
    ) -> None:
        chat_message = incoming_chat_message
        """Send a simple introductory message to the bot."""
        self.reset = True  # true if this is the first message in a conversation
        self.client_id = incoming_chat_message.client_id
        self.headers = stage_specific_headers
        self.agent_config = incoming_chat_message.agent_config_overrides

        self.chat_message = ChatMessage(
            client_id=self.client_id,
            reset=self.reset,
            agent_config_overrides=self.agent_config,
        )

        self.test_reset(
            session=session,
            stage_specific_headers=self.headers,
            incoming_chat_message=self.chat_message,
            chat_url=chat_url,
        )
        assert self.session_id is not None

        self.reset = False

        self.chat_message = ChatMessage(
            client_id=self.client_id,
            reset=self.reset,
            message=message,
            session_id=self.session_id,
        )

        self.response = session.post(
            chat_url, json=self.chat_message.to_json(), headers=self.headers
        )

        # Assert the response is correct
        assert self.response.status_code == 200
        assert self.response.json()["message"] is not None
        assert isinstance(self.response.json()["message"], str)
        assert self.response.json()["session_id"] is not None
        assert isinstance(self.response.json()["session_id"], str)
        assert len(self.response.json()["session_id"]) > 0

        # return self.response.json()["session_id"]

    @pytest.mark.remote_tests
    def test_recall_name(
        self,
        session: requests.Session,
        stage_specific_headers: dict,
        incoming_chat_message: ChatMessage,
        chat_url,
        message: str = "What's my name?",
    ):
        """Message to the bot: What's my name?"""
        chat_message = incoming_chat_message
        self.client_id = chat_message.client_id
        self.headers = stage_specific_headers
        self.agent_config = chat_message.agent_config_overrides

        self.test_introduction(
            session=session,
            stage_specific_headers=self.headers,
            incoming_chat_message=chat_message,
            chat_url=chat_url,
        )
        self.reset = False

        self.chat_message = ChatMessage(
            client_id=self.client_id,
            reset=self.reset,
            message=message,
            session_id=self.session_id,
        )

        self.response = session.post(
            chat_url, headers=self.headers, json=self.chat_message.to_json()
        )

        # Assert the response is correct
        assert self.response.status_code == 200
        assert self.response.json()["message"] is not None
        assert isinstance(self.response.json()["message"], str)
        assert self.response.json()["session_id"] is not None
        assert isinstance(self.response.json()["session_id"], str)
        assert len(self.response.json()["session_id"]) > 0

        # Assert the response is correct
        assert (
            "futter".casefold() in self.response.json()["message"].casefold()
            or "disconnected".casefold() in self.response.json()["message"].casefold()
        )
        # return self.response.json()["message"]

    @pytest.mark.remote_tests
    def test_recall_food(
        self,
        session: requests.Session,
        stage_specific_headers: dict,
        incoming_chat_message: ChatMessage,
        chat_url,
        message="What's my favorite food?",
    ):
        """Message to the bot to test memory"""
        chat_message = incoming_chat_message

        self.client_id = chat_message.client_id
        self.headers = stage_specific_headers
        self.agent_config = chat_message.agent_config_overrides

        self.test_introduction(
            session=session,
            stage_specific_headers=self.headers,
            incoming_chat_message=chat_message,
            chat_url=chat_url,
        )

        self.reset = False

        self.chat_message = ChatMessage(
            client_id=self.client_id,
            reset=self.reset,
            message=message,
            session_id=self.session_id,
        )

        self.response = session.post(
            chat_url, headers=self.headers, json=self.chat_message.to_json()
        )
        # Assert the response is correct
        assert self.response.status_code == 200
        assert self.response.json()["message"] is not None
        assert isinstance(self.response.json()["message"], str)
        assert self.response.json()["session_id"] is not None
        assert isinstance(self.response.json()["session_id"], str)
        assert len(self.response.json()["session_id"]) > 0

        # Assert the response is correct
        assert (
            "orange".casefold() in self.response.json()["message"].casefold()
            or "disconnected".casefold() in self.response.json()["message"].casefold()
        )
        # return self.response.json()["message"]

    # New conversation, try to get the agent to trigger the tool
    # def test_call_agent(self, client, headers, message="My name is Chad Geepeeti, my DOB is Apr..."):
    #     """Message to the bot to test one shot tool use"""
    #     logger.info(f"expanding input string: {message}")
    #     message = ("My name is Chad Geepeeti, I want to contact a health insurance agent as soon as possible. My date "
    #                "of birth is April 1, 1942. I am currently taking tylonol, and vicoden. I live in CA and my email "
    #                "address is e@my.ass. My phone number is 605-475-6964. Please get me in touch with an agent "
    #                "immediately.")
    #     self._test_reset(client=client, stage_specific_headers=headers)
    #     self.response = self.call_chat(message=message)
    #     logger.info(self.response['json_body']['response'])
    #
    #     # Assert the response is correct
    #     assert self.response.get('status_code') == 200

    # def test_call_agent_with_confirmation(self, client, headers, message="... yes, please call the fucking agent."):
    #     """Message to the bot to test tool use."""
    #     logger.info(f"expanding input string: {message}")
    #     self.test_call_agent(client=client, stage_specific_headers=headers)
    #     message = "Yes, please proceed and get me in touch with an agent."
    #     self._test_recall_name(client=client, stage_specific_headers=headers)
    #     self.response = self.call_chat(message=message)
    #
    #     # Assert the response is correct
    #     assert self.response.get('status_code') == 200
