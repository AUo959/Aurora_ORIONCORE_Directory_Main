#!/usr/bin/env python3
"""session_state_check.py — Validate catalog/session_state.json.

Dependency-free enforcement of catalog/schemas/session_state.schema.json,
the contract for the shared Codex / Claude Code handoff surface. Catches
the drift classes seen in practice: completion reports parked in the
pending queue under a legacy `item` key, missing ids, out-of-vocabulary
status/priority/platform values, and duplicate ids across queues.

Usage:
    python3 tools/session_state_check.py            # validate, print findings
    python3 tools/session_state_check.py --quiet    # exit code only

Exit codes: 0 = valid, 1 = findings, 2 = file missing/unparseable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "catalog" / "session_state.json"

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "protocol",
    "active_task",
    "task_queue",
    "completed_tasks",
    "pending_for_next_session",
    "known_state",
    "last_updated",
    "last_platform",
]

PLATFORMS = {"codex", "claude-code"}
ASSIGNEES = {"codex", "claude-code", "either", "owner"}
ACTIVE_STATUSES = {"active", "suspended", "completed"}
QUEUE_STATUSES = {"queued", "active", "suspended", "completed"}
PRIORITIES = {"high", "medium", "low"}

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z$")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _check_item(
    item: object, where: str, required: list[str], findings: list[str]
) -> None:
    if not isinstance(item, dict):
        findings.append(f"{where}: entry is not an object")
        return
    if "item" in item and "id" not in item:
        findings.append(
            f"{where}: legacy 'item'-keyed entry — completion reports belong "
            "in completed_tasks; queue entries need an 'id'"
        )
        return
    for key in required:
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append(f"{where}: missing or empty '{key}'")
    assigned = item.get("assigned_to")
    if assigned is not None and assigned not in ASSIGNEES:
        findings.append(f"{where}: assigned_to '{assigned}' not in {sorted(ASSIGNEES)}")


def validate(state: object) -> list[str]:
    """Return a list of findings; empty means the document is valid."""
    findings: list[str] = []
    if not isinstance(state, dict):
        return ["document root is not an object"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in state:
            findings.append(f"missing top-level key '{key}'")

    ts = state.get("last_updated")
    if isinstance(ts, str) and not _TIMESTAMP_RE.match(ts):
        findings.append(f"last_updated '{ts}' is not ISO-8601 UTC (…Z)")

    platform = state.get("last_platform")
    if platform is not None and platform not in PLATFORMS:
        findings.append(f"last_platform '{platform}' not in {sorted(PLATFORMS)}")

    active = state.get("active_task")
    if isinstance(active, dict):
        _check_item(active, "active_task", ["id", "status", "description"], findings)
        status = active.get("status")
        if status is not None and status not in ACTIVE_STATUSES:
            findings.append(
                f"active_task: status '{status}' not in {sorted(ACTIVE_STATUSES)}"
            )
        if active.get("assigned_to") is None:
            findings.append("active_task: missing 'assigned_to'")
    elif active is not None:
        findings.append("active_task is not an object")

    seen_ids: dict[str, str] = {}
    for section, required in (
        ("task_queue", ["id", "status", "description"]),
        ("pending_for_next_session", ["id", "description"]),
    ):
        entries = state.get(section)
        if entries is None:
            continue
        if not isinstance(entries, list):
            findings.append(f"{section} is not a list")
            continue
        for i, item in enumerate(entries):
            where = f"{section}[{i}]"
            _check_item(item, where, required, findings)
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            if section == "task_queue" and status is not None and status not in QUEUE_STATUSES:
                findings.append(f"{where}: status '{status}' not in {sorted(QUEUE_STATUSES)}")
            priority = item.get("priority")
            if priority is not None and priority not in PRIORITIES:
                findings.append(f"{where}: priority '{priority}' not in {sorted(PRIORITIES)}")
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                if item_id in seen_ids:
                    findings.append(
                        f"{where}: duplicate id '{item_id}' (also in {seen_ids[item_id]})"
                    )
                else:
                    seen_ids[item_id] = where

    completed = state.get("completed_tasks")
    if isinstance(completed, list):
        for i, item in enumerate(completed):
            if not isinstance(item, dict):
                findings.append(f"completed_tasks[{i}]: entry is not an object")
            elif not (isinstance(item.get("id"), str) and item["id"].strip()):
                findings.append(f"completed_tasks[{i}]: missing or empty 'id'")
    elif completed is not None:
        findings.append("completed_tasks is not a list")

    known = state.get("known_state")
    if isinstance(known, dict):
        sha = known.get("main_sha")
        if not (isinstance(sha, str) and _SHA_RE.match(sha)):
            findings.append(f"known_state.main_sha '{sha}' is not a git sha")
    elif known is not None:
        findings.append("known_state is not an object")

    return findings


def check_file(path: Path = STATE_PATH) -> tuple[int, list[str]]:
    """Validate the file at *path*. Returns (exit_code, findings)."""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return 2, [f"{path}: not found"]
    except json.JSONDecodeError as exc:
        return 2, [f"{path}: invalid JSON — {exc}"]
    findings = validate(state)
    return (1 if findings else 0), findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=STATE_PATH, help="State file to validate")
    parser.add_argument("--quiet", action="store_true", help="Suppress output; exit code only")
    args = parser.parse_args()

    code, findings = check_file(args.path)
    if not args.quiet:
        if findings:
            print(f"session-state-check: {len(findings)} finding(s) in {args.path}")
            for f in findings:
                print(f"  - {f}")
        else:
            print(f"session-state-check: OK ({args.path})")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
