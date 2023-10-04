import pathlib
import uuid

import pytest

from openbrain.orm.model_lead import Lead

tests_dir = pathlib.Path(__file__).parent.absolute()
test_resources_dir = tests_dir / "resources" / "examples"


@pytest.mark.orm_tests
def test_lead_config(default_lead: Lead) -> None:
    lead = default_lead
    assert lead.lead_id is not None


@pytest.fixture
def incoming_lead(simple_lead):
    outgoing_lead = simple_lead
    return outgoing_lead


class TestLead:
    @pytest.mark.ci_cd
    @pytest.mark.orm_tests
    def test_lead_operations(self, incoming_lead):
        # 1. Test creation of AgentConfig
        assert incoming_lead is not None

        # 2. Test copy of AgentConfig
        copied_lead = Lead(**incoming_lead.dict())
        assert copied_lead is not None

        # 3. Compare each value one by one asserting their equality
        for key, value in incoming_lead.to_dict().items():
            original_value = value
            original_value_type = type(original_value)
            copied_value = getattr(copied_lead, key)
            copied_value_type = type(copied_value)
            assert original_value == copied_value
            assert original_value_type == copied_value_type

        # 4. Use == to assert equality
        assert incoming_lead == copied_lead

        # 5. Compare to a different one asserting not the same
        different_lead = Lead(client_id="Different", session_id=str(uuid.uuid4()))
        assert different_lead != incoming_lead

    @pytest.mark.ci_cd
    @pytest.mark.orm_tests
    def test_lead_save_retrieve(self, incoming_lead):
        # 1. Save the unique Lead to DynamoDB
        save_response = incoming_lead.save()
        assert save_response is not None  # Add more robust checks based on your DynamoDB response structure

        # 2. Retrieve the saved Lead from DynamoDB
        retrieved_lead = Lead.get(lead_id=incoming_lead.lead_id, client_id=incoming_lead.client_id)
        assert retrieved_lead is not None

        # 3. Compare each value one by one asserting their equality
        for key, value in incoming_lead.to_dict().items():
            original_value = value
            original_value_type = type(original_value)
            copied_value = getattr(retrieved_lead, key)
            copied_value_type = type(copied_value)
            assert original_value == copied_value
            assert original_value_type == copied_value_type

        # 4. Use == to assert equality between the original and retrieved Leads
        assert incoming_lead == retrieved_lead

    @pytest.mark.ci_cd
    @pytest.mark.orm_tests
    def test_lead_update_refresh(self, incoming_lead):
        # 1. Save the unique Lead to DynamoDB
        save_response = incoming_lead.save()
        assert save_response is not None  # Add more robust checks based on your DynamoDB response structure

        # 2. Update some fields
        updated_fields = {
            "state_of_residence": "XY",
            "session_id": "CHANGED",
        }
        for field, value in updated_fields.items():
            setattr(incoming_lead, field, value)

        # 3. Save the updated Lead
        update_response = incoming_lead.save()
        assert update_response is not None  # Add more robust checks based on your DynamoDB response structure

        # 4. Retrieve the updated Lead
        retrieved_lead = Lead.get(lead_id=incoming_lead.lead_id, client_id=incoming_lead.client_id)
        assert retrieved_lead is not None

        for field, expected_value in updated_fields.items():
            retrieved_value = getattr(retrieved_lead, field)
            assert retrieved_value == expected_value

        # 5. Refresh the original Lead object and confirm it reflects the updated values
        incoming_lead.refresh()
        for field, expected_value in updated_fields.items():
            refreshed_value = getattr(incoming_lead, field)
            assert refreshed_value == expected_value

    @pytest.mark.ci_cd
    @pytest.mark.orm_tests
    def test_lead_update_refresh_extensive(self, incoming_lead):
        # Step 1: Get a unique lead
        # incoming_lead = lead_fixture

        assert incoming_lead is not None

        # Step 2: Save the unique lead to DynamoDB
        save_response = incoming_lead.save()
        assert save_response is not None  # Add more robust checks based on your DynamoDB response structure

        # Step 3: Update some fields
        updated_fields = {
            "full_name": "Updated_Full_Name",
            "email_address": "updated_email@example.com",
        }
        for field, value in updated_fields.items():
            setattr(incoming_lead, field, value)

        # Step 4: Retrieve the lead from DynamoDB
        retrieved_lead = Lead.get(lead_id=incoming_lead.lead_id, client_id=incoming_lead.client_id)
        assert retrieved_lead is not None

        # Step 5: Assert differences between updated and retrieved lead
        for field, updated_value in updated_fields.items():
            retrieved_value = getattr(retrieved_lead, field)
            assert retrieved_value != updated_value

        # Step 6: Assert that the updated lead and retrieved lead are not equal
        assert incoming_lead != retrieved_lead

        # Step 7: Refresh the original lead object and confirm it reflects the saved values
        incoming_lead.refresh()

        # Step 8: Assert equality between the original and retrieved Leads
        assert incoming_lead == retrieved_lead

        # Step 9: Save the updated lead
        update_response = incoming_lead.save()
        assert update_response is not None  # Add more robust checks based on your DynamoDB response structure

        # Step 10: Retrieve the updated lead
        retrieved_updated_lead = Lead.get(lead_id=incoming_lead.lead_id, client_id=incoming_lead.client_id)
        assert retrieved_updated_lead is not None

        # Step 11: Compare each value one by one, asserting their equality
        for key, value in incoming_lead.to_dict().items():
            original_value = value
            original_value_type = type(original_value)
            copied_value = getattr(retrieved_updated_lead, key)
            copied_value_type = type(copied_value)
            assert original_value == copied_value
            assert original_value_type == copied_value_type

        # Step 12: Assert that the updated lead and the newly retrieved lead are still equal
        assert incoming_lead == retrieved_updated_lead
