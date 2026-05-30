#!/usr/bin/env python3
"""THREADCORE governance scan CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Local script import path support
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from threadcore_report import render_markdown  # noqa: E402
from threadcore_rules import DEFAULT_CANONICAL_ROOTS, scan_repo  # noqa: E402


def _parse_roots(raw_roots: str | None) -> list[str]:
    if not raw_roots:
        return list(DEFAULT_CANONICAL_ROOTS)
    roots = [item.strip() for item in raw_roots.split(",") if item.strip()]
    if not roots:
        return list(DEFAULT_CANONICAL_ROOTS)
    return roots


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate THREADCORE artifacts with deterministic rules.")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--roots", help="Optional CSV list of scan roots (absolute or repo-relative)")
    parser.add_argument(
        "--strictness",
        choices=["balanced", "strict", "lenient"],
        default="balanced",
        help="Validation strictness profile",
    )
    parser.add_argument("--out-json", required=True, help="Path to write machine-readable findings JSON")
    parser.add_argument("--out-md", required=True, help="Path to write markdown diagnostics report")
    parser.add_argument("--emit-l3-bridge", help="Optional path to write standalone L3 bridge JSON")
    parser.add_argument(
        "--fail-on-block",
        action="store_true",
        help="Return non-zero if any BLOCK findings are present",
    )
    args = parser.parse_args()

    roots = _parse_roots(args.roots)
    report = scan_repo(repo_root=args.repo, roots=roots, strictness=args.strictness)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")

    if args.emit_l3_bridge:
        bridge_path = Path(args.emit_l3_bridge)
        bridge_path.parent.mkdir(parents=True, exist_ok=True)
        bridge_path.write_text(
            json.dumps(report.get("l3_bridge", {}), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    block_count = report["summary"]["by_severity"].get("BLOCK", 0)
    if args.fail_on_block and block_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
