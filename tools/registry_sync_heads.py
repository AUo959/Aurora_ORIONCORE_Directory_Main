#!/usr/bin/env python3
"""Refresh nested-repo `head_sha` pins in catalog/repo_registry.yaml.

The `repo_head_match` gate in workspace_verify blocks commits when a nested
repo's actual HEAD differs from its registry pin. That gate is deliberate — it
catches nested repos moving unnoticed — but refreshing the pin by hand after an
*intentional* nested commit is pure toil. This tool does exactly that refresh
and nothing else.

Scope discipline: only `head_sha` values are rewritten, by surgical line edit,
so YAML formatting, folded `validation_command` blocks, and every other field
are preserved byte-for-byte. Unlike `workspace_scan.py`, this does not
regenerate the manifest, inventory, or workspace map.

Repos whose pin is `~pending~`/`~remote~`, or whose path is absent or not a git
repo, are reported as skipped and never modified.

Usage:
    python3 tools/registry_sync_heads.py            # apply (default)
    python3 tools/registry_sync_heads.py --check    # report only; exit 1 on drift
    python3 tools/registry_sync_heads.py --json     # machine-readable report

Exit codes: 0 = no drift (or drift applied), 1 = drift found in --check mode,
2 = execution error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "catalog" / "repo_registry.yaml"
PLACEHOLDER = re.compile(r"^~.*~$")


def git(args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True,
        env={"GIT_OPTIONAL_LOCKS": "0", "PATH": _path()},
    )


def _path():
    import os
    return os.environ.get("PATH", "/usr/bin:/bin:/usr/local/bin")


def parse_registry(text):
    """Yield (repo_name, field, value, line_index) for repo block scalars.

    Hand-rolled rather than yaml.safe_load + dump: round-tripping through PyYAML
    reflows the folded validation_command blocks and reorders keys, producing a
    huge diff for a 40-character change.
    """
    repos = {}
    order = []
    current = None
    for i, line in enumerate(text.splitlines()):
        m = re.match(r"^- name:\s*(.+?)\s*$", line)
        if m:
            current = m.group(1)
            repos[current] = {"_line_name": i}
            order.append(current)
            continue
        if current is None:
            continue
        m = re.match(r"^  (\w+):\s*(.*?)\s*$", line)
        if m:
            key, val = m.group(1), m.group(2)
            repos[current][key] = val
            repos[current][f"_line_{key}"] = i
    return repos, order


def commits_between(repo_path, old, new):
    """How far the pin lags, when both commits are present locally."""
    r = git(["rev-list", "--count", f"{old}..{new}"], cwd=repo_path)
    if r.returncode != 0:
        return None
    try:
        return int(r.stdout.strip())
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="report drift without writing; exit 1 if any pin is stale")
    ap.add_argument("--json", action="store_true", help="emit a JSON report")
    args = ap.parse_args()

    if not REGISTRY.exists():
        print(f"ERROR: {REGISTRY} not found", file=sys.stderr)
        return 2

    text = REGISTRY.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    repos, order = parse_registry(text)

    drifted, skipped, ok = [], [], []
    for name in order:
        entry = repos[name]
        pinned = entry.get("head_sha", "")
        rel = entry.get("path", "")
        repo_dir = (ROOT / rel) if rel else None

        if not rel or PLACEHOLDER.match(pinned or ""):
            skipped.append({"repo": name, "reason": "placeholder pin or no local path"})
            continue
        if repo_dir is None or not (repo_dir / ".git").exists():
            skipped.append({"repo": name, "reason": "path missing or not a git repo"})
            continue

        head = git(["rev-parse", "HEAD"], cwd=repo_dir)
        if head.returncode != 0:
            skipped.append({"repo": name, "reason": "git rev-parse failed"})
            continue
        actual = head.stdout.strip()

        if actual == pinned:
            ok.append(name)
            continue

        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir).stdout.strip()
        ahead = commits_between(repo_dir, pinned, actual)
        drifted.append({
            "repo": name, "path": rel, "pinned": pinned, "actual": actual,
            "branch": branch, "pin_behind_by": ahead,
            "line": entry.get("_line_head_sha"),
        })

    if drifted and not args.check:
        for d in drifted:
            i = d["line"]
            lines[i] = re.sub(r"(head_sha:\s*).*", rf"\g<1>{d['actual']}", lines[i])
        REGISTRY.write_text("".join(lines), encoding="utf-8")

    if args.json:
        print(json.dumps({
            "registry": str(REGISTRY.relative_to(ROOT)),
            "mode": "check" if args.check else "apply",
            "in_sync": ok, "skipped": skipped, "drifted": drifted,
        }, indent=2))
    else:
        verb = "STALE" if args.check else "UPDATED"
        print(f"registry-sync: {len(ok)} in sync, {len(drifted)} drifted, "
              f"{len(skipped)} skipped")
        for d in drifted:
            behind = (f" (pin {d['pin_behind_by']} commit(s) behind)"
                      if d["pin_behind_by"] else "")
            print(f"  [{verb}] {d['repo']} @{d['branch']}{behind}")
            print(f"      {d['pinned'][:12]} -> {d['actual'][:12]}")
        for s in skipped:
            print(f"  [skipped ] {s['repo']}: {s['reason']}")
        if drifted and not args.check:
            print("\nPins refreshed. Commit catalog/repo_registry.yaml with your changes.")
        elif drifted:
            print("\nRun `make registry-sync` to refresh these pins.")

    return 1 if (drifted and args.check) else 0


if __name__ == "__main__":
    sys.exit(main())
