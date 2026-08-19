#!/usr/bin/env python3
"""Materialise the nested-repo workspace from `catalog/repo_registry.yaml`.

The control plane vendors its nested repos as ordinary working clones that the
root `.gitignore` excludes (`/*` and `/GUMAS_SIM_2.5/*`). Nothing in the tree
records how to recreate them, so a fresh clone of this repository produces a
workspace whose registry references five paths that do not exist and whose
`repo_head_match` / `repo_branch_match` gates cannot run at all.

This tool closes that loop: for every registry entry with a real local `path`
and a `remote_url`, it clones the repo if absent, then checks out the recorded
`head_sha`. The registry becomes the operative link rather than documentation of
one. It is deliberately compatible with a later move to submodules — the pins it
reads are the same pins `tools/registry_sync_heads.py` writes.

Placeholder paths (`~remote~`, `~sibling~/...`, `.`) and placeholder pins
(`~pending~`, `~untracked~`, `~self~`) are skipped and reported.

Usage:
    python3 tools/registry_bootstrap.py --check    # report only; exit 1 if work is needed
    python3 tools/registry_bootstrap.py            # clone and checkout
    python3 tools/registry_bootstrap.py --json     # machine-readable report

Exit codes: 0 = workspace matches the registry, 1 = drift found in --check mode,
2 = execution error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "catalog" / "repo_registry.yaml"
PLACEHOLDER = re.compile(r"^~.*~")

# Nested clones must never inherit the control plane's git environment.
GIT_ENV_STRIP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX")


def git(args, cwd=None):
    import os

    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_STRIP}
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, env=env
    )


def actionable(entry):
    """Return (path, url, sha, branch) when the entry describes a real local clone."""
    path = str(entry.get("path", ""))
    url = entry.get("remote_url")
    sha = str(entry.get("head_sha", ""))
    if not url or not path or path == "." or PLACEHOLDER.match(path):
        return None
    if PLACEHOLDER.match(sha):
        return None
    return path, url, sha, str(entry.get("branch", "main"))


def inspect(entry):
    got = actionable(entry)
    if got is None:
        return {"name": entry.get("name"), "state": "skipped",
                "reason": "placeholder path/pin or no remote_url"}
    path, url, sha, branch = got
    target = ROOT / path
    if not (target / ".git").exists():
        return {"name": entry.get("name"), "state": "missing", "path": path,
                "remote_url": url, "head_sha": sha, "branch": branch}
    head = git(["rev-parse", "HEAD"], cwd=target)
    if head.returncode != 0:
        return {"name": entry.get("name"), "state": "unreadable", "path": path,
                "detail": head.stderr.strip()}
    actual = head.stdout.strip()
    return {"name": entry.get("name"),
            "state": "in_sync" if actual == sha else "wrong_commit",
            "path": path, "remote_url": url,
            "head_sha": sha, "actual_sha": actual, "branch": branch}


def materialise(record):
    target = ROOT / record["path"]
    if record["state"] == "missing":
        target.parent.mkdir(parents=True, exist_ok=True)
        clone = git(["clone", record["remote_url"], str(target)])
        if clone.returncode != 0:
            return f"clone failed: {clone.stderr.strip()}"
    fetch = git(["fetch", "--all", "--tags"], cwd=target)
    if fetch.returncode != 0:
        return f"fetch failed: {fetch.stderr.strip()}"
    out = git(["checkout", record["head_sha"]], cwd=target)
    if out.returncode != 0:
        return f"checkout failed: {out.stderr.strip()}"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="report only; exit 1 when the workspace does not match the registry")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    args = ap.parse_args()

    try:
        registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"registry-bootstrap: cannot read {REGISTRY}: {exc}", file=sys.stderr)
        return 2

    records = [inspect(e) for e in registry.get("repos", [])]
    needs_work = [r for r in records if r["state"] in ("missing", "wrong_commit")]

    if not args.check:
        for record in needs_work:
            err = materialise(record)
            record["result"] = err or "materialised"
            if err:
                record["state"] = "failed"

    if args.json:
        print(json.dumps({"records": records}, indent=2))
    else:
        counts = {}
        for r in records:
            counts[r["state"]] = counts.get(r["state"], 0) + 1
        print("registry-bootstrap: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
        for r in records:
            if r["state"] == "skipped":
                print(f"  [skipped ] {r['name']}: {r['reason']}")
            elif r["state"] == "in_sync":
                print(f"  [ok      ] {r['name']} @ {r['head_sha'][:12]}")
            elif r["state"] == "failed":
                print(f"  [FAILED  ] {r['name']}: {r.get('result')}")
            else:
                verb = "would materialise" if args.check else r.get("result", "materialised")
                detail = r.get("detail") or f"{r['state']} -> {verb}"
                print(f"  [{'drift   ' if args.check else 'fixed   '}] {r['name']} ({r.get('path')}): {detail}")

    if args.check and needs_work:
        print("\nWorkspace does not match the registry. Run `make registry-bootstrap`.")
        return 1
    if any(r["state"] == "failed" for r in records):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
