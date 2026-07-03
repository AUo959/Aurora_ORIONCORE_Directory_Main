from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_demo_readiness as demo_readiness  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def seed_stack_report(root: Path, *, status: str = "ready", required_ready: int = 2, required_total: int = 2) -> None:
    write_json(
        root / demo_readiness.STACK_REPORT_PATH,
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": status,
            "summary": {
                "required_ready": required_ready,
                "required_total": required_total,
                "endpoint_ready": 2,
                "endpoint_total": 3,
                "gpu_profile_status": "gated",
            },
            "endpoints": [
                {
                    "service": "aurora_gui",
                    "url": "http://127.0.0.1:8080/api/operator/snapshot",
                    "status": "ready",
                    "http_status": 200,
                    "content_type": "application/json",
                },
                {
                    "service": "command_node",
                    "url": "http://127.0.0.1:3001/",
                    "status": "ready",
                    "http_status": 200,
                    "content_type": "text/plain",
                },
                {
                    "service": "nemo_service",
                    "url": "http://127.0.0.1:8090/nemo/health",
                    "status": "gated",
                    "reason": "service_not_ready",
                },
            ],
        },
    )


def seed_command_report(root: Path, *, live_execution_count: int = 0, simulated_count: int = 1) -> None:
    write_json(
        root / demo_readiness.COMMAND_REPORT_PATH,
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "ready",
            "summary": {
                "total_commands": 4,
                "valid_count": 2,
                "invalid_count": 1,
                "not_validated_count": 1,
                "warning_count": 2,
                "simulated_count": simulated_count,
                "live_execution_count": live_execution_count,
            },
        },
    )


def gate_by_id(payload: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return next(gate for gate in payload["gates"] if gate["gate_id"] == gate_id)


def test_ready_report_from_stack_and_command_receipts(tmp_path: Path) -> None:
    seed_stack_report(tmp_path)
    seed_command_report(tmp_path)

    payload = demo_readiness.build_report(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "ready"
    assert payload["mutation_posture"] == "advisory_only"
    assert payload["nested_repo_mutation"] is False
    assert payload["live_runtime_execution"] is False
    assert payload["summary"]["required_ready"] == payload["summary"]["required_total"]
    assert gate_by_id(payload, "required_services_ready")["status"] == "ready"
    assert gate_by_id(payload, "command_boundary_preserved")["status"] == "ready"
    assert gate_by_id(payload, "range_simulation_available")["status"] == "ready"


def test_missing_receipts_mark_attention_not_crash(tmp_path: Path) -> None:
    payload = demo_readiness.build_report(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "attention"
    assert payload["summary"]["required_ready"] == 0
    assert gate_by_id(payload, "stack_report_available")["status"] == "attention"
    assert gate_by_id(payload, "command_snapshot_available")["status"] == "attention"


def test_required_service_gap_blocks_readiness(tmp_path: Path) -> None:
    seed_stack_report(tmp_path, status="blocked", required_ready=1, required_total=2)
    seed_command_report(tmp_path)

    payload = demo_readiness.build_report(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "blocked"
    assert gate_by_id(payload, "required_services_ready")["status"] == "blocked"


def test_live_execution_claim_blocks_readiness(tmp_path: Path) -> None:
    seed_stack_report(tmp_path)
    seed_command_report(tmp_path, live_execution_count=1)

    payload = demo_readiness.build_report(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "blocked"
    assert gate_by_id(payload, "command_boundary_preserved")["status"] == "blocked"


def test_missing_simulation_marks_attention(tmp_path: Path) -> None:
    seed_stack_report(tmp_path)
    seed_command_report(tmp_path, simulated_count=0)

    payload = demo_readiness.build_report(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "attention"
    assert gate_by_id(payload, "range_simulation_available")["status"] == "attention"


def test_write_report_creates_parent_dirs(tmp_path: Path) -> None:
    seed_stack_report(tmp_path)
    seed_command_report(tmp_path)
    payload = demo_readiness.build_report(tmp_path, generated_at="2026-06-26T00:00:00Z")
    out = tmp_path / "reports/analysis/aurora_demo_readiness_latest.json"

    demo_readiness.write_report(out, payload)

    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["tool"] == "aurora_demo_readiness"
