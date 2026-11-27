#!/usr/bin/env python3
"""Classify unlanded branches by what content is genuinely absent from main.

Why this is not "check whether the issue is closed"
---------------------------------------------------
A closed issue says the *problem* was resolved. It does not say this branch's
work is what resolved it, or that the branch holds nothing else. Issues get
closed by a different PR, by being reframed, or administratively, while the
branch still carries work that never landed. Retiring on issue state alone is
deciding without reading — the failure mode this workspace keeps correcting
(the GUMAS v2.0 package, the 37 markdown blobs, the 1,044-claim prose ledger
were all "already exhausted" until someone read them).

So this tool answers a narrower, checkable question: **what is on this branch
that is not in main?** It classifies; it does not judge. Judgement needs a
human reading the diffs this points at.

The three signals
-----------------
``git cherry`` detects patch-equivalence, so it catches work that landed via
rebase or cherry-pick under a different SHA. It does *not* reliably catch
squash-merges, where one upstream commit absorbs many branch commits.

So the decisive signal is the three-dot diff, ``git diff main...branch``: the
net content on the branch since the merge base. Empty means the branch adds
nothing to main no matter how its commits are shaped — squash-merge included.
Non-empty means there is real content to read.

``main_touched_same_files`` is a supersession *hint*, not a verdict. Main having
edited the same files since the merge base means a conflict is likely and the
branch may have been overtaken — or it may mean the branch fixes something main
then modified around. Only reading tells you which.

Usage
-----
    python3 tools/branch_salvage_triage.py                 # all repos
    python3 tools/branch_salvage_triage.py --repo root
    python3 tools/branch_salvage_triage.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REPOS = {
    "root": REPO_ROOT,
    "aurora-cloudbank-symbolic-main": REPO_ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture" / "aurora-cloudbank-symbolic-main",
    "CanonRec": REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec",
    "qgia-knowledge-library-main": REPO_ROOT / "qgia-knowledge-library-main",
    "qgia-knowledge-spine-main": REPO_ROOT / "qgia-knowledge-spine-main",
}

PROTECTED = {"main", "master", "HEAD"}


def git(repo: Path, *args, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=False, timeout=timeout)


def classify(repo: Path, branch: str, base: str = "origin/main") -> dict:
    result: dict = {"branch": branch}

    merge_base = git(repo, "merge-base", base, branch).stdout.strip()
    if not merge_base:
        return {**result, "class": "NO_MERGE_BASE"}
    result["merge_base"] = merge_base[:12]

    # Patch-equivalence: '+' commits are not upstream, '-' already are.
    cherry = git(repo, "cherry", base, branch).stdout.splitlines()
    result["commits_not_upstream"] = sum(1 for c in cherry if c.startswith("+"))
    result["commits_already_upstream"] = sum(1 for c in cherry if c.startswith("-"))

    # The decisive signal — net content on the branch that main lacks.
    diff = git(repo, "diff", "--numstat", f"{base}...{branch}").stdout.splitlines()
    files, added, removed = [], 0, 0
    for line in diff:
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, r, path = parts
        files.append(path)
        added += int(a) if a.isdigit() else 0
        removed += int(r) if r.isdigit() else 0
    result["unique_files"] = len(files)
    result["unique_added"] = added
    result["unique_removed"] = removed
    result["files"] = files[:40]

    if not files:
        result["class"] = "ALREADY_IN_MAIN"
        return result

    # Has main modified the same files since the merge base? Hint only.
    main_changed = set(
        git(repo, "diff", "--name-only", f"{merge_base}..{base}").stdout.splitlines()
    )
    overlap = sorted(set(files) & main_changed)
    result["main_touched_same_files"] = len(overlap)
    result["overlap_files"] = overlap[:20]
    result["class"] = "UNIQUE_OVERLAPPING" if overlap else "UNIQUE_CLEAN"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--json", dest="as_json")
    args = ap.parse_args()

    names = [args.repo] if args.repo else list(REPOS)
    everything: dict[str, list] = {}

    for name in names:
        repo = REPOS[name]
        if not (repo / ".git").exists():
            continue
        git(repo, "fetch", "origin", "main", "--quiet", timeout=180)
        heads = [
            line for line in
            git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.splitlines()
            if line and line not in PROTECTED
        ]
        rows = [classify(repo, b) for b in heads]
        everything[name] = rows

        counts: dict[str, int] = {}
        for row in rows:
            counts[row["class"]] = counts.get(row["class"], 0) + 1
        print(f"\n=== {name}: {len(rows)} branches ===")
        for cls, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {n:4d}  {cls}")

        salvageable = [r for r in rows if r["class"].startswith("UNIQUE")]
        if salvageable:
            print(f"\n  {'branch':<62} {'files':>5} {'+':>6} {'-':>6} {'ovlp':>5}")
            for r in sorted(salvageable, key=lambda r: -r["unique_added"]):
                print(f"  {r['branch']:<62} {r['unique_files']:5d} "
                      f"{r['unique_added']:6d} {r['unique_removed']:6d} "
                      f"{r.get('main_touched_same_files', 0):5d}")

    if args.as_json:
        Path(args.as_json).write_text(json.dumps(everything, indent=2), encoding="utf-8")
        print(f"\nwrote {args.as_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
