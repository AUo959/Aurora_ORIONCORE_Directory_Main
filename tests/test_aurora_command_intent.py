from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"

sys.path.insert(0, str(TOOLS_ROOT))

import aurora_command_intent as gateway  # noqa: E402


SCHEMA_KEYS = {
    "schema_version",
    "raw_text",
    "normalized_text",
    "intent_type",
    "grammar_family",
    "ast_shape",
    "command_heads",
    "range_edges",
    "arguments",
    "modifier",
    "warnings",
    "validation_status",
    "validation_issues",
    "runtime_handler_verified",
    "runtime_refs",
    "execution_status",
    "target_repo",
    "authority_refs",
    "recommended_next_action",
    "receipt_refs",
}


def require_cloudbank_parser() -> None:
    if not gateway.COMMAND_GRAMMAR_PATH.exists():
        pytest.skip("CloudBank command grammar is not present in this root checkout")


def test_parse_uses_cloudbank_parser_for_symbolic_command() -> None:
    require_cloudbank_parser()

    record = gateway.parse_command_intent("#025//.deep")

    assert set(record) == SCHEMA_KEYS
    assert record["normalized_text"] == "025//.deep"
    assert record["grammar_family"] == "aurora_symbolic_command"
    assert record["ast_shape"] == "command_invocation"
    assert record["command_heads"] == ["025"]
    assert record["modifier"] == "deep"
    assert record["validation_status"] == "valid_with_warnings"
    assert record["runtime_handler_verified"] is False
    assert record["execution_status"] == "not_requested"
    assert any(warning["code"] == "legacy_hash_prefix" for warning in record["warnings"])
    assert gateway.COMMAND_GRAMMAR_REF in record["authority_refs"]


def test_envelope_is_schema_shaped_and_keeps_execution_blocked() -> None:
    require_cloudbank_parser()

    envelope = gateway.envelope_for(
        "THREADWAKE",
        intent_type="execute_request",
        target_repo=gateway.CLOUDBANK_REPO_REF,
        receipt_refs=["reports/example-receipt.md"],
    )

    assert set(envelope) == SCHEMA_KEYS
    assert envelope["schema_version"] == "1.0.0"
    assert envelope["normalized_text"] == "THREADWAKE//."
    assert envelope["intent_type"] == "execute_request"
    assert envelope["validation_status"] == "valid_with_warnings"
    assert envelope["execution_status"] == "blocked_pending_verification"
    assert envelope["runtime_handler_verified"] is False
    assert envelope["target_repo"] == gateway.CLOUDBANK_REPO_REF
    assert envelope["receipt_refs"] == ["reports/example-receipt.md"]
    assert "explicit approval" in envelope["recommended_next_action"]


def test_mesh_text_maps_to_mesh_family_without_runtime_execution() -> None:
    envelope = gateway.envelope_for("@mesh ops status", intent_type="mesh_route_map")

    assert set(envelope) == SCHEMA_KEYS
    assert envelope["grammar_family"] == "mesh_router"
    assert envelope["ast_shape"] == "mesh_route"
    assert envelope["validation_status"] == "not_validated"
    assert envelope["runtime_handler_verified"] is False
    assert envelope["execution_status"] == "not_requested"


def test_simulate_range_executes_only_in_process_range_chain() -> None:
    require_cloudbank_parser()

    status, payload = gateway.simulate_range("001//005//", max_steps=10)

    assert status == 0
    assert payload["ok"] is True
    assert payload["mode"] == "in_process_simulation"
    assert payload["live_runtime_execution"] is False
    assert payload["simulation_label"] == "in-process SymbolicEngine simulation only; not live runtime execution"
    assert payload["chain_id"] == "001//005//"
    assert payload["step_count"] == 5
    assert len(payload["results"]) == 5
    assert payload["intent"]["ast_shape"] == "range_chain"
    assert payload["intent"]["runtime_handler_verified"] is True
    assert payload["intent"]["execution_status"] == "executed"
    assert gateway.SYMBOLIC_ENGINE_REF + "::SymbolicEngine.execute_chain_notation" in payload["intent"]["runtime_refs"]


def test_simulate_range_rejects_non_range_command() -> None:
    require_cloudbank_parser()

    status, payload = gateway.simulate_range("THREADWAKE//.", max_steps=10)

    assert status == 2
    assert payload["ok"] is False
    assert payload["live_runtime_execution"] is False
    assert payload["error"] == "simulate-range only accepts valid numeric RangeChain input."
    assert payload["intent"]["ast_shape"] == "command_invocation"
    assert payload["intent"]["execution_status"] == "blocked_pending_verification"


def test_cli_envelope_outputs_schema_shaped_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS_ROOT / "aurora_command_intent.py"),
            "envelope",
            "--text",
            "001//005//",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert set(payload) == SCHEMA_KEYS
    if not gateway.COMMAND_GRAMMAR_PATH.exists():
        assert payload["ast_shape"] == "unknown"
        assert payload["validation_issues"][0]["code"] == "cloudbank_parser_unavailable"
        return
    assert payload["ast_shape"] == "range_chain"
    assert payload["range_edges"] == {"start": "001", "end": "005"}
    assert payload["execution_status"] == "not_requested"


def test_parse_reports_missing_cloudbank_parser(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gateway, "COMMAND_GRAMMAR_PATH", tmp_path / "missing-command-grammar")

    record = gateway.parse_command_intent("THREADWAKE")

    assert set(record) == SCHEMA_KEYS
    assert record["validation_status"] == "not_validated"
    assert record["validation_issues"][0]["code"] == "cloudbank_parser_unavailable"
    assert record["runtime_handler_verified"] is False
    assert "Restore the CloudBank parser path" in record["recommended_next_action"]
