"""Read local connection settings and open PostgreSQL connections."""

import getpass
import json
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
_password = None


def get_connection():
    """Return a new connection; its context manager commits or rolls back.

    Passwords are requested once per process and never written to disk.
    PGPASSWORD may instead supply a password for local automated runs.
    """
    global _password
    path = ROOT / "config.json"
    if not path.exists():
        raise ValueError("Copy config.example.json to config.json first. See README.md.")
    try:
        settings = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Cannot read config.json. Check the file and JSON syntax.") from error
    if not isinstance(settings, dict):
        raise ValueError("config.json must contain a JSON object.")
    allowed = {"host", "port", "dbname", "user"}
    if set(settings) != allowed:
        raise ValueError("config.json needs exactly host, port, dbname, and user.")
    for field in ("host", "dbname", "user"):
        if not isinstance(settings[field], str) or not settings[field].strip():
            raise ValueError(f"config.json: {field} must be nonempty text.")
    port = settings["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("config.json: port must be an integer from 1 to 65535.")
    if _password is None:
        _password = os.environ.get("PGPASSWORD")
        if _password is None:
            _password = getpass.getpass("PostgreSQL password (typing is hidden): ")
    return psycopg.connect(
        **settings,
        password=_password,
        connect_timeout=5,
        options="-c search_path=public",
    )
