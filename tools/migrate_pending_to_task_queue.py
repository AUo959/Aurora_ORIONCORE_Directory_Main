#!/usr/bin/env python3
"""Migrate `pending_for_next_session` entries into the lifecycle `task_queue`.

Why this exists
---------------
The session-queue lifecycle contract deprecates `pending_for_next_session` —
`session_state_check` requires it to be empty, with entries moved into
`task_queue`. But the contract shipped without a migration path, so adopting it
meant either hand-writing 13 required fields for every open item or importing a
stale snapshot of the queue. The second option is what made the original branch
unmergeable: its `session_state.json` carried the 2026-08-01 queue (25 items)
and would have overwritten the live one (38 items), discarding weeks of work.

What it will and will not invent
--------------------------------
Four of the required fields are semantic: `next_action`, `definition_of_done`,
`review_at`, `repo`. This tool derives them mechanically and says so, rather
than authoring intent on behalf of whoever queued the item:

* `next_action` / `definition_of_done` are derived from the existing
  description and carry a ``[migrated]`` marker. They are honest placeholders,
  not a claim about what the author meant.
* `created_at` is the migration time, because the original queue format did not
  record one. Pretending to know it would be worse than admitting we don't.
* `repo` is inferred from the id and description; unmatched items get `root`.

**No item is given `approval_required: true` by inference.** The owner gate
demands `gate_scope`, at least one `evidence_ref`, and at least two
`decision_options`. Manufacturing those would fabricate a decision the owner
never framed, and would defeat the very check that makes the gate meaningful.
Owner-assigned items migrate as `kind=decision`, `status=waiting`,
`waiting_on=owner` — visible and correctly classified — with the formal gate
left to be filled in deliberately. `--gate` accepts a JSON file supplying real
gate material for specific ids.

Usage
-----
    python3 tools/migrate_pending_to_task_queue.py --dry-run
    python3 tools/migrate_pending_to_task_queue.py --apply
    python3 tools/migrate_pending_to_task_queue.py --apply --gate gates.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE = REPO_ROOT / "catalog" / "session_state.json"
POLICY = REPO_ROOT / "catalog" / "session_queue_policy.json"

#: id/description substrings -> repo. First match wins; order matters.
REPO_HINTS = (
    ("cloudbank", "aurora-cloudbank-symbolic-main"),
    ("canonrec", "CanonRec"),
    ("qgia", "qgia-knowledge-library-main"),
    ("gumas", "aurora-cloudbank-symbolic-main"),
)

MARKER = "[migrated]"

#: The schema_version the lifecycle contract expects.
LIFECYCLE_SCHEMA_VERSION = 3


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _first_sentence(text: str) -> str:
    """The leading clause of a description is usually its actionable core."""
    cleaned = " ".join(str(text).split())
    match = re.split(r"(?<=[.;])\s+", cleaned, maxsplit=1)
    head = match[0].strip() if match else cleaned
    return head or cleaned


def _repo_for(entry: dict) -> str:
    haystack = f"{entry.get('id', '')} {entry.get('description', '')}".lower()
    for needle, repo in REPO_HINTS:
        if needle in haystack:
            return repo
    return "root"


def migrate_entry(entry: dict, now: datetime, policy: dict,
                  gates: dict) -> dict:
    owner_held = entry.get("assigned_to") == "owner"
    priority = entry.get("priority", "medium")

    # Review horizon by priority, not one flat date.
    #
    # The first version used the policy's ready_review_grace_days (0) for every
    # migrated item, which made all 33 of them due for review the instant the
    # migration ran. A queue-health report where everything is overdue on day
    # one carries no signal and trains people to scroll past it — the same
    # failure as the devkit P1s and the 58-entry publication ledger.
    #
    # Staggering is not hiding: nothing is suppressed, and high-priority work
    # plus every owner decision still surfaces immediately.
    if owner_held or priority == "high":
        review_days = 0
    elif priority == "medium":
        review_days = 14
    else:
        review_days = 30
    description = str(entry.get("description") or "").strip()
    lead = _first_sentence(description)

    item = {
        "id": entry["id"],
        "status": "waiting" if owner_held else "ready",
        "assigned_to": entry.get("assigned_to", "either"),
        "priority": entry.get("priority", "medium"),
        "kind": "decision" if owner_held else "work",
        "repo": _repo_for(entry),
        "description": description,
        "created_at": _stamp(now),
        "updated_at": _stamp(now),
        "review_at": _stamp(now + timedelta(days=review_days)),
        "next_action": f"{MARKER} {lead}",
        "definition_of_done": (
            f"{MARKER} Derived from the queued description; confirm the real "
            f"exit condition when this item is next picked up."
        ),
        "approval_required": False,
    }

    if item["status"] == "waiting":
        item["waiting_on"] = "owner"
        item["trigger"] = (
            "Owner reviews the queue and rules on this item."
        )

    # Real gate material, supplied deliberately rather than inferred.
    gate = gates.get(entry["id"])
    if gate:
        item.update(gate)
    return item


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--gate", help="JSON file: {id: {gate fields}}")
    args = ap.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8")) if POLICY.exists() else {}
    gates = json.loads(Path(args.gate).read_text(encoding="utf-8")) if args.gate else {}

    pending = state.get("pending_for_next_session")
    entries = pending if isinstance(pending, list) else (pending or {}).get("entries") or []
    if not entries:
        print("nothing to migrate: pending_for_next_session is already empty")
        return 0

    now = _now()

    # Entries already sitting in task_queue may predate the lifecycle contract
    # (status 'queued', no kind/created_at/...). Migrating only
    # pending_for_next_session leaves those failing the checker, which is how
    # the first run of this tool left the state file half-converted.
    legacy = [
        item for item in (state.get("task_queue") or [])
        if "kind" not in item
    ]
    for item in legacy:
        converted = migrate_entry(item, now, policy, gates)
        item.clear()
        item.update(converted)
    if legacy:
        print(f"legacy task_queue entries converted: {len(legacy)}")

    existing = {i.get("id") for i in state.get("task_queue") or []}
    migrated, skipped = [], []
    for entry in entries:
        if entry.get("id") in existing:
            skipped.append(entry.get("id"))
            continue
        migrated.append(migrate_entry(entry, now, policy, gates))

    unmatched = sorted(set(gates) - {e.get("id") for e in entries} - existing)
    if unmatched:
        # A gate naming an id that does not exist is silent otherwise, and a
        # mistyped id would quietly drop real owner-gate material.
        print(f"WARNING: gate ids not found in the queue: {unmatched}")

    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for item in migrated:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1

    print(f"pending entries      : {len(entries)}")
    print(f"already in task_queue: {len(skipped)}")
    print(f"to migrate           : {len(migrated)}")
    print(f"  by kind   : {by_kind}")
    print(f"  by status : {by_status}")
    print(f"  with real gate material: "
          f"{sum(1 for i in migrated if i.get('approval_required'))}")

    if not args.apply:
        print("\ndry run — pass --apply to write")
        return 0

    state.setdefault("task_queue", []).extend(migrated)
    if isinstance(pending, list):
        state["pending_for_next_session"] = []
    else:
        state["pending_for_next_session"]["entries"] = []
    # The checker gates on this; leaving it at 2 fails every other assertion
    # with a misleading "not lifecycle schema version 3".
    state["schema_version"] = LIFECYCLE_SCHEMA_VERSION
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    print(f"\nwrote {STATE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
