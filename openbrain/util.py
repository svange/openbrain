import os
from dataclasses import dataclass, field, asdict
from enum import Enum

import boto3
from aws_lambda_powertools import (
    Logger,
    Metrics,
    Tracer,
)
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

from openbrain.exceptions import ObMissingEnvironmentVariable

load_dotenv()

# MODE = os.getenv("MODE", "LOCAL")


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

    SESSION_TABLE_NAME = None
    # LEAD_TABLE_NAME = None
    AGENT_CONFIG_TABLE_NAME = None
    ACTION_TABLE_NAME = None
    # SECRET_STORE_NAME = "ObSecrets"

    # Central Infrastructure
    EVENTBUS_NAME = "ObEventBus"

    # DB Tables
    INFRA_STACK_NAME = "OpenBrain"
    SESSION_TABLE_PUBLISHED_NAME = "ObSessionTableName"
    # LEAD_TABLE_PUBLISHED_NAME = "ObLeadTableName"
    AGENT_CONFIG_TABLE_PUBLISHED_NAME = "ObAgentConfigTableName"
    ACTION_TABLE_PUBLISHED_NAME = "ObActionTableName"
    # SECRET_STORE_PUBLISHED_NAME = "OpenbrainSecretStore"

    # Other Values with defaults
    DEFAULT_CLIENT_ID = "public"
    DEFAULT_PROFILE_NAME = "default"
    PROJECT = "openbrain"
    LOG_LEVEL = "INFO"

    # MODES
    OB_MODE = "LOCAL"
    OB_MODE_DEV = "DEV"
    OB_MODE_PROD = "PROD"
    OB_MODE_LOCAL = "LOCAL"

    # EventBridge Tool Defaults
    OB_TOOL_EVENT_SOURCE = "in.openbra"
    OB_TOOL_EVENT_DETAIL_TYPE = "Openbrain Tool Event"


@dataclass()
class Config:
    """Configuration class for Openbrain"""

    OB_MODE: str = field(default=os.environ.get(Defaults.OB_MODE.name, Defaults.OB_MODE.value))
    AWS_REGION: str = field(default_factory=detect_aws_region)
    INFRA_STACK_NAME: str = field(
        default=os.environ.get(Defaults.INFRA_STACK_NAME.name, Defaults.INFRA_STACK_NAME.value)
    )

    # DB TABLES
    SESSION_TABLE_NAME: str = field(
        default=os.environ.get(Defaults.SESSION_TABLE_NAME.name, Defaults.SESSION_TABLE_NAME.value)
    )
    # LEAD_TABLE_NAME: str = field(
    #     default=os.environ.get(Defaults.LEAD_TABLE_NAME.name, Defaults.LEAD_TABLE_NAME.value)
    # )
    AGENT_CONFIG_TABLE_NAME: str = field(
        default=os.environ.get(
            Defaults.AGENT_CONFIG_TABLE_NAME.name, Defaults.AGENT_CONFIG_TABLE_NAME.value
        )
    )
    ACTION_TABLE_NAME: str = field(
        default=os.environ.get(
            Defaults.ACTION_TABLE_NAME.name, Defaults.ACTION_TABLE_NAME.value)
    )

    SESSION_TABLE_PUBLISHED_NAME: str = field(
        default=os.environ.get(
            Defaults.SESSION_TABLE_PUBLISHED_NAME.name, Defaults.SESSION_TABLE_PUBLISHED_NAME.value
        )
    )
    # LEAD_TABLE_PUBLISHED_NAME: str = field(
    #     default=os.environ.get(
    #         Defaults.LEAD_TABLE_PUBLISHED_NAME.name, Defaults.LEAD_TABLE_PUBLISHED_NAME.value
    #     )
    # )
    AGENT_CONFIG_TABLE_PUBLISHED_NAME: str = field(
        default=os.environ.get(
            Defaults.AGENT_CONFIG_TABLE_PUBLISHED_NAME.name,
            Defaults.AGENT_CONFIG_TABLE_PUBLISHED_NAME.value,
        )
    )
    ACTION_TABLE_PUBLISHED_NAME: str = field(
        default=os.environ.get(
            Defaults.ACTION_TABLE_PUBLISHED_NAME.name,
            Defaults.ACTION_TABLE_PUBLISHED_NAME.value,
        )
    )

    # MISC RESOURCES
    EVENTBUS_NAME: str = field(
        default=os.environ.get(Defaults.EVENTBUS_NAME.name, Defaults.EVENTBUS_NAME.value)
    )
    # SECRET_STORE_NAME: str = field(
    #     default=os.environ.get(Defaults.SECRET_STORE_NAME.name, Defaults.SECRET_STORE_NAME.value)
    # )

    LOG_LEVEL: str = field(
        default=os.environ.get(Defaults.LOG_LEVEL.name, Defaults.LOG_LEVEL.value)
    )
    _central_infra_outputs: dict[str, str] = field(
        default=None, init=False, repr=False, compare=False, hash=False
    )

    # MODES
    RECOGNIZED_OB_MODES: list[str] = field(
        default_factory=lambda: [x.value for x in Defaults if x.name.startswith("OB_MODE_")]
    )

    def __post_init__(self):
        if self.OB_MODE not in self.RECOGNIZED_OB_MODES:
            # raise ValueError(f"Environment variable OB_MODE={self.OB_MODE} must be one of {self.RECOGNIZED_OB_MODES}")
            logger = get_logger()
            logger.warning(
                f"Environment variable OB_MODE={self.OB_MODE} must be one of {self.RECOGNIZED_OB_MODES}"
            )
        self.set_dynamic_values()


    def set_dynamic_values(self):
        _logger = get_logger()
        dynamic_attributes = [
            attrib.replace("_PUBLISHED_NAME", "_NAME")
            for attrib in self.__dict__
            if attrib.endswith("_PUBLISHED_NAME")
        ]
        defaults = asdict(self)
        undefined_resources = []
        no_published_name = []
        for attrib in dynamic_attributes:
            if self.OB_MODE == "LOCAL":
                logger.debug(f"Running in local mode, ignoring dynamic values for {attrib}")
                continue

            attrib_published_name = getattr(self, attrib.replace("_NAME", "_PUBLISHED_NAME"))
            _logger.debug(
                f"{attrib} not defined in environment variables, searching for friendly name {attrib_published_name}"
            )

            # If the friendly name is using the default, emit a warning
            if attrib_published_name == defaults[attrib]:
                _logger.debug(
                    f"{attrib} is using the default friendly name. Do you have this infrastructure deployed?"
                )

            if not attrib_published_name:
                _logger.warning(f"{attrib} not defined in environment variables")
                print(
                    f"WARNING: Must define {attrib} in environment variables or define {attrib_published_name} and {Defaults.INFRA_STACK_NAME} in environment variables"
                )
                no_published_name.append((attrib, attrib_published_name))
                continue

            try:
                resource_name = self._get_resource_from_central_infra(attrib_published_name)
                setattr(self, attrib, resource_name)
            except ClientError as e:
                print(
                    f"ERROR: Can't find {attrib} in environment variables or central infrastructure"
                )
                undefined_resources.append((attrib, attrib_published_name))

        # Run through accumulated errors and raise
        if no_published_name or undefined_resources:
            for attrib, attrib_published_name in no_published_name:
                print(
                    f"ERROR: Must define {attrib} in environment variables or define {attrib_published_name} and {Defaults.INFRA_STACK_NAME.value} in environment variables"
                )

            for attrib, attrib_published_name in undefined_resources:
                print(
                    f"ERROR: Can't find {attrib_published_name} values from your central infrastructure"
                )

            # raise ObMissingEnvironmentVariable(
            #     "Missing environment variables or central infrastructure. Please define all resource names in "
            #     "environment OR define the central infrastructure stack name in environment and resource friendly "
            #     "names."
            # )

    def _get_resource_from_central_infra(self, friendly_name):
        logger = get_logger()

        if not self._central_infra_outputs:  # Lazy load
            boto_session = boto3.Session()
            cf_client = boto_session.client("cloudformation")

            try:
                response = cf_client.describe_stacks(StackName=self.INFRA_STACK_NAME)
                self._central_infra_outputs = {
                    x["OutputKey"]: x["OutputValue"] for x in response["Stacks"][0]["Outputs"]
                }
            except NoCredentialsError or ClientError as e:
                logger.warning(
                    f"Can't find central infrastructure stack {self.INFRA_STACK_NAME} - to find resources from "
                    f"friendly names. Please define all resource names in the environment OR define the central "
                    f"infrastructure stack name in the environment and resource friendly names"
                )
                logger.warning(str(e))
                # raise e

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
    logger.debug(config)
    # if config.OB_MODE == Defaults.OB_MODE_LOCAL.value:
    #     identity = boto3.client("sts").get_caller_identity()
    #     logger = get_logger()
    #     logger.debug(identity)
