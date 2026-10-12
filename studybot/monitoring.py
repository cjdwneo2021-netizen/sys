"""Persist public operational counters without credentials or error messages."""
from datetime import datetime, timezone
import os

from .storage import read_json, write_json


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def settings(config):
    return {"provider": config.provider, "model": config.model,
            "max_calls": config.max_calls, "daily_calls": config.daily_calls,
            "deadline_seconds": config.deadline_seconds, "idle_seconds": config.idle_seconds}


def record_operation(config, operation, status, count=None):
    path = config.root / "state/operations.json"
    value = read_json(path, {})
    entry = {"at": utc_now(), "status": status, "count": count, "settings": settings(config)}
    repository, run_id = os.getenv("GITHUB_REPOSITORY", ""), os.getenv("GITHUB_RUN_ID", "")
    if repository and run_id:
        entry["run_url"] = f"https://github.com/{repository}/actions/runs/{run_id}"
    value[operation] = entry
    write_json(path, value)
