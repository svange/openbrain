import os
from dataclasses import dataclass, field, asdict
from enum import Enum

import boto3
from aws_lambda_powertools import (
    Logger,
    Metrics,
    Tracer,
)
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from openbrain.exceptions import ObMissingEnvironmentVariable

load_dotenv()

MODE = os.getenv("MODE", "LOCAL")

def get_logger() -> Logger:
    logger = Logger(service=f"{__name__}")
    # boto3.set_stream_logger()
    # boto3.set_stream_logger("botocore")
    return logger


def get_metrics() -> Metrics:
    metrics = Metrics(service=f"{__name__}")
    return metrics


def get_tracer() -> Tracer:
    tracer = Tracer(service=f"{__name__}")
    return tracer


if MODE == "DEV":
    identity = boto3.client("sts").get_caller_identity()
    logger = get_logger()
    logger.debug(identity)


def detect_aws_region() -> str:
    """Detects the AWS region from the environment or boto3 session"""
    region_from_env = os.getenv("AWS_REGION", None)
    if os.getenv("AWS_REGION"):
        return os.getenv("AWS_REGION")
    else:
        session = boto3.session.Session()
        return session.region_name


class Defaults(Enum):
    """Default values for environment variables and other constants."""

    # Dynamic values without defaults, must defined in environment variables or central infrastructure
    SESSION_TABLE = None
    LEAD_TABLE = None
    AGENT_CONFIG_TABLE = None
    EVENTBUS = None
    SECRET_STORE = None

    # Central Infrastructure and friendly names
    INFRA_STACK_NAME = "ai-infra"
    SESSION_TABLE_FRIENDLY_NAME = "OpenbrainSessionTable"
    LEAD_TABLE_FRIENDLY_NAME = "OpenbrainLeadTable"
    EVENTBUS_FRIENDLY_NAME = "AiEventBus"
    AGENT_CONFIG_TABLE_FRIENDLY_NAME = "OpenbrainAgentConfigTable"
    SECRET_STORE_FRIENDLY_NAME = "OpenbrainSecretStore"

    # Other Values with defaults
    DEFAULT_CLIENT_ID = "public"
    DEFAULT_PROFILE_NAME = "default"
    MODE = "LOCAL"
    PROJECT = "openbrain"
    LOG_LEVEL = "INFO"

    # Lists
    RECOGNIZED_MODES = ["DEV", "PROD", "LOCAL"]


@dataclass()
class Config:
    MODE: str = field(default=os.environ.get(Defaults.MODE.name, Defaults.MODE.value))
    AWS_REGION: str = field(default_factory=detect_aws_region)
    INFRA_STACK_NAME: str = field(default=os.environ.get(Defaults.INFRA_STACK_NAME.name, Defaults.INFRA_STACK_NAME.value))

    # DB TABLES
    SESSION_TABLE: str = field(default=os.environ.get(Defaults.SESSION_TABLE.name, Defaults.SESSION_TABLE.value))
    LEAD_TABLE: str = field(default=os.environ.get(Defaults.LEAD_TABLE.name, Defaults.LEAD_TABLE.value))
    AGENT_CONFIG_TABLE: str = field(default=os.environ.get(Defaults.AGENT_CONFIG_TABLE.name, Defaults.AGENT_CONFIG_TABLE.value))

    SESSION_TABLE_FRIENDLY_NAME: str = field(
        default=os.environ.get(Defaults.SESSION_TABLE_FRIENDLY_NAME.name, Defaults.SESSION_TABLE_FRIENDLY_NAME.value)
    )
    LEAD_TABLE_FRIENDLY_NAME: str = field(
        default=os.environ.get(Defaults.LEAD_TABLE_FRIENDLY_NAME.name, Defaults.LEAD_TABLE_FRIENDLY_NAME.value)
    )
    AGENT_CONFIG_TABLE_FRIENDLY_NAME: str = field(
        default=os.environ.get(
            Defaults.AGENT_CONFIG_TABLE_FRIENDLY_NAME.name,
            Defaults.AGENT_CONFIG_TABLE_FRIENDLY_NAME.value,
        )
    )

    # MISC RESOURCES
    EVENTBUS: str = field(default=os.environ.get(Defaults.EVENTBUS.name, Defaults.EVENTBUS.value))
    SECRET_STORE: str = field(default=os.environ.get(Defaults.SECRET_STORE.name, Defaults.SECRET_STORE.value))

    EVENTBUS_FRIENDLY_NAME: str = field(
        default=os.environ.get(Defaults.EVENTBUS_FRIENDLY_NAME.name, Defaults.EVENTBUS_FRIENDLY_NAME.value)
    )
    SECRET_STORE_FRIENDLY_NAME: str = field(
        default=os.environ.get(Defaults.SECRET_STORE_FRIENDLY_NAME.name, Defaults.SECRET_STORE_FRIENDLY_NAME.value)
    )

    LOG_LEVEL: str = field(default=os.environ.get(Defaults.LOG_LEVEL.name, Defaults.LOG_LEVEL.value))
    _central_infra_outputs: dict[str, str] = field(default=None, init=False, repr=False, compare=False, hash=False)

    def __post_init__(self):
        if self.MODE not in Defaults.RECOGNIZED_MODES.value:
            raise ValueError(f"Environment variable MODE={self.MODE} must be one of {Defaults.RECOGNIZED_MODES.value}")
        self.set_dynamic_values()

    def set_dynamic_values(self):
        _logger = get_logger()
        dynamic_attributes = [
            attrib.replace("_FRIENDLY_NAME", "") for attrib in self.__dict__ if attrib.endswith("_FRIENDLY_NAME")
        ]
        defaults = asdict(self)
        undefined_resources = []
        no_friendly_name = []
        for attrib in dynamic_attributes:
            if self.MODE == "LOCAL":
                logger.debug(f"Running in local mode, ignoring dynamic values for {attrib}")
                continue

            attrib_friendly_name = getattr(self, attrib + "_FRIENDLY_NAME")
            _logger.debug(f"{attrib} not defined in environment variables, searching for friendly name {attrib_friendly_name}")

            # If the friendly name is using the default, emit a warning
            if attrib_friendly_name == defaults[attrib]:
                _logger.debug(f"{attrib} is using the default friendly name. Do you have this infrastructure deployed?")

            if not attrib_friendly_name:
                _logger.error(f"{attrib} not defined in environment variables")
                print(
                    f"ERROR: Must define {attrib} in environment variables or define {attrib_friendly_name} and {Defaults.INFRA_STACK_NAME} in environment variables"
                )
                no_friendly_name.append((attrib, attrib_friendly_name))
                continue

            try:
                resource_name = self._get_resource_from_central_infra(attrib_friendly_name)
                setattr(self, attrib, resource_name)
            except ClientError as e:
                print(f"ERROR: Can't find {attrib} in environment variables or central infrastructure")
                undefined_resources.append((attrib, attrib_friendly_name))

        # Run through accumulated errors and raise
        if no_friendly_name or undefined_resources:
            for attrib, attrib_friendly_name in no_friendly_name:
                print(
                    f"ERROR: Must define {attrib} in environment variables or define {attrib_friendly_name} and {Defaults.INFRA_STACK_NAME.value} in environment variables"
                )

            for attrib, attrib_friendly_name in undefined_resources:
                print(f"ERROR: Can't find {attrib_friendly_name} values from your central infrastructure")

            raise ObMissingEnvironmentVariable(
                "Missing environment variables or central infrastructure. Please define all resource names in "
                "environment OR define the central infrastructure stack name in environment and resource friendly "
                "names."
            )

    def _get_resource_from_central_infra(self, friendly_name):
        logger = get_logger()

        if not self._central_infra_outputs:  # Lazy load
            boto_session = boto3.Session()
            cf_client = boto_session.client("cloudformation")

            try:
                response = cf_client.describe_stacks(StackName=self.INFRA_STACK_NAME)
                self._central_infra_outputs = {x["OutputKey"]: x["OutputValue"] for x in response["Stacks"][0]["Outputs"]}
            except ClientError as e:
                logger.error(
                    f"Can't find central infrastructure stack {self.INFRA_STACK_NAME} - to find resources from "
                    f"friendly names. Please define all resource names in the environment OR define the central "
                    f"infrastructure stack name in the environment and resource friendly names"
                )
                raise e

        return self._central_infra_outputs[friendly_name]


class ConfigSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls):
        cls._instance = Config()


logger = get_logger()
metrics = get_metrics()
tracer = get_tracer()
config = ConfigSingleton()

if __name__ == "__main__":
    c = config
