#!/usr/bin/env python3
"""Query the Aurora Canon Engine (ACE) capability router and supported slices."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ace import (
    ACEError,
    build_capability_index,
    build_invocation_envelope,
    compile_character_invocation,
    compile_facility_invocation,
    compile_facility_invocation_from_seam,
    resolve_invocation,
)
from ace.core import ROOT, load_json, validate_json_schema


def _object(path: str, label: str) -> dict[str, Any]:
    payload = load_json(Path(path).expanduser().resolve())
    if not isinstance(payload, dict):
        raise ACEError(f"{label} JSON must contain an object", code="input_validation_failed")
    return payload


def _caller(args: argparse.Namespace) -> tuple[str, str]:
    return (
        args.caller_kind or args.requester_kind,
        args.caller_ref or args.requester_id,
    )


def _invocation(args: argparse.Namespace, mode: str) -> dict[str, Any]:
    caller_kind, caller_ref = _caller(args)
    if args.seam:
        if args.query or args.question or args.context:
            raise ACEError("--seam cannot be combined with --query, --question, or --context", code="input_validation_failed")
        return compile_facility_invocation_from_seam(
            _object(args.seam, "coherence seam"),
            seed=args.seed,
            mode=mode,
            session_ref=args.session_ref,
        )
    if args.query:
        if args.question or args.context:
            raise ACEError("--query cannot be combined with --question or --context", code="input_validation_failed")
        query = _object(args.query, "query envelope")
        return build_invocation_envelope(
            query,
            invocation_mode=args.invocation_mode,
            caller_kind=caller_kind,
            caller_ref=caller_ref,
            parent_invocation_ref=args.parent_invocation_ref,
            trigger_kind=args.trigger_kind,
            trigger_reason=args.trigger_reason,
            seam_ref=args.seam_ref,
            trigger_policy_ref=args.trigger_policy_ref,
        )
    if not args.question or not args.context:
        raise ACEError("provide --seam, --query, or both --question and --context", code="input_validation_failed")
    context = _object(args.context, "context")
    common = {
        "seed": args.seed,
        "mode": mode,
        "invocation_mode": args.invocation_mode,
        "caller_kind": caller_kind,
        "caller_ref": caller_ref,
        "parent_invocation_ref": args.parent_invocation_ref,
        "trigger_kind": args.trigger_kind,
        "trigger_reason": args.trigger_reason,
        "seam_ref": args.seam_ref,
        "trigger_policy_ref": args.trigger_policy_ref,
        "session_ref": args.session_ref,
    }
    if args.subject_kind == "facility":
        return compile_facility_invocation(
            args.question,
            context,
            subject_ref=context.get("subject_ref"),
            **common,
        )
    return compile_character_invocation(args.question, context, **common)


def _add_invocation_arguments(sub: argparse.ArgumentParser) -> None:
    sub.add_argument(
        "--invocation-mode",
        choices=["interactive", "embedded", "autonomic"],
        default="interactive",
        help="How ACE was invoked. Automatic invocation remains inspectable.",
    )
    sub.add_argument(
        "--caller-kind",
        choices=["user", "operations", "agent", "system", "capability"],
        help="First-class caller class. Defaults to --requester-kind.",
    )
    sub.add_argument("--caller-ref", help="First-class caller identity. Defaults to --requester-id.")
    sub.add_argument("--parent-invocation-ref", help="Parent ACE/Aurora workflow invocation reference.")
    sub.add_argument(
        "--trigger-kind",
        choices=["direct_query", "capability_call", "coherence_seam", "policy_event"],
        help="Reason class that caused ACE to run.",
    )
    sub.add_argument("--trigger-reason", help="Human-readable reason ACE was invoked.")
    sub.add_argument("--seam-ref", help="Required coherence-seam reference for autonomic invocation.")
    sub.add_argument("--trigger-policy-ref", help="Required trigger-policy reference for autonomic invocation.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("capabilities", help="Show the warm, evidence-checked ACE capability index.")

    for command, help_text in (
        ("plan", "Compile a supported ACE query and specialist execution plan without writing artifacts."),
        ("resolve", "Execute a supported ACE query into an atomic commit-ready packet."),
    ):
        sub = subparsers.add_parser(command, help=help_text)
        sub.add_argument("--seam", help="CloudBank ACE coherence-seam JSON; currently supports facility topology seams.")
        sub.add_argument("--query", help="Existing ACE query-envelope JSON.")
        sub.add_argument("--question", help="Natural-language question to compile.")
        sub.add_argument("--context", help="Structured subject context JSON object.")
        sub.add_argument(
            "--subject-kind",
            choices=["character", "facility"],
            default="character",
            help="Compiler used for direct --question/--context input.",
        )
        sub.add_argument("--seed", type=int, default=808)
        sub.add_argument("--requester-kind", choices=["user", "operations", "agent", "system"], default="user")
        sub.add_argument("--requester-id", default="ORION.ROLE.PILOT")
        sub.add_argument("--session-ref")
        _add_invocation_arguments(sub)
        if command == "resolve":
            sub.add_argument("--out", required=True, help="New packet directory outside nested repositories.")

    validate = subparsers.add_parser("validate", help="Validate an ACE query, invocation, or determination receipt.")
    validate.add_argument("artifact")
    validate.add_argument("--kind", choices=["query", "invocation", "determination"], required=True)
    return parser


def _selected_capabilities(query: dict[str, Any]) -> list[dict[str, Any]]:
    index = build_capability_index()
    preferred = {
        ref
        for output in query["requested_outputs"]
        for ref in output["preferred_capability_refs"]
    }
    entity_type = query.get("subject", {}).get("entity_type")
    required = {"ace.capability.context.resolve"}
    if entity_type == "character":
        required |= {
            "ace.capability.canonrec.project.name_reservations",
            "ace.capability.gumas.state.build_character",
            "ace.capability.canonrec.validate.entity",
            "ace.capability.canonrec.validate.naming_receipt",
        }
    elif entity_type == "facility":
        required.add("ace.capability.canonrec.materialize.entity")
    return [
        item
        for item in index["capabilities"]
        if item["capability_id"] in preferred | required
    ]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capabilities":
            print(json.dumps(build_capability_index(), indent=2, sort_keys=True))
            return 0
        if args.command == "plan":
            invocation = _invocation(args, "plan_only")
            query = invocation["query"]
            print(
                json.dumps(
                    {"invocation": invocation, "selected_capabilities": _selected_capabilities(query)},
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "resolve":
            invocation = _invocation(args, "commit_ready")
            result = resolve_invocation(invocation, Path(args.out))
            receipt = result["determination"]
            print(
                json.dumps(
                    {
                        "ok": True,
                        "invocation_id": invocation["invocation_id"],
                        "invocation_mode": invocation["invocation_mode"],
                        "subject_type": invocation["query"]["subject"]["entity_type"],
                        "invocation_sidecar": result["invocation_sidecar"],
                        "packet": str(Path(args.out).expanduser().resolve()),
                        "status": receipt["status"],
                        "materialization": receipt["materialization"]["status"],
                        "answer": receipt["answer"]["summary"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        schema_name = {
            "query": "aurora_ace_query_envelope.schema.json",
            "invocation": "aurora_ace_invocation_envelope.schema.json",
            "determination": "aurora_ace_determination_receipt.schema.json",
        }[args.kind]
        report = validate_json_schema(
            Path(args.artifact).expanduser().resolve(),
            ROOT / "catalog/schemas" / schema_name,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ok"] else 1
    except ACEError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "code": exc.code}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
