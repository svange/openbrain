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
    def test_client_email(self, incoming_client):
        client = incoming_client
        assert client

        email = client.email
        client.save()
        client.email = "new_email"

        retrieved_client_by_email = client.get(email=email)
        retrieved_client = retrieved_client_by_email.model_dump()
        assert retrieved_client_by_email.email != client.email
        retrieved_client.pop("email")
        for key, value in retrieved_client.items():
            assert getattr(client, key) == value


    @pytest.mark.ci_cd
    @pytest.mark.orm_tests
    @pytest.mark.xfail(reason="Pipeline policy prevents this from passing. Find a better way than adding this permission to every pipeline.")
    def test_client_location_id(self, incoming_client):
        client = incoming_client
        assert client

        location_id = client.leadmo_location_id
        client.save()
        client.email = "new_email"

        retrieved_client_by_email = client.get(location_id=location_id)
        retrieved_client = retrieved_client_by_email.model_dump()
        assert retrieved_client_by_email.email != client.email
        retrieved_client.pop("email")
        for key, value in retrieved_client.items():
            assert getattr(client, key) == value


        client.lls_api_key = "new_lls_api_key"
        assert client.lls_api_key == "new_lls_api_key"

        client.refresh()

        assert client.lls_api_key != "new_lls_api_key"
