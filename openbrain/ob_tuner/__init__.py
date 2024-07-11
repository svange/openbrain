import os
from dotenv import load_dotenv
load_dotenv()
os.environ["INFRA_STACK_NAME"] = os.environ.get("GRADIO_INFRA_STACK_NAME", "LOCAL")
