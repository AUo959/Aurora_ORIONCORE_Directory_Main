#!/usr/bin/env python3
"""Build a read-only Aurora Docker demo readiness receipt.

This tool consumes persisted root receipts and turns them into explicit
operator-console gates. It does not call Docker, probe HTTP endpoints, parse
commands, execute runtime handlers, mutate nested repos, or promote canon.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_REPORT_PATH = Path("reports/analysis/aurora_demo_readiness_latest.json")
STACK_REPORT_PATH = Path("reports/analysis/aurora_stack_validation_latest.json")
COMMAND_REPORT_PATH = Path("reports/analysis/aurora_command_intent_snapshot_latest.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc.msg}"
    except OSError as exc:
        return None, f"unreadable: {exc}"


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"ready", "pass", "passed", "ok", "clean", "gated"}:
        return "ready"
    if text in {"blocked", "fail", "failed", "error", "unhealthy"}:
        return "blocked"
    if text in {"attention", "missing", "unknown", "warn", "warning", "open"}:
        return "attention"
    return text or "unknown"


def gate(
    gate_id: str,
    title: str,
    status: str,
    *,
    required: bool,
    evidence: Optional[dict[str, Any]] = None,
    recommended_next_action: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "title": title,
        "status": normalize_status(status),
        "required": required,
        "evidence": evidence or {},
        "recommended_next_action": recommended_next_action,
    }


def endpoint_by_service(stack_report: dict[str, Any], service: str) -> dict[str, Any]:
    endpoints = stack_report.get("endpoints", [])
    if not isinstance(endpoints, list):
        return {}
    for endpoint in endpoints:
        if isinstance(endpoint, dict) and endpoint.get("service") == service:
            return endpoint
    return {}


def stack_gates(root: Path, stack_report: Optional[dict[str, Any]], stack_error: Optional[str]) -> list[dict[str, Any]]:
    if stack_report is None:
        return [
            gate(
                "stack_report_available",
                "Stack validation report is available",
                "attention",
                required=True,
                evidence={"path": STACK_REPORT_PATH.as_posix(), "error": stack_error},
                recommended_next_action="Run make stack-validation-report before demo readiness.",
            )
        ]

    summary = stack_report.get("summary") if isinstance(stack_report.get("summary"), dict) else {}
    required_ready = int(summary.get("required_ready") or 0)
    required_total = int(summary.get("required_total") or 0)
    endpoint_ready = int(summary.get("endpoint_ready") or 0)
    gpu_profile_status = str(summary.get("gpu_profile_status") or "unknown")
    gui_endpoint = endpoint_by_service(stack_report, "aurora_gui")
    command_endpoint = endpoint_by_service(stack_report, "command_node")

    required_status = "ready" if required_total > 0 and required_ready == required_total else "blocked"
    gui_status = "ready" if normalize_status(gui_endpoint.get("status")) == "ready" else "blocked"
    command_status = "ready" if normalize_status(command_endpoint.get("status")) == "ready" else "blocked"
    return [
        gate(
            "stack_report_available",
            "Stack validation report is available",
            normalize_status(stack_report.get("status")),
            required=True,
            evidence={"path": STACK_REPORT_PATH.as_posix(), "generated_at": stack_report.get("generated_at")},
            recommended_next_action=None
            if normalize_status(stack_report.get("status")) == "ready"
            else "Refresh the Docker stack receipt with make stack-validation-report.",
        ),
        gate(
            "required_services_ready",
            "Required Docker services are ready",
            required_status,
            required=True,
            evidence={"required_ready": required_ready, "required_total": required_total},
            recommended_next_action=None
            if required_status == "ready"
            else "Start or repair required compose services before treating the demo as ready.",
        ),
        gate(
            "operator_snapshot_endpoint_ready",
            "Operator snapshot endpoint is reachable",
            gui_status,
            required=True,
            evidence={
                "service": "aurora_gui",
                "url": gui_endpoint.get("url"),
                "http_status": gui_endpoint.get("http_status"),
                "content_type": gui_endpoint.get("content_type"),
            },
            recommended_next_action=None
            if gui_status == "ready"
            else "Verify aurora_gui and /api/operator/snapshot before demo use.",
        ),
        gate(
            "command_node_endpoint_ready",
            "Command Node endpoint is reachable",
            command_status,
            required=True,
            evidence={
                "service": "command_node",
                "url": command_endpoint.get("url"),
                "http_status": command_endpoint.get("http_status"),
                "content_type": command_endpoint.get("content_type"),
            },
            recommended_next_action=None
            if command_status == "ready"
            else "Verify command_node before demo use.",
        ),
        gate(
            "gpu_profile_gated_or_ready",
            "GPU profile is explicitly gated or ready",
            "ready" if gpu_profile_status in {"gated", "ready"} else "attention",
            required=False,
            evidence={"gpu_profile_status": gpu_profile_status, "endpoint_ready": endpoint_ready},
            recommended_next_action=None
            if gpu_profile_status in {"gated", "ready"}
            else "Refresh stack validation to explain optional GPU profile state.",
        ),
    ]


def command_gates(
    root: Path,
    command_report: Optional[dict[str, Any]],
    command_error: Optional[str],
) -> list[dict[str, Any]]:
    if command_report is None:
        return [
            gate(
                "command_snapshot_available",
                "Command-intent snapshot is available",
                "attention",
                required=True,
                evidence={"path": COMMAND_REPORT_PATH.as_posix(), "error": command_error},
                recommended_next_action="Run make command-intent-snapshot-report before demo readiness.",
            )
        ]

    summary = command_report.get("summary") if isinstance(command_report.get("summary"), dict) else {}
    total_commands = int(summary.get("total_commands") or 0)
    valid_count = int(summary.get("valid_count") or 0)
    invalid_count = int(summary.get("invalid_count") or 0)
    simulated_count = int(summary.get("simulated_count") or 0)
    live_execution_count = int(summary.get("live_execution_count") or 0)
    not_validated_count = int(summary.get("not_validated_count") or 0)

    report_status = normalize_status(command_report.get("status"))
    boundary_status = "blocked" if live_execution_count else "ready"
    simulation_status = "ready" if simulated_count > 0 else "attention"
    coverage_status = "ready" if total_commands >= 4 and valid_count > 0 and invalid_count > 0 else "attention"
    return [
        gate(
            "command_snapshot_available",
            "Command-intent snapshot is available",
            report_status,
            required=True,
            evidence={"path": COMMAND_REPORT_PATH.as_posix(), "generated_at": command_report.get("generated_at")},
            recommended_next_action=None
            if report_status == "ready"
            else "Refresh command-intent evidence with make command-intent-snapshot-report.",
        ),
        gate(
            "command_boundary_preserved",
            "Command boundary preserves no live execution",
            boundary_status,
            required=True,
            evidence={"live_execution_count": live_execution_count},
            recommended_next_action=None
            if boundary_status == "ready"
            else "Stop and investigate before presenting this as a read-only demo.",
        ),
        gate(
            "range_simulation_available",
            "In-process range simulation evidence is available",
            simulation_status,
            required=True,
            evidence={"simulated_count": simulated_count},
            recommended_next_action=None
            if simulation_status == "ready"
            else "Refresh command-intent probes or repair the in-process SymbolicEngine path.",
        ),
        gate(
            "command_probe_coverage",
            "Command probes cover valid, invalid, and mesh-route evidence",
            coverage_status,
            required=False,
            evidence={
                "total_commands": total_commands,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "not_validated_count": not_validated_count,
            },
            recommended_next_action=None
            if coverage_status == "ready"
            else "Add or refresh default command probes before relying on the demo narrative.",
        ),
    ]


def summarize(gates: list[dict[str, Any]]) -> dict[str, Any]:
    required = [gate for gate in gates if gate["required"]]
    optional = [gate for gate in gates if not gate["required"]]
    return {
        "gate_count": len(gates),
        "required_gate_count": len(required),
        "optional_gate_count": len(optional),
        "ready_gate_count": sum(1 for gate in gates if gate["status"] == "ready"),
        "attention_gate_count": sum(1 for gate in gates if gate["status"] in {"attention", "missing", "unknown"}),
        "blocked_gate_count": sum(1 for gate in gates if gate["status"] == "blocked"),
        "required_ready": sum(1 for gate in required if gate["status"] == "ready"),
        "required_total": len(required),
        "optional_ready": sum(1 for gate in optional if gate["status"] == "ready"),
        "optional_total": len(optional),
    }


def report_status(gates: list[dict[str, Any]]) -> str:
    required = [gate for gate in gates if gate["required"]]
    if any(gate["status"] == "blocked" for gate in required):
        return "blocked"
    if any(gate["status"] != "ready" for gate in required):
        return "attention"
    if any(gate["status"] != "ready" for gate in gates):
        return "attention"
    return "ready"


def build_report(root: Path, generated_at: Optional[str] = None) -> dict[str, Any]:
    stack_report, stack_error = read_json(root / STACK_REPORT_PATH)
    command_report, command_error = read_json(root / COMMAND_REPORT_PATH)
    gates = [
        *stack_gates(root, stack_report, stack_error),
        *command_gates(root, command_report, command_error),
    ]
    summary = summarize(gates)
    return {
        "schema_version": 1,
        "tool": "aurora_demo_readiness",
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "status": report_status(gates),
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "live_runtime_execution": False,
        "summary": summary,
        "gates": gates,
        "source_reports": [
            {
                "id": "stack_validation",
                "path": STACK_REPORT_PATH.as_posix(),
                "available": stack_report is not None,
                "generated_at": stack_report.get("generated_at") if stack_report else None,
                "status": normalize_status(stack_report.get("status")) if stack_report else "missing",
                "error": stack_error,
            },
            {
                "id": "command_intent_snapshot",
                "path": COMMAND_REPORT_PATH.as_posix(),
                "available": command_report is not None,
                "generated_at": command_report.get("generated_at") if command_report else None,
                "status": normalize_status(command_report.get("status")) if command_report else "missing",
                "error": command_error,
            },
        ],
        "validation_commands": [
            "python3 tools/aurora_stack_validation.py --persist-report --summary",
            "python3 tools/aurora_command_intent_snapshot.py --persist-report --summary",
            "python3 tools/aurora_demo_readiness.py --persist-report --summary",
            "python3 tools/aurora_operator_snapshot.py --persist-report --summary",
            "python3 -m pytest -q tests/test_aurora_demo_readiness.py tests/test_aurora_operator_snapshot.py",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"status: {payload['status']}")
    print(f"required_gates: {summary['required_ready']}/{summary['required_total']}")
    print(f"optional_gates: {summary['optional_ready']}/{summary['optional_total']}")
    print(f"blocked_gates: {summary['blocked_gate_count']}")
    print(f"attention_gates: {summary['attention_gate_count']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the read-only Aurora Docker demo readiness receipt.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--report-out", help="Write the report to this path.")
    parser.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT_PATH}.")
    parser.add_argument("--summary", action="store_true", help="Print a concise summary instead of JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = build_report(root)

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
