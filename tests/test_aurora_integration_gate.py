from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"

sys.path.insert(0, str(TOOLS_ROOT))

import aurora_integration_gate as gate  # noqa: E402


def test_command_gateway_safety_probe_does_not_claim_live_execution() -> None:
    report = gate.command_gateway_safety_probe()

    assert report["status"] in {"pass", "warn"}
    envelope = report["details"]["execute_request_envelope"]
    assert envelope["execution_status"] == "blocked_pending_verification"
    assert envelope["execution_scope"] == "blocked_pending_runtime_verification"
    assert envelope["live_runtime_execution"] is False
    assert envelope["runtime_handler_verified"] is False
    assert envelope["gumas_mutation_auth_required"] is True
    assert envelope["gumas_mutation_auth_status"] == "required_not_verified"
    assert envelope["gumas_mutation_auth_refs"] == []

    if report["details"]["cloudbank_parser_present"]:
        simulation = report["details"]["simulate_range"]
        assert simulation["execution_scope"] == "in_process_simulation"
        assert simulation["live_runtime_execution"] is False
        assert simulation["simulation_status"] == "completed"
        assert simulation["gumas_mutation_auth_required"] is False
        assert simulation["gumas_mutation_auth_status"] == "not_applicable"
        assert simulation["intent_gumas_mutation_auth_required"] is False
        assert simulation["intent_gumas_mutation_auth_status"] == "not_applicable"
        assert simulation["intent_execution_status"] == "not_applicable"
        assert simulation["intent_runtime_handler_verified"] is False


def test_provenance_gate_accepts_unpromoted_recovery_candidates(tmp_path: Path) -> None:
    report_path = tmp_path / "recovery.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "READY",
                "generated_at": "2026-05-21T00:00:00Z",
                "summary": {"candidate_count": 1, "discovered_candidate_count": 1},
                "candidates": [
                    {
                        "path": "intake/example.md",
                        "promotion_status": "pending_review",
                        "canonical_status": "not_promoted",
                        "restricted_material_possible": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = gate.provenance_gate(report_path)

    assert result["status"] == "pass"
    assert result["details"]["candidate_count"] == 1


def test_provenance_gate_rejects_promotion_without_receipt(tmp_path: Path) -> None:
    report_path = tmp_path / "recovery.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "READY",
                "generated_at": "2026-05-21T00:00:00Z",
                "summary": {"candidate_count": 1, "discovered_candidate_count": 1},
                "candidates": [
                    {
                        "path": "intake/example.md",
                        "promotion_status": "promoted",
                        "canonical_status": "promoted",
                        "restricted_material_possible": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = gate.provenance_gate(report_path)

    assert result["status"] == "fail"
    assert "without receipt" in result["failures"][0]


def test_schema_presence_check_covers_audit_handoff_record() -> None:
    result = gate.schema_presence_check()

    assert result["status"] == "pass"
    assert any(path.endswith("audit-handoff-record.schema.json") for path in result["details"])
    assert any(path.endswith("aurora_confidence_record.schema.json") for path in result["details"])


def test_docs_path_authority_declares_gumas_mutation_auth_gate() -> None:
    result = gate.docs_path_authority_check()

    assert result["status"] == "pass"
    assert all(details["gumas_mutation_auth_present"] for details in result["details"].values())


def test_confidence_audit_probe_requires_alert_for_low_score() -> None:
    result = gate.confidence_audit_probe()

    assert result["status"] == "pass"
    assert result["details"]["requires_user_alert"] is True
    assert result["details"]["alert_reason"] == "confidence_below_threshold"
    assert result["details"]["live_runtime_execution"] is False
    assert result["details"]["nested_repo_mutation"] is False


def test_build_report_without_subprocess_is_read_only() -> None:
    report = gate.build_report(run_subprocess=False)

    assert report["tool"] == "aurora_integration_gate"
    assert report["run_mode"] == "read_only"
    assert report["nested_repo_mutation"] is False
    assert report["commands"] == []
    assert report["verdict"] in {"pass", "warn", "fail"}


def test_default_commands_include_recommendation_engine_summary() -> None:
    commands = {name: command for name, command in gate.default_commands()}

    assert "recommendation_engine_summary" in commands
    assert commands["recommendation_engine_summary"][-2:] == [
        "tools/aurora_recommendation_engine.py",
        "--summary",
    ]
