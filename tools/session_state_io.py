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
    python3 tools/session_state_io.py set-tool-version <tool> <version>
    python3 tools/session_state_io.py suspend-active --next-step TEXT
        [--next-step-detail TEXT]
    python3 tools/session_state_io.py record-commits   # mechanical: recent_commits + main_sha from git log
    python3 tools/session_state_io.py archive-completed [--keep N]

Long handoff narratives (next_step_detail > 600 chars) are spilled to a
per-session file under catalog/handoffs/ with a pointer left in the state —
keeps the shared file small and contention low.

Mutations refuse to run (exit 3) while the OTHER platform holds an active
mutating session claim overlapping catalog/session_state.json; override
with --force when you know the claim is abandoned.

Exit codes: 0 ok, 1 refused (validation findings or unknown id),
2 io error, 3 blocked by another platform's active claim.
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
HANDOFF_DIR = REPO_ROOT / "catalog" / "handoffs"
ARCHIVE_PATH = REPO_ROOT / "catalog" / "session_state_archive.json"
SPILL_THRESHOLD = 600  # chars of next_step_detail kept inline
ARCHIVE_KEEP_DEFAULT = 10

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


def blocking_claims(platform: str, root: Path = REPO_ROOT) -> list[dict]:
    """Active mutating claims by the OTHER platform overlapping the state file."""
    try:
        import session_claim
        from datetime import datetime, timezone as _tz

        now = datetime.now(_tz.utc).replace(microsecond=0)
        state_rel = "catalog/session_state.json"
        blockers = []
        for record in session_claim.load_claim_records(root):
            claim = record.get("claim", record)
            if not session_claim.is_active_claim(claim, now):
                continue
            if claim.get("platform") == platform:
                continue
            if not session_claim.posture_is_mutating(str(claim.get("posture", "mutating"))):
                continue
            paths = claim.get("paths") or ["."]
            if any(session_claim.path_overlaps(p, state_rel) for p in paths):
                blockers.append(claim)
        return blockers
    except Exception:
        return []  # claim system unavailable — never block on infrastructure


def _spill_handoff(detail: str, platform: str, next_step: str) -> str:
    """Write a long narrative to catalog/handoffs/ and return the inline pointer."""
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    step_slug = "".join(c if c.isalnum() or c == "-" else "-" for c in next_step.lower())[:48].strip("-")
    name = f"{ts}-{platform}-{step_slug or 'handoff'}.md"
    path = HANDOFF_DIR / name
    path.write_text(
        f"# Session handoff — {platform} — {ts}\n\n"
        f"Next step: {next_step}\n\n{detail}\n",
        encoding="utf-8",
    )
    first_line = detail.strip().splitlines()[0][:200]
    return f"{first_line} [full handoff: catalog/handoffs/{name}]"


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


def op_set_tool_version(args: argparse.Namespace) -> int:
    state = load()
    versions = state.setdefault("tool_versions", {})
    if not isinstance(versions, dict):
        print("session-state-io: tool_versions must be an object", file=sys.stderr)
        return 1
    versions[args.tool] = args.version
    state["last_platform"] = args.platform
    state["last_updated"] = _now()
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: tool_versions.{args.tool} set")
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
        detail = args.next_step_detail
        if len(detail) > SPILL_THRESHOLD:
            detail = _spill_handoff(detail, args.platform, args.next_step)
        active["next_step_detail"] = detail
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: active_task suspended (next_step: {args.next_step})")
    return 0


def op_record_commits(args: argparse.Namespace) -> int:
    """Mechanically refresh recent_commits + known_state.main_sha from git."""
    import subprocess

    def _git(*cmd: str) -> str:
        return subprocess.run(["git", *cmd], capture_output=True, text=True,
                              cwd=REPO_ROOT).stdout.strip()

    state = load()
    head = _git("rev-parse", "HEAD")
    known = state.get("known_state", {}).get("main_sha", "")
    # A recorded sha can vanish from local history (e.g. after a rebase);
    # fall back to the last 10 commits rather than silently recording none.
    if known and not _git("rev-parse", "--verify", "--quiet", f"{known}^{{commit}}"):
        known = ""
    raw = _git("log", "--oneline", f"{known}..HEAD") if known else _git("log", "--oneline", "-10")
    existing = state.get("recent_commits", [])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    added = 0
    for line in reversed([l for l in raw.splitlines() if l.strip()]):
        sha, _, summary = line.partition(" ")
        if not any(e.get("sha") == sha for e in existing):
            existing.insert(0, {"sha": sha, "date": today,
                                "platform": args.platform, "summary": summary})
            added += 1
    state["recent_commits"] = existing[:10]
    state.setdefault("known_state", {})["main_sha"] = head
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: recorded {added} commit(s); main_sha={head[:9]}")
    return 0


def op_archive_completed(args: argparse.Namespace) -> int:
    """Move all but the newest --keep completed_tasks to the archive file."""
    state = load()
    completed = state.get("completed_tasks", [])
    if len(completed) <= args.keep:
        print(f"session-state-io: {len(completed)} completed task(s) — nothing to archive")
        return 0
    to_archive, remain = completed[:-args.keep], completed[-args.keep:]
    archive = {"schema_version": 1, "completed_tasks": []}
    if ARCHIVE_PATH.exists():
        archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    known_ids = {t.get("id") for t in archive["completed_tasks"]}
    archive["completed_tasks"].extend(t for t in to_archive if t.get("id") not in known_ids)
    ARCHIVE_PATH.write_text(json.dumps(archive, indent=2, ensure_ascii=True) + "\n",
                            encoding="utf-8")
    state["completed_tasks"] = remain
    findings = save(state)
    if findings:
        return _refuse(findings)
    try:
        archive_label = str(ARCHIVE_PATH.relative_to(REPO_ROOT))
    except ValueError:
        archive_label = str(ARCHIVE_PATH)
    print(f"session-state-io: archived {len(to_archive)} task(s) to "
          f"{archive_label}; {len(remain)} kept inline")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", default=detect_platform(),
                        choices=["codex", "claude-code"],
                        help="Writing platform (auto-detected by default)")
    parser.add_argument("--force", action="store_true",
                        help="Write even if the other platform holds an active claim")
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

    p = sub.add_parser("set-tool-version", help="Set a tool_versions entry (+platform/updated)")
    p.add_argument("tool")
    p.add_argument("version")

    p = sub.add_parser("suspend-active", help="Suspend active_task with a next step")
    p.add_argument("--next-step", required=True)
    p.add_argument("--next-step-detail")

    sub.add_parser("record-commits",
                   help="Refresh recent_commits + known_state.main_sha from git log")

    p = sub.add_parser("archive-completed",
                       help="Move older completed_tasks to catalog/session_state_archive.json")
    p.add_argument("--keep", type=int, default=ARCHIVE_KEEP_DEFAULT)

    args = parser.parse_args()
    handlers = {
        "fmt": op_fmt,
        "get": op_get,
        "complete-item": op_complete_item,
        "add-pending": op_add_pending,
        "set-summary": op_set_summary,
        "set-tool-version": op_set_tool_version,
        "suspend-active": op_suspend_active,
        "record-commits": op_record_commits,
        "archive-completed": op_archive_completed,
    }
    if args.command != "get" and not args.force:
        blockers = blocking_claims(args.platform)
        if blockers:
            claim = blockers[0]
            print("session-state-io: BLOCKED — active mutating claim by "
                  f"'{claim.get('platform')}' overlaps the state file "
                  f"(claim id: {claim.get('claim_id') or claim.get('id', '?')}, "
                  f"task: {claim.get('task', '?')}). "
                  "Wait, release the claim, or re-run with --force.",
                  file=sys.stderr)
            return 3
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
