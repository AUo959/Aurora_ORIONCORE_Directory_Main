#!/usr/bin/env python3
"""Render markdown diagnostics from THREADCORE governance scan JSON."""

from __future__ import annotations

import json
from typing import Any


def _rows(findings: list[dict[str, Any]], severity: str) -> list[dict[str, Any]]:
    return [f for f in findings if f.get("severity") == severity]


def _render_finding_list(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "- None"
    lines = []
    for row in rows:
        lines.append(
            f"- [{row['rule_id']}] `{row['file']}`: {row['message']}"
            f"\n  Suggested fix: {row['suggested_fix']}"
        )
    return "\n".join(lines)


def _render_patch_plan(findings: list[dict[str, Any]]) -> str:
    ordered = [f for f in findings if f.get("severity") in {"BLOCK", "WARN"}]
    unique = []
    seen = set()
    for item in ordered:
        fix = item.get("suggested_fix", "")
        if fix and fix not in seen:
            seen.add(fix)
            unique.append(fix)

    if not unique:
        return "1. No patch actions required."

    return "\n".join(f"{idx}. {fix}" for idx, fix in enumerate(unique, start=1))


def render_markdown(report: dict[str, Any]) -> str:
    findings = report.get("findings", [])
    block_rows = _rows(findings, "BLOCK")
    warn_rows = _rows(findings, "WARN")

    bridge = report.get("l3_bridge", {})
    bridge_preview = json.dumps(bridge, indent=2, ensure_ascii=False)

    lines = []
    lines.append("# THREADCORE Governance Report")
    lines.append("")

    lines.append("## Scope")
    lines.append(f"- Repo: `{report['scan_meta']['repo']}`")
    lines.append(f"- Strictness: `{report['scan_meta']['strictness']}`")
    lines.append("- Roots:")
    for root in report["scan_meta"]["roots"]:
        lines.append(f"- `{root}`")
    lines.append(f"- Total artifacts: {report['summary']['total_artifacts']}")
    lines.append(f"- Total findings: {report['summary']['total_findings']}")
    lines.append("")

    lines.append("## Blocking Findings")
    lines.append(_render_finding_list(block_rows))
    lines.append("")

    lines.append("## Warnings")
    lines.append(_render_finding_list(warn_rows))
    lines.append("")

    lines.append("## Suggested Patch Plan")
    lines.append(_render_patch_plan(findings))
    lines.append("")

    lines.append("## L3 Bridge Preview")
    lines.append("```json")
    lines.append(bridge_preview)
    lines.append("```")

    return "\n".join(lines) + "\n"
