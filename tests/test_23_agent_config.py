import uuid

import pytest

from chalicelib.orm.model_agent_config import AgentConfig


@pytest.fixture
def incoming_agent_config(default_agent_config):
    outgoing_agent_config = default_agent_config
    outgoing_agent_config.profile_name = "test_profile_name"
    outgoing_agent_config.client_id = "test_client_id"
    outgoing_agent_config.save()
    return outgoing_agent_config  # Change this to default, clean, dirty fixture to expand/constrict the scope of the test


class TestAgentConfig:
    # Test to validate fundamental operations on AgentConfig
    @pytest.mark.orm_tests
    def test_agent_config_operations(self, incoming_agent_config):
        # 1. Test creation of AgentConfig
        assert incoming_agent_config is not None

        # 2. Test copy of AgentConfig
        serialized_agent_config = incoming_agent_config.to_json()
        copied_agent_config = AgentConfig.from_json(serialized_agent_config)

        assert copied_agent_config is not None
        # 3. Compare each value one by one asserting their equality
        for key, value in incoming_agent_config.to_dict().items():
            copied_agent_config_dict = dict(copied_agent_config)
            assert value == copied_agent_config_dict.get(key)

        # 4. Use == to assert equality
        assert copied_agent_config == incoming_agent_config
        assert copied_agent_config is not incoming_agent_config

        # 5. Compare to a different one asserting not the same
        different_agent_config = AgentConfig(profile_name="Different", session_id=str(uuid.uuid4()))
        assert different_agent_config != incoming_agent_config

    @pytest.mark.orm_tests
    def test_agent_config_save_retrieve(self, incoming_agent_config):
        # 1. Save the unique AgentConfig to DynamoDB
        save_response = incoming_agent_config.save()
        assert (
            save_response is not None
        )  # Add more robust checks based on your DynamoDB response structure

        # 2. Retrieve the saved AgentConfig from DynamoDB
        retrieved_agent_config = AgentConfig.get(
            profile_name=incoming_agent_config.profile_name,
            client_id=incoming_agent_config.client_id,
        )
        assert retrieved_agent_config is not None

        # 3. Compare each value one by one asserting their equality
        for key, value in incoming_agent_config.to_dict().items():
            original_value = value
            retrieved_value = getattr(retrieved_agent_config, key)
            assert original_value == retrieved_value

            original_type = type(original_value)
            retrieved_type = type(retrieved_value)
            assert original_type == retrieved_type

        # 4. Use == to assert equality between the original and retrieved AgentConfigs
        assert incoming_agent_config == retrieved_agent_config

    # # Test to validate updating fields and refreshing the AgentConfig object
    @pytest.mark.orm_tests
    def test_agent_config_update_refresh(self, incoming_agent_config):
        original_agent_config = incoming_agent_config
        modified_agent_config = AgentConfig.from_json(original_agent_config.to_json())
        assert original_agent_config == modified_agent_config

        # 1. Save the unique AgentConfig to DynamoDB
        save_response = incoming_agent_config.save()
        assert (
            save_response is not None
        )  # Add more robust checks based on your DynamoDB response structure

        # 2. Update some fields
        changed_fields = {
            "executor_max_iterations": 7,
            "executor_temp": 0.69,
            "prompt_layer_tags": "banana",
        }
        for key, value in changed_fields.items():
            setattr(modified_agent_config, key, value)

        # 3. Save the updated AgentConfig
        update_response = modified_agent_config.save()
        assert (
            update_response is not None
        )  # Add more robust checks based on your DynamoDB response structure

        # 4. Retrieve the updated AgentConfig
        retrieved_updated_agent_config = AgentConfig.get(
            profile_name=modified_agent_config.profile_name,
            client_id=modified_agent_config.client_id,
        )

        # 5. Compare each value one by one asserting their equality
        for key, value in retrieved_updated_agent_config.to_dict().items():
            original_value = getattr(original_agent_config, key)
            modified_value = getattr(modified_agent_config, key)
            retrieved_value = value
            original_value_type = type(original_value)
            modified_value_type = type(modified_value)
            retrieved_value_type = type(retrieved_value)

            assert original_value_type == modified_value_type
            assert original_value_type == retrieved_value_type

            if key in changed_fields.keys():
                assert original_value != modified_value
                assert modified_value == retrieved_value
            else:
                assert original_value == retrieved_value
                assert modified_value == retrieved_value

        original_agent_config.refresh()

        # 5. Refresh the original AgentConfig object and confirm it reflects the updated values
        for key, value in retrieved_updated_agent_config.to_dict().items():
            original_value = getattr(original_agent_config, key)
            modified_value = getattr(modified_agent_config, key)
            retrieved_value = value
            original_value_type = type(original_value)
            modified_value_type = type(modified_value)
            retrieved_value_type = type(retrieved_value)

            assert original_value_type == modified_value_type
            assert original_value_type == retrieved_value_type

            assert original_value == modified_value
            assert modified_value == retrieved_value

        incoming_agent_config.save()

        # assert incoming_agent_config is not None
        #
        # # Step 2: Save the unique agent_config to DynamoDB
        # save_response = incoming_agent_config.save()
        # assert (
        #     save_response is not None
        # )  # Add more robust checks based on your DynamoDB response structure
        #
        # # Step 3: Update some fields
        # changed_fields = {
        #     "executor_max_iterations": "420",
        #     "executor_temp": "0.69",
        #     "prompt_layer_tags": "banana",
        # }
        # for field, value in changed_fields.items():
        #     setattr(incoming_agent_config, field, value)
        #
        # # Step 4: Retrieve the agent_config from DynamoDB
        # original_agent_config = AgentConfig.get(
        #     profile_name=incoming_agent_config.profile_name,
        #     client_id=incoming_agent_config.client_id,
        # )
        #
        # assert original_agent_config is not None
        #
        # # Step 5: Assert differences between updated and retrieved agent_config
        # for f, changed_value in changed_fields.items():
        #     original_value = getattr(original_agent_config, f)
        #     assert original_value != changed_value
        #
        # # Step 6: Assert that the updated agent_config and retrieved agent_config are not equal
        # assert incoming_agent_config != original_agent_config
        #
        # # Step 7: Refresh the original agent_config object and confirm it reflects the saved values
        # incoming_agent_config.refresh()
        #
        # # Step 8: Assert equality between the original and retrieved Leads
        # assert incoming_agent_config == original_agent_config
        #
        # # Step 9: Save the updated agent_config
        # update_response = incoming_agent_config.save()
        # assert (
        #     update_response is not None
        # )  # Add more robust checks based on your DynamoDB response structure
        #
        # # Step 10: Retrieve the updated agent_config
        # retrieved_updated_agent_config = AgentConfig.get(
        #     profile_name=incoming_agent_config.profile_name,
        #     client_id=incoming_agent_config.client_id,
        # )
        #
        # assert retrieved_updated_agent_config is not None
        #
        # # Step 11: Compare each value one by one, asserting their equality
        # for key, value in incoming_agent_config.to_dict().items():
        #     original_value = value
        #     retrieved_value = getattr(retrieved_updated_agent_config, key)
        #     assert original_value == retrieved_value
        #
        # # Step 12: Assert that the updated agent_config and the newly retrieved agent_config are still equal
        # assert incoming_agent_config == retrieved_updated_agent_config
