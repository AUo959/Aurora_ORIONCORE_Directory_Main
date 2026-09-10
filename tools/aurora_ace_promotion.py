#!/usr/bin/env python3
"""Prepare and verify an offline review of a persistent sandbox character."""

import argparse
import json
from pathlib import Path

from ace.core import ACEError
from ace.promotion import prepare, verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("prepare")
    create.add_argument("--world", type=Path, required=True)
    create.add_argument("--request-id", required=True)
    create.add_argument("--target-root", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (
            prepare(args.world, args.request_id, args.target_root, args.output)
            if args.command == "prepare"
            else verify(args.output)
        )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "review_ready" else 2
    except ACEError as exc:
        print(json.dumps({"status": "refused", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
