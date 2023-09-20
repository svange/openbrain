# import argparse
# import os
# import pathlib
# import subprocess
# import logging
# import sys
#
# import boto3
# import pytest
# from dotenv import load_dotenv
#
# import pprint
#
# load_dotenv()
# LOG_FILE = "ci_cd.log"
#
# central_infra_stack_name = os.getenv("INFRA_STACK_NAME")
# app_name = os.getenv("APP_NAME")
# dev_api_url = os.getenv("DEV_API_URL")
# prod_api_url = os.getenv("PROD_API_URL")
#
# dev_iam_role_name = f"{app_name}-dev"
# prod_iam_role_name = f"{app_name}-prod"
#
# dev_common_access_policy_friendly_name = "DevCommonAccessPolicy"
# prod_common_access_policy_friendly_name = "ProdCommonAccessPolicy"
#
# logger = logging.getLogger("CICD Script")
# logging.basicConfig()
#
# # Add this directory to the PYTHONPATH for the call to pytest
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/chalicelib")
#
#
# def live_logs(stage: str = "dev", _filter=None) -> None:
#     command = ["chalice", "logs", "--stage", stage, "--follow"]
#     with subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
#         for line in p.stdout:
#             with open(LOG_FILE, mode="a", encoding="utf-8") as f:
#                 f.write(line.decode("utf-8"))
#
#             if not _filter:
#                 print(line.decode("utf-8"))
#             elif _filter and _filter in str(line):
#                 print(line.decode("utf-8"))
#
#         if p.returncode:
#             logger.critical("Wut.")
#             raise SystemExit("Deployment failed.")
#
#
# def get_central_infra_outputs() -> dict:
#     cloudformation = boto3.client("cloudformation")
#     response = cloudformation.describe_stacks(StackName=central_infra_stack_name)
#     values = {item["OutputKey"]: item["OutputValue"] for item in response["Stacks"][0]["Outputs"]}
#     # sort dictionary by key
#     values = dict(sorted(values.items()))
#     return values
#
#
# def attach_common_policy(role_name: str, _policy_arn: str, dry_run: bool = True) -> None:
#     """Attach the common access policy to the role based on the stage. The role is created by chalice, the specific stage's policy ARN is retrieved from the central infrastructure stack."""
#     if dry_run:
#         logger.warning("Dry run enabled. Not attaching policy.")
#         return
#     logger.info(f"Attaching {_policy_arn} to {role_name}")
#     iam = boto3.client("iam")
#     iam.attach_role_policy(RoleName=role_name, PolicyArn=_policy_arn)
#
#
# def deploy(stage: str = "dev", dry_run: bool = True) -> None:
#     if dry_run:
#         logger.warning("Dry run enabled. Not deploying.")
#         return
#     logger.info(f"Deploying {app_name} to {stage}")
#     command = ["pipenv", "requirements"]
#
#     # with subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
#     #     requirements = []
#     #     for line in p.stdout:
#     #         print(line.decode("utf-8"))
#     #         requirements.append(line.decode("utf-8"))
#     #
#     #     if p.returncode:
#     #         logger.critical("Error: deploy failed.")
#     #         raise SystemExit("Deployment failed.")
#     #
#     #     # delete the old requirements.txt if it exists
#     #     if os.path.exists("requirements.txt"):
#     #         logger.info("Removing old requirements.txt")
#     #         os.remove("requirements.txt")
#     #
#     #     with open("requirements.txt", "w") as f:
#     #         logger.info("Writing new requirements.txt")
#     #         clean_requirements = [line.replace("\n", "") for line in requirements]
#     #         f.write("".join(clean_requirements))
#
#     reqs = subprocess.run(["pipenv", "requirements"], capture_output=True, text=True)
#     with open("requirements.txt", "w") as f:
#         logger.info("Writing new requirements.txt")
#         f.write(reqs.stdout)
#
#     command = ["chalice", "deploy", "--stage", stage]
#
#     with subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
#         for line in p.stdout:
#             print(line.decode("utf-8"))
#
#         if p.returncode:
#             logger.critical("Error: deploy failed.")
#             raise SystemExit("Deployment failed.")
#
#         logger.info(p.stdout)
#         logger.info("Deployment complete!")
#
#
# def deployment_test() -> int:
#     logger.info("Running deployment test.")
#     # Add this directory to the PYTHONPATH for the call to pytest
#     sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#     sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/chalicelib")
#
#     if args.skip_tests:
#         logger.info("Skipping tests.")
#         return 0
#     retcode = pytest.main(["-x", "tests"])
#     return retcode
#
#
# def remote_tests(remote_stage: str = "dev") -> int:
#     logger.info(f"Running remote test against {remote_stage}.")
#
#     if remote_stage not in ["dev", "prod"]:
#         raise NotImplementedError("Only stages dev and prod are supported.")
#
#     retcode = pytest.main(["-m", "remote_tests"])
#     return retcode
#     pass
#
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Utility script for deployment.")
#     parser.add_argument(
#         "--stage",
#         type=str,
#         default="dev",
#         help="Stage to deploy to.",
#         choices=["dev", "prod"],
#     )
#     parser.add_argument("--dry-run", "-d", action="store_true")
#     parser.add_argument("--verbose", "-v", action="store_true")
#     parser.add_argument("--live-logs", action="store_true")
#     parser.add_argument("--filter", type=str, default=None)
#
#     parser.add_argument("--central-infra-outputs", action="store_true")
#     parser.add_argument("--attach-common-policy", action="store_true")
#     parser.add_argument("--deploy", action="store_true")
#     # Testing
#     parser.add_argument("--deployment-test", action="store_true")
#     parser.add_argument("--remote-tests-prod", action="store_true")
#     parser.add_argument("--remote-tests-dev", action="store_true")
#     parser.add_argument("--remote-tests", action="store_true")
#     parser.add_argument("--disconnected-test", action="store_true")
#     parser.add_argument("--skip-tests", action="store_true")
#
#     args = parser.parse_args()
#
#     if args.verbose:
#         logger.setLevel(logging.INFO)
#         logger.info("Verbose logging enabled.")
#     else:
#         logger.setLevel(logging.WARNING)
#
#     central_infra_outputs = get_central_infra_outputs()
#
#     if args.stage == "dev":
#         role = dev_iam_role_name
#         policy_arn = central_infra_outputs[dev_common_access_policy_friendly_name]
#     elif args.stage == "prod":
#         role = prod_iam_role_name
#         policy_arn = central_infra_outputs[prod_common_access_policy_friendly_name]
#     else:
#         raise Exception("Invalid stage")
#
#     if args.live_logs:
#         logger.info("Running live logs.")
#         live_logs(stage=args.stage, _filter=args.filter)
#
#     if args.central_infra_outputs:
#         pprint.pprint(central_infra_outputs, indent=4)
#
#     if args.remote_tests_dev or args.remote_tests:
#         logger.info("Running remote tests against dev.")
#         remote_tests("dev")
#
#     if args.remote_tests_prod or args.remote_tests:
#         logger.info("Running remote tests against prod.")
#         remote_tests("prod")
#
#     if args.deployment_test:
#         logger.info("Running deployment test.")
#         return_code = deployment_test()
#         exit(return_code)
#
#     if args.deploy:
#         logger.info(f"Running deployment tests for {app_name}")
#         return_code = deployment_test()
#         if return_code != 0:
#             logger.error(f"Deployment test failed for {app_name}")
#             exit(return_code)
#
#         logger.info(f"Deploying {app_name} to {args.stage}")
#
#         deploy(stage=args.stage, dry_run=args.dry_run)
#         logger.info(f"Deployed {app_name} to {args.stage}")
#         args.attach_common_policy = True
#
#     if args.attach_common_policy:
#         attach_common_policy(role, policy_arn, dry_run=args.dry_run)
#         logger.info(f"Attached {policy_arn} to {role}")
