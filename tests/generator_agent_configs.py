import random

import ulid
from faker import Faker

from openbrain.orm.model_agent_config import AgentConfig, EXECUTOR_MODEL_TYPES, CHAT_LANGUAGE_MODELS, FUNCTION_LANGUAGE_MODELS, COMPLETION_LANGUAGE_MODELS

fake = Faker()

def generate_agent_config(try_to_break_shit: bool = False):
    if try_to_break_shit:
        garbage_choices = (
                EXECUTOR_MODEL_TYPES + CHAT_LANGUAGE_MODELS + COMPLETION_LANGUAGE_MODELS + FUNCTION_LANGUAGE_MODELS + [fake.word() for _ in range(5)]
        )
        model_types = garbage_choices
        completion_models = garbage_choices
        chat_models = garbage_choices
        function_models = garbage_choices
        fake_executor_max_iterations = random.uniform(-5000.0, 5000)
        fake_executor_max_execution_time = fake.random_int(min=-5000, max=5000)
        fake_executor_temp = random.uniform(-5000.0, 5000)
    else:
        model_types = EXECUTOR_MODEL_TYPES
        completion_models = COMPLETION_LANGUAGE_MODELS
        chat_models = CHAT_LANGUAGE_MODELS
        function_models = FUNCTION_LANGUAGE_MODELS
        fake_executor_max_iterations = (fake.random_int(min=1, max=10),)
        fake_executor_max_execution_time = (fake.random_int(min=1, max=20),)
        fake_executor_temp = (fake.random_element([0.2, 0.5, 0.7, 0.9]),)

    return AgentConfig(
        profile_name=fake.word(),
        client_id=fake.uuid4(),
        executor_id=str(ulid.ULID().to_uuid()),
        system_message=fake.sentence(),
        icebreaker=fake.sentence(),
        # executor_model_type=fake.random_element(executor_model_types),
        # executor_chat_model=fake.random_element(executor_chat_models),
        # executor_completion_model=fake.random_element(executor_completion_models),
        executor_max_iterations=fake_executor_max_iterations,
        executor_max_execution_time=fake_executor_max_execution_time,
        executor_temp=fake_executor_temp,
        llm=fake.random_element(function_models),
        # prompt_layer_tags=fake.word(),
        # outgoing_webhook_url=fake.url(),
        # email_address=fake.email(),
    )
