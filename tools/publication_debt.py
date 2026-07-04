#!/usr/bin/env python3
"""
publication_debt.py — the landing ledger.

The workspace's recurring failure mode is work that matures locally and
never gets published: a session ends, no PR is created, and finished work
strands on a branch (the March lineage, the April features, the June
handoffs all failed this exact way). This tool makes that state a tracked,
visible debt instead of a silent one.

Usage:
    python3 tools/publication_debt.py scan            # print debt; exit 2 if any
    python3 tools/publication_debt.py record          # scan + write session_state publication_debt[]
    python3 tools/publication_debt.py scan --json     # machine-readable

Detected debt classes (git-only; offline-safe):
    unpushed_main     — a repo's main is ahead of origin/main
    stranded_branch   — a non-main local branch carries commits absent from
                        origin/main and has no matching remote branch
                        (nothing on GitHub can see it; no PR can exist)
    unpublished_branch— a non-main local branch is pushed but its remote has
                        no open PR (checked only when `gh` is available;
                        otherwise reported as unverified)
    dirty_tree        — uncommitted tracked changes in a registered repo

The session stop hook calls `record` so every handoff carries the ledger;
workspace_verify warns while debt is outstanding. Clearing debt = publish
the work (push + PR) or retire the branch deliberately.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "catalog" / "session_state.json"
EXEMPTIONS_PATH = REPO_ROOT / "catalog" / "publication_debt_exemptions.yaml"


def load_exemptions(root: Path = REPO_ROOT) -> list[dict]:
    path = root / "catalog" / "publication_debt_exemptions.yaml"
    if not path.exists():
        return []
    sys.path.insert(0, str(root / "tools"))
    from _workspace_common import load_yaml_like

    payload = load_yaml_like(path) or {}
    return [e for e in payload.get("exemptions", []) if isinstance(e, dict) and e.get("reason")]


def is_exempt(debt: dict, exemptions: list[dict], today: str) -> str | None:
    """Return the exemption reason when this debt entry is covered."""
    for ex in exemptions:
        if ex.get("repo") and ex["repo"] != debt["repo"]:
            continue
        if ex.get("expires") and str(ex["expires"]) < today:
            continue
        if ex.get("class") and ex["class"] == debt["class"] and not ex.get("branches"):
            return str(ex["reason"])
        if debt.get("branch") and debt["branch"] in (ex.get("branches") or []):
            return str(ex["reason"])
    return None

EXEMPT_BRANCH_PREFIXES = ("salvage/", "rescue/", "draft/", "backup/")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(  # noqa: S603, S607 - git with repo-audit controlled args
        ["git", "-C", str(repo), *args], capture_output=True, text=True  # noqa: S607
    )
    return result.stdout.strip()


def _live_remote_branches(repo: Path) -> set[str] | None:
    """Branch names actually on origin right now, or None if unreachable.

    Local tracking refs (refs/remotes/origin/*) go stale in both directions —
    2026-07-04 field finding: two branches classified 'pushed' had no remote
    ref at all. One ls-remote per repo gives ground truth; None (offline)
    falls back to tracking refs with the entry annotated as unverified.
    """
    result = subprocess.run(  # noqa: S603, S607 - git with repo-audit controlled args
        ["git", "-C", str(repo), "ls-remote", "--heads", "origin"],  # noqa: S607
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return None
    branches: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[1].startswith("refs/heads/"):
            branches.add(parts[1][len("refs/heads/"):])
    return branches


def registered_repos(root: Path = REPO_ROOT) -> list[tuple[str, Path]]:
    sys.path.insert(0, str(root / "tools"))
    from _workspace_common import load_yaml_like

    repos: list[tuple[str, Path]] = [("root", root)]
    registry = root / "catalog" / "repo_registry.yaml"
    if registry.exists():
        payload = load_yaml_like(registry) or {}
        for entry in payload.get("repos", []):
            path = str(entry.get("path", ""))
            if not path or path.startswith("~"):
                continue
            repo_path = root / path
            if (repo_path / ".git").exists():
                repos.append((str(entry.get("name", path)), repo_path))
    return repos


def _branch_has_open_pr(repo: Path, branch: str) -> bool | None:
    """True/False when `gh` can answer; None when it cannot (offline etc.)."""
    if shutil.which("gh") is None:
        return None
    url = _git(repo, "remote", "get-url", "origin")
    if not url:
        return None
    result = subprocess.run(  # noqa: S603, S607 - gh with registry-controlled branch names
        ["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number"],  # noqa: S607
        capture_output=True, text=True, cwd=repo,
    )
    if result.returncode != 0:
        return None
    try:
        return bool(json.loads(result.stdout or "[]"))
    except json.JSONDecodeError:
        return None


def scan_repo(name: str, repo: Path) -> list[dict]:
    debts: list[dict] = []
    if not _git(repo, "rev-parse", "--verify", "-q", "origin/main"):
        return debts

    dirty = [
        line for line in _git(repo, "status", "--porcelain").splitlines()
        if line and not line.startswith("??")
    ]
    if dirty:
        debts.append({
            "repo": name, "class": "dirty_tree",
            "detail": f"{len(dirty)} uncommitted tracked path(s)",
            "remediation": "Commit or deliberately discard the working-tree changes.",
        })

    try:
        live_branches = _live_remote_branches(repo)
    except Exception:
        live_branches = None

    for branch in _git(repo, "for-each-ref", "refs/heads", "--format=%(refname:short)").splitlines():
        if not branch or branch.startswith(EXEMPT_BRANCH_PREFIXES):
            continue
        counts = _git(repo, "rev-list", "--left-right", "--count", f"origin/main...{branch}")
        ahead = int(counts.split()[1]) if counts and len(counts.split()) > 1 else 0
        if ahead == 0:
            continue
        if branch == "main":
            debts.append({
                "repo": name, "class": "unpushed_main",
                "detail": f"main is {ahead} commit(s) ahead of origin/main",
                "remediation": "Push main (or PR it if the repo requires review).",
            })
            continue
        if live_branches is not None:
            has_remote = branch in live_branches
            remote_note = ""
        else:
            has_remote = bool(_git(repo, "rev-parse", "--verify", "-q", f"refs/remotes/origin/{branch}"))
            remote_note = " (remote UNVERIFIED — offline; classification from local tracking refs)"
        if not has_remote:
            debts.append({
                "repo": name, "class": "stranded_branch", "branch": branch,
                "detail": f"{ahead} commit(s) exist only on this machine{remote_note}",
                "remediation": f"Push and open a PR: git push -u origin {branch} && gh pr create",
            })
        else:
            pr = _branch_has_open_pr(repo, branch)
            if pr is False:
                debts.append({
                    "repo": name, "class": "unpublished_branch", "branch": branch,
                    "detail": f"pushed, {ahead} commit(s) ahead, no open PR{remote_note}",
                    "remediation": f"gh pr create --head {branch} (or retire the branch deliberately)",
                })
            elif pr is None:
                debts.append({
                    "repo": name, "class": "unpublished_branch", "branch": branch,
                    "detail": (
                        f"pushed, {ahead} commit(s) ahead, PR state UNVERIFIED "
                        "(gh failed or is unavailable in the current execution context)"
                    ),
                    "remediation": (
                        "Run `make gh-auth-check` with Codex escalated/unsandboxed execution before "
                        "treating the token as broken; then verify or create the PR."
                    ),
                })
    return debts


def scan_all(root: Path = REPO_ROOT) -> list[dict]:
    exemptions = load_exemptions(root)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    debts: list[dict] = []
    for name, repo in registered_repos(root):
        for debt in scan_repo(name, repo):
            reason = is_exempt(debt, exemptions, today)
            if reason:
                debt["exempt"] = reason
            debts.append(debt)
    return debts


def record(debts: list[dict]) -> None:
    if not STATE_PATH.exists():
        return
    state = json.loads(STATE_PATH.read_text())
    state["publication_debt"] = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entries": debts,
        "rule": "Clear by publishing (push + PR) or deliberately retiring; the next session reads this FIRST.",
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["scan", "record"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    all_entries = scan_all()
    debts = [d for d in all_entries if not d.get("exempt")]
    exempted = [d for d in all_entries if d.get("exempt")]
    if args.command == "record":
        record(debts)

    if args.json:
        print(json.dumps(all_entries, indent=2))
    else:
        if not debts:
            print("Landing ledger clean: no undecided unpublished work.")
        else:
            print(f"PUBLICATION DEBT — {len(debts)} entr{'y' if len(debts)==1 else 'ies'}:")
            for d in debts:
                branch = f" [{d['branch']}]" if d.get("branch") else ""
                print(f"  {d['repo']}{branch} ({d['class']}): {d['detail']}")
                print(f"      → {d['remediation']}")
        if exempted:
            print(f"(+{len(exempted)} exempted by documented decision — see catalog/publication_debt_exemptions.yaml)")
    return 2 if debts else 0


if __name__ == "__main__":
    sys.exit(main())
