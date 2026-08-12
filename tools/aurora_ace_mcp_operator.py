#!/usr/bin/env python3
"""Local operator CLI for ACE v0.9 MCP transaction choreography."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ace.core import ACEError
from ace.mcp_operator_transaction import (
    commit_operator_transaction,
    inspect_operator_transaction,
    prepare_operator_transaction,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("invocation file must contain one JSON object")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Drive the local ACE operator lifecycle without widening MCP authority: "
            "prepare -> explicit confirmation -> commit -> inspect."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="resolve and preview a transaction")
    prepare.add_argument("--invocation", type=Path, required=True)
    prepare.add_argument("--output-name", required=True)
    prepare.add_argument("--authority-ref", required=True)

    commit = sub.add_parser("commit", help="commit one prepared transaction exactly once")
    commit.add_argument("--transaction-id", required=True)
    commit.add_argument("--authorization-token", required=True)
    commit.add_argument(
        "--acknowledge-side-effects",
        action="store_true",
        help="explicitly acknowledge the side effects listed in the prepared preview",
    )
    commit.add_argument("--commit-message")

    inspect = sub.add_parser("inspect", help="read one durable operator transaction receipt")
    inspect.add_argument("--transaction-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_operator_transaction(
                _load_json(args.invocation),
                args.output_name,
                args.authority_ref,
            )
        elif args.command == "commit":
            result = commit_operator_transaction(
                args.transaction_id,
                args.authorization_token,
                args.acknowledge_side_effects,
                args.commit_message,
            )
        else:
            result = inspect_operator_transaction(args.transaction_id)
    except (ACEError, OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error_code": getattr(exc, "code", None),
            "message": str(exc),
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
