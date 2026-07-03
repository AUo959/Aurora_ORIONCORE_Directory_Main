#!/usr/bin/env python3
"""Build a read-only Aurora operator-console snapshot.

This tool aggregates existing root reports and registered-repo marker files into
one compact JSON payload for a local operator UI. It does not refresh source
reports, execute runtime commands, mutate nested repos, or promote canon.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_REPORT_PATH = Path("reports/analysis/aurora_operator_snapshot_latest.json")

SOURCE_REPORTS = [
    {
        "id": "mission_control",
        "title": "Mission Control",
        "path": "reports/analysis/aurora_mission_control_latest.json",
        "summary_keys": ["source_count", "operator_inbox_count", "blocking_count", "build_lanes"],
    },
    {
        "id": "devkit",
        "title": "Developer Toolkit",
        "path": "reports/analysis/aurora_devkit_latest.json",
        "summary_keys": [],
    },
    {
        "id": "stack_validation",
        "title": "CloudBank Stack Validation",
        "path": "reports/analysis/aurora_stack_validation_latest.json",
        "summary_keys": ["required_ready", "required_total", "endpoint_ready", "endpoint_total", "gpu_profile_status"],
    },
    {
        "id": "command_intent_snapshot",
        "title": "Command Intent Snapshot",
        "path": "reports/analysis/aurora_command_intent_snapshot_latest.json",
        "summary_keys": [
            "total_commands",
            "valid_count",
            "invalid_count",
            "not_validated_count",
            "warning_count",
            "simulated_count",
            "live_execution_count",
        ],
    },
    {
        "id": "simulation_readiness",
        "title": "Simulation Readiness",
        "path": "reports/analysis/aurora_simulation_readiness_latest.json",
        "summary_keys": [
            "surface_count",
            "required_surface_count",
            "ready_surface_count",
            "attention_surface_count",
            "blocked_surface_count",
            "ready_required_surface_count",
            "blocked_required_surface_count",
            "execution_path_count",
            "available_execution_path_count",
            "persisted_output_turn",
            "primary_event_ledger_records",
            "smoke_probe_status",
            "smoke_probe_requested",
        ],
    },
    {
        "id": "demo_readiness",
        "title": "Docker Demo Readiness",
        "path": "reports/analysis/aurora_demo_readiness_latest.json",
        "summary_keys": [
            "gate_count",
            "required_gate_count",
            "optional_gate_count",
            "ready_gate_count",
            "attention_gate_count",
            "blocked_gate_count",
            "required_ready",
            "required_total",
            "optional_ready",
            "optional_total",
        ],
    },
    {
        "id": "kubernetes_readiness",
        "title": "Kubernetes Readiness",
        "path": "reports/analysis/aurora_kubernetes_readiness_latest.json",
        "summary_keys": [
            "gate_count",
            "required_gate_count",
            "optional_gate_count",
            "ready_gate_count",
            "attention_gate_count",
            "blocked_gate_count",
            "required_ready",
            "required_total",
            "optional_ready",
            "optional_total",
            "manifest_file_count",
            "resource_count",
            "kind_counts",
            "finding_count",
            "apply_blocker_count",
            "informational_finding_count",
            "apply_blocker_category_counts",
        ],
    },
    {
        "id": "recommendations",
        "title": "Recommendations",
        "path": "reports/analysis/aurora_recommendations_latest.json",
        "summary_keys": ["recommendation_count", "blocking_count", "approval_required_count"],
    },
    {
        "id": "confidence_audit",
        "title": "Confidence Audit",
        "path": "reports/analysis/aurora_confidence_audit_latest.json",
        "summary_keys": ["record_count", "user_alert_count", "below_threshold_count", "verdict"],
    },
    {
        "id": "recovery_index",
        "title": "Recovery Index",
        "path": "reports/analysis/workspace_recovery_index_latest.json",
        "summary_keys": ["candidate_count", "discovered_candidate_count", "candidate_limit_applied"],
    },
]

CLOUDBANK_PATH = Path("GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    last_decode_error: Optional[json.JSONDecodeError] = None
    for attempt in range(2):
        try:
            return json.loads(path.read_text(encoding="utf-8")), None
        except FileNotFoundError:
            return None, "missing"
        except json.JSONDecodeError as exc:
            last_decode_error = exc
            if attempt == 0:
                time.sleep(0.05)
                continue
        except OSError as exc:
            return None, f"unreadable: {exc}"
    assert last_decode_error is not None
    return None, f"invalid_json: {last_decode_error.msg}"


def normalize_status(value: Any) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    if text in {"ready", "pass", "passed", "ok", "clean"}:
        return "ready"
    if text in {"blocked", "fail", "failed", "error", "unhealthy"}:
        return "blocked"
    if text in {"warn", "warning", "attention", "open", "dirty", "degraded"}:
        return "attention"
    return text or "unknown"


def worst_status(statuses: Iterable[str]) -> str:
    ordered = list(statuses)
    if any(status == "blocked" for status in ordered):
        return "blocked"
    if any(status in {"attention", "missing", "unknown"} for status in ordered):
        return "attention"
    return "ready"


def compact_summary(data: dict[str, Any], summary_keys: list[str]) -> dict[str, Any]:
    summary = data.get("summary")
    if isinstance(summary, dict):
        if summary_keys:
            return {key: summary.get(key) for key in summary_keys if key in summary}
        return summary

    out: dict[str, Any] = {}
    for key in ("status", "verdict", "generated_at"):
        if key in data:
            out[key] = data[key]
    return out


def source_record(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    report_path = root / spec["path"]
    data, error = read_json(report_path)
    if data is None:
        return {
            "id": spec["id"],
            "title": spec["title"],
            "path": spec["path"],
            "available": False,
            "status": "missing",
            "generated_at": None,
            "summary": {},
            "error": error,
        }

    raw_status = data.get("status", data.get("verdict"))
    return {
        "id": spec["id"],
        "title": spec["title"],
        "path": spec["path"],
        "available": True,
        "status": normalize_status(raw_status),
        "raw_status": raw_status,
        "generated_at": data.get("generated_at"),
        "summary": compact_summary(data, list(spec.get("summary_keys", []))),
    }


def load_source_reports(root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    reports = [source_record(root, spec) for spec in SOURCE_REPORTS]
    data_by_id: dict[str, dict[str, Any]] = {}
    for spec in SOURCE_REPORTS:
        data, _ = read_json(root / spec["path"])
        if data is not None:
            data_by_id[spec["id"]] = data
    return reports, data_by_id


def compact_inbox_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id") or item.get("recommendation_id"),
        "title": item.get("title"),
        "priority": item.get("priority"),
        "category": item.get("category"),
        "status": item.get("status"),
        "target_repo": item.get("target_repo"),
        "approval_required": item.get("approval_required"),
        "recommended_next_action": item.get("recommended_next_action"),
    }


def collect_operator_items(data_by_id: dict[str, dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    mission_items = data_by_id.get("mission_control", {}).get("operator_inbox", [])
    if isinstance(mission_items, list):
        items.extend(compact_inbox_item(item) for item in mission_items[:limit] if isinstance(item, dict))

    recommendations = data_by_id.get("recommendations", {}).get("recommendations", [])
    if isinstance(recommendations, list):
        items.extend(compact_inbox_item(item) for item in recommendations[:limit] if isinstance(item, dict))

    return items[:limit]


def devkit_registered_env(data_by_id: dict[str, dict[str, Any]], repo_name: str) -> Optional[dict[str, Any]]:
    envs = data_by_id.get("devkit", {}).get("registered_python_environments", [])
    if not isinstance(envs, list):
        return None
    for env in envs:
        if isinstance(env, dict) and env.get("repo_name") == repo_name:
            return {
                "repo_name": env.get("repo_name"),
                "status": normalize_status(env.get("status")),
                "raw_status": env.get("status"),
                "path": env.get("path"),
                "resolved_path": env.get("resolved_path"),
                "path_resolution": env.get("path_resolution"),
                "evidence": env.get("evidence"),
                "status_file_state": env.get("status_file_state"),
                "notes": env.get("notes"),
            }
    return None


def file_marker(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    return {"path": rel, "exists": path.exists()}


def cloudbank_runtime_lane(root: Path, data_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    markers = [
        file_marker(root, (CLOUDBANK_PATH / "docker-compose.yml").as_posix()),
        file_marker(root, (CLOUDBANK_PATH / "api/aurora_gui_cloudhub_fastapi.py").as_posix()),
        file_marker(root, (CLOUDBANK_PATH / "static/aurora-simulation-console.html").as_posix()),
        file_marker(root, (CLOUDBANK_PATH / "static/synergy-dashboard.html").as_posix()),
        file_marker(root, (CLOUDBANK_PATH / "services/command_node/index.js").as_posix()),
        file_marker(root, (CLOUDBANK_PATH / "services/nemo_service/README.md").as_posix()),
    ]
    marker_status = "ready" if all(marker["exists"] for marker in markers) else "attention"
    env = devkit_registered_env(data_by_id, "aurora-cloudbank-symbolic-main")
    env_status = env["status"] if env else "unknown"
    stack_report = data_by_id.get("stack_validation", {})
    stack_status = normalize_status(stack_report.get("status")) if stack_report else "unknown"
    stack_summary = stack_report.get("summary") if isinstance(stack_report.get("summary"), dict) else {}
    stack_services = stack_report.get("services") if isinstance(stack_report.get("services"), list) else []
    return {
        "lane_id": "cloudbank-docker-runtime",
        "title": "CloudBank Docker runtime",
        "status": worst_status([marker_status, env_status, stack_status]),
        "repo": "aurora-cloudbank-symbolic-main",
        "path": CLOUDBANK_PATH.as_posix(),
        "markers": markers,
        "registered_python_environment": env,
        "stack_validation": {
            "available": bool(stack_report),
            "status": stack_status,
            "generated_at": stack_report.get("generated_at"),
            "summary": stack_summary,
            "services": [
                {
                    "service": service.get("service"),
                    "status": service.get("status"),
                    "running": service.get("running"),
                    "health": service.get("health"),
                    "profile": service.get("profile"),
                }
                for service in stack_services
                if isinstance(service, dict)
            ],
        },
        "validated_local_ports": [
            {"service": "aurora_gui", "url": "http://127.0.0.1:8080", "source": "docker-compose.yml"},
            {"service": "command_node", "url": "http://127.0.0.1:3001", "source": "docker-compose.yml"},
        ],
        "gpu_profile": {
            "service": "nemo_service",
            "profile": "gpu",
            "status": "gated",
            "note": "Displayed as a capability lane; not assumed available without Docker/GPU verification.",
        },
    }


def root_control_lane(source_reports: list[dict[str, Any]]) -> dict[str, Any]:
    root_sources = [source for source in source_reports if source["id"] not in {"devkit", "stack_validation"}]
    return {
        "lane_id": "root-control-plane",
        "title": "Root control-plane reports",
        "status": worst_status(source["status"] for source in root_sources),
        "source_report_ids": [source["id"] for source in root_sources],
        "mutation_posture": "advisory_only",
    }


def command_intent_lane(root: Path, data_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    markers = [
        file_marker(root, "tools/aurora_command_intent.py"),
        file_marker(root, "tools/aurora_command_intent_snapshot.py"),
        file_marker(root, (CLOUDBANK_PATH / "src/aurora/core/command_grammar").as_posix()),
        file_marker(
            root,
            "plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json",
        ),
    ]
    marker_status = "ready" if all(marker["exists"] for marker in markers) else "attention"
    snapshot_report = data_by_id.get("command_intent_snapshot", {})
    snapshot_status = normalize_status(snapshot_report.get("status")) if snapshot_report else "missing"
    snapshot_summary = snapshot_report.get("summary") if isinstance(snapshot_report.get("summary"), dict) else {}
    return {
        "lane_id": "command-intent-parse-simulate",
        "title": "Command intent gateway",
        "status": worst_status([marker_status, snapshot_status]),
        "markers": markers,
        "command_intent_snapshot": {
            "available": bool(snapshot_report),
            "status": snapshot_status,
            "generated_at": snapshot_report.get("generated_at"),
            "summary": snapshot_summary,
        },
        "execution_boundary": "parse_and_in_process_simulation_only",
        "live_runtime_execution": False,
    }


def simulation_readiness_lane(data_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = data_by_id.get("simulation_readiness", {})
    status = normalize_status(report.get("status")) if report else "missing"
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    surfaces = report.get("simulation_surfaces") if isinstance(report.get("simulation_surfaces"), list) else []
    paths = report.get("execution_paths") if isinstance(report.get("execution_paths"), list) else []
    smoke_probe = report.get("smoke_probe") if isinstance(report.get("smoke_probe"), dict) else {}
    artifacts = report.get("artifact_evidence") if isinstance(report.get("artifact_evidence"), dict) else {}
    return {
        "lane_id": "simulation-runtime-readiness",
        "title": "Simulation runtime readiness",
        "status": status,
        "simulation_readiness": {
            "available": bool(report),
            "status": status,
            "generated_at": report.get("generated_at"),
            "summary": summary,
            "surfaces": [
                {
                    "surface_id": surface.get("surface_id"),
                    "title": surface.get("title"),
                    "role": surface.get("role"),
                    "repo": surface.get("repo"),
                    "status": surface.get("status"),
                    "required": surface.get("required"),
                    "execution_boundary": surface.get("execution_boundary"),
                }
                for surface in surfaces[:8]
                if isinstance(surface, dict)
            ],
            "execution_paths": [
                {
                    "path_id": path.get("path_id"),
                    "title": path.get("title"),
                    "status": path.get("status"),
                    "writes_to_repo": path.get("writes_to_repo"),
                    "nested_repo_mutation": path.get("nested_repo_mutation"),
                }
                for path in paths[:6]
                if isinstance(path, dict)
            ],
            "artifact_evidence": artifacts,
            "smoke_probe": smoke_probe,
        },
        "execution_boundary": "inventory_plus_bounded_local_simulation_smoke",
        "live_runtime_execution": False,
    }


def demo_readiness_lane(data_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = data_by_id.get("demo_readiness", {})
    status = normalize_status(report.get("status")) if report else "missing"
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    gates = report.get("gates") if isinstance(report.get("gates"), list) else []
    return {
        "lane_id": "docker-demo-readiness",
        "title": "Docker demo readiness",
        "status": status,
        "demo_readiness": {
            "available": bool(report),
            "status": status,
            "generated_at": report.get("generated_at"),
            "summary": summary,
            "gates": [
                {
                    "gate_id": gate.get("gate_id"),
                    "title": gate.get("title"),
                    "status": gate.get("status"),
                    "required": gate.get("required"),
                }
                for gate in gates
                if isinstance(gate, dict)
            ],
        },
        "execution_boundary": "readiness_receipt_from_persisted_reports_only",
        "live_runtime_execution": False,
    }


def kubernetes_readiness_lane(data_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = data_by_id.get("kubernetes_readiness", {})
    status = normalize_status(report.get("status")) if report else "missing"
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    cluster_probe = report.get("cluster_probe") if isinstance(report.get("cluster_probe"), dict) else {}
    apply_blockers = report.get("apply_blockers") if isinstance(report.get("apply_blockers"), list) else []
    remediation_plan = report.get("remediation_plan") if isinstance(report.get("remediation_plan"), list) else []
    return {
        "lane_id": "kubernetes-readiness",
        "title": "Kubernetes readiness",
        "status": status,
        "kubernetes_readiness": {
            "available": bool(report),
            "status": status,
            "generated_at": report.get("generated_at"),
            "summary": summary,
            "cluster_probe": cluster_probe,
            "apply_blockers": apply_blockers[:12],
            "apply_blocker_total": len(apply_blockers),
            "remediation_plan": remediation_plan,
        },
        "execution_boundary": "manifest_and_client_readiness_only",
        "live_runtime_execution": False,
    }


def canon_lane(root: Path) -> dict[str, Any]:
    readme_rel = "GUMAS_SIM_2.5/CanonRec/canon/L1/station/operational_library_v2_2/README.md"
    readme_path = root / readme_rel
    status_hint = "unknown"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8", errors="replace")
        status_hint = "staging" if "STAGING" in text else "present"
    return {
        "lane_id": "canonrec-staging",
        "title": "CanonRec station canon staging",
        "status": "attention" if status_hint == "staging" else "ready",
        "repo": "CanonRec",
        "marker": file_marker(root, readme_rel),
        "status_hint": status_hint,
        "promotion_boundary": "owner_promotion_required",
    }


def duelsim_lane(root: Path) -> dict[str, Any]:
    base = Path("GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0")
    markers = [
        file_marker(root, (base / "app_server.py").as_posix()),
        file_marker(root, (base / "scripts/release_gate_v2_4_1.py").as_posix()),
        file_marker(root, (base / "README.md").as_posix()),
    ]
    return {
        "lane_id": "duelsim-release-gate",
        "title": "DuelSim app and release gate",
        "status": "ready" if all(marker["exists"] for marker in markers) else "attention",
        "repo": "DuelSim_v2.0",
        "markers": markers,
    }


def qgia_lane(root: Path) -> dict[str, Any]:
    markers = [
        file_marker(root, "qgia-knowledge-library-main/data/intake/evidence-ledger.jsonl"),
        file_marker(root, "qgia-knowledge-library-main/data/truth/outcome-ledger.jsonl"),
        file_marker(root, "qgia-knowledge-spine-main/data/forecasts/forecast-ledger.jsonl"),
        file_marker(root, "qgia-knowledge-spine-main/data/priors/prior-table.json"),
        file_marker(root, "qgia-knowledge-spine-main/data/calibration/calibration-report.json"),
    ]
    return {
        "lane_id": "qgia-closed-loop-bootstrap",
        "title": "QGIA closed-loop bootstrap ledgers",
        "status": "ready" if all(marker["exists"] for marker in markers) else "attention",
        "repos": ["qgia-knowledge-library-main", "qgia-knowledge-spine-main"],
        "markers": markers,
        "runtime_claim": "bootstrap_artifacts_present_only",
    }


def build_lanes(root: Path, source_reports: list[dict[str, Any]], data_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        root_control_lane(source_reports),
        simulation_readiness_lane(data_by_id),
        demo_readiness_lane(data_by_id),
        kubernetes_readiness_lane(data_by_id),
        cloudbank_runtime_lane(root, data_by_id),
        command_intent_lane(root, data_by_id),
        canon_lane(root),
        duelsim_lane(root),
        qgia_lane(root),
    ]


def recommended_actions(source_reports: list[dict[str, Any]], lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    missing_reports = [source for source in source_reports if not source["available"]]
    if missing_reports:
        actions.append(
            {
                "priority": "P1",
                "title": "Refresh missing root source reports",
                "detail": "One or more operator snapshot inputs are missing.",
                "source_ids": [source["id"] for source in missing_reports],
                "suggested_commands": [
                    "make mission-control-report",
                    "make recommendations-report",
                    "make devkit-report",
                    "make stack-validation-report",
                    "make command-intent-snapshot-report",
                    "make simulation-readiness-report",
                    "make demo-readiness-report",
                    "make kubernetes-readiness-report",
                    "make confidence-audit-report",
                    "make recovery-report",
                ],
            }
        )

    blocked_lanes = [lane for lane in lanes if lane["status"] == "blocked"]
    if blocked_lanes:
        actions.append(
            {
                "priority": "P0",
                "title": "Resolve blocked operator lanes",
                "detail": "A source report or registered runtime lane is blocked.",
                "lane_ids": [lane["lane_id"] for lane in blocked_lanes],
            }
        )

    attention_lanes = [lane for lane in lanes if lane["status"] == "attention"]
    if attention_lanes:
        actions.append(
            {
                "priority": "P2",
                "title": "Review attention lanes before treating the console as green",
                "detail": "Attention can mean advisory work, staging status, missing optional evidence, or stale reports.",
                "lane_ids": [lane["lane_id"] for lane in attention_lanes],
            }
        )

    return actions


def build_snapshot(root: Path, generated_at: Optional[str] = None) -> dict[str, Any]:
    source_reports, data_by_id = load_source_reports(root)
    lanes = build_lanes(root, source_reports, data_by_id)
    items = collect_operator_items(data_by_id)
    actions = recommended_actions(source_reports, lanes)
    status = worst_status([*(source["status"] for source in source_reports), *(lane["status"] for lane in lanes)])
    return {
        "schema_version": 1,
        "tool": "aurora_operator_snapshot",
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "status": status,
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "live_runtime_execution": False,
        "summary": {
            "source_report_count": len(source_reports),
            "available_source_report_count": sum(1 for source in source_reports if source["available"]),
            "lane_count": len(lanes),
            "operator_item_count": len(items),
            "recommended_action_count": len(actions),
        },
        "source_reports": source_reports,
        "operator_items": items,
        "lanes": lanes,
        "recommended_actions": actions,
        "validation_commands": [
            "python3 tools/aurora_stack_validation.py --persist-report",
            "python3 tools/aurora_command_intent_snapshot.py --persist-report",
            "python3 tools/aurora_simulation_readiness.py --persist-report",
            "python3 tools/aurora_demo_readiness.py --persist-report",
            "python3 tools/aurora_kubernetes_readiness.py --persist-report",
            "python3 tools/aurora_operator_snapshot.py --summary",
            "python3 tools/aurora_operator_snapshot.py --persist-report",
            "python3 -m pytest -q tests/test_aurora_simulation_readiness.py tests/test_aurora_kubernetes_readiness.py tests/test_aurora_demo_readiness.py tests/test_aurora_command_intent_snapshot.py tests/test_aurora_operator_snapshot.py",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"status: {payload['status']}")
    print(f"source_reports: {summary['available_source_report_count']}/{summary['source_report_count']}")
    print(f"lanes: {summary['lane_count']}")
    print(f"operator_items: {summary['operator_item_count']}")
    print(f"recommended_actions: {summary['recommended_action_count']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Aurora operator-console snapshot.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--report-out", help="Write the snapshot to this path.")
    parser.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT_PATH}.")
    parser.add_argument("--summary", action="store_true", help="Print a concise summary instead of JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = build_snapshot(root)

    if args.persist_report:
        write_report(root / DEFAULT_REPORT_PATH, payload)
    if args.report_out:
        write_report(Path(args.report_out), payload)

    if args.summary:
        print_summary(payload)
    elif args.json or not (args.persist_report or args.report_out):
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
