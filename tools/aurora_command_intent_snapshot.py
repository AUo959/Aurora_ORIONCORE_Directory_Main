#!/usr/bin/env python3
"""Build a read-only Aurora command-intent snapshot.

This report wraps the root command-intent gateway with deterministic probes for
operator consoles. It parses command-like text and may run valid numeric range
chains through the in-process CloudBank simulator, but it never sends mesh
messages, executes live runtime handlers, mutates nested repos, or promotes
canon.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

import aurora_command_intent as command_intent


DEFAULT_REPORT_PATH = Path("reports/analysis/aurora_command_intent_snapshot_latest.json")
DEFAULT_COMMANDS = ["THREADWAKE", "001//005//", "@mesh status", "UNKNOWNCOMMAND//."]

COMPACT_INTENT_KEYS = [
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
    "run_mode",
    "execution_scope",
    "live_runtime_execution",
    "simulation_status",
    "runtime_handler_verified",
    "runtime_refs",
    "gumas_mutation_auth_required",
    "gumas_mutation_auth_status",
    "target_repo",
    "authority_refs",
    "recommended_next_action",
]

ATTENTION_ISSUE_CODES = {
    "cloudbank_parser_unavailable",
    "parse_error",
    "symbolic_engine_unavailable",
    "simulation_failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact_intent(intent: dict[str, Any]) -> dict[str, Any]:
    return {key: intent.get(key) for key in COMPACT_INTENT_KEYS if key in intent}


def issue_codes(intent: dict[str, Any]) -> set[str]:
    issues = intent.get("validation_issues", [])
    if not isinstance(issues, list):
        return set()
    return {str(issue.get("code")) for issue in issues if isinstance(issue, dict) and issue.get("code")}


def status_for_record(intent: dict[str, Any], simulation: Optional[dict[str, Any]]) -> str:
    if issue_codes(intent) & ATTENTION_ISSUE_CODES:
        return "attention"
    if simulation and simulation.get("simulation_status") in {"failed", "blocked"}:
        return "attention"
    return "ready"


def should_simulate(intent: dict[str, Any]) -> bool:
    return (
        intent.get("ast_shape") == "range_chain"
        and intent.get("validation_status") in {"valid", "valid_with_warnings"}
        and intent.get("range_edges") is not None
    )


def compact_simulation(payload: dict[str, Any], status_code: int) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "ok": bool(payload.get("ok")),
        "run_mode": payload.get("run_mode"),
        "execution_scope": payload.get("execution_scope"),
        "live_runtime_execution": bool(payload.get("live_runtime_execution")),
        "simulation_status": payload.get("simulation_status"),
        "simulation_label": payload.get("simulation_label"),
        "chain_id": payload.get("chain_id"),
        "step_count": payload.get("step_count"),
        "runtime_authority": payload.get("runtime_authority"),
        "error": payload.get("error"),
    }


def build_command_record(raw_text: str, max_steps: int) -> dict[str, Any]:
    intent = command_intent.parse_command_intent(raw_text)
    simulation = None

    if should_simulate(intent):
        status_code, simulation_payload = command_intent.simulate_range(raw_text, max_steps=max_steps)
        simulation = compact_simulation(simulation_payload, status_code)
        simulated_intent = simulation_payload.get("intent")
        if isinstance(simulated_intent, dict):
            intent = simulated_intent

    compact = compact_intent(intent)
    compact["tool_status"] = status_for_record(intent, simulation)
    compact["probe_mode"] = "in_process_simulation" if simulation else "parse_only"
    if simulation:
        compact["simulation"] = simulation
    return compact


def load_commands_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []

    if stripped.startswith("["):
        data = json.loads(stripped)
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a JSON array or newline-delimited commands.")
        commands: list[str] = []
        for item in data:
            if isinstance(item, str):
                commands.append(item)
            elif isinstance(item, dict) and isinstance(item.get("raw_text"), str):
                commands.append(item["raw_text"])
            else:
                raise ValueError(f"{path} contains a command that is not a string or raw_text object.")
        return commands

    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def collect_commands(commands: Iterable[str], command_files: Iterable[Path], include_defaults: bool) -> list[str]:
    collected = list(DEFAULT_COMMANDS if include_defaults else [])
    collected.extend(commands)
    for path in command_files:
        collected.extend(load_commands_file(path))
    return collected


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_commands": len(records),
        "valid_count": sum(1 for record in records if record.get("validation_status") in {"valid", "valid_with_warnings"}),
        "invalid_count": sum(1 for record in records if record.get("validation_status") == "invalid"),
        "not_validated_count": sum(1 for record in records if record.get("validation_status") == "not_validated"),
        "warning_count": sum(len(record.get("warnings") or []) for record in records),
        "validation_issue_count": sum(len(record.get("validation_issues") or []) for record in records),
        "simulated_count": sum(
            1
            for record in records
            if isinstance(record.get("simulation"), dict)
            and record["simulation"].get("simulation_status") == "completed"
        ),
        "runtime_verified_count": sum(1 for record in records if record.get("runtime_handler_verified") is True),
        "live_execution_count": sum(1 for record in records if record.get("live_runtime_execution") is True),
        "attention_command_count": sum(1 for record in records if record.get("tool_status") == "attention"),
    }


def report_status(records: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if not records:
        return "attention"
    if summary["live_execution_count"] > 0:
        return "blocked"
    if summary["attention_command_count"] > 0:
        return "attention"
    return "ready"


def build_snapshot(
    root: Path,
    commands: Optional[Iterable[str]] = None,
    *,
    generated_at: Optional[str] = None,
    max_steps: int = 100,
) -> dict[str, Any]:
    requested_commands = list(DEFAULT_COMMANDS if commands is None else commands)
    records = [build_command_record(raw_text, max_steps=max_steps) for raw_text in requested_commands]
    summary = summarize(records)
    return {
        "schema_version": 1,
        "tool": "aurora_command_intent_snapshot",
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "status": report_status(records, summary),
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "live_runtime_execution": False,
        "summary": summary,
        "commands": records,
        "authority_refs": [
            command_intent.COMMAND_GRAMMAR_REF,
            command_intent.SYMBOLIC_ENGINE_REF,
            command_intent.SCHEMA_REF,
        ],
        "validation_commands": [
            "python3 tools/aurora_command_intent_snapshot.py --persist-report --summary",
            "python3 tools/aurora_operator_snapshot.py --persist-report --summary",
            "python3 -m pytest -q tests/test_aurora_command_intent_snapshot.py tests/test_aurora_operator_snapshot.py",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"status: {payload['status']}")
    print(f"commands: {summary['total_commands']}")
    print(f"valid: {summary['valid_count']}")
    print(f"invalid: {summary['invalid_count']}")
    print(f"warnings: {summary['warning_count']}")
    print(f"simulated: {summary['simulated_count']}")
    print(f"live_execution: {summary['live_execution_count']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the read-only Aurora command-intent snapshot.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--command", action="append", default=[], help="Additional command text to include.")
    parser.add_argument("--commands-file", action="append", type=Path, default=[], help="Text or JSON command list.")
    parser.add_argument("--no-defaults", action="store_true", help="Use only commands supplied by flags/files.")
    parser.add_argument("--max-steps", type=int, default=100, help="Safety limit for in-process range simulation.")
    parser.add_argument("--report-out", help="Write the snapshot to this path.")
    parser.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT_PATH}.")
    parser.add_argument("--summary", action="store_true", help="Print a concise summary instead of JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    commands = collect_commands(args.command, args.commands_file, include_defaults=not args.no_defaults)
    payload = build_snapshot(root, commands, max_steps=args.max_steps)

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
