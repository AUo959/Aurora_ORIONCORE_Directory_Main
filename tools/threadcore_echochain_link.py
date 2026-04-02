#!/usr/bin/env python3
"""Generate and validate THREADCORE echochain-link receipts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "catalog/schemas/threadcore_echochain_link.schema.json"
REQUIRED_FIELDS = ("node", "linked_to", "type", "status", "glyphs", "approved_by", "integration", "timestamp")
CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonicalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    ordered = {}
    if "schema_version" in payload:
        ordered["schema_version"] = payload["schema_version"]
    for field in ("node", "linked_to", "type", "status", "glyphs", "approved_by", "integration", "timestamp"):
        ordered[field] = payload[field]
    return ordered


def validate_payload(payload: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"], warnings
    allowed = set(REQUIRED_FIELDS) | {"schema_version"}
    unknown = sorted(set(payload.keys()) - allowed)
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors, warnings
    for field in ("node", "linked_to"):
        if not isinstance(payload[field], str) or not CODE_PATTERN.match(payload[field]):
            errors.append(f"field does not match expected format: {field}")
    if not isinstance(payload["type"], str) or not re.match(r"^[a-z][a-z0-9\-]*$", payload["type"]):
        errors.append("field does not match expected format: type")
    if payload["status"] not in {"active", "inactive", "draft", "superseded"}:
        errors.append("field does not match expected format: status")
    if not isinstance(payload["glyphs"], list) or not payload["glyphs"]:
        errors.append("glyphs must be a non-empty array")
    else:
        for index, glyph in enumerate(payload["glyphs"]):
            if not isinstance(glyph, str) or not glyph:
                errors.append(f"glyphs[{index}] must be a non-empty string")
    for field in ("approved_by", "integration"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            errors.append(f"field must be a non-empty string: {field}")
    if not isinstance(payload["timestamp"], str) or not TIME_PATTERN.match(payload["timestamp"]):
        errors.append("field does not match expected format: timestamp")
    if "schema_version" in payload and (not isinstance(payload["schema_version"], int) or payload["schema_version"] < 1):
        errors.append("schema_version must be an integer >= 1")
    if payload.get("approved_by") == "THREADCORE":
        warnings.append("approved_by is symbolic authority metadata, not cryptographic provenance")
    return errors, warnings


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or validate THREADCORE echochain-link receipts.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--node", required=True)
    generate.add_argument("--linked-to", required=True)
    generate.add_argument("--type", default="symbolic-continuity")
    generate.add_argument("--status", default="active")
    generate.add_argument("--glyph", dest="glyphs", action="append", required=True)
    generate.add_argument("--approved-by", default="THREADCORE")
    generate.add_argument("--integration", required=True)
    generate.add_argument("--timestamp", default=None)
    generate.add_argument("--schema-version", type=int, default=None)
    generate.add_argument("--out", default=None)
    validate = subparsers.add_parser("validate")
    validate.add_argument("artifact")
    validate.add_argument("--report-out", default=None)
    return parser


def run_generate(args: argparse.Namespace) -> int:
    payload = {
        "node": args.node,
        "linked_to": args.linked_to,
        "type": args.type,
        "status": args.status,
        "glyphs": args.glyphs,
        "approved_by": args.approved_by,
        "integration": args.integration,
        "timestamp": args.timestamp or utc_now_iso(),
    }
    if args.schema_version is not None:
        payload["schema_version"] = args.schema_version
    payload = canonicalize(payload)
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
    artifact = Path(args.artifact).resolve()
    payload = load_json(artifact)
    errors, warnings = validate_payload(payload)
    normalized_payload = None
    if isinstance(payload, dict):
        try:
            normalized_payload = canonicalize(payload)
        except KeyError:
            normalized_payload = None
    report = {
        "ok": not errors,
        "family": "threadcore_echochain_link",
        "artifact": str(artifact),
        "schema_path": str(SCHEMA_PATH),
        "errors": errors,
        "warnings": warnings,
        "normalized_payload": normalized_payload,
    }
    if args.report_out:
        write_json(Path(args.report_out).resolve(), report)
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "generate":
        return run_generate(args)
    return run_validate(args)


if __name__ == "__main__":
    raise SystemExit(main())
