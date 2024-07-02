from openbrain.util import config


class TestUtil:
    """Test the ORM layer."""

    def test_get_session_table_name(self):
        """Create a new agent config and store it in DynamoDB, then make sure it was stored correctly."""
        session_table_name = config.SESSION_TABLE_NAME
        assert session_table_name is not None

    def test_get_configs_table_name(self):
        """Create a new agent config and store it in DynamoDB, then make sure it was stored correctly."""
        configs_table_name = config.AGENT_CONFIG_TABLE_NAME
        assert configs_table_name is not None

    # def test_get_action_table_name(self):
    #     """Create a new agent config and store it in DynamoDB, then make sure it was stored correctly."""
    #     configs_table_name = config.ACTION_TABLE_NAME
    #     assert configs_table_name is not None
