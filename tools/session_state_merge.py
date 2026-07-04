#!/usr/bin/env python3
"""session_state_merge.py — structural 3-way git merge driver for session state.

catalog/session_state.json is edited by both Codex and Claude Code, often in
overlapping sessions. Textual merge either conflicts or silently drops one
side. This driver merges STRUCTURALLY, implementing the protocol's
conflict_rule ("do not overwrite — append") plus removal semantics:

- completed_tasks / recent_commits: union by id/sha (append-only surfaces).
- pending_for_next_session / task_queue: 3-way set merge by id — an item
  removed by either side (completed) stays removed; items added by either
  side are kept; an item modified on both sides takes the newer side's copy.
- last_updated: max. last_platform / last_session_summary and snapshot
  blocks (publication_debt, known_state, ...): the side whose top-level
  last_updated is newer.
- active_task: field-wise 3-way; if both sides appended to next_step_detail,
  both suffixes are kept (ours then theirs).

The merged result must pass the queue contract (session_state_check) or the
driver exits non-zero and git falls back to a normal conflict for a human.

Install (idempotent, per clone):
    python3 tools/session_state_merge.py --install
Wiring: .gitattributes maps the file to this driver; `make setup` and the
Claude Code stop hook run --install.

Driver protocol: argv = %O %A %B (ancestor, ours, theirs); result is written
to %A; exit 0 = merged, non-zero = conflict.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import session_state_check  # noqa: E402
import session_state_io  # noqa: E402

DRIVER_NAME = "session-state"
DRIVER_CMD = "python3 tools/session_state_merge.py %O %A %B"

# Keys where the newer side (by top-level last_updated) wins outright when
# both sides changed: point-in-time snapshots, not append surfaces.
SNAPSHOT_KEYS = {
    "last_platform",
    "last_session_summary",
    "known_state",
    "publication_debt",
    "review_debt",
    "tool_versions",
    "security_events",
    "_summary_set_manually",
}


def _by_key(entries: list, key: str) -> dict:
    out = {}
    for e in entries:
        if isinstance(e, dict) and isinstance(e.get(key), str):
            out[e[key]] = e
    return out


def _merge_append_only(ours: list, theirs: list, key: str) -> list:
    """Union by identity key; ours' order first, then theirs' novel entries."""
    seen = set(_by_key(ours, key))
    return ours + [e for e in theirs if isinstance(e, dict) and e.get(key) not in seen]


def _merge_queue(base: list, ours: list, theirs: list, ours_newer: bool) -> list:
    """3-way set merge by id: removals win, additions kept, mods take newer."""
    base_by = _by_key(base, "id")
    ours_by, theirs_by = _by_key(ours, "id"), _by_key(theirs, "id")
    merged: list = []
    for item in ours:
        item_id = item.get("id") if isinstance(item, dict) else None
        if item_id is None:
            merged.append(item)
            continue
        if item_id in base_by and item_id not in theirs_by:
            continue  # theirs removed (completed) it — removal wins
        their_item = theirs_by.get(item_id, item)
        base_item = base_by.get(item_id)
        if their_item == item or their_item == base_item:
            merged.append(item)  # identical, or only ours modified
        elif item == base_item:
            merged.append(their_item)  # only theirs modified
        else:
            merged.append(item if ours_newer else their_item)  # both modified
    for item_id, item in theirs_by.items():
        if item_id not in ours_by and item_id not in base_by:
            merged.append(item)  # theirs added it
    return merged


def _merge_active_task(base: dict, ours: dict, theirs: dict, newer: dict) -> dict:
    merged = {}
    for key in dict.fromkeys(list(ours) + list(theirs)):
        b, o, t = base.get(key), ours.get(key), theirs.get(key)
        if o == t:
            merged[key] = o
        elif t == b and key in ours:
            merged[key] = o
        elif o == b and key in theirs:
            merged[key] = t
        elif key == "next_step_detail" and all(isinstance(x, str) for x in (b, o, t)) \
                and o.startswith(b) and t.startswith(b):
            merged[key] = o + t[len(b):]  # both appended: keep both suffixes
        else:
            merged[key] = newer.get(key, o if key in ours else t)
    return merged


def merge_states(base: dict, ours: dict, theirs: dict) -> dict:
    """Structurally merge two descendants of base. Returns the merged state."""
    ours_newer = str(ours.get("last_updated", "")) >= str(theirs.get("last_updated", ""))
    newer, older = (ours, theirs) if ours_newer else (theirs, ours)

    merged: dict = {}
    for key in dict.fromkeys(list(ours) + list(theirs)):
        b, o, t = base.get(key), ours.get(key), theirs.get(key)
        if o == t:
            merged[key] = o
        elif t == b and key in ours:
            merged[key] = o  # only ours changed
        elif o == b and key in theirs:
            merged[key] = t  # only theirs changed
        # Both changed differently:
        elif key == "last_updated":
            merged[key] = max(str(o), str(t))
        elif key == "completed_tasks":
            merged[key] = _merge_append_only(o or [], t or [], "id")
        elif key == "recent_commits":
            newer_list, older_list = (o, t) if ours_newer else (t, o)
            union = _merge_append_only(newer_list or [], older_list or [], "sha")
            # Stable sort newest-date-first so the cap drops the oldest
            # entries, not whichever side's novel commits landed last.
            union.sort(key=lambda e: str(e.get("date", "")) if isinstance(e, dict) else "",
                       reverse=True)
            merged[key] = union[:10]
        elif key in ("pending_for_next_session", "task_queue"):
            merged[key] = _merge_queue(b or [], o or [], t or [], ours_newer)
        elif key == "active_task" and all(isinstance(x, dict) for x in (b or {}, o, t)):
            merged[key] = _merge_active_task(b or {}, o, t,
                                             newer.get(key, {}) if isinstance(newer.get(key), dict) else {})
        elif key in SNAPSHOT_KEYS:
            merged[key] = newer.get(key, older.get(key))
        else:
            merged[key] = newer.get(key, older.get(key))
    return merged


def install() -> int:
    subprocess.run(
        ["git", "config", f"merge.{DRIVER_NAME}.name",
         "structural session_state.json merge"],
        check=True,
    )
    subprocess.run(
        ["git", "config", f"merge.{DRIVER_NAME}.driver", DRIVER_CMD],
        check=True,
    )
    print(f"session-state-merge: driver '{DRIVER_NAME}' configured for this clone")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--install":
        return install()
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2

    base_path, ours_path, theirs_path = (Path(p) for p in argv[1:4])
    try:
        base = json.loads(base_path.read_text(encoding="utf-8") or "{}")
        ours = json.loads(ours_path.read_text(encoding="utf-8"))
        theirs = json.loads(theirs_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"session-state-merge: cannot parse inputs ({exc}); "
              "falling back to normal conflict", file=sys.stderr)
        return 1

    merged = merge_states(base, ours, theirs)
    findings = session_state_check.validate(merged)
    if findings:
        print(f"session-state-merge: merged state fails the queue contract "
              f"({len(findings)} finding(s)); falling back to normal conflict",
              file=sys.stderr)
        for f in findings[:5]:
            print(f"  - {f}", file=sys.stderr)
        return 1

    ours_path.write_text(session_state_io.dumps_canonical(merged), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
