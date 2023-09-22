import ulid
from faker import Faker

from openbrain.agents.gpt_agent import GptAgent
from openbrain.orm.model_chat_session import ChatSession
from tests.generator_agent_configs import generate_agent_config
from tests.generator_leads import generate_lead

fake = Faker()


def generate_chat_session(try_to_break_shit: bool = False):
    agent_config = generate_agent_config(try_to_break_shit=try_to_break_shit)
    lead = generate_lead(try_to_break_shit=try_to_break_shit)
    gpt_agent = GptAgent(agent_config)
    frozen_agent_memory = gpt_agent.serialize()["frozen_agent_memory"]
    frozen_agent_config = gpt_agent.serialize()["frozen_agent_config"]
    frozen_lead = lead.to_json()

    return ChatSession(
        client_id=fake.uuid4(),
        frozen_agent_memory=frozen_agent_memory,
        frozen_agent_config=frozen_agent_config,
        session_id=str(ulid.ULID().to_uuid()),
        agent_config=fake.word(),
        frozen_lead=frozen_lead,
    )
