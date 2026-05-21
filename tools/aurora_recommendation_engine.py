#!/usr/bin/env python3
"""Aurora root recommendation engine.

This tool normalizes existing root-control-plane evidence into ranked,
advisory-only next actions. It does not mutate files unless the caller asks to
write a report, and it never promotes canon, executes runtime commands, sends
mesh messages, or changes nested repositories.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import aurora_devkit
import aurora_integration_gate
import workspace_recovery_index
import workspace_verify
from _workspace_common import now_iso_utc, serialized_root, write_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "recommendation_engine_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "aurora_recommendations_latest.json"

RECOMMENDATION_FIELDS = (
    "recommendation_id",
    "title",
    "category",
    "priority",
    "confidence",
    "target_repo",
    "owner_surface",
    "evidence_refs",
    "source",
    "recommended_next_action",
    "suggested_commands",
    "approval_required",
    "mutation_posture",
    "blocking",
    "status",
)
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
STATUS_RANK = {"blocked": 0, "open": 1, "informational": 2}
VALID_CATEGORIES = {
    "validation",
    "provenance",
    "recovery_review",
    "developer_tooling",
    "integration_gate",
    "git_state",
    "boundary",
}

Collector = Callable[[Path, dict[str, Any]], dict[str, Any]]


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:80] or "item"


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Recommendation manifest must be a JSON object: {path}")
    return payload


def source_ids(manifest: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for item in manifest.get("sources", []):
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict) and item.get("id") and item.get("enabled", True):
            ids.append(str(item["id"]))
    return ids or [
        "workspace_verify",
        "integration_gate",
        "recovery_index",
        "devkit",
        "git_status",
    ]


def cap_refs(refs: list[str], manifest: dict[str, Any]) -> list[str]:
    max_refs = int(manifest.get("max_evidence_refs", 12))
    return [str(ref) for ref in refs if str(ref)][:max_refs]


def recommendation(
    *,
    category: str,
    source: str,
    priority: str,
    title: str,
    recommended_next_action: str,
    target_repo: str = "root",
    owner_surface: str = "root control-plane repo",
    evidence_refs: list[str] | None = None,
    suggested_commands: list[str] | None = None,
    approval_required: bool = False,
    blocking: bool = False,
    status: str = "open",
    confidence: str = "medium",
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Unsupported recommendation category: {category}")
    if priority not in PRIORITY_RANK:
        raise ValueError(f"Unsupported priority: {priority}")
    if confidence not in {"high", "medium", "low"}:
        raise ValueError(f"Unsupported confidence: {confidence}")
    if status not in STATUS_RANK:
        raise ValueError(f"Unsupported status: {status}")
    record = {
        "recommendation_id": f"aurora-rec-{priority.lower()}-{source}-{category}-{slug(title)}",
        "title": title,
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "target_repo": target_repo,
        "owner_surface": owner_surface,
        "evidence_refs": cap_refs(evidence_refs or [], manifest or {}),
        "source": source,
        "recommended_next_action": recommended_next_action,
        "suggested_commands": suggested_commands or [],
        "approval_required": approval_required,
        "mutation_posture": "advisory_only",
        "blocking": blocking,
        "status": status,
    }
    assert set(record) == set(RECOMMENDATION_FIELDS)
    return record


def collect_workspace_verify(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    findings = workspace_verify.run_checks(
        root,
        include_determinism=False,
        include_relocation_rehearsal=False,
    )
    return workspace_verify.build_report(root, "recommendation_engine", findings)


def collect_recovery_index(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    recovery_manifest = root / "catalog" / "recovery_index_manifest.json"
    return workspace_recovery_index.build_report(root, recovery_manifest)


def collect_devkit(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    return aurora_devkit.build_report(
        root,
        root / "catalog" / "dev_toolkit_manifest.json",
        aurora_devkit.DEFAULT_SKILLS_ROOT,
        aurora_devkit.DEFAULT_AUTOMATIONS_ROOT,
    )


def collect_integration_gate(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del root, manifest
    return aurora_integration_gate.build_report(run_subprocess=False)


def clean_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"}
    }


def collect_git_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    result = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env=clean_git_env(),
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    branch_line = lines[0] if lines and lines[0].startswith("## ") else ""
    change_lines = lines[1:] if branch_line else lines
    changed_paths: list[str] = []
    for line in change_lines:
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed_paths.append(path)
    return {
        "status": "dirty" if changed_paths else "clean",
        "returncode": result.returncode,
        "branch": branch_line.removeprefix("## "),
        "changed_paths": sorted(changed_paths),
        "raw": lines,
        "stderr": result.stderr.strip(),
    }


DEFAULT_COLLECTORS: dict[str, Collector] = {
    "workspace_verify": collect_workspace_verify,
    "integration_gate": collect_integration_gate,
    "recovery_index": collect_recovery_index,
    "devkit": collect_devkit,
    "git_status": collect_git_status,
}


def collect_sources(
    root: Path,
    manifest: dict[str, Any],
    collectors: dict[str, Collector] | None = None,
) -> dict[str, dict[str, Any]]:
    active = dict(DEFAULT_COLLECTORS)
    active.update(collectors or {})
    reports: dict[str, dict[str, Any]] = {}
    for source_id in source_ids(manifest):
        collector = active.get(source_id)
        if collector is None:
            reports[source_id] = {
                "status": "error",
                "error": f"No collector registered for source: {source_id}",
            }
            continue
        try:
            reports[source_id] = collector(root, manifest)
        except Exception as exc:  # pragma: no cover - exercised through tests.
            reports[source_id] = {
                "status": "error",
                "error": str(exc),
            }
    return reports


def category_for_workspace_finding(finding: dict[str, Any]) -> str:
    check = str(finding.get("check", ""))
    if check.startswith("repo_") or "registry" in check or "boundary" in check:
        return "boundary"
    return "validation"


def recommendations_from_workspace_verify(
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for finding in report.get("findings", []):
        if not isinstance(finding, dict):
            continue
        blocking = bool(finding.get("blocking"))
        priority = "P0" if blocking else "P1"
        check = str(finding.get("check", "workspace_verify"))
        out.append(
            recommendation(
                category=category_for_workspace_finding(finding),
                source="workspace_verify",
                priority=priority,
                title=f"Resolve workspace verifier finding: {check}",
                evidence_refs=[f"tools/workspace_verify.py::{check}"],
                suggested_commands=["python3 tools/workspace_verify.py"],
                recommended_next_action=str(finding.get("suggested_fix") or "Resolve the verifier finding before relying on downstream recommendations."),
                approval_required=False,
                blocking=blocking,
                status="blocked" if blocking else "open",
                confidence="high",
                manifest=manifest,
            )
        )
    return out


def recommendations_from_integration_gate(
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in list(report.get("checks", [])) + list(report.get("commands", [])):
        if not isinstance(record, dict) or record.get("status") == "pass":
            continue
        status = str(record.get("status", "fail"))
        priority = "P0" if status == "fail" else "P1"
        name = str(record.get("name", "integration_gate"))
        messages = [str(item) for item in record.get("failures", []) or record.get("warnings", [])]
        out.append(
            recommendation(
                category="integration_gate",
                source="integration_gate",
                priority=priority,
                title=f"Resolve integration gate {status}: {name}",
                evidence_refs=[f"tools/aurora_integration_gate.py::{name}"],
                suggested_commands=["python3 tools/aurora_integration_gate.py --summary"],
                recommended_next_action="; ".join(messages) if messages else "Inspect the integration gate record and resolve the reported safety issue.",
                approval_required=False,
                blocking=status == "fail",
                status="blocked" if status == "fail" else "open",
                confidence="high",
                manifest=manifest,
            )
        )
    return out


def recommendations_from_recovery_index(
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    candidates = [item for item in report.get("candidates", []) if isinstance(item, dict)]
    promoted_without_receipt = [
        item
        for item in candidates
        if (
            item.get("promotion_status") != "pending_review"
            or item.get("canonical_status") != "not_promoted"
        )
        and not (item.get("promotion_receipt") or item.get("receipt_ref") or item.get("receipt_refs"))
    ]
    if promoted_without_receipt:
        out.append(
            recommendation(
                category="provenance",
                source="recovery_index",
                priority="P0",
                title="Recovery candidates changed promotion status without receipts",
                evidence_refs=[str(item.get("path", "<unknown>")) for item in promoted_without_receipt],
                suggested_commands=["python3 tools/workspace_recovery_index.py --summary"],
                recommended_next_action="Restore pending_review/not_promoted labels or attach the explicit promotion receipt before treating the material as canonical.",
                approval_required=True,
                blocking=True,
                status="blocked",
                confidence="high",
                manifest=manifest,
            )
        )

    restricted = [item for item in candidates if item.get("restricted_material_possible")]
    if restricted:
        out.append(
            recommendation(
                category="recovery_review",
                source="recovery_index",
                priority="P1",
                title=f"Review {len(restricted)} restricted recovery candidates carefully",
                evidence_refs=[str(item.get("path", "<unknown>")) for item in restricted],
                suggested_commands=["python3 tools/workspace_recovery_index.py --summary"],
                recommended_next_action="Handle restricted candidates through a separate review decision; do not copy them into issues, PRs, or canon surfaces by default.",
                approval_required=True,
                blocking=False,
                status="open",
                confidence="medium",
                manifest=manifest,
            )
        )

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        target = str(item.get("target_repo_hint") or "review-required")
        owner = str(item.get("owner_surface_hint") or "manual recovery review")
        groups[(target, owner)].append(item)

    max_groups = int(manifest.get("max_recovery_groups", 8))
    ranked_groups = sorted(
        groups.items(),
        key=lambda pair: (-len(pair[1]), pair[0][0], pair[0][1]),
    )[:max_groups]
    for (target, owner), items in ranked_groups:
        if not items:
            continue
        out.append(
            recommendation(
                category="recovery_review",
                source="recovery_index",
                priority="P2",
                title=f"Review {len(items)} recovery candidates routed to {target}",
                target_repo=target,
                owner_surface=owner,
                evidence_refs=[str(item.get("path", "<unknown>")) for item in items],
                suggested_commands=[
                    "python3 tools/workspace_recovery_index.py --summary",
                    "python3 tools/workspace_recovery_index.py --persist-report",
                ],
                recommended_next_action="Review candidates as routing evidence only. Do not promote until an owner-surface decision compares canonical state, validates behavior, and leaves a receipt or PR.",
                approval_required=True,
                blocking=False,
                status="open",
                confidence="medium",
                manifest=manifest,
            )
        )
    return out


def install_plan_by_tool(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("tool_id")): item
        for item in report.get("install_plan", [])
        if isinstance(item, dict) and item.get("tool_id")
    }


def tool_id_from_finding_id(finding_id: str) -> str:
    if finding_id.startswith("tool_"):
        parts = finding_id.split("_")
        if len(parts) >= 3:
            return "_".join(parts[1:-1])
    return ""


def recommendations_from_devkit(
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    plan_by_tool = install_plan_by_tool(report)
    for finding in report.get("findings", []):
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity", "warning"))
        finding_id = str(finding.get("id", "devkit_finding"))
        tool_id = tool_id_from_finding_id(finding_id)
        plan = plan_by_tool.get(tool_id, {})
        suggested = []
        for key in ("install_command_text", "update_command_text"):
            if plan.get(key):
                suggested.append(str(plan[key]))
        priority = "P1" if severity == "blocker" else "P2"
        out.append(
            recommendation(
                category="developer_tooling",
                source="devkit",
                priority=priority,
                title=str(finding.get("message") or f"Resolve devkit finding: {finding_id}"),
                evidence_refs=[f"catalog/dev_toolkit_manifest.json::{finding_id}"],
                suggested_commands=suggested or ["python3 tools/aurora_devkit.py --install-plan"],
                recommended_next_action=str(finding.get("next_step") or plan.get("notes") or "Review the devkit finding and apply tooling changes only with explicit approval."),
                approval_required=True,
                blocking=severity == "blocker",
                status="blocked" if plan.get("status") == "blocked" else "open",
                confidence="high",
                manifest=manifest,
            )
        )
    return out


def recommendations_from_git_status(
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    changed_paths = [str(path) for path in report.get("changed_paths", []) if str(path)]
    if report.get("returncode", 0) != 0:
        return [
            recommendation(
                category="git_state",
                source="git_status",
                priority="P1",
                title="Git status could not be read",
                evidence_refs=[str(report.get("stderr", "git status failed"))],
                suggested_commands=["git status --short --branch"],
                recommended_next_action="Repair or inspect the root git checkout before relying on worktree recommendations.",
                approval_required=False,
                blocking=False,
                status="open",
                confidence="medium",
                manifest=manifest,
            )
        ]
    if not changed_paths:
        return []
    return [
        recommendation(
            category="git_state",
            source="git_status",
            priority="P2",
            title=f"Root worktree has {len(changed_paths)} in-progress paths",
            evidence_refs=changed_paths,
            suggested_commands=["git status --short --branch"],
            recommended_next_action="Review ownership before staging or committing. Treat existing command-grammar, integration-gate, and recommendation-engine edits as separate root-control-plane work unless intentionally combined.",
            approval_required=False,
            blocking=False,
            status="informational",
            confidence="high",
            manifest=manifest,
        )
    ]


def recommendations_from_source_error(
    source_id: str,
    report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    if report.get("status") != "error" and "error" not in report:
        return []
    return [
        recommendation(
            category="validation",
            source=source_id,
            priority="P1",
            title=f"Recommendation source failed: {source_id}",
            evidence_refs=[str(report.get("error", "unknown collector error"))],
            suggested_commands=["python3 tools/aurora_recommendation_engine.py --summary"],
            recommended_next_action="Repair the source collector or its input artifact before treating the recommendation set as complete.",
            approval_required=False,
            blocking=False,
            status="open",
            confidence="medium",
            manifest=manifest,
        )
    ]


def build_recommendations(
    sources: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    builders = {
        "workspace_verify": recommendations_from_workspace_verify,
        "integration_gate": recommendations_from_integration_gate,
        "recovery_index": recommendations_from_recovery_index,
        "devkit": recommendations_from_devkit,
        "git_status": recommendations_from_git_status,
    }
    for source_id, report in sources.items():
        out.extend(recommendations_from_source_error(source_id, report, manifest))
        builder = builders.get(source_id)
        if builder and not report.get("error"):
            out.extend(builder(report, manifest))
    return sort_and_limit(out, manifest)


def sort_and_limit(
    recommendations: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    sorted_items = sorted(
        recommendations,
        key=lambda item: (
            PRIORITY_RANK[item["priority"]],
            STATUS_RANK[item["status"]],
            not item["blocking"],
            item["category"],
            item["source"],
            item["recommendation_id"],
        ),
    )
    return sorted_items[: int(manifest.get("max_recommendations", 50))]


def summarize_recommendations(recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    by_priority = Counter(item["priority"] for item in recommendations)
    by_category = Counter(item["category"] for item in recommendations)
    by_status = Counter(item["status"] for item in recommendations)
    return {
        "recommendation_count": len(recommendations),
        "blocking_count": sum(1 for item in recommendations if item["blocking"]),
        "approval_required_count": sum(1 for item in recommendations if item["approval_required"]),
        "by_priority": dict(sorted(by_priority.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_status": dict(sorted(by_status.items())),
    }


def source_summary(name: str, report: dict[str, Any]) -> dict[str, Any]:
    if name == "workspace_verify":
        return {
            "status": report.get("status"),
            "finding_count": report.get("summary", {}).get("finding_count"),
            "blocking_count": report.get("summary", {}).get("blocking_count"),
        }
    if name == "integration_gate":
        return {
            "status": report.get("verdict"),
            "check_count": len(report.get("checks", [])),
            "command_count": len(report.get("commands", [])),
        }
    if name == "recovery_index":
        return {
            "status": report.get("status"),
            "candidate_count": report.get("summary", {}).get("candidate_count"),
            "discovered_candidate_count": report.get("summary", {}).get("discovered_candidate_count"),
        }
    if name == "devkit":
        return {
            "status": report.get("status"),
            "finding_count": len(report.get("findings", [])),
            "install_plan_items": len(report.get("install_plan", [])),
        }
    if name == "git_status":
        return {
            "status": report.get("status"),
            "changed_path_count": len(report.get("changed_paths", [])),
            "branch": report.get("branch", ""),
        }
    return {
        "status": report.get("status"),
        "error": report.get("error"),
    }


def report_status(recommendations: list[dict[str, Any]]) -> str:
    if any(item["priority"] == "P0" for item in recommendations):
        return "blocked"
    if recommendations:
        return "open"
    return "clear"


def build_report(
    root: Path,
    manifest_path: Path,
    collectors: dict[str, Collector] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    sources = collect_sources(root, manifest, collectors=collectors)
    recommendations = build_recommendations(sources, manifest)
    return {
        "schema_version": 1,
        "generated_at": generated_at or now_iso_utc(),
        "root": serialized_root(root),
        "tool": "aurora_recommendation_engine",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "manifest_path": manifest_path.resolve().relative_to(root.resolve()).as_posix()
        if manifest_path.resolve().is_relative_to(root.resolve())
        else str(manifest_path),
        "status": report_status(recommendations),
        "summary": summarize_recommendations(recommendations),
        "source_reports": {
            name: source_summary(name, source_report)
            for name, source_report in sources.items()
        },
        "recommendations": recommendations,
        "validation_commands": manifest.get("validation_commands", []),
    }


def format_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"Aurora Recommendations: {report['status']}",
        f"- Run mode: {report['run_mode']}",
        f"- Mutation posture: {report['mutation_posture']}",
        f"- Nested repo mutation: {report['nested_repo_mutation']}",
        f"- Recommendations: {summary['recommendation_count']}",
        f"- Blocking: {summary['blocking_count']}",
        f"- Approval required: {summary['approval_required_count']}",
    ]
    if report["recommendations"]:
        lines.append("- Top recommendations:")
        for item in report["recommendations"][:8]:
            lines.append(
                f"  - [{item['priority']}] {item['category']}: {item['title']}"
            )
    else:
        lines.append("- Top recommendations: none")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Aurora root advisory recommendations.")
    parser.add_argument("--root", default=str(ROOT), help="Aurora root workspace path.")
    parser.add_argument("--manifest", help="Recommendation manifest path. Defaults to <root>/catalog/recommendation_engine_manifest.json.")
    parser.add_argument("--summary", action="store_true", help="Print a compact text summary instead of JSON.")
    parser.add_argument("--persist-report", action="store_true", help="Write reports/analysis/aurora_recommendations_latest.json.")
    parser.add_argument("--report-out", help="Write the JSON report to this path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else root / "catalog" / "recommendation_engine_manifest.json"
    report = build_report(root, manifest_path)
    manifest = load_manifest(manifest_path)

    if args.persist_report:
        default_report = root / str(manifest.get("default_report_path", DEFAULT_REPORT.relative_to(ROOT)))
        write_json(default_report, report)

    if args.report_out:
        write_json(Path(args.report_out).expanduser().resolve(), report)

    if args.summary:
        print(format_summary(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
