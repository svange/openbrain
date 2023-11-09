import json
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from typing import TypeAlias

import boto3
from pydantic import BaseModel, Extra

from openbrain.util import config, Defaults, get_logger, get_tracer, get_metrics

# LOGGING
logger = get_logger()
TRecordable: TypeAlias = "Recordable"
TSerializable: TypeAlias = "Serializable"


def snake_to_camel_case(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Value must be a string.")
    words = value.split("_")
    value = "".join(word.title() for word in words if word)
    return f"{value[0].lower()}{value[1:]}"


class Serializable(BaseModel, metaclass=ABCMeta):
    """Base class for all serializable objects. Provides a stable interface and convenient serialization methods."""

    class Config:
        """Pydantic configuration for the Serializable class"""

        alias_generator = snake_to_camel_case
        extra = Extra.ignore
        populate_by_name = True
        validate_assignment = True

    class Meta:
        """PynamoDB configuration for the Serializable class"""

        table_name = config.AGENT_CONFIG_TABLE_NAME
        region = config.AWS_REGION

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
        """Returns a JSON string representation of the object using the Pydantic alias generator (camelCase here)"""
        obj_dict = self.dict(by_alias=True)
        return json.dumps(obj_dict)

    @classmethod
    def from_json(cls, json_string: str) -> TSerializable:
        """Returns a new object from a JSON string representation of the object"""
        json_dict = json.loads(json_string)
        obj = cls(**json_dict)
        return obj

    @classmethod
    def from_dict(cls, dictionary: dict) -> TSerializable:
        """Returns a new object from a dictionary representation of the object"""
        return cls(**dictionary)

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the object"""
        return self.__dict__

    def to_dict_by_alias(self) -> dict:
        """Returns a dictionary representation of the object using the Pydantic alias generator (camelCase here)"""
        return self.dict(by_alias=True)


class Recordable(Serializable, metaclass=ABCMeta):
    """Base class for all recordable objects. Provides a stable interface and convenient persistence methods."""

    @staticmethod
    def _get_dynamo_client() -> boto3.resource:
        """Returns a DynamoDB client"""
        return boto3.resource("dynamodb")

    @classmethod
    def _get(cls, range_key_name: str, range_key_value: str, hash_key_name: str, hash_key_value: str, table_name: str) -> dict:
        """Get an object from the database."""
        dynamodb = cls._get_dynamo_client()
        table = dynamodb.Table(table_name)
        logger.debug(
            f"Retrieving object: {table=} | {hash_key_name=} | {hash_key_value=} | {range_key_name=} | {range_key_value=}"
        )
        response = table.get_item(Key={hash_key_name: hash_key_value, range_key_name: range_key_value})
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
        disable_surgical_update: bool = True,
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
            response = table.get_item(Key={hash_key_name: hash_key_value, range_key_name: range_key_value})
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


class InMemoryDb(dict):
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(InMemoryDb, cls).__new__(cls)
        return cls.instance


class Ephemeral(Serializable, metaclass=ABCMeta):
    """Base class for in memory objects as an alternative to cloud (for demo purposes)."""

    @classmethod
    def _get(cls, range_key_name: str, range_key_value: str, hash_key_name: str, hash_key_value: str, table_name: str) -> dict:
        """Get an object from the DICT."""
        object_dict = InMemoryDb()
        if not object_dict.get(table_name):
            raise LookupError(f"Failed to find: {table_name=}")
        if not object_dict[table_name].get(hash_key_value):
            raise LookupError(f"Failed to find: {hash_key_name=} | {hash_key_value=}")
        if not object_dict[table_name][hash_key_value].get(range_key_value):
            raise LookupError(f"Failed to find: f{range_key_name=} | {range_key_value=}")
        return object_dict[table_name][hash_key_value][range_key_value].to_dict()

    def _save(
        self,
        table_name: str,
        range_key_name: str = None,
        hash_key_name: str = None,
        range_key_value: str = None,
        hash_key_value: str = None,
        disable_surgical_update: bool = True,
    ):
        """Save this object to the database."""
        object_dict = InMemoryDb()
        try:
            table = object_dict[table_name]
        except KeyError:
            object_dict[table_name] = {}

        try:
            client = object_dict[table_name][hash_key_value]
        except KeyError:
            object_dict[table_name][hash_key_value] = {}

        object_dict[table_name][hash_key_value][range_key_value] = deepcopy(self)

        return self
