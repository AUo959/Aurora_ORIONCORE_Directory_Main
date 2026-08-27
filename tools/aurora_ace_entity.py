#!/usr/bin/env python3
"""Local operator CLI for ACE generic native L2 entity completion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ace.core import ROOT, write_json
from ace.generic_entity import compile_generic_entity_query
from ace.generic_entity_gate import generic_entity_commit, generic_entity_preview
from ace.generic_entity_runtime import resolve_generic_entity_query

RUNTIME_ROOT = ROOT / "reports/ace/generic_entities"


def _load_json(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ACE generic native L2 entity operator")
    sub = p.add_subparsers(dest="command", required=True)

    compile_p = sub.add_parser("compile")
    compile_p.add_argument("--question", required=True)
    compile_p.add_argument("--kind", required=True)
    compile_p.add_argument("--context", required=True, help="JSON file containing entity context")
    compile_p.add_argument("--seed", default="808")
    compile_p.add_argument("--out-query", required=True)

    resolve_p = sub.add_parser("resolve")
    resolve_p.add_argument("--query", required=True)
    resolve_p.add_argument("--output-name", required=True)

    preview_p = sub.add_parser("preview")
    preview_p.add_argument("--output-name", required=True)
    preview_p.add_argument("--authority-ref", required=True)

    commit_p = sub.add_parser("commit")
    commit_p.add_argument("--output-name", required=True)
    commit_p.add_argument("--authority-ref", required=True)
    commit_p.add_argument("--authorization-token", required=True)
    commit_p.add_argument("--acknowledge-side-effects", action="store_true")
    commit_p.add_argument("--commit-message", default=None)
    return p


def main() -> None:
    args = parser().parse_args()
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    if args.command == "compile":
        query = compile_generic_entity_query(
            args.question,
            args.kind,
            _load_json(args.context),
            seed=args.seed,
            root=ROOT,
        )
        write_json(Path(args.out_query), query)
        result = query
    elif args.command == "resolve":
        output = (RUNTIME_ROOT / args.output_name).resolve()
        if RUNTIME_ROOT.resolve() not in output.parents:
            raise SystemExit("output-name escaped generic entity runtime root")
        result = resolve_generic_entity_query(_load_json(args.query), output, root=ROOT)
    elif args.command == "preview":
        result = generic_entity_preview(args.output_name, args.authority_ref, root=ROOT, runtime_root=RUNTIME_ROOT)
    else:
        result = generic_entity_commit(
            args.output_name,
            args.authority_ref,
            args.authorization_token,
            args.acknowledge_side_effects,
            args.commit_message,
            root=ROOT,
            runtime_root=RUNTIME_ROOT,
        )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
