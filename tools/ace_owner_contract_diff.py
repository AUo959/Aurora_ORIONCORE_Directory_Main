#!/usr/bin/env python3
"""Decide whether a CloudBank baseline move changes the ACE owner contract.

Why this exists
---------------
`catalog/ace/policies/orion_progression_v0_13.json` pins CloudBank twice: a
repository SHA and the exact git blob SHA of `simulation/l1_runtime.py`. When
CloudBank's `main` advances past the pinned commit, `registered_cloudbank()`
fails closed and the Orion progression test goes red. The question that then
has to be answered is *not* "are the SHAs equal" — it is "did anything the
contract depends on actually change".

Answering that by eye is where this goes wrong. The obvious check is whether the
four named methods (`preflight`, `load_run`, `advance`, `export_state`) are
unchanged. That check is necessary and **not sufficient**, and this tool exists
because it produced a false "safe" verdict once already.

The 2026-08-20 case
-------------------
Bumping `9c34d8e9` -> `a19870a5` spans exactly one commit, `18fed59d`
("feat(l1): add governed staffing runtime", CloudBank #1501): 272 insertions,
**zero deletions**. All four contract methods are byte-identical.

But one pre-existing helper changed. `_validate_loaded_state` gained a single
line — `self._validate_loaded_staffing(state)` — and that helper is on
`load_run`'s call path. The new validation raises `PreflightError` when
`world_state["population"]` is not a dict, so `load_run` became strictly more
demanding of persisted state while its own source stayed identical. With
`require_existing_run: true` and `require_resume_ready: true`, that could have
broken resume for runs written before the change.

It did not, but only as a matter of fact rather than of construction: all four
runs under `~/.aurora/l1-runs` carry `world_state.population` as a dict, and an
absent `staffing` key deserialises via `from_payload(None)` to an empty ledger
whose `validate()` passes. That is an empirical finding about live data, and it
is why this tool reports the delta instead of returning a bare boolean — the
person doing the bump still has to look at what changed and check it against
whatever state actually exists.

Usage
-----
    python3 tools/ace_owner_contract_diff.py <old_sha> <new_sha>
    python3 tools/ace_owner_contract_diff.py --from-policy <new_sha>
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOUDBANK = (
    REPO_ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture"
    / "aurora-cloudbank-symbolic-main"
)
POLICY = REPO_ROOT / "catalog" / "ace" / "policies" / "orion_progression_v0_13.json"

#: The methods the policy names explicitly.
CONTRACT_METHODS = ("preflight", "load_run", "advance", "export_state")


def _policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def _source_at(rev: str, path: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(CLOUDBANK), "show", f"{rev}:{path}"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def _methods(src: str, class_name: str) -> dict[str, str]:
    tree = ast.parse(src)
    lines = src.splitlines()
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[item.name] = "\n".join(
                        lines[item.lineno - 1: item.end_lineno]
                    )
    return out


def compare(old_rev: str, new_rev: str) -> dict:
    policy = _policy()
    path = str(policy["owner"]["path"])
    class_name = str(policy["owner"]["class"])

    old = _methods(_source_at(old_rev, path), class_name)
    new = _methods(_source_at(new_rev, path), class_name)

    carried = sorted(set(old) & set(new))
    return {
        "path": path,
        "class": class_name,
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "named_changed": [
            m for m in CONTRACT_METHODS
            if m in old and m in new and old[m] != new[m]
        ],
        "named_missing": [
            m for m in CONTRACT_METHODS if m not in old or m not in new
        ],
        # The check that matters most: a named method can be byte-identical and
        # still change behaviour through a helper it calls.
        "helpers_changed": [m for m in carried if old[m] != new[m]
                            and m not in CONTRACT_METHODS],
        "compared": len(carried),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("old", nargs="?", help="baseline SHA (default: policy pin)")
    ap.add_argument("new", help="candidate SHA")
    ap.add_argument("--from-policy", action="store_true",
                    help="use the policy's current pin as the baseline")
    args = ap.parse_args()

    old = _policy()["cloudbank_repository_sha"] if args.from_policy else args.old
    if not old:
        ap.error("provide an old SHA or pass --from-policy")

    r = compare(old, args.new)

    print(f"{r['class']} in {r['path']}")
    print(f"  {old[:12]} -> {args.new[:12]}")
    print(f"  methods added   : {len(r['added'])}")
    print(f"  methods removed : {len(r['removed'])}")
    print(f"  compared        : {r['compared']} pre-existing")
    print()
    for m in CONTRACT_METHODS:
        if m in r["named_missing"]:
            status = "MISSING"
        elif m in r["named_changed"]:
            status = "CHANGED"
        else:
            status = "identical"
        print(f"    {m:<14} {status}")
    print()

    blocking = r["named_changed"] or r["named_missing"] or r["removed"]
    if blocking:
        print("CONTRACT CHANGED — a named method or a removal is involved.")
        return 2
    if r["helpers_changed"]:
        print("REVIEW REQUIRED — named methods are identical, but these helpers "
              "on their call paths changed:")
        for m in r["helpers_changed"]:
            print(f"    {m}")
        print()
        print("Byte-identical entry points do not imply unchanged behaviour. "
              "Inspect each helper and check it against the persisted runs that "
              "actually exist before bumping the pin.")
        return 1
    print("CONTRACT UNCHANGED — additive only, no helper drift.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
