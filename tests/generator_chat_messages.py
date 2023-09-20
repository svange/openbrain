import random

from faker import Faker
from openbrain.orm.model_chat_message import ChatMessage

# from tests.generator_agent_configs import generate_agent_config

fake = Faker()


def generate_chat_message(try_to_break_shit: bool = False):
    if try_to_break_shit:
        message = fake.random_element([None, "", fake.word(), fake.sentence()])
        reset = random.choice([True, False, None])
        client_id = fake.word()
    else:
        message = fake.sentence()
        reset = random.choice([True, False])
        client_id = "public"

    return ChatMessage(
        client_id=client_id,
        # session_id=fake.uuid4(),
        reset=reset,
        # agent_config_overrides=generate_agent_config(),
        agent_config="default",
        message=message,
    )
