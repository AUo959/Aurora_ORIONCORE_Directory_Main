#!/usr/bin/env python3
"""Root command-intent gateway for Aurora command grammar.

This tool is a control-plane adapter. It delegates parser/runtime semantics to
the CloudBank nested repo when those modules are present, and it does not send
mesh messages or mutate live runtime state.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
CLOUDBANK_REPO = ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture" / "aurora-cloudbank-symbolic-main"
CLOUDBANK_SRC = CLOUDBANK_REPO / "src"
COMMAND_GRAMMAR_PATH = CLOUDBANK_SRC / "aurora" / "core" / "command_grammar"
SYMBOLIC_ENGINE_PATH = CLOUDBANK_SRC / "aurora" / "core" / "symbolic_engine.py"
SCHEMA_PATH = (
    ROOT
    / "plugins"
    / "aurora-command-grammar"
    / "skills"
    / "aurora-command-grammar"
    / "references"
    / "command-intent-envelope.schema.json"
)
CLOUDBANK_REPO_REF = "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"
COMMAND_GRAMMAR_REF = (
    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/"
    "src/aurora/core/command_grammar"
)
SYMBOLIC_ENGINE_REF = (
    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/"
    "src/aurora/core/symbolic_engine.py"
)
SCHEMA_REF = (
    "plugins/aurora-command-grammar/skills/aurora-command-grammar/"
    "references/command-intent-envelope.schema.json"
)

_COMMANDISH_HEAD = re.compile(r"^[+#]?[A-Z0-9][A-Z0-9_.:#-]*(?:\(.*\))?$")


class CloudBankLoadError(RuntimeError):
    """Raised when CloudBank parser or runtime modules cannot be loaded."""


def enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_cloudbank_command_grammar() -> Any:
    if not COMMAND_GRAMMAR_PATH.exists():
        raise CloudBankLoadError(f"CloudBank command grammar path is missing: {relpath(COMMAND_GRAMMAR_PATH)}")

    sys.dont_write_bytecode = True
    src = str(CLOUDBANK_SRC)
    if src not in sys.path:
        sys.path.insert(0, src)

    try:
        module = importlib.import_module("aurora.core.command_grammar")
    except Exception as exc:  # pragma: no cover - message path exercised by callers
        raise CloudBankLoadError(f"Unable to import CloudBank command grammar: {exc}") from exc
    return module


def load_symbolic_engine() -> Any:
    if not SYMBOLIC_ENGINE_PATH.exists():
        raise CloudBankLoadError(f"CloudBank SymbolicEngine path is missing: {relpath(SYMBOLIC_ENGINE_PATH)}")

    load_cloudbank_command_grammar()
    try:
        module = importlib.import_module("aurora.core.symbolic_engine")
    except Exception as exc:  # pragma: no cover - message path exercised by callers
        raise CloudBankLoadError(f"Unable to import CloudBank SymbolicEngine: {exc}") from exc
    return module.SymbolicEngine


def looks_symbolic(raw_text: str, parse_result: Optional[Any] = None) -> bool:
    text = raw_text.strip()
    if not text or text.startswith("@mesh"):
        return False
    if "//" in text or "::" in text or text.startswith(("+", "#")):
        return True
    if parse_result is not None and getattr(parse_result, "is_valid", False):
        return True

    first = text.split()[0]
    if "(" in first:
        first = first.split("(", 1)[0] + "()"
    return bool(_COMMANDISH_HEAD.match(first))


def warning_dicts(warnings: Iterable[Any]) -> List[Dict[str, str]]:
    return [{"code": enum_value(warning.code), "message": str(warning.message)} for warning in warnings]


def issue_dicts(issues: Iterable[Any]) -> List[Dict[str, Optional[str]]]:
    out: List[Dict[str, Optional[str]]] = []
    for issue in issues:
        out.append(
            {
                "code": str(issue.code),
                "severity": enum_value(issue.severity),
                "message": str(issue.message),
                "head": getattr(issue, "head", None),
            }
        )
    return out


def validation_status(warnings: List[Dict[str, str]], issues: List[Dict[str, Optional[str]]]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "invalid"
    if warnings or any(issue["severity"] == "warning" for issue in issues):
        return "valid_with_warnings"
    return "valid"


def ast_fields(ast_node: Any) -> Dict[str, Any]:
    class_name = ast_node.__class__.__name__

    if class_name == "RangeChain":
        return {
            "ast_shape": "range_chain",
            "command_heads": [],
            "range_edges": {"start": f"{ast_node.start:03d}", "end": f"{ast_node.end:03d}"},
            "arguments": [],
            "modifier": None,
        }

    if class_name == "CommandSequence":
        invocations = list(getattr(ast_node, "invocations", ()))
        return {
            "ast_shape": "command_sequence",
            "command_heads": [str(invocation.canonical_head) for invocation in invocations],
            "range_edges": None,
            "arguments": argument_dicts(argument for invocation in invocations for argument in invocation.arguments),
            "modifier": None,
        }

    if class_name == "CommandInvocation":
        return {
            "ast_shape": "command_invocation",
            "command_heads": [str(ast_node.canonical_head)],
            "range_edges": None,
            "arguments": argument_dicts(getattr(ast_node, "arguments", ())),
            "modifier": getattr(ast_node, "modifier", None),
        }

    return {
        "ast_shape": "unknown",
        "command_heads": [],
        "range_edges": None,
        "arguments": [],
        "modifier": None,
    }


def argument_dicts(arguments: Iterable[Any]) -> List[Dict[str, Optional[str]]]:
    out: List[Dict[str, Optional[str]]] = []
    for argument in arguments:
        out.append(
            {
                "name": getattr(argument, "name", None),
                "value": str(argument.value),
                "kind": enum_value(argument.kind),
            }
        )
    return out


def empty_envelope(raw_text: str, grammar_family: str, ast_shape: Optional[str]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "raw_text": raw_text,
        "normalized_text": None,
        "intent_type": "parse",
        "grammar_family": grammar_family,
        "ast_shape": ast_shape,
        "command_heads": [],
        "range_edges": None,
        "arguments": [],
        "modifier": None,
        "warnings": [],
        "validation_status": "not_validated",
        "validation_issues": [],
        "run_mode": "parse_only",
        "execution_scope": "none",
        "live_runtime_execution": False,
        "simulation_status": "not_applicable",
        "runtime_handler_verified": False,
        "runtime_refs": [],
        "execution_status": "not_requested",
        "target_repo": None,
        "authority_refs": [SCHEMA_REF],
        "recommended_next_action": "No command action is available from this input.",
        "receipt_refs": [],
    }


def parse_command_intent(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()
    if not text:
        record = empty_envelope(raw_text, "unknown", "none")
        record["validation_status"] = "invalid"
        record["validation_issues"] = [
            {
                "code": "empty_input",
                "severity": "error",
                "message": "Command text is empty.",
                "head": None,
            }
        ]
        record["recommended_next_action"] = "Provide command text before parsing."
        return record

    if text.startswith("@mesh"):
        record = empty_envelope(raw_text, "mesh_router", "mesh_route")
        record["normalized_text"] = text
        record["validation_status"] = "not_validated"
        record["run_mode"] = "mesh_route_map"
        record["recommended_next_action"] = (
            "Map through the mesh-router runtime contract before routing; no mesh message was sent."
        )
        return record

    authority_refs = [COMMAND_GRAMMAR_REF, SCHEMA_REF]
    try:
        command_grammar = load_cloudbank_command_grammar()
        parser = command_grammar.AuroraCommandGrammar()
        result = parser.parse(raw_text)
    except CloudBankLoadError as exc:
        record = empty_envelope(raw_text, "unknown", "unknown")
        record["validation_issues"] = [
            {
                "code": "cloudbank_parser_unavailable",
                "severity": "error",
                "message": str(exc),
                "head": None,
            }
        ]
        record["authority_refs"] = authority_refs
        record["recommended_next_action"] = "Restore the CloudBank parser path before validating command grammar."
        return record
    except Exception as exc:
        record = empty_envelope(raw_text, "aurora_symbolic_command" if looks_symbolic(raw_text) else "unknown", "unknown")
        record["validation_status"] = "invalid"
        record["validation_issues"] = [
            {
                "code": "parse_error",
                "severity": "error",
                "message": str(exc),
                "head": None,
            }
        ]
        record["authority_refs"] = authority_refs
        record["recommended_next_action"] = "Resolve the parse error before routing or execution."
        return record

    warnings = warning_dicts(result.warnings)
    issues = issue_dicts(result.validation_issues)
    symbolic = looks_symbolic(raw_text, result)
    if not symbolic:
        record = empty_envelope(raw_text, "ordinary_prose", "none")
        record["validation_status"] = "not_applicable"
        record["authority_refs"] = authority_refs
        record["recommended_next_action"] = "Treat as prose unless the user supplies Aurora command notation."
        return record

    record = {
        "schema_version": "1.0.0",
        "raw_text": raw_text,
        "normalized_text": result.normalized_text,
        "intent_type": "parse",
        "grammar_family": "aurora_symbolic_command",
        **ast_fields(result.ast),
        "warnings": warnings,
        "validation_status": validation_status(warnings, issues),
        "validation_issues": issues,
        "run_mode": "parse_only",
        "execution_scope": "none",
        "live_runtime_execution": False,
        "simulation_status": "not_applicable",
        "runtime_handler_verified": False,
        "runtime_refs": [],
        "execution_status": "not_requested",
        "target_repo": None,
        "authority_refs": authority_refs,
        "recommended_next_action": "Verify target repo and live runtime before execution; grammar-valid text is not execution approval.",
        "receipt_refs": [],
    }
    if record["validation_status"] == "invalid":
        record["recommended_next_action"] = "Resolve validation issues before routing or execution."
    return record


def envelope_for(
    raw_text: str,
    intent_type: str = "parse",
    target_repo: Optional[str] = None,
    receipt_refs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    envelope = parse_command_intent(raw_text)
    envelope["intent_type"] = intent_type
    envelope["target_repo"] = target_repo
    envelope["receipt_refs"] = receipt_refs or []
    if intent_type == "background_handoff":
        envelope["run_mode"] = "background_handoff"
    if intent_type == "execute_request":
        envelope["run_mode"] = "blocked_execution_request"
        envelope["execution_scope"] = "blocked_pending_runtime_verification"
        envelope["live_runtime_execution"] = False
        envelope["execution_status"] = "blocked_pending_verification"
        envelope["recommended_next_action"] = (
            "Verify target repo and runtime, then request explicit approval before execution."
        )
    return envelope


def simulate_range(raw_text: str, max_steps: int) -> Tuple[int, Dict[str, Any]]:
    envelope = envelope_for(raw_text, intent_type="execute_request", target_repo=CLOUDBANK_REPO_REF)
    envelope["execution_status"] = "blocked_pending_verification"
    envelope["run_mode"] = "in_process_simulation"
    envelope["execution_scope"] = "in_process_simulation"
    envelope["live_runtime_execution"] = False
    envelope["simulation_status"] = "blocked"

    base = {
        "ok": False,
        "mode": "in_process_simulation",
        "run_mode": "in_process_simulation",
        "execution_scope": "in_process_simulation",
        "live_runtime_execution": False,
        "simulation_status": "blocked",
        "parser_authority": COMMAND_GRAMMAR_REF,
        "runtime_authority": SYMBOLIC_ENGINE_REF,
        "intent": envelope,
    }

    if envelope["ast_shape"] != "range_chain" or envelope["validation_status"] not in {"valid", "valid_with_warnings"}:
        base["error"] = "simulate-range only accepts valid numeric RangeChain input."
        envelope["recommended_next_action"] = "Supply a valid numeric RangeChain such as 001//005//."
        return 2, base

    assert envelope["range_edges"] is not None
    start = int(envelope["range_edges"]["start"])
    end = int(envelope["range_edges"]["end"])
    step_count = end - start + 1
    if step_count > max_steps:
        base["error"] = f"Range has {step_count} steps, exceeding --max-steps={max_steps}."
        envelope["recommended_next_action"] = "Use a smaller in-process range or raise --max-steps deliberately."
        return 2, base

    try:
        symbolic_engine = load_symbolic_engine()
        engine = symbolic_engine()
        results = engine.execute_chain_notation(envelope["normalized_text"] or raw_text)
    except CloudBankLoadError as exc:
        base["error"] = str(exc)
        base["simulation_status"] = "failed"
        envelope["simulation_status"] = "failed"
        envelope["validation_issues"].append(
            {
                "code": "symbolic_engine_unavailable",
                "severity": "error",
                "message": str(exc),
                "head": None,
            }
        )
        envelope["validation_status"] = "not_validated"
        return 2, base
    except Exception as exc:
        base["error"] = str(exc)
        base["simulation_status"] = "failed"
        envelope["simulation_status"] = "failed"
        envelope["execution_status"] = "not_applicable"
        envelope["validation_issues"].append(
            {
                "code": "simulation_failed",
                "severity": "error",
                "message": str(exc),
                "head": None,
            }
        )
        return 1, base

    chain_id = f"{start:03d}//{end:03d}//"
    envelope["runtime_handler_verified"] = False
    envelope["runtime_refs"] = [SYMBOLIC_ENGINE_REF + "::SymbolicEngine.execute_chain_notation"]
    envelope["execution_status"] = "not_applicable"
    envelope["simulation_status"] = "completed"
    envelope["recommended_next_action"] = (
        "Review the in-process simulation output; no live runtime state was changed."
    )
    base.update(
        {
            "ok": True,
            "simulation_status": "completed",
            "simulation_label": "in-process SymbolicEngine simulation only; not live runtime execution",
            "chain_id": chain_id,
            "step_count": len(results),
            "results": results,
            "engine_manifest": engine.export_manifest(),
            "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
            "determinism_note": (
                "SRB resolution values follow CloudBank SymbolicEngine in this process; "
                "set PYTHONHASHSEED for repeatable hash-derived SRB numbers."
            ),
        }
    )
    return 0, base


def resolve_text(args: argparse.Namespace) -> str:
    value = getattr(args, "text_option", None)
    if value is not None:
        return value
    positional = getattr(args, "text", None)
    if positional is not None:
        return positional
    return sys.stdin.read()


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse Aurora command text into typed command-intent records without executing live runtime actions."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Normalize and classify command input.")
    parse.add_argument("text", nargs="?", help="Command text. Reads stdin if omitted.")
    parse.add_argument("--text", dest="text_option", help="Command text, useful when shell quoting is awkward.")

    envelope = subparsers.add_parser("envelope", help="Emit command-intent-envelope-compatible JSON.")
    envelope.add_argument("text", nargs="?", help="Command text. Reads stdin if omitted.")
    envelope.add_argument("--text", dest="text_option", help="Command text, useful when shell quoting is awkward.")
    envelope.add_argument(
        "--intent-type",
        default="parse",
        choices=[
            "parse",
            "normalize",
            "validate",
            "explain",
            "mesh_route_map",
            "execute_request",
            "background_handoff",
        ],
    )
    envelope.add_argument("--target-repo", default=None)
    envelope.add_argument("--receipt-ref", action="append", default=[])

    simulate = subparsers.add_parser(
        "simulate-range",
        help="Run a valid numeric RangeChain through CloudBank SymbolicEngine in memory only.",
    )
    simulate.add_argument("text", nargs="?", help="RangeChain text. Reads stdin if omitted.")
    simulate.add_argument("--text", dest="text_option", help="RangeChain text, useful when shell quoting is awkward.")
    simulate.add_argument("--max-steps", type=int, default=1000, help="Safety limit for in-process simulation.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    raw_text = resolve_text(args)

    if args.command == "parse":
        record = parse_command_intent(raw_text)
        print_json(
            {
                "ok": record["validation_status"] not in {"invalid", "not_validated"},
                "mode": "parse",
                "run_mode": record["run_mode"],
                "execution_scope": record["execution_scope"],
                "live_runtime_execution": record["live_runtime_execution"],
                "parser_authority": COMMAND_GRAMMAR_REF,
                "schema_path": SCHEMA_REF,
                "intent": record,
            }
        )
        return 0

    if args.command == "envelope":
        print_json(
            envelope_for(
                raw_text,
                intent_type=args.intent_type,
                target_repo=args.target_repo,
                receipt_refs=list(args.receipt_ref),
            )
        )
        return 0

    status, payload = simulate_range(raw_text, max_steps=args.max_steps)
    print_json(payload)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
