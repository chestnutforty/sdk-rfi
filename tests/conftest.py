"""Shared test configuration for sdk-rfi."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables: shared .env first, then local .env as override
_shared_env = Path(__file__).resolve().parents[2] / ".env"  # ../../.env (chestnutforty/.env)
_local_env = Path(__file__).resolve().parent.parent / ".env"  # sdk-rfi/.env

if _shared_env.exists():
    load_dotenv(_shared_env)
if _local_env.exists():
    load_dotenv(_local_env, override=True)

# Expand ~ in file paths (dotenv loads them literally)
for _var in ("GOOGLE_APPLICATION_CREDENTIALS",):
    _val = os.environ.get(_var, "")
    if _val and "~" in _val:
        os.environ[_var] = str(Path(_val).expanduser())
