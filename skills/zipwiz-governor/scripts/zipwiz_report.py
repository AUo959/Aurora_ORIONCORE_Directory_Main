#!/usr/bin/env python3
"""Render markdown diagnostics from ZIPWIZ governance scan JSON."""

from __future__ import annotations

import json
from typing import Any


def _rows(findings: list[dict[str, Any]], severity: str) -> list[dict[str, Any]]:
    return [row for row in findings if row.get("severity") == severity]


def _render_finding_list(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "- None"
    lines: list[str] = []
    for row in rows:
        lines.append(
            f"- [{row['rule_id']}] `{row['file']}` ({row['family']}): {row['message']}"
            f"\n  Suggested fix: {row['suggested_fix']}"
            f"\n  Routing hint: {row.get('routing_hint', 'N/A')}"
        )
    return "\n".join(lines)


def _render_patch_plan(findings: list[dict[str, Any]]) -> str:
    actions: list[str] = []
    seen = set()
    for finding in findings:
        if finding.get("severity") not in {"BLOCK", "WARN"}:
            continue
        fix = finding.get("suggested_fix", "").strip()
        if not fix or fix in seen:
            continue
        seen.add(fix)
        actions.append(fix)

    if not actions:
        return "1. No patch actions required."

    return "\n".join(f"{idx}. {item}" for idx, item in enumerate(actions, start=1))


def _render_evolution(events: list[dict[str, Any]]) -> str:
    if not events:
        return "- None"
    lines: list[str] = []
    for event in events:
        date_value = event.get("date") or "unknown-date"
        version = event.get("version") or "unknown-version"
        signal = event.get("signal_type") or "evidence_doc"
        source = event.get("source_file") or "unknown-source"
        summary = event.get("summary") or "ZIPWIZ evidence"
        lines.append(f"- `{date_value}` `{version}` [{signal}] `{source}`\n  {summary}")
    return "\n".join(lines)


def _render_routing(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "- None"
    lines = []
    for row in rows:
        lines.append(
            f"- `{row.get('skill', 'unknown')}`: {row.get('when', 'N/A')}"
            f"\n  Reason: {row.get('reason', 'N/A')}"
        )
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    findings = report.get("findings", [])
    block_rows = _rows(findings, "BLOCK")
    warn_rows = _rows(findings, "WARN")
    events = report.get("evolution_map", [])

    bridge_preview = json.dumps(report.get("l3_bridge", {}), indent=2, ensure_ascii=False)

    lines: list[str] = []
    lines.append("# ZIPWIZ Governance Report")
    lines.append("")

    lines.append("## Scope")
    lines.append(f"- Repo: `{report['scan_meta']['repo']}`")
    lines.append(f"- Strictness: `{report['scan_meta']['strictness']}`")
    lines.append(f"- Include evolution: `{report['scan_meta']['include_evolution']}`")
    lines.append("- Canonical roots:")
    for root in report["scan_meta"]["roots"]:
        lines.append(f"- `{root}`")
    lines.append("- Reference roots:")
    for root in report["scan_meta"]["reference_roots"]:
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

    lines.append("## Evolution Timeline")
    lines.append(_render_evolution(events))
    lines.append("")

    lines.append("## Suggested Patch Plan")
    lines.append(_render_patch_plan(findings))
    lines.append("")

    lines.append("## Cross-Skill Routing")
    lines.append(_render_routing(report.get("cross_skill_routing", [])))
    lines.append("")

    lines.append("## L3 Bridge Preview")
    lines.append("```json")
    lines.append(bridge_preview)
    lines.append("```")

    return "\n".join(lines) + "\n"
