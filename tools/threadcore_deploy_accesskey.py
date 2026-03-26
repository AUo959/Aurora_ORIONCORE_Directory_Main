#!/usr/bin/env python3
"""Generate and validate THREADCORE deploy access-key receipts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

FAMILY = "threadcore_deploy_accesskey"
ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "catalog/schemas/threadcore_deploy_accesskey.schema.json"
REQUIRED_FIELDS = [
    "symbolic_key",
    "associated_bundle",
    "vector",
    "registered_node",
    "linked_echochain",
    "threadcore_manifest",
    "ethics_protocol",
    "timestamp",
]
OPTIONAL_FIELDS = ["schema_version"]
FIELD_PATTERNS = {
    "symbolic_key": re.compile(r"^THREADCORE_DEPLOY::[A-Z0-9][A-Z0-9_:.\-]*$"),
    "associated_bundle": re.compile(r"^.+\.zip$"),
    "vector": re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:.\-]*$"),
    "registered_node": re.compile(
        r"^(VISIBLE_NODE\[[0-9]+\]|THREADCORE::VISIBLE_NODE\.[A-Z0-9][A-Z0-9_.\-]*)$"
    ),
    "linked_echochain": re.compile(r"^[A-Z0-9][A-Z0-9_:.\-]*$"),
    "threadcore_manifest": re.compile(r"^.+\.md$"),
    "ethics_protocol": re.compile(r"^[A-Za-z0-9_.:\-]+$"),
    "timestamp": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"),
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonicalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    if "schema_version" in payload:
        ordered["schema_version"] = payload["schema_version"]
    for field in REQUIRED_FIELDS:
        if field in payload:
            ordered[field] = payload[field]
    return ordered


def validate_payload(payload: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(payload, dict):
        return ["payload must be a JSON object"], warnings

    allowed = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    unknown = sorted(set(payload.keys()) - allowed)
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")

    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing required field: {field}")
            continue
        if not isinstance(payload[field], str):
            errors.append(f"field must be a string: {field}")
            continue
        if not FIELD_PATTERNS[field].match(payload[field]):
            errors.append(f"field does not match expected format: {field}")

    if "schema_version" in payload:
        if not isinstance(payload["schema_version"], int) or payload["schema_version"] < 1:
            errors.append("schema_version must be an integer >= 1")

    if payload.get("registered_node", "").startswith("VISIBLE_NODE["):
        warnings.append("registered_node uses legacy shortform; fully qualified registry tags are also supported")

    return errors, warnings


def build_receipt(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if args.schema_version is not None:
        payload["schema_version"] = args.schema_version
    payload.update(
        {
            "symbolic_key": args.symbolic_key,
            "associated_bundle": args.associated_bundle,
            "vector": args.vector,
            "registered_node": args.registered_node,
            "linked_echochain": args.linked_echochain,
            "threadcore_manifest": args.threadcore_manifest,
            "ethics_protocol": args.ethics_protocol,
            "timestamp": args.timestamp or utc_now_iso(),
        }
    )
    return canonicalize(payload)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or validate THREADCORE deploy access-key receipts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate", help="Generate a THREADCORE deploy access-key receipt."
    )
    generate.add_argument("--symbolic-key", required=True)
    generate.add_argument("--associated-bundle", required=True)
    generate.add_argument("--vector", required=True)
    generate.add_argument("--registered-node", required=True)
    generate.add_argument("--linked-echochain", required=True)
    generate.add_argument("--threadcore-manifest", default="THREADCORE.md")
    generate.add_argument("--ethics-protocol", default="Picard_Delta_3")
    generate.add_argument("--timestamp", default=None)
    generate.add_argument("--schema-version", type=int, default=None)
    generate.add_argument("--out", default=None, help="Optional output JSON path.")

    validate = subparsers.add_parser(
        "validate", help="Validate an existing THREADCORE deploy access-key receipt."
    )
    validate.add_argument("artifact", help="Path to the JSON artifact to validate.")
    validate.add_argument("--report-out", default=None, help="Optional JSON report path.")

    return parser


def run_generate(args: argparse.Namespace) -> int:
    payload = build_receipt(args)
    errors, warnings = validate_payload(payload)
    if errors:
        raise SystemExit("\n".join(errors))

    if args.out:
        write_json(Path(args.out).resolve(), payload)
    print(json.dumps(payload, indent=2))
    if warnings:
        print(json.dumps({"warnings": warnings}, indent=2), file=sys.stderr)
    return 0


def run_validate(args: argparse.Namespace) -> int:
    artifact_path = Path(args.artifact).resolve()
    payload = load_json(artifact_path)
    errors, warnings = validate_payload(payload)
    report = {
        "ok": not errors,
        "family": FAMILY,
        "artifact": str(artifact_path),
        "schema_path": str(SCHEMA_PATH),
        "errors": errors,
        "warnings": warnings,
        "normalized_payload": canonicalize(payload) if isinstance(payload, dict) else None,
    }
    if args.report_out:
        write_json(Path(args.report_out).resolve(), report)
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "generate":
        return run_generate(args)
    if args.command == "validate":
        return run_validate(args)
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
