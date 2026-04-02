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
NODE_PATTERN = re.compile(r"^(VISIBLE_NODE\[[0-9]+\]|THREADCORE::VISIBLE_NODE\.[A-Z0-9][A-Z0-9_.\-]*)$")
CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonicalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    ordered = {}
    if "schema_version" in payload:
        ordered["schema_version"] = payload["schema_version"]
    for field in REQUIRED_FIELDS:
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
    if not isinstance(payload["node_id"], str) or not NODE_PATTERN.match(payload["node_id"]):
        errors.append("field does not match expected format: node_id")
    if not isinstance(payload["vector"], str) or not CODE_PATTERN.match(payload["vector"]):
        errors.append("field does not match expected format: vector")
    if not isinstance(payload["type"], str) or not re.match(r"^[a-z][a-z0-9\-]*$", payload["type"]):
        errors.append("field does not match expected format: type")
    if not isinstance(payload["linked_manifest"], str) or not payload["linked_manifest"].endswith(".json"):
        errors.append("field does not match expected format: linked_manifest")
    if not isinstance(payload["patch_id"], str) or not payload["patch_id"].endswith(".json"):
        errors.append("field does not match expected format: patch_id")
    if not isinstance(payload["bundle"], str) or not payload["bundle"].endswith(".zip"):
        errors.append("field does not match expected format: bundle")
    if not isinstance(payload["registered"], str) or not TIME_PATTERN.match(payload["registered"]):
        errors.append("field does not match expected format: registered")
    if not isinstance(payload["alias"], str) or not payload["alias"].strip():
        errors.append("field must be a non-empty string: alias")
    if not isinstance(payload["ethics"], str) or not re.match(r"^[A-Za-z0-9_.:\-]+$", payload["ethics"]):
        errors.append("field does not match expected format: ethics")
    if "schema_version" in payload and (not isinstance(payload["schema_version"], int) or payload["schema_version"] < 1):
        errors.append("schema_version must be an integer >= 1")
    if payload["node_id"].startswith("VISIBLE_NODE["):
        warnings.append("node_id uses legacy shortform; fully qualified registry tags are also supported")
    return errors, warnings


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or validate THREADCORE visible-node receipts.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
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
    generate.add_argument("--out", default=None)
    validate = subparsers.add_parser("validate")
    validate.add_argument("artifact")
    validate.add_argument("--report-out", default=None)
    return parser


def run_generate(args: argparse.Namespace) -> int:
    payload = {
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
        "family": "threadcore_visible_node",
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
