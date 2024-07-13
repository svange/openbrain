import os

import boto3
from aws_lambda_powertools.utilities.idempotency import idempotent, DynamoDBPersistenceLayer

from openbrain.orm.model_client import Client


def get_leadmo_api_key(location_id):
    """Get API key from the database."""

    if not location_id:
        raise ValueError("location_id is required.")

    client = Client.get(location_id=location_id)
    api_key = client.leadmo_api_key

    return api_key

def conditional_idempotent(func):
    persistence_layer = DynamoDBPersistenceLayer(table_name=os.getenv('IDEMPOTENCY_TABLE_NAME', 'ObIdempotencyTable-Dev'))
    if os.getenv("IDEMPOTENT"):
        return idempotent(persistence_store=persistence_layer)(func)
    return func
