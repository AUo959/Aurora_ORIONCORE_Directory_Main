#!/usr/bin/env python3
"""Root integration quality gate for command intent and agent handoffs.

This gate is root-control-plane tooling. It validates parse/envelope safety,
agent command-context behavior, recovery provenance labels, installed-skill
drift, and root workspace health without mutating nested repositories.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from _workspace_common import now_iso_utc, write_json


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "analysis"
RECOVERY_REPORT = REPORTS / "workspace_recovery_index_latest.json"
COMMAND_SCHEMA = (
    ROOT
    / "plugins"
    / "aurora-command-grammar"
    / "skills"
    / "aurora-command-grammar"
    / "references"
    / "command-intent-envelope.schema.json"
)
AUDIT_SCHEMA = (
    ROOT
    / "plugins"
    / "aurora-command-grammar"
    / "skills"
    / "aurora-command-grammar"
    / "references"
    / "audit-handoff-record.schema.json"
)
CONFIDENCE_SCHEMA = ROOT / "catalog" / "schemas" / "aurora_confidence_record.schema.json"
CONFIDENCE_CONTRACT = ROOT / "catalog" / "contracts" / "aurora_confidence_audit_contract_v1.json"


def tail_text(value: str, limit: int = 3000) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[-limit:]


def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def check_status(failures: list[str], warnings: list[str]) -> str:
    if failures:
        return "fail"
    if warnings:
        return "warn"
    return "pass"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(name: str, command: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    record: dict[str, Any] = {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": tail_text(result.stdout),
        "stderr_tail": tail_text(result.stderr),
        "status": "pass" if result.returncode == 0 else "fail",
        "classification": "root_failure" if result.returncode else "pass",
    }

    if name == "installed_skill_sync_dry_run" and result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
        record["parsed_stdout"] = payload
        if result.returncode == 0 and payload.get("status") == "dry_run":
            record["status"] = "warn"
            record["classification"] = "skill_sync_warning"
        validation = payload.get("validation", {})
        validation_status = validation.get("status")
        validation_returncode = validation.get("_returncode", 0)
        if validation_returncode not in (0, None) or validation_status in {"fail", "invalid_output"}:
            record["status"] = "fail"
            record["classification"] = "skill_validation_failure"

    if name == "workspace_verify" and result.returncode != 0 and result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
        findings = payload.get("findings", [])
        finding_ids = {str(item.get("id", "")) for item in findings if isinstance(item, dict)}
        record["parsed_stdout"] = payload
        if finding_ids and all("repo_registry" in item or "nested" in item for item in finding_ids):
            record["status"] = "warn"
            record["classification"] = "external_registry_mismatch"
    return record


def command_gateway_safety_probe() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "tools"))
    import aurora_command_intent as gateway  # pylint: disable=import-error,import-outside-toplevel

    failures: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {
        "cloudbank_parser_present": gateway.COMMAND_GRAMMAR_PATH.exists(),
    }

    envelope = gateway.envelope_for(
        "THREADWAKE",
        intent_type="execute_request",
        target_repo=gateway.CLOUDBANK_REPO_REF,
    )
    details["execute_request_envelope"] = {
        "execution_status": envelope.get("execution_status"),
        "execution_scope": envelope.get("execution_scope"),
        "live_runtime_execution": envelope.get("live_runtime_execution"),
        "runtime_handler_verified": envelope.get("runtime_handler_verified"),
        "gumas_mutation_auth_required": envelope.get("gumas_mutation_auth_required"),
        "gumas_mutation_auth_status": envelope.get("gumas_mutation_auth_status"),
        "gumas_mutation_auth_refs": envelope.get("gumas_mutation_auth_refs"),
    }
    if envelope.get("execution_status") != "blocked_pending_verification":
        failures.append("execute_request envelope is not blocked pending verification")
    if envelope.get("live_runtime_execution") is not False:
        failures.append("execute_request envelope does not explicitly deny live runtime execution")
    if envelope.get("runtime_handler_verified") is not False:
        failures.append("execute_request envelope claims a runtime handler was verified")
    if envelope.get("gumas_mutation_auth_required") is not True:
        failures.append("execute_request envelope does not require GUMAS mutation authorization")
    if envelope.get("gumas_mutation_auth_status") != "required_not_verified":
        failures.append("execute_request envelope does not block on unverified GUMAS mutation authorization")
    if envelope.get("gumas_mutation_auth_refs"):
        failures.append("execute_request envelope claims GUMAS mutation authorization evidence")

    if not gateway.COMMAND_GRAMMAR_PATH.exists():
        warnings.append("CloudBank parser unavailable; simulate-range probe skipped")
        return {
            "name": "command_gateway_safety",
            "status": check_status(failures, warnings),
            "classification": "parser_unavailable" if warnings and not failures else check_status(failures, warnings),
            "details": details,
            "failures": failures,
            "warnings": warnings,
        }

    status, payload = gateway.simulate_range("001//003//", max_steps=10)
    details["simulate_range"] = {
        "return_status": status,
        "ok": payload.get("ok"),
        "execution_scope": payload.get("execution_scope"),
        "live_runtime_execution": payload.get("live_runtime_execution"),
        "simulation_status": payload.get("simulation_status"),
        "gumas_mutation_auth_required": payload.get("gumas_mutation_auth_required"),
        "gumas_mutation_auth_status": payload.get("gumas_mutation_auth_status"),
        "intent_gumas_mutation_auth_required": payload.get("intent", {}).get("gumas_mutation_auth_required"),
        "intent_gumas_mutation_auth_status": payload.get("intent", {}).get("gumas_mutation_auth_status"),
        "intent_execution_status": payload.get("intent", {}).get("execution_status"),
        "intent_runtime_handler_verified": payload.get("intent", {}).get("runtime_handler_verified"),
    }
    if status != 0:
        failures.append("simulate-range probe did not complete")
    if payload.get("execution_scope") != "in_process_simulation":
        failures.append("simulate-range did not label execution_scope as in_process_simulation")
    if payload.get("live_runtime_execution") is not False:
        failures.append("simulate-range does not explicitly deny live runtime execution")
    if payload.get("simulation_status") != "completed":
        failures.append("simulate-range did not report simulation_status completed")
    if payload.get("gumas_mutation_auth_required") is not False:
        failures.append("simulate-range claims GUMAS mutation authorization is required")
    if payload.get("gumas_mutation_auth_status") != "not_applicable":
        failures.append("simulate-range does not label GUMAS mutation authorization as not_applicable")
    intent = payload.get("intent", {})
    if intent.get("execution_status") != "not_applicable":
        failures.append("simulate-range intent should not claim live execution")
    if intent.get("runtime_handler_verified") is not False:
        failures.append("simulate-range intent should not claim live runtime handler verification")
    if intent.get("gumas_mutation_auth_required") is not False:
        failures.append("simulate-range intent claims GUMAS mutation authorization is required")
    if intent.get("gumas_mutation_auth_status") != "not_applicable":
        failures.append("simulate-range intent should label GUMAS mutation authorization as not_applicable")

    return {
        "name": "command_gateway_safety",
        "status": check_status(failures, warnings),
        "classification": check_status(failures, warnings),
        "details": details,
        "failures": failures,
        "warnings": warnings,
    }


def schema_presence_check() -> dict[str, Any]:
    failures: list[str] = []
    details: dict[str, Any] = {}
    for path in (COMMAND_SCHEMA, AUDIT_SCHEMA, CONFIDENCE_SCHEMA, CONFIDENCE_CONTRACT):
        try:
            payload = load_json(path)
        except FileNotFoundError:
            failures.append(f"missing schema: {relpath(path)}")
            continue
        except json.JSONDecodeError as exc:
            failures.append(f"invalid JSON schema {relpath(path)}: {exc}")
            continue
        details[relpath(path)] = {
            "title": payload.get("title"),
            "required": payload.get("required", []),
        }

    command_props = details.get(relpath(COMMAND_SCHEMA), {})
    required_command_props = {
        "run_mode",
        "execution_scope",
        "live_runtime_execution",
        "simulation_status",
        "gumas_mutation_auth_required",
        "gumas_mutation_auth_status",
        "gumas_mutation_auth_refs",
    }
    if command_props:
        payload = load_json(COMMAND_SCHEMA)
        missing = sorted(required_command_props - set(payload.get("properties", {})))
        if missing:
            failures.append(f"command intent schema missing safety properties: {missing}")
        missing_required = sorted(required_command_props - set(payload.get("required", [])))
        if missing_required:
            failures.append(f"command intent schema missing required safety properties: {missing_required}")

    return {
        "name": "schema_presence",
        "status": check_status(failures, []),
        "classification": check_status(failures, []),
        "details": details,
        "failures": failures,
        "warnings": [],
    }


def confidence_audit_probe() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "tools"))
    import aurora_confidence_audit as confidence  # pylint: disable=import-error,import-outside-toplevel

    failures: list[str] = []
    warnings: list[str] = []
    record = confidence.build_confidence_record(
        {
            "claim_type": "recommendation",
            "text": "Proceed without further evidence.",
            "visibility": "user_facing",
            "score": 0.45,
            "threshold": 0.70,
            "authority_refs": [relpath(CONFIDENCE_CONTRACT)],
        },
        generated_at="2026-05-21T00:00:00Z",
    )
    details = {
        "schema_path": relpath(CONFIDENCE_SCHEMA),
        "contract_path": relpath(CONFIDENCE_CONTRACT),
        "score": record["confidence"]["score"],
        "threshold": record["confidence"]["threshold"],
        "requires_user_alert": record["audit"]["requires_user_alert"],
        "alert_reason": record["audit"]["alert_reason"],
        "live_runtime_execution": record["audit"]["live_runtime_execution"],
        "nested_repo_mutation": record["audit"]["nested_repo_mutation"],
    }
    if record["audit"]["requires_user_alert"] is not True:
        failures.append("low-confidence recommendation did not require a user alert")
    if record["audit"]["alert_reason"] != "confidence_below_threshold":
        failures.append("low-confidence recommendation did not preserve alert reason")
    if record["audit"]["live_runtime_execution"] is not False:
        failures.append("confidence audit probe claims live runtime execution")
    if record["audit"]["nested_repo_mutation"] is not False:
        failures.append("confidence audit probe claims nested repo mutation")
    if not CONFIDENCE_SCHEMA.exists():
        failures.append(f"missing confidence schema: {relpath(CONFIDENCE_SCHEMA)}")
    if not CONFIDENCE_CONTRACT.exists():
        failures.append(f"missing confidence contract: {relpath(CONFIDENCE_CONTRACT)}")

    return {
        "name": "confidence_audit",
        "status": check_status(failures, warnings),
        "classification": check_status(failures, warnings),
        "details": details,
        "failures": failures,
        "warnings": warnings,
    }


def provenance_gate(report_path: Path = RECOVERY_REPORT) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"report_path": relpath(report_path)}
    try:
        report = load_json(report_path)
    except FileNotFoundError:
        failures.append(f"missing recovery report: {relpath(report_path)}")
        return {
            "name": "provenance_gate",
            "status": "fail",
            "classification": "missing_recovery_report",
            "details": details,
            "failures": failures,
            "warnings": warnings,
        }

    candidates = report.get("candidates", [])
    promoted_without_receipts = []
    for candidate in candidates:
        promotion_status = candidate.get("promotion_status")
        canonical_status = candidate.get("canonical_status")
        has_receipt = bool(
            candidate.get("promotion_receipt")
            or candidate.get("receipt_ref")
            or candidate.get("receipt_refs")
        )
        if (promotion_status != "pending_review" or canonical_status != "not_promoted") and not has_receipt:
            promoted_without_receipts.append(candidate.get("path", "<unknown>"))

    if promoted_without_receipts:
        failures.append(
            "recovery candidates changed promotion/canonical status without receipt: "
            + ", ".join(str(item) for item in promoted_without_receipts[:10])
        )

    summary = report.get("summary", {})
    details.update(
        {
            "status": report.get("status"),
            "generated_at": report.get("generated_at"),
            "candidate_count": summary.get("candidate_count", len(candidates)),
            "discovered_candidate_count": summary.get("discovered_candidate_count"),
            "restricted_candidate_count": sum(
                1 for item in candidates if item.get("restricted_material_possible")
            ),
        }
    )
    if report.get("status") not in {"READY", "WARN"}:
        warnings.append(f"recovery report status is {report.get('status')}")

    return {
        "name": "provenance_gate",
        "status": check_status(failures, warnings),
        "classification": check_status(failures, warnings),
        "details": details,
        "failures": failures,
        "warnings": warnings,
    }


def docs_path_authority_check() -> dict[str, Any]:
    canonical = "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"
    stale = "- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`"
    mutation_auth_phrase = "GUMAS mutation authorization"
    failures: list[str] = []
    details: dict[str, Any] = {}
    for path in (ROOT / "README.md", ROOT / "AGENTS.md"):
        text = path.read_text(encoding="utf-8")
        details[relpath(path)] = {
            "canonical_path_present": canonical in text,
            "stale_bullet_present": stale in text,
            "gumas_mutation_auth_present": mutation_auth_phrase in text,
        }
        if canonical not in text:
            failures.append(f"{relpath(path)} does not expose canonical CloudBank path")
        if stale in text:
            failures.append(f"{relpath(path)} still exposes stale CloudBank bullet path")
        if mutation_auth_phrase not in text:
            failures.append(f"{relpath(path)} does not declare the GUMAS mutation authorization gate")
    return {
        "name": "docs_path_authority",
        "status": check_status(failures, []),
        "classification": check_status(failures, []),
        "details": details,
        "failures": failures,
        "warnings": [],
    }


def default_commands() -> list[tuple[str, list[str]]]:
    return [
        (
            "focused_command_agent_tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "tests/test_aurora_command_intent.py",
                "tests/test_aurora_command_grammar_plugin.py",
                "tests/test_agent_dispatcher_skill.py",
                "tests/test_sync_codex_skill.py",
                "tests/test_session_claim.py",
            ],
        ),
        (
            "session_claim_check",
            [sys.executable, "tools/session_claim.py", "check", "--repo", "root", "--paths", ".", "--json"],
        ),
        (
            "installed_skill_sync_dry_run",
            [
                sys.executable,
                "tools/sync_codex_skill.py",
                "--skill",
                "agent-dispatcher",
                "--dry-run",
                "--validate-package",
            ],
        ),
        (
            "recovery_index_summary",
            [sys.executable, "tools/workspace_recovery_index.py", "--summary"],
        ),
        (
            "recommendation_engine_summary",
            [sys.executable, "tools/aurora_recommendation_engine.py", "--summary"],
        ),
        ("workspace_verify", [sys.executable, "tools/workspace_verify.py"]),
    ]


def overall_verdict(checks: list[dict[str, Any]], commands: list[dict[str, Any]]) -> str:
    records = checks + commands
    if any(record.get("status") == "fail" for record in records):
        return "fail"
    if records and all(record.get("classification") == "external_registry_mismatch" for record in records):
        return "blocked_external"
    if any(record.get("status") == "warn" for record in records):
        return "warn"
    return "pass"


def build_report(run_subprocess: bool = True) -> dict[str, Any]:
    checks = [
        command_gateway_safety_probe(),
        schema_presence_check(),
        confidence_audit_probe(),
        provenance_gate(),
        docs_path_authority_check(),
    ]
    commands = [run_command(name, command) for name, command in default_commands()] if run_subprocess else []
    return {
        "schema_version": 1,
        "generated_at": now_iso_utc(),
        "tool": "aurora_integration_gate",
        "root": ".",
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
        },
        "run_mode": "read_only",
        "nested_repo_mutation": False,
        "checks": checks,
        "commands": commands,
        "verdict": overall_verdict(checks, commands),
    }


def format_summary(report: dict[str, Any]) -> str:
    lines = [
        f"Aurora Integration Gate: {report['verdict']}",
        f"- Run mode: {report['run_mode']}",
        f"- Nested repo mutation: {report['nested_repo_mutation']}",
        "- Checks:",
    ]
    for check in report["checks"]:
        lines.append(f"  - {check['name']}: {check['status']} ({check['classification']})")
    if report["commands"]:
        lines.append("- Commands:")
        for command in report["commands"]:
            lines.append(f"  - {command['name']}: {command['status']} ({command['classification']})")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Aurora root integration quality gate.")
    parser.add_argument("--summary", action="store_true", help="Print a compact text summary.")
    parser.add_argument("--report-out", help="Write the JSON report to this path.")
    parser.add_argument(
        "--skip-subprocess",
        action="store_true",
        help="Run built-in safety/provenance checks only; used by focused tests.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(run_subprocess=not args.skip_subprocess)
    if args.report_out:
        write_json(Path(args.report_out).expanduser().resolve(), report)
    if args.summary:
        print(format_summary(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] in {"pass", "warn"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
