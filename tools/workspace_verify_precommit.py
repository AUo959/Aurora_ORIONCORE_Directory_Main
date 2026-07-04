#!/usr/bin/env python3
"""workspace_verify_precommit.py — self-healing pre-commit gate wrapper.

Field finding 2026-07-04: twice in one day a commit was blocked because a
generated surface (workspace manifest / repo registry) drifted after a
legitimate change, and both times the only correct response was identical:
run workspace_scan.py, stage the regenerated surfaces, retry. When every
blocking finding is one of those regenerable classes, this wrapper does
exactly that — regenerate, stage, re-verify — and only fails the commit if
verification still finds problems. Non-regenerable findings (or any mix
including one) fail immediately with the original output: this wrapper
never papers over a real problem.

Happy path runs verify once and touches nothing, so there is no
generated-surface churn on ordinary commits.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Finding checks whose one-and-only fix is regenerating the surfaces.
REGENERABLE_CHECKS = {
    "manifest_top_level_coverage",
    "repo_head_match",
    "repo_branch_match",
}

GENERATED_SURFACES = [
    "catalog/workspace_manifest.yaml",
    "catalog/repo_registry.yaml",
    "catalog/archive_inventory.jsonl",
    "docs/workspace-map.md",
    "reports/analysis/workspace_scan_summary.json",
]


def _run_verify() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "workspace_verify.py")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    return result.returncode, result.stdout


def _blocking_checks(verify_stdout: str) -> set[str] | None:
    """Names of blocking findings, or None if output is unparseable."""
    try:
        report = json.loads(verify_stdout)
    except json.JSONDecodeError:
        return None
    return {
        f.get("check", "?") for f in report.get("findings", [])
        if f.get("blocking")
    }


def main() -> int:
    code, out = _run_verify()
    blocking = _blocking_checks(out)
    if blocking is not None and not blocking:
        return 0
    if blocking is None or not blocking.issubset(REGENERABLE_CHECKS):
        # Real (or unparseable) failure — show it, fail, change nothing.
        print(out)
        return code or 1

    print(f"[pre-commit] blocking findings {sorted(blocking)} are all "
          "regenerable — running workspace_scan and staging surfaces...")
    scan = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "workspace_scan.py")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if scan.returncode != 0:
        print(scan.stdout, scan.stderr)
        return 1
    subprocess.run(["git", "add", *GENERATED_SURFACES],
                   capture_output=True, cwd=REPO_ROOT)

    code, out = _run_verify()
    blocking = _blocking_checks(out)
    if blocking is not None and not blocking:
        print("[pre-commit] surfaces regenerated and staged; verify clean.")
        return 0
    print(out)
    return code or 1


if __name__ == "__main__":
    raise SystemExit(main())
