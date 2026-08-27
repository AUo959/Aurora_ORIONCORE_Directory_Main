#!/usr/bin/env python3
"""Local operator CLI for ACE v0.13 governed Orion L1 progression."""

from __future__ import annotations

import argparse
import json
import sys

from ace.core import ACEError
from ace.orion_progression import (
    commit_orion_advance,
    inspect_orion_progression,
    preview_orion_advance,
    registered_owner_preflight,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Govern one existing Orion L1 tick through the registered CloudBank runtime. "
            "No INIT, provider activation, HTTP, or MCP control surface is exposed."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser(
        "preflight-owner",
        help="verify the exact registered CloudBank owner and run preflight only",
    )
    preflight.set_defaults(command="preflight-owner")

    preview = sub.add_parser(
        "preview",
        help="build a non-mutating state-bound authorization preview",
    )
    preview.add_argument("--run-id", required=True)
    preview.add_argument("--authority-ref", required=True)
    preview.add_argument("--principal-id", default="ORION.ROLE.PILOT")

    commit = sub.add_parser(
        "commit",
        help="consume one fresh authorization for exactly one native tick",
    )
    commit.add_argument("--run-id", required=True)
    commit.add_argument("--authorization-token", required=True)
    commit.add_argument("--authority-ref", required=True)
    commit.add_argument("--principal-id", default="ORION.ROLE.PILOT")
    commit.add_argument(
        "--acknowledge-side-effects",
        action="store_true",
        help="explicitly acknowledge one persisted Orion tick as the side effect",
    )

    inspect = sub.add_parser(
        "inspect",
        help="read one external progression receipt",
    )
    inspect.add_argument("--run-id", required=True)
    inspect.add_argument("--tick", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the local governed Orion progression operator."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "preflight-owner":
            result = registered_owner_preflight()
        elif args.command == "preview":
            result = preview_orion_advance(
                args.run_id,
                args.authority_ref,
                principal_id=args.principal_id,
            )
        elif args.command == "commit":
            result = commit_orion_advance(
                args.run_id,
                args.authorization_token,
                args.authority_ref,
                args.acknowledge_side_effects,
                principal_id=args.principal_id,
            )
        else:
            result = inspect_orion_progression(args.run_id, args.tick)
    except (ACEError, OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error_code": getattr(exc, "code", None),
            "message": str(exc),
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
