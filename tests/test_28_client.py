from __future__ import annotations

import json

import pytest

from openbrain.orm.model_client import Client


@pytest.fixture
def incoming_client(simple_client):
    outgoing_chat_message = simple_client
    return outgoing_chat_message


class TestClient:
    @pytest.mark.ci_cd
    @pytest.mark.orm_tests
    def test_client(self, incoming_client):
        client = incoming_client
        assert client

        email = client.email
        location_id = client.leadmo_location_id

        client.save()

        retrieved_client_by_email = client.get(email=email)
        retrieved_client_by_location_id = client.get(location_id=location_id)

        for key, value in client.dict().items():
            assert retrieved_client_by_email.dict()[key] == value
            assert retrieved_client_by_location_id.dict()[key] == value

        client.lls_api_key = "new_lls_api_key"
        assert client.lls_api_key == "new_lls_api_key"

        client.refresh()

        assert client.lls_api_key != "new_lls_api_key"
