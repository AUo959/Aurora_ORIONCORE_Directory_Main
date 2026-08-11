#!/usr/bin/env python3
"""Query the Aurora Canon Engine (ACE) capability router and character slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ace import ACEError, build_capability_index, compile_character_query, resolve_character_query
from ace.core import ROOT, load_json, validate_json_schema


def _context(path: str) -> dict[str, Any]:
    payload = load_json(Path(path).expanduser().resolve())
    if not isinstance(payload, dict):
        raise ACEError("context JSON must contain an object", code="input_validation_failed")
    return payload


def _compiled(args: argparse.Namespace, mode: str) -> dict[str, Any]:
    if args.query:
        payload = load_json(Path(args.query).expanduser().resolve())
        if not isinstance(payload, dict):
            raise ACEError("query envelope must contain an object", code="input_validation_failed")
        return payload
    if not args.question or not args.context:
        raise ACEError("provide --query or both --question and --context", code="input_validation_failed")
    return compile_character_query(
        args.question,
        _context(args.context),
        seed=args.seed,
        mode=mode,
        requester_kind=args.requester_kind,
        requester_id=args.requester_id,
        session_ref=args.session_ref,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("capabilities", help="Show the warm, evidence-checked ACE capability index.")

    for command, help_text in (
        ("plan", "Compile the semantic query and specialist execution plan without writing artifacts."),
        ("resolve", "Execute a character name/background query into an atomic commit-ready packet."),
    ):
        sub = subparsers.add_parser(command, help=help_text)
        sub.add_argument("--query", help="Existing ACE query-envelope JSON.")
        sub.add_argument("--question", help="Natural-language question to compile.")
        sub.add_argument("--context", help="Character context JSON object.")
        sub.add_argument("--seed", type=int, default=808)
        sub.add_argument("--requester-kind", choices=["user", "operations", "agent", "system"], default="user")
        sub.add_argument("--requester-id", default="ORION.ROLE.PILOT")
        sub.add_argument("--session-ref")
        if command == "resolve":
            sub.add_argument("--out", required=True, help="New packet directory outside nested repositories.")

    validate = subparsers.add_parser("validate", help="Validate an ACE query or determination receipt.")
    validate.add_argument("artifact")
    validate.add_argument("--kind", choices=["query", "determination"], required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capabilities":
            print(json.dumps(build_capability_index(), indent=2, sort_keys=True))
            return 0
        if args.command == "plan":
            query = _compiled(args, "plan_only")
            index = build_capability_index()
            route = [
                item for item in index["capabilities"]
                if item["capability_id"] in {
                    ref
                    for output in query["requested_outputs"]
                    for ref in output["preferred_capability_refs"]
                }
                or item["capability_id"] in {
                    "ace.capability.context.resolve",
                    "ace.capability.canonrec.project.name_reservations",
                    "ace.capability.gumas.state.build_character",
                    "ace.capability.canonrec.validate.entity",
                    "ace.capability.canonrec.validate.naming_receipt",
                }
            ]
            print(json.dumps({"query_envelope": query, "selected_capabilities": route}, indent=2, sort_keys=True))
            return 0
        if args.command == "resolve":
            query = _compiled(args, "commit_ready")
            receipt = resolve_character_query(query, Path(args.out))
            print(json.dumps({
                "ok": True,
                "packet": str(Path(args.out).expanduser().resolve()),
                "status": receipt["status"],
                "materialization": receipt["materialization"]["status"],
                "answer": receipt["answer"]["summary"],
            }, indent=2, sort_keys=True))
            return 0
        schema_name = (
            "aurora_ace_query_envelope.schema.json"
            if args.kind == "query"
            else "aurora_ace_determination_receipt.schema.json"
        )
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
