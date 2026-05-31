#!/usr/bin/env python3
"""
session_stop_hook.py — Runs on Claude Code session Stop.

Four jobs:
  1. Auto-write mechanical fields to catalog/session_state.json
     (last_platform, last_updated, known_state.main_sha, recent_commits)
  2. Commit + push session_state.json so Codex sees it immediately
  3. If there are uncommitted tracked changes, write an orphan marker so
     the next session (either platform) surfaces the abandoned work
  4. Print a summary of what was done

Invoked from .claude/settings.json → hooks → Stop.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "catalog" / "session_state.json"
CLAIMS_DIR = REPO_ROOT / "catalog" / "session_claims"
PLATFORM = "claude-code"
MAX_RECENT_COMMITS = 10


# ── Git helpers ────────────────────────────────────────────────────────────

def _git(*args: str, check: bool = False) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True, text=True, check=check,
        cwd=REPO_ROOT,
    )
    return result.stdout.strip()


def _git_short_sha() -> str:
    return _git("rev-parse", "--short", "HEAD")


def _git_branch() -> str:
    return _git("branch", "--show-current")


def _git_log_since(since_sha: str) -> list[dict]:
    """Return commits from since_sha+1 to HEAD as [{sha, summary}]."""
    if not since_sha:
        raw = _git("log", "--oneline", f"-{MAX_RECENT_COMMITS}")
    else:
        raw = _git("log", "--oneline", f"{since_sha}..HEAD")
    commits = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append({"sha": parts[0], "summary": parts[1]})
    return commits


def _git_uncommitted_tracked() -> list[str]:
    """Return list of tracked files with uncommitted changes."""
    raw = _git("status", "--porcelain")
    changed = []
    for line in raw.splitlines():
        if len(line) >= 3:
            status = line[:2]
            path = line[3:].strip()
            # Only tracked modifications (M, D) — not untracked (??)
            if "?" not in status and path and "catalog/session_state.json" not in path:
                changed.append(path)
    return changed


# ── State update ──────────────────────────────────────────────────────────

def _update_state(state: dict, head: str) -> tuple[dict, list[dict]]:
    """Update mechanical fields. Returns (updated_state, new_commits)."""
    known_sha = state.get("known_state", {}).get("main_sha", "")
    new_commits = _git_log_since(known_sha)

    # Prepend new commits to recent_commits, keep last MAX_RECENT_COMMITS
    existing = state.get("recent_commits", [])
    for c in reversed(new_commits):
        entry = {"sha": c["sha"], "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                 "platform": PLATFORM, "summary": c["summary"]}
        if not any(e.get("sha") == c["sha"] for e in existing):
            existing.insert(0, entry)
    state["recent_commits"] = existing[:MAX_RECENT_COMMITS]

    # Mechanical fields
    state["last_platform"] = PLATFORM
    state["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Summary from new commits if no manual summary was set this session
    if new_commits and not state.get("_summary_set_manually"):
        summaries = [c["summary"][:60] for c in new_commits[:3]]
        state["last_session_summary"] = "; ".join(summaries)

    # Update known SHA
    if "known_state" not in state:
        state["known_state"] = {}
    state["known_state"]["main_sha"] = head

    return state, new_commits


# ── Commit + push ─────────────────────────────────────────────────────────

def _staged_non_state_files() -> list[str]:
    """Return staged files other than session_state.json."""
    raw = _git("diff", "--cached", "--name-only")
    return [
        f for f in raw.splitlines()
        if f and "catalog/session_state.json" not in f
    ]


def _commit_state() -> tuple[bool, str]:
    """Stage + commit session_state.json only.

    Safety guard: if anything other than session_state.json is already staged,
    aborts and returns (False, reason) so partial work is never auto-committed.
    Returns (True, "") on success.
    """
    # Guard: check for other staged files BEFORE staging session_state
    already_staged = _staged_non_state_files()
    if already_staged:
        files_str = ", ".join(already_staged[:3])
        if len(already_staged) > 3:
            files_str += f" (+{len(already_staged) - 3} more)"
        return False, f"staged work present ({files_str}) — skipped auto-commit to avoid premature commit"

    _git("add", str(STATE_PATH.relative_to(REPO_ROOT)))
    result = subprocess.run(
        ["git", "commit", "-m",
         "chore(state): auto-update session handoff [skip ci]\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode == 0:
        return True, ""
    return False, result.stderr.strip() or "git commit failed"


def _push() -> bool:
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    return result.returncode == 0


# ── Orphan marker ─────────────────────────────────────────────────────────

def _write_orphan_marker(changed_files: list[str], head: str) -> Path:
    """Write a machine-local orphan marker for abandoned uncommitted work."""
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    marker_path = CLAIMS_DIR / f".orphan_{PLATFORM}_{ts}.json"
    marker = {
        "schema_version": 1,
        "platform": PLATFORM,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head_sha": head,
        "uncommitted_files": changed_files,
        "note": (
            "Uncommitted changes were present when the Claude Code session ended. "
            "Check these files before starting new work on this machine."
        ),
    }
    marker_path.write_text(json.dumps(marker, indent=2) + "\n")
    return marker_path


# ── Session start check ───────────────────────────────────────────────────

def check_orphans() -> None:
    """Print any orphan markers left from previous sessions. Call on session start."""
    if not CLAIMS_DIR.exists():
        return
    orphans = sorted(CLAIMS_DIR.glob(f".orphan_*.json"))
    if not orphans:
        return
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  ORPHANED WORK FROM PREVIOUS SESSION                     ║")
    print("╠══════════════════════════════════════════════════════════╣")
    for o in orphans:
        try:
            data = json.loads(o.read_text())
            print(f"║  Platform: {data['platform']:<46}║")
            print(f"║  SHA:      {data['head_sha']:<46}║")
            for f in data.get("uncommitted_files", [])[:5]:
                print(f"║    · {f[:52]:<52}║")
            if len(data.get("uncommitted_files", [])) > 5:
                extra = len(data["uncommitted_files"]) - 5
                print(f"║    · ... and {extra} more{' ' * (40 - len(str(extra)))}║")
        except Exception:
            print(f"║  {o.name:<55}║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Review these files before committing new changes.       ║")
    print("║  Delete orphan files once resolved:                      ║")
    print(f"║    rm catalog/session_claims/.orphan_*.json{' ' * 12}║")
    print("╚══════════════════════════════════════════════════════════╝\n")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "check-orphans":
        check_orphans()
        return 0

    if not STATE_PATH.exists():
        return 0

    head = _git_short_sha()
    if not head:
        return 0

    # Load state
    try:
        state = json.loads(STATE_PATH.read_text())
    except Exception:
        return 0

    known_sha = state.get("known_state", {}).get("main_sha", "")
    parent_sha = _git("rev-parse", "--short", "HEAD^")

    # Check if there's actually anything new to record
    if head == known_sha or head == parent_sha:
        return 0

    # Update state
    state, new_commits = _update_state(state, head)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")

    # Check for uncommitted work (before committing state)
    uncommitted = _git_uncommitted_tracked()

    # Commit + push the state file (safety guard is inside _commit_state)
    committed, commit_reason = _commit_state()
    pushed = _push() if committed else False

    # Write orphan marker if there's abandoned work
    orphan_path = None
    if uncommitted:
        orphan_path = _write_orphan_marker(uncommitted, head)

    # Summary output
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  SESSION HANDOFF — AUTO-UPDATED                          ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  HEAD:      {head:<44}║")
    print(f"║  Commits:   {len(new_commits)} new recorded{' ' * (32 - len(str(len(new_commits))))}║")
    commit_str = "yes" if committed else f"skipped: {commit_reason}"
    push_str = "yes — Codex can see it now" if pushed else ("n/a" if not committed else "failed — push manually")
    print(f"║  Committed: {commit_str:<44}║")
    print(f"║  Pushed:    {push_str:<44}║")
    if uncommitted:
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  ⚠  {len(uncommitted)} uncommitted file(s) — orphan marker written:  ║")
        for f in uncommitted[:4]:
            print(f"║    · {f[:52]:<52}║")
        if len(uncommitted) > 4:
            print(f"║    · ... and {len(uncommitted)-4} more{' ' * (38 - len(str(len(uncommitted)-4)))}║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
