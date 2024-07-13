import random

import ulid
from faker import Faker

from openbrain.orm.model_client import Client

fake = Faker()

def generate_client(try_to_break_shit: bool = False):
    email = fake.email()
    leadmo_api_key = fake.uuid4()
    leadmo_location_id = fake.uuid4()
    lls_api_key = fake.uuid4()

    client = Client(
        email=email,
        leadmo_api_key=leadmo_api_key,
        leadmo_location_id=leadmo_location_id,
        lls_api_key=lls_api_key
    )
    return client
