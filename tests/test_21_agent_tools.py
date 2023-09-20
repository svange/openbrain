import os

import pytest

from chalicelib.util import Util
from chalicelib.gpt_agent import GptAgent, send_lead_event, send_business_sns, send_lead_to_lead_momentum, LeadAdaptor
from orm.model_agent_config import AgentConfig
from orm.model_lead import Lead


@pytest.fixture
def incoming_agent_config(default_agent_config):
    outgoing_agent_config = default_agent_config
    return outgoing_agent_config


@pytest.fixture
def incoming_lead(simple_lead):
    outgoing_lead = simple_lead
    return outgoing_lead


class TestAgentTools:
    """Test the GptAgent's tools."""
    def test_send_lead_event(self, incoming_agent_config: AgentConfig, incoming_lead: Lead):
        """Send an event to the lead event stream."""
        # gpt_agent = GptAgent(agent_config=incoming_agent_config, lead=incoming_lead)
        lead_adaptor = LeadAdaptor(**incoming_lead.__dict__)
        send_lead_event(lead_adaptor=lead_adaptor)


