#!/usr/bin/env python3
"""Aurora root Mission Control aggregator.

This tool converts existing root-control-plane reports into an operator inbox
and readiness lanes. It is read-only unless the caller explicitly asks to write
the generated report, and it never promotes canon, executes runtime commands,
sends mesh messages, installs packages, or mutates nested repositories.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import aurora_devkit
import aurora_integration_gate
import aurora_recommendation_engine
import workspace_recovery_index
import workspace_verify
from _workspace_common import now_iso_utc, serialized_root, write_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "mission_control_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "aurora_mission_control_latest.json"

INBOX_FIELDS = (
    "item_id",
    "title",
    "category",
    "priority",
    "source",
    "target_repo",
    "owner_surface",
    "evidence_refs",
    "recommended_next_action",
    "suggested_commands",
    "approval_required",
    "mutation_posture",
    "blocking",
    "status",
)

DEFAULT_SOURCE_IDS = [
    "workspace_verify",
    "integration_gate",
    "recovery_index",
    "devkit",
    "recommendations",
    "git_status",
]

DEFAULT_BUILD_LANES = [
    {
        "lane_id": "root-python-control-tools",
        "title": "Root Python control-plane tooling",
        "required_tools": ["python3", "uv", "sqlite3"],
        "recommended_tools": ["pre-commit", "ruff", "mypy"],
        "next_action": "Use this lane for root CLIs, report generators, validators, and receipt tooling.",
    },
    {
        "lane_id": "frontend-dashboard",
        "title": "Local frontend dashboard",
        "required_tools": ["node", "npm", "corepack", "pnpm"],
        "recommended_tools": [],
        "next_action": "Use this lane for a localhost-only Vite dashboard after a CLI/report contract is stable.",
    },
    {
        "lane_id": "containerized-services",
        "title": "Containerized local services",
        "required_tools": ["docker"],
        "recommended_tools": [],
        "next_action": "Use this lane for devcontainers and reproducible local service stacks.",
    },
    {
        "lane_id": "apple-platforms",
        "title": "Apple platform build checks",
        "required_tools": ["xcodebuild"],
        "recommended_tools": [],
        "next_action": "Use this lane for macOS/iOS feasibility checks and simulator-backed validation.",
    },
    {
        "lane_id": "systems-tools",
        "title": "Systems helper tooling",
        "required_tools": ["rust", "go"],
        "recommended_tools": [],
        "next_action": "Use this lane for high-performance local helpers only after a root contract exists.",
    },
    {
        "lane_id": "github-maintenance",
        "title": "GitHub maintenance and CI triage",
        "required_tools": ["git", "gh"],
        "recommended_tools": [],
        "next_action": "Use this lane for root or explicitly named nested-repo PR/issue/CI workflows.",
    },
]

Collector = Callable[[Path, dict[str, Any]], dict[str, Any]]


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Mission Control manifest must be a JSON object: {path}")
    return payload


def source_ids(manifest: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for item in manifest.get("sources", []):
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict) and item.get("id") and item.get("enabled", True):
            ids.append(str(item["id"]))
    return ids or DEFAULT_SOURCE_IDS


def collect_workspace_verify(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    findings = workspace_verify.run_checks(
        root,
        include_determinism=False,
        include_relocation_rehearsal=False,
    )
    return workspace_verify.build_report(root, "mission_control", findings)


def collect_integration_gate(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del root, manifest
    return aurora_integration_gate.build_report(run_subprocess=False)


def collect_recovery_index(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    return workspace_recovery_index.build_report(
        root,
        root / "catalog" / "recovery_index_manifest.json",
    )


def collect_devkit(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    return aurora_devkit.build_report(
        root,
        root / "catalog" / "dev_toolkit_manifest.json",
        aurora_devkit.DEFAULT_SKILLS_ROOT,
        aurora_devkit.DEFAULT_AUTOMATIONS_ROOT,
    )


def collect_recommendations(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    del manifest
    return aurora_recommendation_engine.build_report(
        root,
        root / "catalog" / "recommendation_engine_manifest.json",
    )


def collect_git_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    return aurora_recommendation_engine.collect_git_status(root, manifest)


DEFAULT_COLLECTORS: dict[str, Collector] = {
    "workspace_verify": collect_workspace_verify,
    "integration_gate": collect_integration_gate,
    "recovery_index": collect_recovery_index,
    "devkit": collect_devkit,
    "recommendations": collect_recommendations,
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


def toolchain_by_id(devkit_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in devkit_report.get("toolchain", [])
        if isinstance(item, dict) and item.get("id")
    }


def build_lanes(devkit_report: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    toolchain = toolchain_by_id(devkit_report)
    lane_defs = manifest.get("build_lanes") or DEFAULT_BUILD_LANES
    lanes: list[dict[str, Any]] = []
    for lane in lane_defs:
        if not isinstance(lane, dict):
            continue
        required = [str(item) for item in lane.get("required_tools", [])]
        recommended = [str(item) for item in lane.get("recommended_tools", [])]
        missing_required = [
            tool_id
            for tool_id in required
            if toolchain.get(tool_id, {}).get("status") != "ok"
        ]
        missing_recommended = [
            tool_id
            for tool_id in recommended
            if toolchain.get(tool_id, {}).get("status") != "ok"
        ]
        if missing_required:
            status = "blocked"
        elif missing_recommended:
            status = "attention"
        else:
            status = "ready"
        lanes.append(
            {
                "lane_id": str(lane.get("lane_id", "unnamed-lane")),
                "title": str(lane.get("title", "Unnamed readiness lane")),
                "status": status,
                "required_tools": required,
                "recommended_tools": recommended,
                "missing_required_tools": missing_required,
                "missing_recommended_tools": missing_recommended,
                "next_action": str(lane.get("next_action", "")),
                "evidence_refs": ["reports/analysis/aurora_devkit_latest.json"],
                "mutation_posture": "readiness_only",
            }
        )
    return lanes


def inbox_from_recommendations(report: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    max_refs = int(manifest.get("max_evidence_refs", 12))
    out: list[dict[str, Any]] = []
    for item in report.get("recommendations", []):
        if not isinstance(item, dict):
            continue
        evidence_refs = [str(ref) for ref in item.get("evidence_refs", [])[:max_refs]]
        title = str(item.get("title", ""))
        category = str(item.get("category", "recommendation"))
        if category == "recovery_review" and "restricted" in title.lower():
            evidence_refs = [
                "reports/analysis/workspace_recovery_index_latest.json::restricted_recovery_candidates_metadata"
            ]
        record = {
            "item_id": str(item.get("recommendation_id", "recommendation")).replace("aurora-rec", "mission"),
            "title": title,
            "category": category,
            "priority": str(item.get("priority", "P3")),
            "source": str(item.get("source", "recommendations")),
            "target_repo": str(item.get("target_repo", "root")),
            "owner_surface": str(item.get("owner_surface", "")),
            "evidence_refs": evidence_refs,
            "recommended_next_action": str(item.get("recommended_next_action", "")),
            "suggested_commands": [str(command) for command in item.get("suggested_commands", [])],
            "approval_required": bool(item.get("approval_required", False)),
            "mutation_posture": "advisory_only",
            "blocking": bool(item.get("blocking", False)),
            "status": str(item.get("status", "open")),
        }
        assert set(record) == set(INBOX_FIELDS)
        out.append(record)
    return out


def inbox_from_source_errors(
    sources: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    del manifest
    out: list[dict[str, Any]] = []
    for source_id, report in sorted(sources.items()):
        if report.get("status") != "error" and "error" not in report:
            continue
        out.append(
            {
                "item_id": f"mission-p1-source-error-{source_id}",
                "title": f"Mission Control source failed: {source_id}",
                "category": "validation",
                "priority": "P1",
                "source": source_id,
                "target_repo": "root",
                "owner_surface": "root control-plane repo",
                "evidence_refs": [str(report.get("error", "unknown collector error"))],
                "recommended_next_action": "Repair the source collector or its input artifact before treating the Mission Control report as complete.",
                "suggested_commands": ["python3 tools/aurora_mission_control.py --summary"],
                "approval_required": False,
                "mutation_posture": "advisory_only",
                "blocking": False,
                "status": "open",
            }
        )
    return out


def sort_and_limit_inbox(items: list[dict[str, Any]], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    status_rank = {"blocked": 0, "open": 1, "informational": 2}
    sorted_items = sorted(
        items,
        key=lambda item: (
            priority_rank.get(item["priority"], 9),
            status_rank.get(item["status"], 9),
            not item["blocking"],
            item["category"],
            item["source"],
            item["item_id"],
        ),
    )
    return sorted_items[: int(manifest.get("max_inbox_items", 12))]


def build_operator_inbox(
    sources: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    out = inbox_from_source_errors(sources, manifest)
    recommendations = sources.get("recommendations", {})
    if recommendations and "error" not in recommendations:
        out.extend(inbox_from_recommendations(recommendations, manifest))
    return sort_and_limit_inbox(out, manifest)


def source_summary(name: str, report: dict[str, Any]) -> dict[str, Any]:
    if "error" in report:
        return {"status": "error", "error": report.get("error")}
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
        candidates = [item for item in report.get("candidates", []) if isinstance(item, dict)]
        return {
            "status": report.get("status"),
            "candidate_count": report.get("summary", {}).get("candidate_count"),
            "discovered_candidate_count": report.get("summary", {}).get("discovered_candidate_count"),
            "restricted_candidate_count": sum(1 for item in candidates if item.get("restricted_material_possible")),
        }
    if name == "devkit":
        toolchain = [item for item in report.get("toolchain", []) if isinstance(item, dict)]
        return {
            "status": report.get("status"),
            "tools_ok": sum(1 for item in toolchain if item.get("status") == "ok"),
            "tools_total": len(toolchain),
            "finding_count": len(report.get("findings", [])),
            "install_plan_items": len(report.get("install_plan", [])),
        }
    if name == "recommendations":
        summary = report.get("summary", {})
        return {
            "status": report.get("status"),
            "recommendation_count": summary.get("recommendation_count"),
            "blocking_count": summary.get("blocking_count"),
            "approval_required_count": summary.get("approval_required_count"),
        }
    if name == "git_status":
        return {
            "status": report.get("status"),
            "changed_path_count": len(report.get("changed_paths", [])),
            "branch": report.get("branch", ""),
        }
    return {"status": report.get("status", "unknown")}


def summarize_lanes(lanes: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(item["status"] for item in lanes)
    return {
        "ready": counts.get("ready", 0),
        "attention": counts.get("attention", 0),
        "blocked": counts.get("blocked", 0),
    }


def summarize_inbox(inbox: list[dict[str, Any]]) -> dict[str, Any]:
    by_priority = Counter(item["priority"] for item in inbox)
    by_category = Counter(item["category"] for item in inbox)
    by_status = Counter(item["status"] for item in inbox)
    return {
        "operator_inbox_count": len(inbox),
        "blocking_count": sum(1 for item in inbox if item["blocking"]),
        "approval_required_count": sum(1 for item in inbox if item["approval_required"]),
        "by_priority": dict(sorted(by_priority.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_status": dict(sorted(by_status.items())),
    }


def report_status(inbox: list[dict[str, Any]], lanes: list[dict[str, Any]]) -> str:
    if any(item["blocking"] or item["priority"] == "P0" for item in inbox):
        return "blocked"
    if any(item["status"] == "blocked" for item in lanes):
        return "blocked"
    if inbox or any(item["status"] == "attention" for item in lanes):
        return "attention"
    return "ready"


def manifest_relative_path(root: Path, manifest_path: Path) -> str:
    resolved_root = root.resolve()
    resolved_manifest = manifest_path.resolve()
    if resolved_manifest.is_relative_to(resolved_root):
        return resolved_manifest.relative_to(resolved_root).as_posix()
    return str(resolved_manifest)


def build_report(
    root: Path,
    manifest_path: Path,
    collectors: dict[str, Collector] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    sources = collect_sources(root, manifest, collectors=collectors)
    inbox = build_operator_inbox(sources, manifest)
    lanes = build_lanes(sources.get("devkit", {}), manifest)
    lane_summary = summarize_lanes(lanes)
    inbox_summary = summarize_inbox(inbox)
    source_error_count = sum(1 for report in sources.values() if report.get("status") == "error" or "error" in report)
    return {
        "schema_version": 1,
        "generated_at": generated_at or now_iso_utc(),
        "root": serialized_root(root),
        "tool": "aurora_mission_control",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "manifest_path": manifest_relative_path(root, manifest_path),
        "status": report_status(inbox, lanes),
        "summary": {
            "source_count": len(sources),
            "source_error_count": source_error_count,
            **inbox_summary,
            "build_lanes": lane_summary,
        },
        "source_reports": {
            name: source_summary(name, source_report)
            for name, source_report in sources.items()
        },
        "build_lanes": lanes,
        "operator_inbox": inbox,
        "validation_commands": manifest.get("validation_commands", []),
    }


def format_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lanes = summary["build_lanes"]
    lines = [
        f"Aurora Mission Control: {report['status']}",
        f"- Run mode: {report['run_mode']}",
        f"- Mutation posture: {report['mutation_posture']}",
        f"- Nested repo mutation: {report['nested_repo_mutation']}",
        f"- Sources: {summary['source_count']} (errors: {summary['source_error_count']})",
        f"- Operator inbox: {summary['operator_inbox_count']} (blocking: {summary['blocking_count']}, approval required: {summary['approval_required_count']})",
        f"- Build lanes: {lanes['ready']} ready, {lanes['attention']} attention, {lanes['blocked']} blocked",
    ]
    if report["operator_inbox"]:
        lines.append("- Top inbox:")
        for item in report["operator_inbox"][:8]:
            lines.append(f"  - [{item['priority']}] {item['category']}: {item['title']}")
    else:
        lines.append("- Top inbox: none")
    ready_lanes = [item for item in report["build_lanes"] if item["status"] == "ready"]
    if ready_lanes:
        lines.append("- Ready lanes:")
        for lane in ready_lanes[:6]:
            lines.append(f"  - {lane['lane_id']}: {lane['title']}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Aurora root Mission Control report.")
    parser.add_argument("--root", default=str(ROOT), help="Aurora root workspace path.")
    parser.add_argument("--manifest", help="Mission Control manifest path. Defaults to <root>/catalog/mission_control_manifest.json.")
    parser.add_argument("--summary", action="store_true", help="Print a compact text summary instead of JSON.")
    parser.add_argument("--persist-report", action="store_true", help="Write reports/analysis/aurora_mission_control_latest.json.")
    parser.add_argument("--report-out", help="Write the JSON report to this path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else root / "catalog" / "mission_control_manifest.json"
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
