import json
from abc import ABCMeta, abstractmethod
from typing import TypeAlias

import boto3
from pydantic import Extra, BaseModel

from chalicelib.util import Util

# LOGGING
logger = Util.logger
TRecordable: TypeAlias = "Recordable"
TSerializable: TypeAlias = "Serializable"


def snake_to_camel_case(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Value must be a string.")
    words = value.split("_")
    value = "".join(word.title() for word in words if word)
    return f"{value[0].lower()}{value[1:]}"


class Serializable(BaseModel, metaclass=ABCMeta):
    class Config:
        alias_generator = snake_to_camel_case
        extra = Extra.ignore
        populate_by_name = True
        validate_assignment = True

    class Meta:
        table_name = Util.AGENT_CONFIG_TABLE_NAME
        region = Util.AWS_REGION

    @abstractmethod
    def save(self):
        """Saves the object to the database"""

    @classmethod
    def get(cls, *args, **kwargs) -> TSerializable:
        """Gets the object from the database"""

    @abstractmethod
    def refresh(self):
        """Refreshes the object from the database"""

    def to_json(self) -> str:
        obj_dict = self.dict(by_alias=True)
        return json.dumps(obj_dict)

    @classmethod
    def from_json(cls, json_string: str) -> TSerializable:
        json_dict = json.loads(json_string)
        obj = cls(**json_dict)
        return obj

    @classmethod
    def from_dict(cls, dictionary: dict) -> TSerializable:
        return cls(**dictionary)

    def to_dict(self) -> dict:
        return self.__dict__

    def to_dict_by_alias(self) -> dict:
        return self.dict(by_alias=True)


class Recordable(Serializable, metaclass=ABCMeta):
    @staticmethod
    def _get_dynamo_client() -> boto3.resource:
        if Util.LOCAL:
            dynamodb = boto3.resource(
                "dynamodb",
                endpoint_url="http://localhost:8000",
                region_name="us-east-1",  # it's for local connections, so it's fake anyway
            )
        else:
            dynamodb = boto3.resource("dynamodb")
        return dynamodb

    @classmethod
    def _get(
            cls,
            range_key_name: str,
            range_key_value: str,
            hash_key_name: str,
            hash_key_value: str,
            table_name: str,
    ) -> dict:
        dynamodb = cls._get_dynamo_client()
        table = dynamodb.Table(table_name)
        logger.info(
            f"Retrieving object: {table=} | {hash_key_name=} | {hash_key_value=} | {range_key_name=} | {range_key_value=}"
        )
        response = table.get_item(
            Key={hash_key_name: hash_key_value, range_key_name: range_key_value}
        )
        item = response.get("Item", {})

        if item is None or len(item) == 0:
            raise LookupError(
                f"Failed to find: {table=} | {hash_key_name=} | {hash_key_value=} | {range_key_name=} | {range_key_value=}"
            )
        # return dynamo_obj_to_python_obj(item)
        return item

    def _save(
            self,
            table_name: str,
            range_key_name: str = None,
            hash_key_name: str = None,
            range_key_value: str = None,
            hash_key_value: str = None,
            disable_surgical_update: bool = True,  # Leave this here until it's fixed
    ):
        """Save this object to the database."""

        dynamodb = self._get_dynamo_client()
        table = dynamodb.Table(table_name)

        if (
                hash_key_name
                and hash_key_value
                and range_key_name
                and range_key_value
                and not disable_surgical_update  # TODO DISABLED
        ):
            # Get item for a more surgical insert
            response = table.get_item(
                Key={hash_key_name: hash_key_value, range_key_name: range_key_value}
            )
            item = response.get("Item", {})
            if item:
                # Update
                response = table.put_item(Item=self.to_dict())  # TODO: do a surgical update
                return response

        # TODO if retrievable, then update, else create

        query_dict = {}
        for key, value in self.to_dict().items():
            if isinstance(value, float):
                query_dict[key] = str(value)
            else:
                query_dict[key] = value

        response = table.put_item(Item=query_dict)
        # change all floats to strings:
        return response
