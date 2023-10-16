__version__ = "0.18.1"

import os

if not os.path.exists(".env"):
    os.environ["MODE"] = "LOCAL"

    print(f"Did not find .env file or env vars, setting MODE=LOCAL in env var.")
