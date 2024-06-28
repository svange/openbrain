import os

import boto3
from aws_lambda_powertools.utilities.idempotency import idempotent, DynamoDBPersistenceLayer


def get_api_key(location_id, leadmo_agent_table_name):
    """Get API key from the database."""

    client = boto3.client('dynamodb')

    try:
        response = client.get_item(
            Key={
                'location_id': {
                    'S': location_id,
                }
            },
            TableName=leadmo_agent_table_name,
        )

        item = response.get("Item")
        api_key = item.get("api_key").get("S")
    except Exception as e:
        print("Failed to get API key from the database.")
        raise e

    if item is None or len(item) == 0:
        raise LookupError(
            f"Failed to find API key: {location_id=}"
        )
    return api_key

def conditional_idempotent(func):
    persistence_layer = DynamoDBPersistenceLayer(table_name=os.getenv('IDEMPOTENCY_TABLE_NAME', 'ObIdempotencyTable-Dev'))
    if os.getenv("DEPLOYED"):
        return idempotent(persistence_store=persistence_layer)(func)
    return func
