from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_operator_snapshot as operator_snapshot  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_marker_files(root: Path) -> None:
    cloudbank = root / operator_snapshot.CLOUDBANK_PATH
    write_file(cloudbank / "docker-compose.yml")
    write_file(cloudbank / "api/aurora_gui_cloudhub_fastapi.py")
    write_file(cloudbank / "static/aurora-simulation-console.html")
    write_file(cloudbank / "static/synergy-dashboard.html")
    write_file(cloudbank / "services/command_node/index.js")
    write_file(cloudbank / "services/nemo_service/README.md")
    write_file(cloudbank / "src/aurora/core/command_grammar/__init__.py")

    write_file(root / "tools/aurora_command_intent.py")
    write_file(root / "tools/aurora_command_intent_snapshot.py")
    write_file(
        root
        / "plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json",
        "{}\n",
    )
    write_file(
        root / "GUMAS_SIM_2.5/CanonRec/canon/L1/station/operational_library_v2_2/README.md",
        "**Status:** STAGING (owner promotion pending)\n",
    )
    write_file(root / "GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0/app_server.py")
    write_file(root / "GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0/scripts/release_gate_v2_4_1.py")
    write_file(root / "GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0/README.md")
    write_file(root / "qgia-knowledge-library-main/data/intake/evidence-ledger.jsonl")
    write_file(root / "qgia-knowledge-library-main/data/truth/outcome-ledger.jsonl")
    write_file(root / "qgia-knowledge-spine-main/data/forecasts/forecast-ledger.jsonl")
    write_file(root / "qgia-knowledge-spine-main/data/priors/prior-table.json", "{}\n")
    write_file(root / "qgia-knowledge-spine-main/data/calibration/calibration-report.json", "{}\n")


def seed_reports(root: Path, *, devkit_status: str = "READY") -> None:
    write_json(
        root / "reports/analysis/aurora_mission_control_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "attention",
            "summary": {"source_count": 9, "operator_inbox_count": 1, "blocking_count": 0},
            "operator_inbox": [
                {
                    "id": "mission-item",
                    "title": "Review staged canon",
                    "priority": "P2",
                    "category": "canon",
                    "status": "open",
                    "target_repo": "CanonRec",
                    "approval_required": True,
                    "evidence_refs": ["restricted/path/not/copied"],
                }
            ],
        },
    )
    write_json(
        root / "reports/analysis/aurora_devkit_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": devkit_status,
            "registered_python_environments": [
                {
                    "repo_name": "aurora-cloudbank-symbolic-main",
                    "status": "ready" if devkit_status == "READY" else "blocked",
                    "path": operator_snapshot.CLOUDBANK_PATH.as_posix(),
                    "resolved_path": str(root / operator_snapshot.CLOUDBANK_PATH),
                    "path_resolution": "root",
                    "evidence": "pip_check",
                }
            ],
        },
    )
    write_json(
        root / "reports/analysis/aurora_stack_validation_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "ready",
            "summary": {
                "required_ready": 2,
                "required_total": 2,
                "endpoint_ready": 2,
                "endpoint_total": 2,
                "gpu_profile_status": "gated",
            },
            "services": [
                {"service": "aurora_gui", "status": "ready", "running": True, "health": "healthy", "profile": "default"},
                {"service": "command_node", "status": "ready", "running": True, "health": "healthy", "profile": "default"},
                {"service": "nemo_service", "status": "gated", "running": False, "health": "profile_gated", "profile": "gpu"},
            ],
        },
    )
    write_json(
        root / "reports/analysis/aurora_recommendations_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "open",
            "summary": {"recommendation_count": 1, "blocking_count": 0},
            "recommendations": [
                {
                    "recommendation_id": "rec-1",
                    "title": "Refresh Docker stack receipt",
                    "priority": "P2",
                    "category": "devkit",
                    "status": "open",
                    "target_repo": "aurora-cloudbank-symbolic-main",
                    "approval_required": False,
                }
            ],
        },
    )
    write_json(
        root / "reports/analysis/aurora_command_intent_snapshot_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "ready",
            "summary": {
                "total_commands": 4,
                "valid_count": 2,
                "invalid_count": 1,
                "not_validated_count": 1,
                "warning_count": 2,
                "simulated_count": 1,
                "live_execution_count": 0,
            },
        },
    )
    write_json(
        root / "reports/analysis/aurora_simulation_readiness_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "ready",
            "summary": {
                "surface_count": 7,
                "required_surface_count": 3,
                "ready_surface_count": 7,
                "attention_surface_count": 0,
                "blocked_surface_count": 0,
                "ready_required_surface_count": 3,
                "blocked_required_surface_count": 0,
                "execution_path_count": 3,
                "available_execution_path_count": 3,
                "persisted_output_turn": 123,
                "primary_event_ledger_records": 4411,
                "smoke_probe_status": "ready",
                "smoke_probe_requested": True,
            },
            "simulation_surfaces": [
                {
                    "surface_id": "gumas_advanced_engine",
                    "title": "GUMAS advanced simulation engine",
                    "role": "primary_multi_turn_simulation_runtime",
                    "repo": "root/GUMAS_SIM_2.5",
                    "status": "ready",
                    "required": True,
                    "execution_boundary": "local_seeded_engine_run",
                },
                {
                    "surface_id": "cloudbank_scenario_seed_bridge",
                    "title": "CloudBank scenario seed bridge",
                    "role": "scenario_seed_uptake_and_runtime_adapter",
                    "repo": "aurora-cloudbank-symbolic-main",
                    "status": "ready",
                    "required": True,
                    "execution_boundary": "scenario_fixture_generation_requires_explicit_nested_repo_gate",
                },
            ],
            "execution_paths": [
                {
                    "path_id": "gumas_advanced_seeded_smoke",
                    "title": "Run bounded GUMAS advanced simulation smoke",
                    "status": "ready",
                    "writes_to_repo": False,
                    "nested_repo_mutation": False,
                }
            ],
            "artifact_evidence": {
                "latest_output": {"available": True, "turn": 123},
                "primary_event_ledger": {"record_count": 4411},
            },
            "smoke_probe": {
                "requested": True,
                "status": "ready",
                "turns": 5,
                "seed": 42,
                "writes_to_repo": False,
                "nested_repo_mutation": False,
                "live_runtime_execution": False,
                "result": {"engine_class": "GUMASAdvancedEngine", "turns_completed": 5},
            },
        },
    )
    write_json(
        root / "reports/analysis/aurora_demo_readiness_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "ready",
            "summary": {
                "gate_count": 9,
                "required_gate_count": 7,
                "optional_gate_count": 2,
                "ready_gate_count": 9,
                "attention_gate_count": 0,
                "blocked_gate_count": 0,
                "required_ready": 7,
                "required_total": 7,
                "optional_ready": 2,
                "optional_total": 2,
            },
            "gates": [
                {"gate_id": "required_services_ready", "title": "Required Docker services are ready", "status": "ready", "required": True},
                {"gate_id": "command_boundary_preserved", "title": "Command boundary preserves no live execution", "status": "ready", "required": True},
            ],
        },
    )
    write_json(
        root / "reports/analysis/aurora_kubernetes_readiness_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "attention",
            "summary": {
                "gate_count": 8,
                "required_gate_count": 5,
                "optional_gate_count": 3,
                "ready_gate_count": 7,
                "attention_gate_count": 1,
                "blocked_gate_count": 0,
                "required_ready": 4,
                "required_total": 5,
                "optional_ready": 3,
                "optional_total": 3,
                "manifest_file_count": 9,
                "resource_count": 18,
                "kind_counts": {"Deployment": 3, "Service": 3, "Namespace": 1},
                "finding_count": 2,
                "apply_blocker_count": 2,
                "informational_finding_count": 0,
                "apply_blocker_category_counts": {"mutable_or_local_image": 1, "secret_placeholder": 1},
            },
            "cluster_probe": {"status": "skipped", "reason": "manifest/client readiness only"},
            "apply_blockers": [
                {
                    "path": "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/k8s/aurora-configmap-secrets.yaml",
                    "line": 137,
                    "category": "secret_placeholder",
                    "severity": "attention",
                    "blocks_apply": True,
                    "detail": "Secret manifest still contains placeholder API key material.",
                    "snippet": "openai-api-key: <redacted>",
                },
                {
                    "path": "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/k8s/aurora-gui-cloudhub-deployment.yaml",
                    "line": 155,
                    "category": "mutable_or_local_image",
                    "severity": "attention",
                    "blocks_apply": True,
                    "detail": "Image reference is local or mutable.",
                    "snippet": "image: aurora-cloudbank-symbolic:latest",
                },
            ],
            "remediation_plan": [
                {
                    "category": "mutable_or_local_image",
                    "blocker_count": 1,
                    "recommended_next_action": "Publish the image to a registry and pin it.",
                },
                {
                    "category": "secret_placeholder",
                    "blocker_count": 1,
                    "recommended_next_action": "Use sealed-secrets or external secret management.",
                },
            ],
        },
    )
    write_json(
        root / "reports/analysis/aurora_confidence_audit_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "summary": {"record_count": 1, "verdict": "pass"},
        },
    )
    write_json(
        root / "reports/analysis/workspace_recovery_index_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "READY",
            "summary": {"candidate_count": 2},
        },
    )


def lane_by_id(payload: dict[str, Any], lane_id: str) -> dict[str, Any]:
    return next(lane for lane in payload["lanes"] if lane["lane_id"] == lane_id)


def test_build_snapshot_aggregates_reports_and_markers(tmp_path: Path) -> None:
    seed_reports(tmp_path)
    seed_marker_files(tmp_path)

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "attention"
    assert payload["mutation_posture"] == "advisory_only"
    assert payload["nested_repo_mutation"] is False
    assert payload["live_runtime_execution"] is False
    assert payload["summary"]["available_source_report_count"] == 10
    assert payload["summary"]["lane_count"] == 9
    simulation_lane = lane_by_id(payload, "simulation-runtime-readiness")
    assert simulation_lane["status"] == "ready"
    assert simulation_lane["simulation_readiness"]["summary"]["persisted_output_turn"] == 123
    assert simulation_lane["simulation_readiness"]["summary"]["primary_event_ledger_records"] == 4411
    assert simulation_lane["simulation_readiness"]["smoke_probe"]["result"]["engine_class"] == "GUMASAdvancedEngine"
    assert simulation_lane["live_runtime_execution"] is False
    readiness_lane = lane_by_id(payload, "docker-demo-readiness")
    assert readiness_lane["status"] == "ready"
    assert readiness_lane["demo_readiness"]["summary"]["required_ready"] == 7
    kubernetes_lane = lane_by_id(payload, "kubernetes-readiness")
    assert kubernetes_lane["status"] == "attention"
    assert kubernetes_lane["kubernetes_readiness"]["summary"]["manifest_file_count"] == 9
    assert kubernetes_lane["kubernetes_readiness"]["summary"]["apply_blocker_count"] == 2
    assert kubernetes_lane["kubernetes_readiness"]["apply_blocker_total"] == 2
    assert kubernetes_lane["kubernetes_readiness"]["apply_blockers"][0]["category"] == "secret_placeholder"
    assert kubernetes_lane["kubernetes_readiness"]["remediation_plan"][0]["category"] == "mutable_or_local_image"
    assert kubernetes_lane["live_runtime_execution"] is False
    assert lane_by_id(payload, "cloudbank-docker-runtime")["status"] == "ready"
    assert lane_by_id(payload, "cloudbank-docker-runtime")["stack_validation"]["status"] == "ready"
    command_lane = lane_by_id(payload, "command-intent-parse-simulate")
    assert command_lane["status"] == "ready"
    assert command_lane["command_intent_snapshot"]["summary"]["simulated_count"] == 1
    assert command_lane["live_runtime_execution"] is False
    assert lane_by_id(payload, "canonrec-staging")["status"] == "attention"
    assert payload["operator_items"][0]["title"] == "Review staged canon"
    assert "evidence_refs" not in payload["operator_items"][0]


def test_missing_reports_are_attention_not_crashes(tmp_path: Path) -> None:
    seed_marker_files(tmp_path)

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "attention"
    assert payload["summary"]["available_source_report_count"] == 0
    assert {source["status"] for source in payload["source_reports"]} == {"missing"}
    assert payload["recommended_actions"][0]["title"] == "Refresh missing root source reports"


def test_blocked_devkit_blocks_cloudbank_lane(tmp_path: Path) -> None:
    seed_reports(tmp_path, devkit_status="BLOCKED")
    seed_marker_files(tmp_path)

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert lane_by_id(payload, "cloudbank-docker-runtime")["status"] == "blocked"
    assert payload["status"] == "blocked"


def test_missing_command_intent_snapshot_marks_lane_attention(tmp_path: Path) -> None:
    seed_reports(tmp_path)
    seed_marker_files(tmp_path)
    (tmp_path / "reports/analysis/aurora_command_intent_snapshot_latest.json").unlink()

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")
    command_lane = lane_by_id(payload, "command-intent-parse-simulate")

    assert command_lane["status"] == "attention"
    assert command_lane["command_intent_snapshot"]["available"] is False


def test_missing_demo_readiness_marks_lane_attention(tmp_path: Path) -> None:
    seed_reports(tmp_path)
    seed_marker_files(tmp_path)
    (tmp_path / "reports/analysis/aurora_demo_readiness_latest.json").unlink()

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")
    readiness_lane = lane_by_id(payload, "docker-demo-readiness")

    assert readiness_lane["status"] == "missing"
    assert readiness_lane["demo_readiness"]["available"] is False
    assert payload["status"] == "attention"


def test_missing_kubernetes_readiness_marks_lane_attention(tmp_path: Path) -> None:
    seed_reports(tmp_path)
    seed_marker_files(tmp_path)
    (tmp_path / "reports/analysis/aurora_kubernetes_readiness_latest.json").unlink()

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")
    kubernetes_lane = lane_by_id(payload, "kubernetes-readiness")

    assert kubernetes_lane["status"] == "missing"
    assert kubernetes_lane["kubernetes_readiness"]["available"] is False
    assert payload["status"] == "attention"


def test_missing_simulation_readiness_marks_lane_attention(tmp_path: Path) -> None:
    seed_reports(tmp_path)
    seed_marker_files(tmp_path)
    (tmp_path / "reports/analysis/aurora_simulation_readiness_latest.json").unlink()

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")
    simulation_lane = lane_by_id(payload, "simulation-runtime-readiness")

    assert simulation_lane["status"] == "missing"
    assert simulation_lane["simulation_readiness"]["available"] is False
    assert payload["status"] == "attention"


def test_blocked_stack_validation_blocks_cloudbank_lane(tmp_path: Path) -> None:
    seed_reports(tmp_path)
    seed_marker_files(tmp_path)
    write_json(
        tmp_path / "reports/analysis/aurora_stack_validation_latest.json",
        {
            "generated_at": "2026-06-26T00:00:00Z",
            "status": "blocked",
            "summary": {"required_ready": 1, "required_total": 2},
            "services": [{"service": "command_node", "status": "blocked", "running": False}],
        },
    )

    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")

    assert lane_by_id(payload, "cloudbank-docker-runtime")["status"] == "blocked"
    assert payload["status"] == "blocked"


def test_write_report_creates_parent_dirs(tmp_path: Path) -> None:
    payload = operator_snapshot.build_snapshot(tmp_path, generated_at="2026-06-26T00:00:00Z")
    out = tmp_path / "reports/analysis/aurora_operator_snapshot_latest.json"

    operator_snapshot.write_report(out, payload)

    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["tool"] == "aurora_operator_snapshot"
