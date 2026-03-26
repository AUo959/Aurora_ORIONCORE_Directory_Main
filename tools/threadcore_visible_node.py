#!/usr/bin/env python3
"""Generate and validate THREADCORE visible-node receipts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

FAMILY = "threadcore_visible_node"
ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "catalog/schemas/threadcore_visible_node.schema.json"
REQUIRED_FIELDS = [
    "node_id",
    "vector",
    "type",
    "linked_manifest",
    "patch_id",
    "bundle",
    "registered",
    "alias",
    "ethics",
]
OPTIONAL_FIELDS = ["schema_version"]
FIELD_PATTERNS = {
    "node_id": re.compile(
        r"^(VISIBLE_NODE\[[0-9]+\]|THREADCORE::VISIBLE_NODE\.[A-Z0-9][A-Z0-9_.\-]*)$"
    ),
    "vector": re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:.\-]*$"),
    "type": re.compile(r"^[a-z][a-z0-9\-]*$"),
    "linked_manifest": re.compile(r"^.+\.json$"),
    "patch_id": re.compile(r"^.+\.json$"),
    "bundle": re.compile(r"^.+\.zip$"),
    "registered": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"),
    "ethics": re.compile(r"^[A-Za-z0-9_.:\-]+$"),
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
        if field == "alias":
            if not isinstance(payload[field], str) or not payload[field].strip():
                errors.append("field must be a non-empty string: alias")
            continue
        if not isinstance(payload[field], str):
            errors.append(f"field must be a string: {field}")
            continue
        if not FIELD_PATTERNS[field].match(payload[field]):
            errors.append(f"field does not match expected format: {field}")

    if "schema_version" in payload:
        if not isinstance(payload["schema_version"], int) or payload["schema_version"] < 1:
            errors.append("schema_version must be an integer >= 1")

    if payload.get("node_id", "").startswith("VISIBLE_NODE["):
        warnings.append("node_id uses legacy shortform; fully qualified registry tags are also supported")

    return errors, warnings


def build_receipt(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if args.schema_version is not None:
        payload["schema_version"] = args.schema_version
    payload.update(
        {
            "node_id": args.node_id,
            "vector": args.vector,
            "type": args.type,
            "linked_manifest": args.linked_manifest,
            "patch_id": args.patch_id,
            "bundle": args.bundle,
            "registered": args.registered or utc_now_iso(),
            "alias": args.alias,
            "ethics": args.ethics,
        }
    )
    return canonicalize(payload)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or validate THREADCORE visible-node receipts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a THREADCORE visible-node receipt.")
    generate.add_argument("--node-id", required=True)
    generate.add_argument("--vector", required=True)
    generate.add_argument("--type", default="mobile-gui")
    generate.add_argument("--linked-manifest", required=True)
    generate.add_argument("--patch-id", required=True)
    generate.add_argument("--bundle", required=True)
    generate.add_argument("--registered", default=None)
    generate.add_argument("--alias", required=True)
    generate.add_argument("--ethics", default="Picard_Delta_3")
    generate.add_argument("--schema-version", type=int, default=None)
    generate.add_argument("--out", default=None, help="Optional output JSON path.")

    validate = subparsers.add_parser("validate", help="Validate an existing THREADCORE visible-node receipt.")
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
