#!/usr/bin/env python3
"""
session_stop_hook.py — Runs on Claude Code session Stop.

Four jobs:
  1. Auto-write mechanical fields to catalog/session_state.json
     (last_platform, last_updated, known_state.main_sha, recent_commits).
     ADVISORY ONLY — the update rides along with the operator's next real
     commit; the hook deliberately never commits or pushes (churn +
     force-push hazard).
  2. Record the landing ledger (publication debt) at session close
  3. On session start, surface tracked project-focus announcements so agents
     know the current collaboration focus before selecting work.
  4. If there are uncommitted tracked changes, write an orphan marker so
     the next session (either platform) surfaces the abandoned work
     (surfaced via the SessionStart hook running `check-orphans`)
  5. Validate session_state.json against the queue contract
     (tools/session_state_check.py) and warn on drift

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


# Mechanical receipts that hooks/gates rewrite around commit time — a dirty
# copy of these is workflow residue, not abandoned work, so they never
# produce orphan markers (2026-07-04 field finding: the pre-push skill-sync
# receipt manufactured a fresh orphan after every skills push).
ORPHAN_EXEMPT_PATHS = (
    "catalog/session_state.json",
    "reports/automation/skill_sync_latest.json",
    "reports/analysis/workspace_verify_latest.json",
    "reports/analysis/workspace_scan_summary.json",
)


def _git_uncommitted_tracked() -> list[str]:
    """Return list of tracked files with uncommitted changes.

    Uses `git diff --name-only HEAD` (staged + unstaged, tracked only):
    parsing `--porcelain` through _git() is unsafe because _git() strips
    stdout, which eats the leading space of the first porcelain line and
    truncates that path's first character.
    """
    raw = _git("diff", "--name-only", "HEAD")
    return [
        path.strip() for path in raw.splitlines()
        if path.strip() and path.strip() not in ORPHAN_EXEMPT_PATHS
    ]


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

    # Summary from new commits if no manual summary was set this session.
    # The flag is one-shot: honor it once, then clear it, so a stale flag
    # can never suppress auto-summaries in later sessions.
    if not state.pop("_summary_set_manually", False) and new_commits:
        summaries = [c["summary"][:60] for c in new_commits[:3]]
        state["last_session_summary"] = "; ".join(summaries)

    # Update known SHA
    if "known_state" not in state:
        state["known_state"] = {}
    state["known_state"]["main_sha"] = head

    return state, new_commits


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

def _debt_staleness_warning() -> None:
    """Warn when the landing-ledger snapshot is older than 24h."""
    try:
        state = json.loads(STATE_PATH.read_text())
        checked_at = state.get("publication_debt", {}).get("checked_at", "")
        if not checked_at:
            return
        age = datetime.now(timezone.utc) - datetime.strptime(
            checked_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if age.total_seconds() > 24 * 3600:
            hours = int(age.total_seconds() // 3600)
            print(f"[session-start] publication_debt snapshot is {hours}h old — "
                  "verify entries against live git/PR state before acting on them.")
    except Exception:
        pass


def _run_project_focus(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(REPO_ROOT / "tools" / "project_focus_announcement.py"), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def surface_project_focus() -> None:
    """Print active project-focus announcements at session start."""
    try:
        result = _run_project_focus("--summary")
        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout.strip())
            return
        detail = (result.stderr or result.stdout).strip().splitlines()
        if detail:
            print(f"[session-start] project focus skipped: {detail[0][:120]}")
    except Exception as exc:  # advisory - never block a session on focus text
        print(f"[session-start] project focus skipped: {exc}")


def check_orphans() -> None:
    """Surface orphan markers from previous sessions; auto-resolve stale ones.

    A marker is resolved when none of its recorded files are still dirty —
    the work it flagged has since been committed (possibly by the other
    platform), so the marker is deleted instead of nagging forever.
    """
    _debt_staleness_warning()
    if not CLAIMS_DIR.exists():
        return
    orphans = sorted(CLAIMS_DIR.glob(".orphan_*.json"))
    if not orphans:
        return

    still_dirty = set(_git_uncommitted_tracked())
    unresolved = []
    resolved = 0
    for marker in orphans:
        try:
            files = set(json.loads(marker.read_text()).get("uncommitted_files", []))
        except Exception:
            unresolved.append(marker)
            continue
        if files & still_dirty:
            unresolved.append(marker)
        else:
            marker.unlink()
            resolved += 1
    if resolved:
        print(f"[session-start] auto-resolved {resolved} orphan marker(s) — "
              "their files have since been committed.")
    orphans = unresolved
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


# ── Auto session claim ─────────────────────────────────────────────────────
# Field finding 2026-07-04: live sessions never filed claims voluntarily, so
# the session_state_io write guard had nothing to key on. SessionStart files
# one automatically; Stop releases it. Machine-local, advisory, TTL-bounded.

AUTO_CLAIM_MARKER = CLAIMS_DIR / ".claude_auto_claim"
AUTO_CLAIM_TTL_MINUTES = 240


def _run_claim(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(REPO_ROOT / "tools" / "session_claim.py"), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def file_auto_claim() -> None:
    """File the per-session advisory claim on the shared state file."""
    try:
        if AUTO_CLAIM_MARKER.exists():
            return  # a claim from this session (or an unreleased one) exists
        claim_id = f"claude-auto-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        result = _run_claim(
            "create", "--platform", "claude-code", "--task-id", "auto-session",
            "--repo", "root", "--paths", "catalog/session_state.json",
            "--mutation-posture", "editing",
            "--ttl-minutes", str(AUTO_CLAIM_TTL_MINUTES),
            "--claim-id", claim_id, "--allow-conflict",
            "--notes", "Automatic session-presence claim (SessionStart hook).",
        )
        if result.returncode == 0:
            CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
            AUTO_CLAIM_MARKER.write_text(claim_id + "\n")
            print(f"[session-start] auto-claim filed: {claim_id}")
        else:
            print(f"[session-start] auto-claim skipped: {result.stderr.strip()[:120]}")
    except Exception as exc:  # advisory — never block a session on claims
        print(f"[session-start] auto-claim skipped: {exc}")


def release_auto_claim() -> None:
    """Release this session's advisory claim, if one was filed."""
    try:
        if not AUTO_CLAIM_MARKER.exists():
            return
        claim_id = AUTO_CLAIM_MARKER.read_text().strip()
        if claim_id:
            _run_claim("release", "--claim-id", claim_id)
        AUTO_CLAIM_MARKER.unlink()
    except Exception:
        pass


# ── Main ──────────────────────────────────────────────────────────────────

def record_landing_ledger() -> None:
    """Record publication debt at session close — the landing ledger.

    Every stranding this workspace ever suffered was a session ending with
    matured work unpublished. The stop hook now refuses to let that state
    be silent: undecided unpublished work is written into session_state so
    the NEXT session reads it before anything else.
    """
    try:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import publication_debt

        entries = publication_debt.scan_all()
        debts = [d for d in entries if not d.get("exempt")]
        publication_debt.record(debts)
        if debts:
            print("╔════════════════════════════════════════════════════════════╗")
            print("║  LANDING LEDGER: unpublished matured work at session close  ║")
            for d in debts[:6]:
                label = f"{d['repo']}" + (f" [{d.get('branch')}]" if d.get('branch') else "")
                print(f"║  - {label}: {d['class']}"[:62].ljust(62) + "║")
            print("║  Publish (push + PR), retire deliberately, or record an     ║")
            print("║  exemption in catalog/publication_debt_exemptions.yaml.     ║")
            print("╚════════════════════════════════════════════════════════════╝")
    except Exception as exc:  # never block session close on ledger failure
        print(f"[stop-hook] landing ledger skipped: {exc}")


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "check-orphans":
        check_orphans()
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "session-start":
        surface_project_focus()
        check_orphans()
        file_auto_claim()
        return 0

    release_auto_claim()
    record_landing_ledger()

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

    # Self-heal the structural merge driver config (idempotent, per clone).
    try:
        _git("config", "merge.session-state.driver",
             "python3 tools/session_state_merge.py %O %A %B")
    except Exception:
        pass

    # Contract check (warn only — never block session close on drift)
    try:
        import session_state_check

        drift = session_state_check.validate(state)
        if drift:
            print(f"[stop-hook] session_state.json contract drift ({len(drift)}):")
            for finding in drift[:5]:
                print(f"  - {finding}")
            print("  Run: make session-state-check")
    except Exception as exc:
        print(f"[stop-hook] contract check skipped: {exc}")

    known_sha = state.get("known_state", {}).get("main_sha", "")

    # How many commits has HEAD advanced past what state last recorded?
    ahead = 0
    if known_sha:
        out = subprocess.run(
            ["git", "rev-list", "--count", f"{known_sha}..HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, check=False,
        )
        if out.returncode == 0:
            ahead = int(out.stdout.strip() or 0)

    # Nothing new landed → nothing to do (no churn).
    if ahead == 0:
        return 0

    # ADVISORY ONLY. Update the state file's mechanical fields on disk so the
    # change rides along with the operator's next real commit. We deliberately do
    # NOT git-commit or git-push here: auto-committing every turn created commit
    # churn, and auto-pushing risked the force-push hazard AGENTS.md warns about.
    state, new_commits = _update_state(state, head)
    try:
        import session_state_io

        drift = session_state_io.save(state)
        if drift:
            # Never lose the mechanical update, but make the drift loud.
            STATE_PATH.write_text(session_state_io.dumps_canonical(state))
            print(f"[stop-hook] wrote state WITH {len(drift)} contract finding(s) — run make session-state-check")
    except ImportError:
        STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")

    uncommitted = _git_uncommitted_tracked()
    if uncommitted:
        _write_orphan_marker(uncommitted, head)

    # Concise reminder.
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  SESSION HANDOFF — state updated on disk (advisory)      ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  HEAD:   {head:<47}║")
    print(f"║  Ahead:  {str(ahead) + ' commit(s) since last recorded':<47}║")
    print("║  Action: include catalog/session_state.json in your next ║")
    print("║          commit. The hook does NOT auto-commit or push.  ║")
    if uncommitted:
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  ⚠  {len(uncommitted)} uncommitted tracked file(s) — orphan marker set ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
