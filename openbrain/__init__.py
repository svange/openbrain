__version__ = "0.20.0"

import os
from pathlib import Path

cwd = Path(os.getcwd()) or '.'

env_file_path = cwd / ".env"

if not os.path.exists(".env") and os.environ.get("MODE") is None:
    os.environ[env_file_path] = "LOCAL"

    print(f"Did not find .env file or env vars, setting MODE=LOCAL in env var.")
