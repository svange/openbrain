import random

from faker import Faker
import ulid
from openbrain.orm.model_agent_config import AgentConfig, DefaultSettings

fake = Faker()

EXECUTOR_COMPLETION_MODELS = DefaultSettings.EXECUTOR_COMPLETION_MODELS.value
EXECUTOR_CHAT_MODELS = DefaultSettings.EXECUTOR_CHAT_MODELS.value
EXECUTOR_MODEL_TYPES = DefaultSettings.EXECUTOR_MODEL_TYPES.value


def generate_agent_config(try_to_break_shit: bool = False):
    if try_to_break_shit:
        garbage_choices = (
            EXECUTOR_MODEL_TYPES
            + EXECUTOR_CHAT_MODELS
            + EXECUTOR_COMPLETION_MODELS
            + [fake.word() for _ in range(5)]
        )
        executor_completion_models = garbage_choices
        executor_chat_models = garbage_choices
        executor_model_types = garbage_choices
        fake_executor_max_iterations = random.uniform(-5000.0, 5000)
        fake_executor_max_execution_time = fake.random_int(min=-5000, max=5000)
        fake_executor_temp = random.uniform(-5000.0, 5000)
    else:
        executor_completion_models = EXECUTOR_COMPLETION_MODELS
        executor_chat_models = EXECUTOR_CHAT_MODELS
        executor_model_types = EXECUTOR_MODEL_TYPES
        fake_executor_max_iterations = (fake.random_int(min=1, max=10),)
        fake_executor_max_execution_time = (fake.random_int(min=1, max=20),)
        fake_executor_temp = (fake.random_element([0.2, 0.5, 0.7, 0.9]),)

    return AgentConfig(
        profile_name=fake.word(),
        client_id=fake.uuid4(),
        executor_id=str(ulid.ULID().to_uuid()),
        system_message=fake.sentence(),
        icebreaker=fake.sentence(),
        executor_model_type=fake.random_element(executor_model_types),
        executor_chat_model=fake.random_element(executor_chat_models),
        executor_completion_model=fake.random_element(executor_completion_models),
        executor_max_iterations=fake_executor_max_iterations,
        executor_max_execution_time=fake_executor_max_execution_time,
        executor_temp=fake_executor_temp,
        prompt_layer_tags=fake.word(),
        outgoing_webhook_url=fake.url(),
        email_address=fake.email(),
    )
