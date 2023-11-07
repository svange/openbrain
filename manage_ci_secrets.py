import requests
import base64
import logging
import json
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from github import Github, Auth

import click


DEFAULT_SECRET_NAME = "ob-api-secrets"

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.FileHandler('manage_secrets.log')

# Set the log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

@click.command()
@click.option('--interactive/--no-interactive', is_flag=True, help="Interactive mode.")
@click.option("--github", '-g', help="Create or update GitHub secrets.", is_flag=True)
# @click.option("--github-repo", '-r', help="GitHub repo to use.", default="ob-infra")
# @click.option("--github-org", '-o', help="GitHub org to use.", default="OpenBra-in")
@click.option("--aws", '-a', help="Create or update AWS secrets.", is_flag=True)
@click.option("--profile", '-p', help="AWS profile name to use.", type=click.STRING)
@click.option("--aws-secret-name", '-s', help="Name of the AWS Secret.", default=DEFAULT_SECRET_NAME, type=click.STRING)
@click.option("--verbose", '-v', help="Verbose output.", is_flag=True)
@click.argument("filename", type=click.Path(exists=True, readable=True), default='.env')
def cli(interactive: bool, github: bool, aws: bool, profile: str, aws_secret_name: str, verbose: bool, filename: click.Path):

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose output enabled.")

    if interactive:
        aws = input("Create or update AWS secrets? (Y/n): ")
        if not aws:  # default
            aws = True
        elif aws.lower() == "y":
            aws = True
        elif aws.lower() == "n":
            aws = False
        else:
            raise ValueError("Invalid input. Exiting.")

        github = input("Create or update GitHub secrets? (Y/n): ")
        if not github:  # default
            github = True
        elif github.lower() == "y":
            github = True
        elif github.lower() == "n":
            github = False
        else:
            raise ValueError("Invalid input. Exiting.")

        # List all of the files in the current directory that begin ith .env
        env_files = [file for file in os.listdir(".") if file.startswith(".env")]

        # If there are no .env files, exit
        if not env_files:
            logger.info("No .env files found in the current directory. Exiting.")
            sys.exit(1)

        env_file_options = enumerate(env_files, start=1)

        # Print a list of .env files in the current directory
        logger.info("Select a .env file:")
        for index, file in env_file_options:
            logger.info(f"{index}. {file}")

        # Prompt the user to select a .env file
        selection = input("Enter a number: ")
        try:
            selection = int(selection)
        except ValueError:
            logger.info("Invalid selection. Exiting.")
            sys.exit(1)

        # If the selection is out of range, exit
        if selection < 1 or selection > len(env_files):
            logger.info("Invalid selection. Exiting.")
            sys.exit(1)

        filename = env_files[selection - 1]
        logger.info(f"Using {filename} for secrets.")
        # perform_update(github=github, aws=aws, filename=filename)

    results = perform_update(aws, github, filename, profile, aws_secret_name)
    print(results)


def perform_update(aws, github, filename, profile=None, aws_secret_name=DEFAULT_SECRET_NAME):
    if not filename:
        raise ValueError("No filename specified. Exiting to avoid an accident.")

    load_dotenv(filename)
    github_repo = os.environ.get("GH_REPO", "ObInfra")
    github_org = os.environ.get("GH_ORG", None)
    github_user = os.environ.get("GH_USER", None)
    ob_infra_secret_store = os.environ.get("OB_INFRA_SECRET_STORE", aws_secret_name)

    github_token = os.environ.get("GH_TOKEN", None)
    aws_profile = os.environ.get("AWS_PROFILE", None)

    if not profile and not aws_profile:
        logger.info("No AWS profile specified, and no AWS_PROFILE environment variable set. Exiting to avoid an accident.")
    elif profile:
        logger.info(f"Using AWS profile {profile} from the command line")
        os.environ["AWS_PROFILE"] = profile
    else:
        logger.info(f"Using AWS profile {os.getenv('AWS_PROFILE')} from the environment")
        profile = os.getenv("AWS_PROFILE")

    if aws_secret_name:
        logger.info(f"WARNING: Search the templates for { DEFAULT_SECRET_NAME } and replace any findings with your secret name. Not templating this yet.")

    # Convert the filename to a pathlib.Path object
    file_path = Path(filename.__str__())
    # Read the .env file and convert it to a JSON object
    env_data = {}
    with file_path.open("r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";") or "=" not in line:
                continue
            key, value = line.strip().split("=", 1)
            # Skip AWS Variables as they'll only confuse the pipeline
            if key.startswith("AWS_PROFILE"):
                continue
            env_data[key] = os.getenv(key)
    env_json = json.dumps(env_data)

    results = []
    if github:
        result = create_or_update_github_secrets(github_repo=github_repo, github_org=github_org, github_user=github_user, env_data=env_data)
        results.append(result)
    if aws:
        result = create_or_update_aws_secrets(aws_secret_name, env_json)
        results.append(result)

    return results

def create_or_update_aws_secrets(secret_name, env_json):
    # Check if the secret already exists
    check_command = [
        "aws",
        "secretsmanager",
        "describe-secret",
        "--secret-id",
        secret_name,
    ]

    # Use subprocess.Popen to capture and print output streams in real-time
    process = subprocess.Popen(
        check_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,  # Ensure text mode for streams
    )

    # Capture and print stdout and stderr in real-time
    while True:
        stdout_line = process.stdout.readline()
        stderr_line = process.stderr.readline()
        if not stdout_line and not stderr_line:
            break

        # Print stdout and stderr lines
        if stdout_line:
            logger.info(stdout_line.strip())
        if stderr_line:
            logger.info(stderr_line.strip())

    # Wait for the process to complete and get the return code
    return_code = process.wait()

    try:
        # Secret exists, update it
        update_command = [
            "aws",
            "secretsmanager",
            "update-secret",
            "--secret-id",
            secret_name,
            "--secret-string",
            env_json,
        ]
        subprocess.run(update_command, check=True)
        logger.info(f"Updated secret '{secret_name}' successfully.")
    except subprocess.CalledProcessError:
        # Secret doesn't exist, create it
        create_command = [
            "aws",
            "secretsmanager",
            "create-secret",
            "--name",
            secret_name,
            "--secret-string",
            env_json,
        ]
        subprocess.run(create_command, check=True)

    # Get the ARN of the secret
    info_command = [
        "aws",
        "secretsmanager",
        "describe-secret",
        "--secret-id",
        secret_name,
    ]
    info_process = subprocess.run(
        info_command, check=True, stdout=subprocess.PIPE
    )
    info_json = json.loads(info_process.stdout)
    secret_arn = info_json["ARN"]

    logger.info(f"Secret ARN: {secret_arn}")
    #
    # # Get the current policy for the secret
    # policy_command = [
    #     "aws",
    #     "secretsmanager",
    #     "get-resource-policy",
    #     "--secret-id",
    #     secret_name,
    # ]


def create_or_update_github_secrets(github_org, github_repo, github_user, env_data):
    auth = Auth.Token(os.environ.get("GH_TOKEN", None))
    g = Github(auth=auth)
    if github_org:
        g_org = g.get_organization(github_org)
        repo = g_org.get_repo(github_repo)
    elif github_user:
        g_user = g.get_user(github_user)
        repo = g_user.get_repo(github_repo)
    else:
        raise ValueError("Must specify either GITHUB_ORG or GH_USER")
    secrets = [secret for secret in repo.get_secrets()]
    secret_names = [secret.name for secret in secrets]

    results = []
    for env_var_name, env_var_value in env_data.items():
        # Create or update secrets
        if env_var_name in secret_names:
            logger.info(f"Updating secret {env_var_name}...")
            results.append(repo.create_secret(env_var_name, env_var_value))

        else:
            logger.info(f"Creating secret {env_var_name}...")
            results.append(repo.create_secret(env_var_name, env_var_value))

    for secret_name in secret_names:
        if secret_name not in env_data.keys():
            logger.info(f"Deleting secret {secret_name}...")
            results.append(repo.delete_secret(secret_name))

    return results


if __name__ == "__main__":
    cli()
