#!/usr/bin/env python3
"""ZIPWIZ governance scan CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from zipwiz_report import render_markdown  # noqa: E402
from zipwiz_rules import DEFAULT_CANONICAL_ROOTS, DEFAULT_REFERENCE_ROOTS, scan_repo  # noqa: E402


def _parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return list(default)
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or list(default)


def _build_diagnostic_matrix(
    repo: str, roots: list[str], reference_roots: list[str], warn_threshold: int | None = None
) -> dict:
    matrix: dict[str, dict] = {}
    runs = [
        ("balanced", "balanced", True),
        ("strict", "strict", True),
        ("lenient", "lenient", True),
        ("balanced_no_evolution", "balanced", False),
    ]

    for key, strictness, include_evolution in runs:
        report = scan_repo(
            repo_root=repo,
            roots=roots,
            reference_roots=reference_roots,
            strictness=strictness,
            include_evolution=include_evolution,
        )
        findings = report.get("findings", [])
        top_rules = Counter(f["rule_id"] for f in findings).most_common(10)
        top_warn_rules = Counter(f["rule_id"] for f in findings if f.get("severity") == "WARN").most_common(10)
        warn_count = report.get("summary", {}).get("by_severity", {}).get("WARN", 0)
        matrix[key] = {
            "strictness": strictness,
            "include_evolution": include_evolution,
            "summary": report.get("summary", {}),
            "top_rules": [{"rule_id": rid, "count": count} for rid, count in top_rules],
            "top_warn_rules": [{"rule_id": rid, "count": count} for rid, count in top_warn_rules],
            "warn_summary": {
                "warn_count": warn_count,
                "warn_threshold": warn_threshold,
                "warn_threshold_exceeded": bool(
                    warn_threshold is not None and warn_count > warn_threshold
                ),
            },
        }

    return matrix


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ZIPWIZ artifacts with deterministic governance checks."
    )
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--roots", help="Optional CSV list of canonical scan roots")
    parser.add_argument("--reference-roots", help="Optional CSV list of reference-only roots")
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
        "--include-evolution",
        action="store_true",
        default=True,
        help="Include ZIPWIZ evolution timeline extraction (default: enabled)",
    )
    parser.add_argument(
        "--no-include-evolution",
        dest="include_evolution",
        action="store_false",
        help="Disable ZIPWIZ evolution timeline extraction",
    )
    parser.add_argument(
        "--diagnostic-mode",
        action="store_true",
        help="Run balanced/strict/lenient/no-evolution matrix and print summary JSON",
    )
    parser.add_argument(
        "--diagnostic-json",
        help="Optional path to write diagnostic matrix JSON (used with --diagnostic-mode)",
    )
    parser.add_argument(
        "--warn-threshold",
        type=int,
        help="Optional warning threshold for diagnostic-mode summaries",
    )
    parser.add_argument(
        "--fail-on-block",
        action="store_true",
        help="Return non-zero if any BLOCK findings are present",
    )
    args = parser.parse_args()

    roots = _parse_csv(args.roots, DEFAULT_CANONICAL_ROOTS)
    reference_roots = _parse_csv(args.reference_roots, DEFAULT_REFERENCE_ROOTS)

    report = scan_repo(
        repo_root=args.repo,
        roots=roots,
        reference_roots=reference_roots,
        strictness=args.strictness,
        include_evolution=args.include_evolution,
    )

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")

    if args.emit_l3_bridge:
        out_bridge = Path(args.emit_l3_bridge)
        out_bridge.parent.mkdir(parents=True, exist_ok=True)
        out_bridge.write_text(
            json.dumps(report.get("l3_bridge", {}), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if args.diagnostic_mode:
        diagnostic_matrix = _build_diagnostic_matrix(
            args.repo,
            roots,
            reference_roots,
            warn_threshold=args.warn_threshold,
        )
        payload = {
            "diagnostic_meta": {"warn_threshold": args.warn_threshold},
            "diagnostic_matrix": diagnostic_matrix,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if args.diagnostic_json:
            out_diag = Path(args.diagnostic_json)
            out_diag.parent.mkdir(parents=True, exist_ok=True)
            out_diag.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    block_count = report["summary"]["by_severity"].get("BLOCK", 0)
    if args.fail_on_block and block_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
