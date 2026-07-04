#!/usr/bin/env python3
"""session_state_io.py — the canonical write path for catalog/session_state.json.

Both platforms (Codex and Claude Code) edit the same shared state file.
Freeform read-modify-write caused two failure modes observed 2026-07-04:
serialization drift (\\u escapes vs literal Unicode → noisy diffs) and a
near-clobber when a concurrent session committed between one session's
read and write. This module fixes both:

- ONE serialization style: json indent=2, ensure_ascii=True (matches the
  json-module default, so even an accidental raw json.dump diverges
  minimally), trailing newline.
- Structured mutations that re-read the file at apply time (shrinking the
  read-to-write race window to milliseconds) and validate against the
  queue contract (tools/session_state_check.py) BEFORE writing. Invalid
  states are never written.

CLI:
    python3 tools/session_state_io.py fmt
    python3 tools/session_state_io.py get last_platform
    python3 tools/session_state_io.py complete-item <id> [--detail TEXT]
    python3 tools/session_state_io.py add-pending <id> --description TEXT
        [--priority high|medium|low] [--assigned-to codex|claude-code|either|owner]
    python3 tools/session_state_io.py set-summary TEXT
    python3 tools/session_state_io.py suspend-active --next-step TEXT
        [--next-step-detail TEXT]

Exit codes: 0 ok, 1 refused (validation findings or unknown id), 2 io error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "catalog" / "session_state.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import session_state_check  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_platform() -> str:
    """Best-effort platform detection; override with --platform."""
    if os.environ.get("CLAUDECODE"):
        return "claude-code"
    if os.environ.get("CODEX_HOME") or os.environ.get("CODEX_CLI_PATH"):
        return "codex"
    return "claude-code"


def load(path: Path = STATE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dumps_canonical(state: dict) -> str:
    return json.dumps(state, indent=2, ensure_ascii=True) + "\n"


def save(state: dict, path: Path = STATE_PATH, *, validate: bool = True) -> list[str]:
    """Validate then write canonically. Returns findings; writes only if none."""
    findings = session_state_check.validate(state) if validate else []
    if findings:
        return findings
    path.write_text(dumps_canonical(state), encoding="utf-8")
    return []


def _refuse(findings: list[str]) -> int:
    print(f"session-state-io: REFUSED — {len(findings)} contract finding(s):", file=sys.stderr)
    for f in findings:
        print(f"  - {f}", file=sys.stderr)
    return 1


# ── Mutations (each loads fresh at apply time) ─────────────────────────────

def op_fmt(_args: argparse.Namespace) -> int:
    state = load()
    findings = save(state)
    if findings:
        return _refuse(findings)
    print("session-state-io: reformatted canonically")
    return 0


def op_get(args: argparse.Namespace) -> int:
    value: object = load()
    for piece in args.keypath.split("."):
        if isinstance(value, list):
            value = value[int(piece)]
        else:
            value = value[piece]  # type: ignore[index]
    print(value if isinstance(value, str) else json.dumps(value, indent=2))
    return 0


def op_complete_item(args: argparse.Namespace) -> int:
    state = load()
    for section in ("pending_for_next_session", "task_queue"):
        entries = state.get(section, [])
        match = next((e for e in entries if e.get("id") == args.item_id), None)
        if match:
            entries.remove(match)
            break
    else:
        print(f"session-state-io: no queue item with id '{args.item_id}'", file=sys.stderr)
        return 1
    completed = {
        "id": args.item_id,
        "status": "completed",
        "completed_at": _now(),
        "platform": args.platform,
    }
    if args.detail:
        completed["detail"] = args.detail
    elif match.get("description"):
        completed["detail"] = match["description"]
    state.setdefault("completed_tasks", []).append(completed)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: completed '{args.item_id}' (from {section})")
    return 0


def op_add_pending(args: argparse.Namespace) -> int:
    state = load()
    item = {
        "id": args.item_id,
        "priority": args.priority,
        "assigned_to": args.assigned_to,
        "description": args.description,
    }
    state.setdefault("pending_for_next_session", []).append(item)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: queued '{args.item_id}' ({args.priority}, {args.assigned_to})")
    return 0


def op_set_summary(args: argparse.Namespace) -> int:
    state = load()
    state["last_session_summary"] = args.text
    state["last_platform"] = args.platform
    state["last_updated"] = _now()
    # Tells the stop hook not to overwrite this with commit subjects; the
    # hook clears the flag after honoring it once.
    state["_summary_set_manually"] = True
    findings = save(state)
    if findings:
        return _refuse(findings)
    print("session-state-io: summary set")
    return 0


def op_suspend_active(args: argparse.Namespace) -> int:
    state = load()
    active = state.get("active_task")
    if not isinstance(active, dict):
        print("session-state-io: no active_task object", file=sys.stderr)
        return 1
    active["status"] = "suspended"
    active["updated_at"] = _now()
    active["next_step"] = args.next_step
    if args.next_step_detail:
        active["next_step_detail"] = args.next_step_detail
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: active_task suspended (next_step: {args.next_step})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", default=detect_platform(),
                        choices=["codex", "claude-code"],
                        help="Writing platform (auto-detected by default)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fmt", help="Rewrite the file in canonical serialization")

    p = sub.add_parser("get", help="Print a value by dotted keypath")
    p.add_argument("keypath")

    p = sub.add_parser("complete-item", help="Move a queue/pending item to completed_tasks")
    p.add_argument("item_id")
    p.add_argument("--detail", help="Completion detail (defaults to the item's description)")

    p = sub.add_parser("add-pending", help="Append a well-formed pending item")
    p.add_argument("item_id")
    p.add_argument("--description", required=True)
    p.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    p.add_argument("--assigned-to", default="either",
                   choices=["codex", "claude-code", "either", "owner"])

    p = sub.add_parser("set-summary", help="Set last_session_summary (+platform/updated)")
    p.add_argument("text")

    p = sub.add_parser("suspend-active", help="Suspend active_task with a next step")
    p.add_argument("--next-step", required=True)
    p.add_argument("--next-step-detail")

    args = parser.parse_args()
    handlers = {
        "fmt": op_fmt,
        "get": op_get,
        "complete-item": op_complete_item,
        "add-pending": op_add_pending,
        "set-summary": op_set_summary,
        "suspend-active": op_suspend_active,
    }
    try:
        return handlers[args.command](args)
    except FileNotFoundError:
        print(f"session-state-io: {STATE_PATH} not found", file=sys.stderr)
        return 2
    except (KeyError, IndexError, ValueError) as exc:
        print(f"session-state-io: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
