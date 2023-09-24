import json
import os
from typing import Dict

import boto3
from aws_lambda_powertools import (  # TODO make this optional or learn to stream logs from one module to another
    Logger,
    Metrics,
    Tracer,
)
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


def _get_logger() -> Logger:
    logger = Logger(service=f'{os.environ.get("PROJECT")}')
    # boto3.set_stream_logger()
    # boto3.set_stream_logger("botocore")
    return logger


def _get_metrics() -> Metrics:
    metrics = Metrics(service=f'{os.environ.get("PROJECT")}')
    return metrics


def _get_tracer() -> Tracer:
    tracer = Tracer(service=f'{os.environ.get("PROJECT")}')
    return tracer


class Util:
    """A central source of truth for infrastructure resources and other utility functions.
    Loads API keys from AWS Secrets Manager and sets them as environment variables."""

    logger = _get_logger()
    metrics = _get_metrics()
    tracer = _get_tracer()
    CENTRAL_STACK_OUTPUTS_KNOWN_KEYS = [
        "DevCommonAccessPolicy",
        "DevSessionTable",
        "DevAgentConfigTable",
        "DevLeadTable",
        "ProdSecrets",
        "DevSecrets",
        "ProdCommonAccessPolicy",
        "ProdSessionTable",
        "ProdAgentConfigTable",
        "ProdLeadTable",
        "DevEventBus",
        "ProdEventBus",
        "DevInfraTopic",
        "DevBusinessTopic",
        "ProdInfraTopic",
        "ProdBusinessTopic",
        "STAGES",
        "DomainName",
    ]
    PROJECT = os.environ.get("PROJECT")

    SESSION_TABLE_FRIENDLY_NAME = os.environ.get("SESSION_TABLE_FRIENDLY_NAME")
    AGENT_CONFIG_TABLE_FRIENDLY_NAME = os.environ.get("AGENT_CONFIG_TABLE_FRIENDLY_NAME")
    LEAD_TABLE_FRIENDLY_NAME = os.environ.get("LEAD_TABLE_FRIENDLY_NAME")
    DEFAULT_CLIENT_ID = "public"

    INFRA_STACK_NAME = os.environ.get("INFRA_STACK_NAME")
    SECRET_STORE_FRIENDLY_NAME = os.environ.get("SECRET_STORE_FRIENDLY_NAME")
    EVENT_BUS_FRIENDLY_NAME = os.environ.get("EVENTBUS_FRIENDLY_NAME")
    SNS_BUSINESS_TOPIC_FRIENDLY_NAME = os.environ.get("BUSINESS_TOPIC_FRIENDLY_NAME")
    SNS_INFRASTRUCTURE_TOPIC_FRIENDLY_NAME = os.environ.get("INFRASTRUCTURE_TOPIC_FRIENDLY_NAME")
    BOTO_SESSION = boto3.Session()
    AWS_REGION = BOTO_SESSION.region_name
    CENTRAL_INFRA_OUTPUTS: Dict[str, str]
    SESSION_TABLE_NAME: str
    AGENT_CONFIG_TABLE_NAME: str
    LEAD_TABLE_NAME: str
    SNS_BUSINESS_TOPIC_ARN: str
    SNS_INFRASTRUCTURE_TOPIC_ARN: str
    TOP_LEVEL_DOMAIN: str

    @staticmethod
    def get_central_infra_hints(
        boto_session: boto3.Session,
        infra_project_name: str,
    ) -> Dict[str, str]:
        f"""Use friendly names get dynamically named resources from {infra_project_name} stack."""
        cf_client = boto_session.client("cloudformation")
        response = cf_client.describe_stacks(StackName=infra_project_name)
        central_infra_outputs = {x["OutputKey"]: x["OutputValue"] for x in response["Stacks"][0]["Outputs"]}
        return central_infra_outputs

    CENTRAL_INFRA_OUTPUTS = get_central_infra_hints(
        boto_session=BOTO_SESSION,
        infra_project_name=INFRA_STACK_NAME,
    )

    TOP_LEVEL_DOMAIN = CENTRAL_INFRA_OUTPUTS["DevDomainName"]
    SESSION_TABLE_NAME = CENTRAL_INFRA_OUTPUTS[SESSION_TABLE_FRIENDLY_NAME]
    AGENT_CONFIG_TABLE_NAME = CENTRAL_INFRA_OUTPUTS[AGENT_CONFIG_TABLE_FRIENDLY_NAME]
    LEAD_TABLE_NAME = CENTRAL_INFRA_OUTPUTS[LEAD_TABLE_FRIENDLY_NAME]
    SECRETS_STORE_ARN = CENTRAL_INFRA_OUTPUTS[SECRET_STORE_FRIENDLY_NAME]
    SECRETS_STORE_REGION = SECRETS_STORE_ARN.split(":")[3]
    SNS_BUSINESS_TOPIC_ARN = CENTRAL_INFRA_OUTPUTS[SNS_BUSINESS_TOPIC_FRIENDLY_NAME]
    SNS_INFRASTRUCTURE_TOPIC_ARN = CENTRAL_INFRA_OUTPUTS[SNS_INFRASTRUCTURE_TOPIC_FRIENDLY_NAME]

    @staticmethod
    def get_secret(
        boto_session: boto3.Session,
        sercret_name: str,
        secrets_store_region: str,
    ) -> dict:
        """Get a secret from AWS Secrets Manager."""
        # Create a Secrets Manager client
        session = boto_session
        client = session.client(service_name="secretsmanager", region_name=secrets_store_region)

        try:
            get_secret_value_response = client.get_secret_value(SecretId=sercret_name)
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            raise e

        # Decrypts secret using the associated KMS key.
        secret = json.loads(get_secret_value_response["SecretString"])

        return secret

    SECRETS = get_secret(BOTO_SESSION, SECRETS_STORE_ARN, SECRETS_STORE_REGION)

    # set OpenAI and Promptlayer API keys as env vars
    CENSOR_TEMPLATE = """You are a censorship agent working with an OpenAI chat model. Your job is to take what I'm
    going to say to a potential customer and make sure it conforms to the following rules:

    Only ask for one piece of information at a time. For example, change "Great! Can I have your full name,
    date of birth, list of..." into "Great! Please provide me with your full name so that I..." Do not disclose the
    conversational plan to the user. Always be truthful and do not make things up. Maintain the original tone of the
    message. Given the following message that I'm about to send to the user, please revise it to ensure it follows
    the rules stated above:

    MESSAGE: {message}

    OUTPUT: """
    FILTER_TEMPLATE = """You are an input cleaning wizard helping me, an OpenAI chat model, to better understand
    customers. Your task is to clean and rephrase the user input to make it clearer and more understandable for me.
    Given the following chat history and user message, please rephrase the user message accordingly. Remember to only
    output the cleaned message with no surrounding text, and always provide a non-empty response. If the message
    conforms to all of the rules, don't change it at all, and just output it directly. Let's begin!

    CHAT_HISTORY: {chat_history}

    MESSAGE: {message}

    OUTPUT: """

    # Testing Templates
    UNIT_TESTING_TEMPLATE = """You are a unit testing agent working with an OpenAI chat model. Your job is to take
    the last response from the bot we're testing, which I will give you, and respond as a user might. For this
    conversation, your goal is: {goal} For this conversation, your disposition is: {disposition}

    Remember to respond as you would to the bot directly, and not as you would to me. Let's begin!
    MESSAGE: {message}"""

    # Data refinement templates
    SUMMARIZE_TEMPLATE = """As a health insurance broker, summarize the given health insurance document focusing on
    information crucial for someone shopping for a plan. Include details like insurance company name, plan names,
    states offered, deductibles, copays, out-of-pocket maximums, monthly premiums, and any other relevant information
    if they are in the document. If you see unusually structured data, try to interpret it as a table, as this data
    is just text extracted from PDFs. Use tables when needed and limit the summary to 2400 words. {text}

    Summary: """
    REFINE_TEMPLATE = (
        "Your job is to produce a final summary\n"
        "We have provided an existing summary up to a certain point: {existing_answer}\n"
        "We have the opportunity to refine the existing summary"
        "(only if needed) with some more context below.\n"
        "------------\n"
        "{text}\n"
        "------------\n"
        "Given the new context, "
        "If the context isn't useful, return the original summary."
        "Include details like insurance company name, plan names, states offered, deductibles, copays, out-of-pocket "
        "maximums, monthly premiums, and any other information relevant to someone shopping for health insurance, "
        "if found in the context. If you see unusually structured data, try to interpret it as a table, as this data "
        "is just text extracted from PDFs. Use tables when needed and limit the summary to 2400 words."
    )
