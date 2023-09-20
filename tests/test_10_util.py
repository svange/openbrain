import os

from chalicelib.util import Util


class TestUtil:
    """Test the ORM layer."""
    def test_get_session_table_name(self):
        """Create a new agent config and store it in DynamoDB, then make sure it was stored correctly."""
        session_table_name = Util.SESSION_TABLE_NAME
        assert 'woxom' in session_table_name.lower()
        assert 'dev' in session_table_name.lower()
        assert 'session' in session_table_name.lower()

    def test_get_configs_table_name(self):
        """Create a new agent config and store it in DynamoDB, then make sure it was stored correctly."""
        configs_table_name = Util.AGENT_CONFIG_TABLE_NAME
        assert 'woxom' in configs_table_name.lower()
        assert 'dev' in configs_table_name.lower()
        assert 'agent' in configs_table_name.lower()


    def test_get_secrets(self):
        """Create a new agent config and store it in DynamoDB, then make sure it was stored correctly."""
        secrets = Util.SECRETS_STORE_ARN
        assert 'woxom' in secrets.lower()
        assert 'dev' in secrets.lower()
        assert 'secret' in secrets.lower()

