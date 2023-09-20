import argparse
import json
import os
import subprocess
import logging
import sys
import openbrain

import boto3
import pytest
from dotenv import load_dotenv

import pprint

load_dotenv()
LOG_FILE = "ci_cd.log"

APP_NAME = os.getenv("PROJECT")
CENTRAL_INFRA_STACK_NAME = os.getenv("INFRA_STACK_NAME")
AWS_PROFILE = os.environ.get("AWS_PROFILE", "default")

logger = logging.getLogger("CICD Script")
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

BOTO_SESSION = boto3.Session()
# if BOTO_SESSION.region_name is None:
#     AWS_REGION = os.environ.get("AWS_REGION")
#     BOTO_SESSION = boto3.Session(region_name=AWS_REGION)
# else:
#     AWS_REGION = BOTO_SESSION.region_name

def run_command(command: list):
    process = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ,
                               shell=True)

    for c in iter(lambda: process.stdout.read(1), b""):
        sys.stdout.buffer.write(c)

    process.communicate()  # Wait for the process to complete and get stderr if any
    if process.returncode:
        logger.critical(f"Error: the following command failed: {command}")
        raise SystemExit("Deployment failed.")


def deploy_infra(dry_run: bool = False):
    """Deploy infrastructure stack"""

    commands = [
        ['sam', 'build'],
        ['sam', 'validate'],
        [
            'sam', 'deploy', '--no-confirm-changeset', '--parameter-overrides',
            f"GitHubOrg={os.environ.get('GITHUBORG', 'NONE_PROVIDED')}",
            f"RepositoryName={os.environ.get('REPOSITORYNAME', 'NONE_PROVIDED')}",
            f"DevOpenAIKey={os.environ.get('DEV_OPENAI_KEY', 'NONE_PROVIDED')}",
            f"DevPromptLayerKey={os.environ.get('DEV_PROMPTLAYER_KEY', 'NONE_PROVIDED')}",
            f"DevHuggingFaceKey={os.environ.get('DEV_HUGGINGFACE_KEY', 'NONE_PROVIDED')}",
            f"DevPineconeKey={os.environ.get('DEV_PINECONE_KEY', 'NONE_PROVIDED')}",
            f"DevWeviateKey={os.environ.get('DEV_WEVIATE_KEY', 'NONE_PROVIDED')}",
            f"DevMilvusKey={os.environ.get('DEV_MILVUS_KEY', 'NONE_PROVIDED')}",
            f"DevGoogleKey={os.environ.get('DEV_GOOGLE_KEY', 'NONE_PROVIDED')}",
            f"DevMetaKey={os.environ.get('DEV_META_KEY', 'NONE_PROVIDED')}",
            f"DevAnthropicKey={os.environ.get('DEV_ANTHROPIC_KEY', 'NONE_PROVIDED')}",
            f"ProdOpenAIKey={os.environ.get('PROD_OPENAI_KEY', 'NONE_PROVIDED')}",
            f"ProdPromptLayerKey={os.environ.get('PROD_PROMPTLAYER_KEY', 'NONE_PROVIDED')}",
            f"ProdHuggingFaceKey={os.environ.get('PROD_HUGGINGFACE_KEY', 'NONE_PROVIDED')}",
            f"ProdPineconeKey={os.environ.get('PROD_PINECONE_KEY', 'NONE_PROVIDED')}",
            f"ProdWeviateKey={os.environ.get('PROD_WEVIATE_KEY', 'NONE_PROVIDED')}",
            f"ProdMilvusKey={os.environ.get('PROD_MILVUS_KEY', 'NONE_PROVIDED')}",
            f"ProdGoogleKey={os.environ.get('PROD_GOOGLE_KEY', 'NONE_PROVIDED')}",
            f"ProdMetaKey={os.environ.get('PROD_META_KEY', 'NONE_PROVIDED')}",
            f"ProdAnthropicKey={os.environ.get('PROD_ANTHROPIC_KEY', 'NONE_PROVIDED')}"
        ]
    ]
    [command.append(f"--profile={AWS_PROFILE}") for command in commands]

    if dry_run:
        last_command = commands.pop()
        # We're removing the last command if this is a dry run, so fail if our assumption is broken.
        if "deploy" not in ' '.join(last_command):
            raise SystemExit("The word 'deploy' not found in the last command. Aborting! Assumption broke.")
        for command in commands:
            if "deploy" in ' '.join(command):
                raise SystemExit(
                    "The word 'deploy' found in a command before the last command. Aborting! Assumption broke.")

    for command in commands:
        logger.debug(f"Running {' '.join(command)}")
        run_command(command)


def build_python():
    """Use poetry to build the python package."""
    commands = [
        ['poetry', 'lock'],
        ['poetry', 'build'],
    ]

    for command in commands:
        logger.debug(f"Running {' '.join(command)}")
        run_command(command)


def publish_python(stage: str = "dev"):
    """Use poetry to publish the python package to pypi. If stage == dev, publish to pypi-test"""
    if stage == "dev":
        commands = [
            ['poetry', 'publish', '-r', 'test-pypi'],
        ]
    elif stage == "prod":
        commands = [
            ['poetry', 'publish'],
        ]
    else:
        raise SystemExit(f"Unknown {stage=}")

    for command in commands:
        logger.debug(f"Running: {' '.join(command)}")
        run_command(command)


def test_python():
    """Test the python package."""
    logger.info("Running deployment test.")
    # Add this directory to the PYTHONPATH for the call to pytest
    # sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # sys.path.append(os.path.dirname(os.path.abspath(__file__)) + f"/{APP_NAME}")
    rc = pytest.main(["-x", "tests"])
    if rc != 0:
        logger.critical("Error: tests failed.")
        raise SystemExit("Tests failed.")
    return rc


def get_central_infra_outputs() -> dict:
    """Get the outputs from the central infrastructure stack."""
    cloudformation = BOTO_SESSION.client("cloudformation")
    response = cloudformation.describe_stacks(StackName=CENTRAL_INFRA_STACK_NAME)
    values = {item["OutputKey"]: item["OutputValue"] for item in response["Stacks"][0]["Outputs"]}
    # sort dictionary by key
    values = dict(sorted(values.items()))
    return values


# def attach_common_policy(role_name: str, _policy_arn: str, dry_run: bool = True) -> None:
#     """Attach the common access policy to the role based on the stage. The role is created by chalice, the specific stage's policy ARN is retrieved from the central infrastructure stack."""
#     if dry_run:
#         logger.warning("Dry run enabled. Not attaching policy.")
#         return
#     logger.info(f"Attaching {_policy_arn} to {role_name}")
#     iam = boto3.client("iam")
#     iam.attach_role_policy(RoleName=role_name, PolicyArn=_policy_arn)


if __name__ == "__main__":
    stages = ['dev', 'prod']
    parser = argparse.ArgumentParser(
        description="Utility script for deployment of python packages and supporting infrastructure.")
    # Tuning
    parser.add_argument("--dry-run", "-d", action="store_true", help="Prevents any changes from being made.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logs debug messages.")
    parser.add_argument("--print-central-infra-outputs", '-p', action="store_true", help="Prints the central infrastructure outputs as they currently exist.")
    parser.add_argument("--stage", "-s", default="dev", choices=stages, help=f"If 'dev', publish to pypi-test, if 'prod', publish to pypi.")

    # Harmless
    parser.add_argument("--test-python", "-t", action="store_true", help="Run pytest tests")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest tests")
    parser.add_argument("--skip-build", action="store_true", help="Skip poetry build commands")

    # Dangerous
    parser.add_argument("--build-python", "-B", action="store_true", help="Run poetry build commands in an idempotent manner.")
    parser.add_argument("--publish-python", "-P", action="store_true", help="Publish python using poetry")
    parser.add_argument("--deploy-infra", "-I", action="store_true", help="Deploy the central infrastructure stack ")

    # Setup type hints and auto-complete
    args = parser.parse_args()
    args_skip_tests: bool = args.skip_tests
    arg_dry_run: bool = args.dry_run
    arg_verbose: bool = args.verbose
    args_stage: str = args.stage
    arg_print_central_infra_outputs: bool = args.print_central_infra_outputs
    arg_test_python: bool = args.test_python
    arg_build_python: bool = args.build_python
    arg_publish_python: bool = args.publish_python
    arg_deploy_infra: bool = args.deploy_infra

    # Setup logging
    if arg_verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if arg_publish_python:
        arg_build_python = True
    if arg_build_python:
        arg_test_python = True

    log_message = []
    log_message.append("Taking the following actions:")
    if arg_print_central_infra_outputs:
        log_message.append("  - Print central infrastructure outputs")
    if arg_test_python:
        log_message.append("  - Test python")
    if arg_build_python:
        log_message.append("  - Build python")
    if arg_publish_python:
        log_message.append("  - Publish python")
    if arg_deploy_infra:
        log_message.append("  - Deploy infrastructure")

    if args.skip_tests:
        arg_test_python = False
    if args.skip_build:
        arg_build_python = False
    if arg_verbose:
        print('\n'.join(log_message))

    central_infra_outputs = get_central_infra_outputs()
    if arg_print_central_infra_outputs:
        pprint.pprint(central_infra_outputs, indent=4)

    # Business logic starts here

    # INFRA
    if arg_deploy_infra:
        deploy_infra(dry_run=arg_dry_run)

    # PYTHON

    if arg_test_python:
        test_python()

    if arg_build_python:
        build_python()
        exit(0)

    if arg_publish_python:
        publish_python(stage=args_stage)
        exit(0)
