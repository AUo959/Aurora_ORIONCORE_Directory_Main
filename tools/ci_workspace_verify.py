#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Mapping

import workspace_verify


SESSION_STATE_PATH = "catalog/session_state.json"
PR_EVENTS = {"pull_request", "pull_request_target"}


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def _pull_request_base_ref(root: Path, env: Mapping[str, str]) -> str | None:
    if env.get("GITHUB_EVENT_NAME") not in PR_EVENTS:
        return None
    base_branch = env.get("GITHUB_BASE_REF", "").strip()
    if not base_branch:
        return None

    remote_ref = f"refs/remotes/origin/{base_branch}"
    resolved = _git(root, ["rev-parse", "--verify", remote_ref])
    if resolved.returncode == 0:
        return remote_ref

    local_ref = f"refs/heads/{base_branch}"
    resolved = _git(root, ["rev-parse", "--verify", local_ref])
    if resolved.returncode == 0:
        return local_ref
    return None


def _session_state_changed_in_pr(root: Path, base_ref: str) -> bool | None:
    result = _git(root, ["diff", "--quiet", f"{base_ref}...HEAD", "--", SESSION_STATE_PATH])
    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True
    return None


def _base_freshness(root: Path, base_ref: str) -> tuple[int, str] | None:
    state_path = root / SESSION_STATE_PATH
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    known_sha = str(state.get("known_state", {}).get("main_sha", "")).strip()
    if not known_sha:
        return None

    ancestor = _git(root, ["merge-base", "--is-ancestor", known_sha, base_ref])
    if ancestor.returncode != 0:
        return None

    count = _git(root, ["rev-list", "--count", f"{known_sha}..{base_ref}"])
    if count.returncode != 0:
        return None
    try:
        return int(count.stdout.strip() or "0"), known_sha
    except ValueError:
        return None


def adjust_pr_session_state_freshness(
    root: Path,
    findings: list[workspace_verify.Finding],
    env: Mapping[str, str] | None = None,
) -> list[workspace_verify.Finding]:
    """Re-anchor unchanged PR handoff freshness to the authoritative PR base.

    `known_state.main_sha` describes the canonical/default-branch handoff anchor.
    GitHub pull-request jobs check out a synthetic merge commit, so feature-only
    commits must not make an otherwise current handoff appear stale.

    The exception is intentionally narrow:
    - only GitHub pull-request contexts are eligible;
    - the PR must leave catalog/session_state.json unchanged;
    - the canonical PR base must resolve locally and contain known_state.main_sha;
    - a genuinely stale base remains warning/blocking at the existing thresholds;
    - a PR that edits session state receives the original strict verifier result.
    """
    environment = os.environ if env is None else env
    base_ref = _pull_request_base_ref(root, environment)
    if base_ref is None:
        return findings

    changed = _session_state_changed_in_pr(root, base_ref)
    if changed is not False:
        return findings

    freshness = _base_freshness(root, base_ref)
    if freshness is None:
        return findings
    ahead, known_sha = freshness

    adjusted: list[workspace_verify.Finding] = []
    for finding in findings:
        if finding.check != "session_state_freshness":
            adjusted.append(finding)
            continue

        if ahead <= 1:
            continue

        details = (
            f"catalog/session_state.json is {ahead} commit(s) behind the authoritative "
            f"PR base {base_ref} (last recorded: {known_sha}); feature/synthetic merge "
            "commits are excluded from handoff freshness."
        )
        if ahead >= workspace_verify.SESSION_STATE_BLOCKING_COMMITS:
            adjusted.append(replace(finding, details=details, severity="error", blocking=True))
        else:
            adjusted.append(replace(finding, details=details, severity="warning", blocking=False))
    return adjusted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Aurora workspace verification with PR-aware session-state freshness semantics."
    )
    parser.add_argument("--root", default=None)
    parser.add_argument("--check-determinism", action="store_true")
    parser.add_argument("--exercise-relocation", action="store_true")
    parser.add_argument("--report-out", default=None)
    args = parser.parse_args()

    root = workspace_verify.resolve_root(args.root)
    findings = workspace_verify.run_checks(
        root,
        include_determinism=args.check_determinism,
        include_relocation_rehearsal=args.exercise_relocation,
    )
    findings = adjust_pr_session_state_freshness(root, findings)
    report = workspace_verify.build_report(root, "ci", findings)

    if args.report_out:
        workspace_verify.write_json(Path(args.report_out), report)
    else:
        print(json.dumps(report, indent=2))

    return 1 if any(finding.blocking for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
