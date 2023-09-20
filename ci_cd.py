import argparse
import json
import os
import subprocess
import logging
import sys
import openbrain

import boto3
import toml
import pytest
from dotenv import load_dotenv

import pprint

load_dotenv()
LOG_FILE = "ci_cd.log"

APP_NAME = os.getenv("PROJECT")
CENTRAL_INFRA_STACK_NAME = os.getenv("INFRA_STACK_NAME")
AWS_PROFILE = os.environ.get("AWS_PROFILE", "default")

logger = logging.getLogger("CICD Script")
logging.basicConfig()

# Add this directory to the PYTHONPATH for the call to pytest
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/openbrain")


def run_command(command: str):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ, shell=True)

    for c in iter(lambda: process.stdout.read(1), b""):
        sys.stdout.buffer.write(c)

    process.communicate()  # Wait for the process to complete and get stderr if any
    if process.returncode:
        logger.critical(f"Error: the following command failed: {command}")
        raise SystemExit("Deployment failed.")


def deploy_infra():
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

    if args.dry_run:
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


def package_python():
    raise NotImplementedError("package_python not implemented yet.")


def distribute_python():
    raise NotImplementedError("distribute_python not implemented yet.")


def format_dependency_string(name: str, details: dict) -> str:
    version = details.get("version", "")
    extras = f"[{','.join(details.get('extras', []))}]" if details.get("extras") else ""
    markers = f"; {details['markers']}" if details.get("markers") else ""
    return f"{name}{extras} = \"{version}\"{markers}"


def update_pyproject_from_pipfile():
    """Update pyproject.toml dependencies from Pipfile.lock"""

    command = ["pipenv", "lock"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        output = process.stdout.readline()

        if output:
            print(output.strip().decode("utf-8"))

        return_code = process.poll()

        if return_code is not None:
            if return_code != 0:
                raise SystemExit(f"Error running {command=}, returned {return_code=}")
            break

    logger.info("Requirements management completed successfully!")

    with open('Pipfile.lock', 'r') as f:
        pipfile_lock_data = json.load(f)

    # Extract dependencies and dev-dependencies
    default_dependencies = pipfile_lock_data.get('default', {})
    dev_dependencies = pipfile_lock_data.get('develop', {})

    # Read pyproject.toml
    pyproject_data = toml.load('pyproject.toml')

    # Transform dependencies to TOML format
    pyproject_data['dependencies'] = {k: format_dependency_string(k, v) for k, v in default_dependencies.items()}
    pyproject_data['dev-dependencies'] = {k: format_dependency_string(k, v) for k, v in dev_dependencies.items()}

    # Write back to pyproject.toml
    with open('pyproject.toml', 'w') as f:
        toml.dump(pyproject_data, f)

    print("pyproject.toml updated successfully.")


def get_central_infra_outputs() -> dict:
    cloudformation = boto3.client("cloudformation")
    response = cloudformation.describe_stacks(StackName=CENTRAL_INFRA_STACK_NAME)
    values = {item["OutputKey"]: item["OutputValue"] for item in response["Stacks"][0]["Outputs"]}
    # sort dictionary by key
    values = dict(sorted(values.items()))
    return values


def attach_common_policy(role_name: str, _policy_arn: str, dry_run: bool = True) -> None:
    """Attach the common access policy to the role based on the stage. The role is created by chalice, the specific stage's policy ARN is retrieved from the central infrastructure stack."""
    if dry_run:
        logger.warning("Dry run enabled. Not attaching policy.")
        return
    logger.info(f"Attaching {_policy_arn} to {role_name}")
    iam = boto3.client("iam")
    iam.attach_role_policy(RoleName=role_name, PolicyArn=_policy_arn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utility script for deployment of python packages and supporting infrastructure.")
    parser.add_argument("--dry-run", "-d", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--print-central-infra-outputs", '-p', action="store_true")

    parser.add_argument("--test-python", "-T", action="store_true")
    parser.add_argument("--update-python-reqs", "-R", action="store_true")
    parser.add_argument("--package-python", "-P", action="store_true")
    parser.add_argument("--distribute-python", "-D", action="store_true")

    parser.add_argument("--deploy-infra", "-I", action="store_true")

    # SETUP
    args = parser.parse_args()
    if args.distribute_python:
        args.package_python = True
    if args.package_python:
        args.test_python = True
    if args.test_python:
        args.update_python_reqs = True

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    central_infra_outputs = get_central_infra_outputs()
    if args.print_central_infra_outputs:
        pprint.pprint(central_infra_outputs, indent=4)

    # Business logic starts here

    # INFRA
    if args.deploy_infra:
        deploy_infra()
        exit(0)

    # PYTHON
    if args.update_python_reqs:
        update_pyproject_from_pipfile()
        exit(0)

    if args.package_python:
        package_python()
        exit(0)

    if args.distribute_python:
        distribute_python()
        exit(0)
