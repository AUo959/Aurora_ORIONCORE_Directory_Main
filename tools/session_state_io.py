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
    python3 tools/session_state_io.py add-item <id> --description TEXT
        --next-action TEXT --definition-of-done TEXT [lifecycle options]
    python3 tools/session_state_io.py start-item <id>
    python3 tools/session_state_io.py ready-item <id> --review-at TIMESTAMP
    python3 tools/session_state_io.py complete-active [--detail TEXT]
    python3 tools/session_state_io.py complete-item <id> [--detail TEXT]
    python3 tools/session_state_io.py wait-active --waiting-on owner|external|artifact|date
        --trigger TEXT --review-at TIMESTAMP [owner-gate options]
    python3 tools/session_state_io.py park-active --reason TEXT --review-at TIMESTAMP
    python3 tools/session_state_io.py set-summary TEXT
    python3 tools/session_state_io.py set-tool-version <tool> <version>
    python3 tools/session_state_io.py suspend-active --next-step TEXT
        --resume-by TIMESTAMP [--next-step-detail TEXT]
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


def _touch_state(state: dict, platform: str) -> None:
    state["last_platform"] = platform
    state["last_updated"] = _now()


def _find_queue_item(state: dict, item_id: str) -> tuple[dict | None, list]:
    queue = state.setdefault("task_queue", [])
    match = next((item for item in queue if item.get("id") == item_id), None)
    return match, queue


def _completion_record(
    item: dict,
    *,
    platform: str,
    detail: str | None,
    status: str = "completed",
    approval_evidence: str | None = None,
) -> dict:
    record = {
        "id": item["id"],
        "status": status,
        "completed_at": _now(),
        "platform": platform,
        "detail": detail or item.get("description") or item.get("definition_of_done", ""),
    }
    if item.get("evidence_refs"):
        record["evidence_refs"] = item["evidence_refs"]
    for field in ("gate_scope", "decision_options", "trigger"):
        if item.get(field):
            record[field] = item[field]
    if approval_evidence:
        record["approval_evidence"] = approval_evidence
    return record


def detect_platform() -> str:
    """Best-effort platform detection; override with --platform."""
    if os.environ.get("CLAUDECODE"):
        return "claude-code"
    if os.environ.get("CODEX_HOME") or os.environ.get("CODEX_CLI_PATH"):
        return "codex"
    return "claude-code"


def load(path: Path | None = None) -> dict:
    # Resolved at call time, not bound as a def-time default, so STATE_PATH can be
    # redirected (tests, alternate checkouts). A def-time default silently ignores
    # any reassignment of STATE_PATH and writes to the real state file.
    return json.loads((path or STATE_PATH).read_text(encoding="utf-8"))


def dumps_canonical(state: dict) -> str:
    return json.dumps(state, indent=2, ensure_ascii=True) + "\n"


def save(state: dict, path: Path | None = None, *, validate: bool = True) -> list[str]:
    """Validate then write canonically. Returns findings; writes only if none.

    `path` resolves at call time (see load) so STATE_PATH stays redirectable.
    """
    findings = session_state_check.validate(state) if validate else []
    if findings:
        return findings
    (path or STATE_PATH).write_text(dumps_canonical(state), encoding="utf-8")
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
    match, queue = _find_queue_item(state, args.item_id)
    if match is None:
        print(f"session-state-io: no queue item with id '{args.item_id}'", file=sys.stderr)
        return 1
    if match.get("approval_required") and not args.approval_evidence:
        print(
            "session-state-io: owner-gated decisions require --approval-evidence",
            file=sys.stderr,
        )
        return 1
    queue.remove(match)
    state.setdefault("completed_tasks", []).append(
        _completion_record(
            match,
            platform=args.platform,
            detail=args.detail,
            # getattr, not attribute access: these op_ functions are also
            # called with hand-built Namespaces (see tests/test_session_state_io_ext.py),
            # and only the CLI parser guarantees every optional flag is present.
            # Hard-requiring a parser-supplied attribute makes the function
            # usable from exactly one caller.
            approval_evidence=getattr(args, "approval_evidence", None),
        )
    )
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: completed '{args.item_id}' (from task_queue)")
    return 0


def _queue_item_from_args(args: argparse.Namespace) -> dict:
    now = _now()
    status = "waiting" if args.approval_required else args.status
    assigned_to = "owner" if args.approval_required else args.assigned_to
    kind = "decision" if args.approval_required else args.kind
    item = {
        "id": args.item_id,
        "status": status,
        "priority": args.priority,
        "assigned_to": assigned_to,
        "kind": kind,
        "repo": args.repo,
        "description": args.description,
        "created_at": args.created_at or now,
        "updated_at": now,
        "review_at": args.review_at,
        "next_action": args.next_action,
        "definition_of_done": args.definition_of_done,
        "approval_required": args.approval_required,
    }
    if status == "waiting":
        item["waiting_on"] = "owner" if args.approval_required else args.waiting_on
        item["trigger"] = args.trigger
    elif status == "parked":
        item["trigger"] = args.trigger
    if args.evidence_ref:
        item["evidence_refs"] = args.evidence_ref
    if args.approval_required:
        item["gate_scope"] = args.gate_scope
        item["decision_options"] = args.decision_option or []
    return item


def op_add_item(args: argparse.Namespace) -> int:
    state = load()
    item = _queue_item_from_args(args)
    state.setdefault("task_queue", []).append(item)
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(
        f"session-state-io: queued '{args.item_id}' "
        f"({item['status']}, {args.priority}, {item['assigned_to']})"
    )
    return 0


def op_add_pending(args: argparse.Namespace) -> int:
    """Compatibility alias: old pending additions become actionable queue work."""
    now = _now()
    args.status = "ready"
    args.kind = "work"
    args.repo = "root"
    args.created_at = now
    args.review_at = args.review_at or now
    args.next_action = args.description
    args.definition_of_done = "The described work is completed and validated."
    args.approval_required = False
    args.waiting_on = None
    args.trigger = None
    args.gate_scope = None
    args.evidence_ref = []
    args.decision_option = []
    print(
        "session-state-io: add-pending is deprecated; routing item into task_queue status='ready'",
        file=sys.stderr,
    )
    return op_add_item(args)


def op_start_item(args: argparse.Namespace) -> int:
    state = load()
    if state.get("active_task") is not None:
        print("session-state-io: active_task is already occupied", file=sys.stderr)
        return 1
    match, queue = _find_queue_item(state, args.item_id)
    if match is None:
        print(f"session-state-io: no queue item with id '{args.item_id}'", file=sys.stderr)
        return 1
    if match.get("status") != "ready" or match.get("approval_required"):
        print(
            "session-state-io: only non-gated status='ready' items can be started",
            file=sys.stderr,
        )
        return 1
    queue.remove(match)
    match["status"] = "active"
    match["started_at"] = _now()
    match["updated_at"] = _now()
    match.pop("review_at", None)
    state["active_task"] = match
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: started '{args.item_id}'")
    return 0


def op_ready_item(args: argparse.Namespace) -> int:
    """Return waiting/parked work to ready, with auditable gate correction."""
    state = load()
    match, _queue = _find_queue_item(state, args.item_id)
    if match is None:
        print(f"session-state-io: no queue item with id '{args.item_id}'", file=sys.stderr)
        return 1
    if match.get("status") not in {"waiting", "parked"}:
        print(
            "session-state-io: ready-item requires status='waiting' or 'parked'",
            file=sys.stderr,
        )
        return 1
    was_owner_gate = match.get("approval_required") is True
    if was_owner_gate and not args.reason:
        print(
            "session-state-io: reclassifying an owner gate requires --reason",
            file=sys.stderr,
        )
        return 1
    now = _now()
    match["status"] = "ready"
    match["updated_at"] = now
    match["review_at"] = args.review_at
    match["approval_required"] = False
    if args.next_action:
        match["next_action"] = args.next_action
    if args.assigned_to:
        match["assigned_to"] = args.assigned_to
    elif was_owner_gate:
        match["assigned_to"] = "either"
    if was_owner_gate:
        match["kind"] = "work"
        match["gate_reclassified_at"] = now
        match["gate_reclassification_reason"] = args.reason
    for field in ("waiting_on", "trigger", "gate_scope", "decision_options"):
        match.pop(field, None)
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: returned '{args.item_id}' to ready")
    return 0


def op_complete_active(args: argparse.Namespace) -> int:
    state = load()
    active = state.get("active_task")
    if not isinstance(active, dict):
        print("session-state-io: no active task to complete", file=sys.stderr)
        return 1
    state.setdefault("completed_tasks", []).append(
        _completion_record(active, platform=args.platform, detail=args.detail)
    )
    state["active_task"] = None
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: completed active task '{active['id']}' and cleared slot")
    return 0


def op_wait_active(args: argparse.Namespace) -> int:
    state = load()
    active = state.get("active_task")
    if not isinstance(active, dict):
        print("session-state-io: no active task to move to waiting", file=sys.stderr)
        return 1
    active["status"] = "waiting"
    active["updated_at"] = _now()
    active["review_at"] = args.review_at
    active["waiting_on"] = args.waiting_on
    active["trigger"] = args.trigger
    active["approval_required"] = args.approval_required
    active.pop("resume_by", None)
    if args.approval_required:
        active["kind"] = "decision"
        active["assigned_to"] = "owner"
        active["gate_scope"] = args.gate_scope
        active["evidence_refs"] = args.evidence_ref or []
        active["decision_options"] = args.decision_option or []
    state.setdefault("task_queue", []).append(active)
    state["active_task"] = None
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: moved '{active['id']}' to waiting and cleared active slot")
    return 0


def op_park_active(args: argparse.Namespace) -> int:
    state = load()
    active = state.get("active_task")
    if not isinstance(active, dict):
        print("session-state-io: no active task to park", file=sys.stderr)
        return 1
    active["status"] = "parked"
    active["updated_at"] = _now()
    active["review_at"] = args.review_at
    active["trigger"] = args.reason
    active["approval_required"] = False
    active.pop("resume_by", None)
    state.setdefault("task_queue", []).append(active)
    state["active_task"] = None
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: parked '{active['id']}' and cleared active slot")
    return 0


def op_cancel_item(args: argparse.Namespace) -> int:
    state = load()
    active = state.get("active_task")
    if isinstance(active, dict) and active.get("id") == args.item_id:
        item = active
        state["active_task"] = None
    else:
        item, queue = _find_queue_item(state, args.item_id)
        if item is None:
            print(f"session-state-io: no open item with id '{args.item_id}'", file=sys.stderr)
            return 1
        queue.remove(item)
    state.setdefault("completed_tasks", []).append(
        _completion_record(
            item,
            platform=args.platform,
            detail=args.reason,
            status="cancelled",
        )
    )
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: cancelled '{args.item_id}'")
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
    active["resume_by"] = args.resume_by
    active["next_action"] = args.next_step
    active["next_step"] = args.next_step
    if args.next_step_detail:
        detail = args.next_step_detail
        if len(detail) > SPILL_THRESHOLD:
            detail = _spill_handoff(detail, args.platform, args.next_step)
        active["next_step_detail"] = detail
    _touch_state(state, args.platform)
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: active_task suspended (next_step: {args.next_step})")
    return 0


def op_complete_active(args: argparse.Namespace) -> int:
    """Retire active_task: log it into completed_tasks and clear the slot.

    Counterpart to suspend-active. Without this, an active_task can only ever be
    moved *into* 'suspended' (complete-item searches only task_queue and
    pending_for_next_session), so a finished task resurfaces at every session
    start forever. active_task is in REQUIRED_TOP_LEVEL so it cannot be deleted;
    the contract does allow null, which is what we set.
    """
    state = load()
    active = state.get("active_task")
    if not isinstance(active, dict):
        print("session-state-io: no active_task object to complete", file=sys.stderr)
        return 1
    completed = {
        "id": active.get("id"),
        "status": "completed",
        "completed_at": _now(),
        "platform": args.platform,
    }
    detail = args.detail or active.get("description")
    if detail:
        completed["detail"] = detail
    state.setdefault("completed_tasks", []).append(completed)
    state["active_task"] = None
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: active_task '{completed['id']}' completed and cleared")
    return 0


def op_reroute_active(args: argparse.Namespace) -> int:
    """Move active_task into task_queue (where complete-item works) and clear the slot.

    For work that is NOT finished but should not occupy the active slot — e.g. an
    item blocked on a gate that belongs to a process rather than to this session.
    """
    state = load()
    active = state.get("active_task")
    if not isinstance(active, dict):
        print("session-state-io: no active_task object to reroute", file=sys.stderr)
        return 1
    # This verb predates the lifecycle contract. It used to emit
    # `status: "queued"` with none of the required fields, which the contract
    # validator now refuses — so rerouting failed closed rather than writing a
    # malformed item. Emit a conforming item instead.
    #
    # `ready` rather than `waiting`: reroute exists for work that is unfinished
    # but not blocked on *this* session. If it were blocked on a named party,
    # `wait-active` is the verb, and that one demands a trigger.
    now = _now()
    description = args.description or active.get("description") or ""
    item = {
        "id": active.get("id"),
        "status": "ready",
        "priority": active.get("priority", "medium"),
        "assigned_to": active.get("assigned_to", "either"),
        "kind": active.get("kind", "work"),
        "repo": active.get("repo", "root"),
        "description": description,
        "created_at": active.get("created_at", now),
        "updated_at": now,
        "review_at": active.get("review_at", now),
        "next_action": (
            active.get("next_step")
            or f"Resume: {description}" if description else "Resume this item."
        ),
        "definition_of_done": active.get(
            "definition_of_done",
            "Carried over on reroute; confirm the exit condition when resumed.",
        ),
        "approval_required": False,
    }
    for key in ("context_files", "next_step", "next_step_detail"):
        if active.get(key) is not None:
            item[key] = active[key]
    state.setdefault("task_queue", []).append(item)
    state["active_task"] = None
    findings = save(state)
    if findings:
        return _refuse(findings)
    print(f"session-state-io: active_task '{item['id']}' rerouted to task_queue and cleared")
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
    for line in reversed([entry for entry in raw.splitlines() if entry.strip()]):
        sha, _, summary = line.partition(" ")
        if not any(e.get("sha") == sha for e in existing):
            existing.insert(0, {"sha": sha, "date": today,
                                "platform": args.platform, "summary": summary})
            added += 1
    state["recent_commits"] = existing[:10]
    state.setdefault("known_state", {})["main_sha"] = head
    _touch_state(state, args.platform)
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
    _touch_state(state, args.platform)
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

    def add_item_arguments(p: argparse.ArgumentParser) -> None:
        p.add_argument("item_id")
        p.add_argument("--description", required=True)
        p.add_argument("--next-action", required=True)
        p.add_argument("--definition-of-done", required=True)
        p.add_argument("--status", default="ready", choices=["ready", "waiting", "parked"])
        p.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
        p.add_argument("--assigned-to", default="either", choices=["codex", "claude-code", "either", "owner"])
        p.add_argument("--kind", default="work", choices=["work", "decision", "watch"])
        p.add_argument("--repo", default="root")
        p.add_argument("--created-at")
        p.add_argument("--review-at", required=True)
        p.add_argument("--waiting-on", choices=["owner", "external", "artifact", "date"])
        p.add_argument("--trigger")
        p.add_argument("--approval-required", action="store_true")
        p.add_argument("--gate-scope")
        p.add_argument("--evidence-ref", action="append")
        p.add_argument("--decision-option", action="append")

    sub.add_parser("fmt", help="Rewrite the file in canonical serialization")

    p = sub.add_parser("get", help="Print a value by dotted keypath")
    p.add_argument("keypath")

    p = sub.add_parser("complete-item", help="Move a task_queue item to completed_tasks")
    p.add_argument("item_id")
    p.add_argument("--detail", help="Completion detail (defaults to the item's description)")
    p.add_argument("--approval-evidence", help="Required when completing a true owner-gated decision")

    p = sub.add_parser("add-item", help="Append a lifecycle-aware task_queue item")
    add_item_arguments(p)

    p = sub.add_parser("add-pending", help="Deprecated alias: add an immediately ready task")
    p.add_argument("item_id")
    p.add_argument("--description", required=True)
    p.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    p.add_argument("--assigned-to", default="either",
                   choices=["codex", "claude-code", "either", "owner"])
    p.add_argument("--review-at")

    p = sub.add_parser("start-item", help="Move a ready queue item into active_task")
    p.add_argument("item_id")

    p = sub.add_parser("ready-item", help="Return waiting/parked work to ready")
    p.add_argument("item_id")
    p.add_argument("--review-at", required=True)
    p.add_argument("--next-action")
    p.add_argument("--assigned-to", choices=["codex", "claude-code", "either"])
    p.add_argument(
        "--reason",
        help="Required when correcting a previously owner-gated item",
    )

    p = sub.add_parser("complete-active", help="Complete active_task and clear the active slot atomically")
    p.add_argument("--detail")

    p = sub.add_parser("wait-active", help="Move active_task to a concrete waiting trigger")
    p.add_argument("--waiting-on", required=True, choices=["owner", "external", "artifact", "date"])
    p.add_argument("--trigger", required=True)
    p.add_argument("--review-at", required=True)
    p.add_argument("--approval-required", action="store_true")
    p.add_argument("--gate-scope")
    p.add_argument("--evidence-ref", action="append")
    p.add_argument("--decision-option", action="append")

    p = sub.add_parser("park-active", help="Deliberately park active_task with a review date")
    p.add_argument("--reason", required=True)
    p.add_argument("--review-at", required=True)

    p = sub.add_parser("cancel-item", help="Cancel an active or queued item with a receipt")
    p.add_argument("item_id")
    p.add_argument("--reason", required=True)

    p = sub.add_parser("set-summary", help="Set last_session_summary (+platform/updated)")
    p.add_argument("text")

    p = sub.add_parser("set-tool-version", help="Set a tool_versions entry (+platform/updated)")
    p.add_argument("tool")
    p.add_argument("version")

    p = sub.add_parser("suspend-active", help="Suspend active_task with a next step")
    p.add_argument("--next-step", required=True)
    p.add_argument("--resume-by", required=True)
    p.add_argument("--next-step-detail")

    p = sub.add_parser("reroute-active",
                       help="Move active_task into task_queue and clear the slot "
                            "(for unfinished work that shouldn't hold the active slot)")
    p.add_argument("--description", help="Override the description carried to the queue item")

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
        "add-item": op_add_item,
        "add-pending": op_add_pending,
        "start-item": op_start_item,
        "ready-item": op_ready_item,
        "complete-active": op_complete_active,
        "wait-active": op_wait_active,
        "park-active": op_park_active,
        "cancel-item": op_cancel_item,
        "set-summary": op_set_summary,
        "set-tool-version": op_set_tool_version,
        "suspend-active": op_suspend_active,
        "reroute-active": op_reroute_active,
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
