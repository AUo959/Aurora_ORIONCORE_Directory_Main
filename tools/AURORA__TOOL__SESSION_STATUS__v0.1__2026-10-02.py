"""Read-only local status projection for the Claude Code Aurora mod."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404
from datetime import datetime, timezone
from pathlib import Path

from _workspace_common import load_yaml_like
from session_claim import list_claims, parse_time


def git_value(root: Path, *args: str) -> str | None:
    env = {k: v for k, v in os.environ.items() if k not in
           {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"}}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    executable = shutil.which("git")
    if executable is None:
        return None
    try:
        # No shell; callers supply fixed Git query verbs and a separate path argument.
        result = subprocess.run([executable, "-C", str(root), *args], env=env,  # noqa: S603  # nosec B603
                                capture_output=True, text=True, timeout=3, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def active_task(state: dict, warnings: list) -> dict:
    active = state.get("active_task") or {}
    if not isinstance(active, dict):
        active = {}
        warnings.append("Active task malformed")
    return active


def cloudbank_status(root: Path, entries: list, warnings: list) -> dict:
    cloudbank = next((r for r in entries if isinstance(r, dict) and
                      r.get("name") == "aurora-cloudbank-symbolic-main"), {})
    path = cloudbank.get("path")
    checkout = None
    if isinstance(path, str) and path != "~remote~":
        candidate = (root / path).resolve()
        if candidate != root and root in candidate.parents:
            # A plain directory inside the parent Git repo is not a nested checkout.
            top = git_value(candidate, "rev-parse", "--show-toplevel") if candidate.is_dir() else None
            if top and Path(top).resolve() == candidate:
                checkout = candidate
    observed = git_value(checkout, "rev-parse", "HEAD") if checkout else None
    pin = cloudbank.get("head_sha")
    pin_status = "unavailable"
    if observed is not None:
        pin_status = "match" if observed == pin else "drift"
    if pin_status != "match":
        warnings.append("CloudBank checkout missing or unreadable" if observed is None else "CloudBank pin drift")
    return {"pin": pin, "observed_head": observed, "status": pin_status}


def read_sources(root: Path, now: datetime, warnings: list) -> tuple:
    try:
        state = json.loads((root / "catalog/session_state.json").read_text())
        if not isinstance(state, dict) or state.get("schema_version") != 3:
            raise ValueError("unsupported state")
    except (OSError, ValueError):
        state = {}
        warnings.append("Session state unavailable or unsupported")
    updated = parse_time(str(state.get("last_updated") or ""))
    if updated is None or (now - updated).total_seconds() > 86400:
        warnings.append("Session record older than 24h or undated; refresh before relying on it")
    try:
        registry = load_yaml_like(root / "catalog/repo_registry.yaml")
        entries = registry["repos"]
        if not isinstance(entries, list):
            raise ValueError("invalid registry")
    except Exception:  # A corrupt YAML source is an unavailable status, never a stale success.
        entries = []
        warnings.append("Repository registry unavailable")
    return state, entries


def build_report(root: Path, now: datetime | None = None) -> dict:
    root = root.resolve()
    now = now or datetime.now(timezone.utc)
    warnings = []
    state, entries = read_sources(root, now, warnings)
    active = active_task(state, warnings)
    target = active.get("repo") or "root"
    cloudbank = cloudbank_status(root, entries, warnings)
    claims = list_claims(root, now)
    if claims["summary"]["invalid"]:
        warnings.append("Invalid local claim records")
    queue = state.get("task_queue", [])
    if not isinstance(queue, list):
        queue = []
        warnings.append("Task queue malformed")
    waits = [item for item in queue if isinstance(item, dict)
             and item.get("status") == "waiting" and item.get("repo") == target]
    return {
        "schema_version": 1, "mode": "read_only", "claim_scope": "local_only",
        "checked_at": now.isoformat(), "target_repo": target,
        "target_source": "active_task" if active.get("repo") else "root_default",
        "branch": git_value(root, "branch", "--show-current") or "detached_or_unavailable",
        "active_task": active.get("id") or "none_recorded",
        "next_action": active.get("next_step") or active.get("next_action") or "No active continuation recorded",
        "session_updated_at": state.get("last_updated"),
        "claims": claims["summary"],
        "cloudbank": cloudbank,
        "waiting_items": [item.get("id") for item in waits],
        "warnings": warnings,
        "authority": "Status is advisory; it grants no execution or publication permission",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build_report(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
