from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_command_intent_snapshot as command_snapshot  # noqa: E402


def fake_intent(raw_text: str, *, status: str = "valid", ast_shape: str = "command_invocation") -> dict[str, Any]:
    return {
        "raw_text": raw_text,
        "normalized_text": f"{raw_text}//.",
        "intent_type": "parse",
        "grammar_family": "aurora_symbolic_command",
        "ast_shape": ast_shape,
        "command_heads": [raw_text.split("//", 1)[0]] if ast_shape == "command_invocation" else [],
        "range_edges": {"start": "001", "end": "003"} if ast_shape == "range_chain" else None,
        "arguments": [],
        "modifier": None,
        "warnings": [{"code": "normalized", "message": "normalized"}] if status == "valid_with_warnings" else [],
        "validation_status": status,
        "validation_issues": [],
        "run_mode": "parse_only",
        "execution_scope": "none",
        "live_runtime_execution": False,
        "simulation_status": "not_applicable",
        "runtime_handler_verified": False,
        "runtime_refs": [],
        "gumas_mutation_auth_required": False,
        "gumas_mutation_auth_status": "not_applicable",
        "target_repo": None,
        "authority_refs": ["parser", "schema"],
        "recommended_next_action": "Verify before execution.",
    }


def test_build_snapshot_compacts_parse_and_simulation(monkeypatch: Any, tmp_path: Path) -> None:
    def parse(raw_text: str) -> dict[str, Any]:
        if raw_text == "001//003//":
            return fake_intent(raw_text, status="valid_with_warnings", ast_shape="range_chain")
        if raw_text == "UNKNOWNCOMMAND//.":
            intent = fake_intent(raw_text, status="invalid")
            intent["validation_issues"] = [
                {"code": "unknown_command", "severity": "error", "message": "unknown", "head": "UNKNOWNCOMMAND"}
            ]
            return intent
        if raw_text.startswith("@mesh"):
            intent = fake_intent(raw_text, status="not_validated", ast_shape="mesh_route")
            intent["grammar_family"] = "mesh_router"
            intent["normalized_text"] = raw_text
            return intent
        return fake_intent(raw_text, status="valid_with_warnings")

    def simulate(raw_text: str, max_steps: int) -> tuple[int, dict[str, Any]]:
        intent = fake_intent(raw_text, status="valid_with_warnings", ast_shape="range_chain")
        intent.update(
            {
                "run_mode": "in_process_simulation",
                "execution_scope": "in_process_simulation",
                "simulation_status": "completed",
                "target_repo": "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
            }
        )
        return (
            0,
            {
                "ok": True,
                "run_mode": "in_process_simulation",
                "execution_scope": "in_process_simulation",
                "live_runtime_execution": False,
                "simulation_status": "completed",
                "simulation_label": "in-process SymbolicEngine simulation only; not live runtime execution",
                "chain_id": raw_text,
                "step_count": 3,
                "runtime_authority": "symbolic_engine",
                "intent": intent,
            },
        )

    monkeypatch.setattr(command_snapshot.command_intent, "parse_command_intent", parse)
    monkeypatch.setattr(command_snapshot.command_intent, "simulate_range", simulate)

    payload = command_snapshot.build_snapshot(
        tmp_path,
        ["THREADWAKE", "001//003//", "@mesh status", "UNKNOWNCOMMAND//."],
        generated_at="2026-06-26T00:00:00Z",
    )

    assert payload["status"] == "ready"
    assert payload["mutation_posture"] == "advisory_only"
    assert payload["nested_repo_mutation"] is False
    assert payload["live_runtime_execution"] is False
    assert payload["summary"]["total_commands"] == 4
    assert payload["summary"]["valid_count"] == 2
    assert payload["summary"]["invalid_count"] == 1
    assert payload["summary"]["not_validated_count"] == 1
    assert payload["summary"]["simulated_count"] == 1
    assert payload["summary"]["runtime_verified_count"] == 0
    assert payload["commands"][1]["probe_mode"] == "in_process_simulation"
    assert payload["commands"][1]["simulation"]["step_count"] == 3


def test_parser_availability_issue_marks_report_attention(monkeypatch: Any, tmp_path: Path) -> None:
    def parse(raw_text: str) -> dict[str, Any]:
        intent = fake_intent(raw_text, status="not_validated", ast_shape="unknown")
        intent["validation_issues"] = [
            {
                "code": "cloudbank_parser_unavailable",
                "severity": "error",
                "message": "missing parser",
                "head": None,
            }
        ]
        return intent

    monkeypatch.setattr(command_snapshot.command_intent, "parse_command_intent", parse)

    payload = command_snapshot.build_snapshot(tmp_path, ["THREADWAKE"], generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "attention"
    assert payload["summary"]["attention_command_count"] == 1
    assert payload["commands"][0]["tool_status"] == "attention"


def test_write_report_creates_parent_dirs(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setattr(command_snapshot.command_intent, "parse_command_intent", lambda raw: fake_intent(raw))
    payload = command_snapshot.build_snapshot(tmp_path, ["THREADWAKE"], generated_at="2026-06-26T00:00:00Z")
    out = tmp_path / "reports/analysis/aurora_command_intent_snapshot_latest.json"

    command_snapshot.write_report(out, payload)

    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["tool"] == "aurora_command_intent_snapshot"


def test_load_commands_file_supports_json_and_text(tmp_path: Path) -> None:
    json_path = tmp_path / "commands.json"
    text_path = tmp_path / "commands.txt"
    json_path.write_text(json.dumps(["THREADWAKE", {"raw_text": "001//002//"}]), encoding="utf-8")
    text_path.write_text("# comment\n@mesh status\nUNKNOWNCOMMAND//.\n", encoding="utf-8")

    assert command_snapshot.load_commands_file(json_path) == ["THREADWAKE", "001//002//"]
    assert command_snapshot.load_commands_file(text_path) == ["@mesh status", "UNKNOWNCOMMAND//."]
