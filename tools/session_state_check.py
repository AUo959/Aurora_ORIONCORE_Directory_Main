#!/usr/bin/env python3
"""Validate the shared Aurora session-state and queue contract.

This is the dependency-free mirror of
``catalog/schemas/session_state.schema.json``. It validates structure and
cross-field lifecycle rules; wall-clock aging belongs to
``session_queue_health.py``.
"""

from __future__ import annotations

import argparse
import json
import re
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
ACTIVE_STATUSES = {"active", "suspended"}
QUEUE_STATUSES = {"ready", "waiting", "parked"}
PRIORITIES = {"high", "medium", "low"}
KINDS = {"work", "decision", "watch"}
WAITING_ON = {"owner", "external", "artifact", "date"}

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z$")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _check_timestamp(value: object, where: str, findings: list[str]) -> None:
    if not isinstance(value, str) or not _TIMESTAMP_RE.match(value):
        findings.append(f"{where}: '{value}' is not ISO-8601 UTC (...Z)")


def _check_nonempty(item: dict, where: str, keys: list[str], findings: list[str]) -> None:
    for key in keys:
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append(f"{where}: missing or empty '{key}'")


def _check_lifecycle_fields(item: dict, where: str, findings: list[str]) -> None:
    _check_nonempty(
        item,
        where,
        [
            "id",
            "status",
            "assigned_to",
            "priority",
            "kind",
            "repo",
            "description",
            "created_at",
            "updated_at",
            "next_action",
            "definition_of_done",
        ],
        findings,
    )
    if item.get("assigned_to") not in ASSIGNEES:
        findings.append(
            f"{where}: assigned_to '{item.get('assigned_to')}' not in {sorted(ASSIGNEES)}"
        )
    if item.get("priority") not in PRIORITIES:
        findings.append(
            f"{where}: priority '{item.get('priority')}' not in {sorted(PRIORITIES)}"
        )
    if item.get("kind") not in KINDS:
        findings.append(f"{where}: kind '{item.get('kind')}' not in {sorted(KINDS)}")
    _check_timestamp(item.get("created_at"), f"{where}.created_at", findings)
    _check_timestamp(item.get("updated_at"), f"{where}.updated_at", findings)
    if "reopened_at" in item or "reopen_reason" in item:
        _check_timestamp(item.get("reopened_at"), f"{where}.reopened_at", findings)
        if not isinstance(item.get("reopen_reason"), str) or not item[
            "reopen_reason"
        ].strip():
            findings.append(
                f"{where}: reopened items require a non-empty reopen_reason"
            )
    if "gate_reclassified_at" in item or "gate_reclassification_reason" in item:
        _check_timestamp(
            item.get("gate_reclassified_at"),
            f"{where}.gate_reclassified_at",
            findings,
        )
        reason = item.get("gate_reclassification_reason")
        if not isinstance(reason, str) or not reason.strip():
            findings.append(
                f"{where}: gate reclassification requires a non-empty reason"
            )
    if not isinstance(item.get("approval_required"), bool):
        findings.append(f"{where}: approval_required must be boolean")


def validate(state: object) -> list[str]:
    """Return contract findings; an empty list means the document is valid."""
    findings: list[str] = []
    if not isinstance(state, dict):
        return ["document root is not an object"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in state:
            findings.append(f"missing top-level key '{key}'")

    schema_version = state.get("schema_version")
    if schema_version not in {3, "3", "3.0"}:
        findings.append(
            f"schema_version '{schema_version}' is not lifecycle schema version 3"
        )

    _check_timestamp(state.get("last_updated"), "last_updated", findings)
    platform = state.get("last_platform")
    if platform not in PLATFORMS:
        findings.append(f"last_platform '{platform}' not in {sorted(PLATFORMS)}")

    seen_ids: dict[str, str] = {}
    open_items: dict[str, dict] = {}
    active = state.get("active_task")
    if isinstance(active, dict):
        _check_lifecycle_fields(active, "active_task", findings)
        status = active.get("status")
        if status not in ACTIVE_STATUSES:
            findings.append(
                f"active_task: status '{status}' not in {sorted(ACTIVE_STATUSES)}"
            )
        if active.get("approval_required") is not False:
            findings.append(
                "active_task: approval_required must be false; concrete owner decisions belong in waiting task_queue items"
            )
        if status == "suspended":
            _check_timestamp(active.get("resume_by"), "active_task.resume_by", findings)
        if "waiting_on" in active or "gate_scope" in active:
            findings.append(
                "active_task: waiting/gate fields are not allowed; move it to task_queue status='waiting'"
            )
        if isinstance(active.get("id"), str) and active["id"]:
            seen_ids[active["id"]] = "active_task"
            open_items[active["id"]] = active
    elif active is not None:
        findings.append("active_task must be an object or null")

    queue = state.get("task_queue")
    if not isinstance(queue, list):
        findings.append("task_queue is not a list")
    else:
        for index, item in enumerate(queue):
            where = f"task_queue[{index}]"
            if not isinstance(item, dict):
                findings.append(f"{where}: entry is not an object")
                continue
            _check_lifecycle_fields(item, where, findings)
            status = item.get("status")
            if status not in QUEUE_STATUSES:
                findings.append(f"{where}: status '{status}' not in {sorted(QUEUE_STATUSES)}")
            _check_timestamp(item.get("review_at"), f"{where}.review_at", findings)
            if status == "waiting":
                if item.get("waiting_on") not in WAITING_ON:
                    findings.append(
                        f"{where}: waiting_on '{item.get('waiting_on')}' not in {sorted(WAITING_ON)}"
                    )
                if not isinstance(item.get("trigger"), str) or not item["trigger"].strip():
                    findings.append(f"{where}: waiting items require a concrete trigger")
            if status == "parked" and (
                not isinstance(item.get("trigger"), str) or not item["trigger"].strip()
            ):
                findings.append(f"{where}: parked items require a review reason/trigger")
            if item.get("approval_required") is True:
                if not (
                    item.get("kind") == "decision"
                    and status == "waiting"
                    and item.get("waiting_on") == "owner"
                    and item.get("assigned_to") == "owner"
                ):
                    findings.append(
                        f"{where}: owner gates require kind='decision', status='waiting', "
                        "waiting_on='owner', assigned_to='owner'"
                    )
                if not isinstance(item.get("gate_scope"), str) or not item["gate_scope"].strip():
                    findings.append(f"{where}: owner gates require gate_scope")
                evidence = item.get("evidence_refs")
                if not isinstance(evidence, list) or not evidence:
                    findings.append(f"{where}: owner gates require at least one evidence_ref")
                options = item.get("decision_options")
                if not isinstance(options, list) or len(options) < 2:
                    findings.append(f"{where}: owner gates require at least two decision_options")
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                if item_id in seen_ids:
                    findings.append(
                        f"{where}: duplicate id '{item_id}' (also in {seen_ids[item_id]})"
                    )
                else:
                    seen_ids[item_id] = where
                    open_items[item_id] = item

    pending = state.get("pending_for_next_session")
    if not isinstance(pending, list):
        findings.append("pending_for_next_session is not a list")
    elif pending:
        findings.append(
            "pending_for_next_session is deprecated and must be empty; migrate entries into task_queue"
        )

    completed = state.get("completed_tasks")
    completed_ids: set[str] = set()
    if isinstance(completed, list):
        for index, item in enumerate(completed):
            where = f"completed_tasks[{index}]"
            if not isinstance(item, dict):
                findings.append(f"{where}: entry is not an object")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id.strip():
                findings.append(f"{where}: missing or empty 'id'")
                continue
            if item_id in completed_ids:
                findings.append(f"{where}: duplicate completed id '{item_id}'")
            completed_ids.add(item_id)
            if item_id in seen_ids:
                open_item = open_items[item_id]
                reopened_at = open_item.get("reopened_at")
                reopen_reason = open_item.get("reopen_reason")
                if not (
                    isinstance(reopened_at, str)
                    and _TIMESTAMP_RE.match(reopened_at)
                    and isinstance(reopen_reason, str)
                    and reopen_reason.strip()
                ):
                    findings.append(
                        f"{where}: duplicate open/completed id '{item_id}' (also in {seen_ids[item_id]}); "
                        "an intentionally reopened item requires reopened_at and reopen_reason"
                    )
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
    parser.add_argument("--path", type=Path, default=STATE_PATH)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    code, findings = check_file(args.path)
    if not args.quiet:
        if findings:
            print(f"session-state-check: {len(findings)} finding(s) in {args.path}")
            for item in findings:
                print(f"  - {item}")
        else:
            print(f"session-state-check: OK ({args.path})")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
