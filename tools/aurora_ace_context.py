#!/usr/bin/env python3
"""Grant bounded simulation assignments and operate their durable ACE queue."""

import argparse
import json
from pathlib import Path

from ace.contextual import ContextQueue
from ace.core import ACEError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    grant = sub.add_parser("authorize")
    grant.add_argument("--assignment", type=Path, required=True)
    revoke = sub.add_parser("revoke")
    revoke.add_argument("--assignment-id", required=True)
    revoke.add_argument("--reason", required=True)
    submit = sub.add_parser("submit")
    submit.add_argument("--assignment-id", required=True)
    submit.add_argument("--need-id", required=True)
    submit.add_argument("--question", required=True)
    submit.add_argument("--context", type=json.loads, default={})
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--job-id", required=True)
    sub.add_parser("status")
    sub.add_parser("work")
    args = parser.parse_args()
    try:
        queue = ContextQueue(args.world)
        if args.command == "authorize":
            result = queue.authorize(**json.loads(args.assignment.read_text()))
        elif args.command == "revoke":
            result = queue.revoke(args.assignment_id, args.reason)
        elif args.command == "submit":
            result = queue.submit(
                args.assignment_id, args.need_id, args.question, args.context
            )
        elif args.command == "inspect":
            result = queue.inspect(args.job_id)
        elif args.command == "work":
            result = queue.work_once()
        else:
            result = queue.status()
        print(json.dumps(result, indent=2))
        return 0
    except (ACEError, ValueError, TypeError, OSError) as exc:
        print(json.dumps({"status": "refused", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
