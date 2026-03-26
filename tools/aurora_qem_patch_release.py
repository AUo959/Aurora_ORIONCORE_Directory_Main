#!/usr/bin/env python3
"""Generate and validate Aurora QEM patch-release receipts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

FAMILY = "aurora_qem_patch_release"
ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "catalog/schemas/aurora_qem_patch_release.schema.json"
REQUIRED_FIELDS = [
    "patch_code",
    "version",
    "vector_origin",
    "includes",
    "symbolic_glyphs",
    "ethics_protocol",
    "sealed_in",
    "timestamp",
    "vector_released_as",
]
OPTIONAL_FIELDS = ["schema_version"]
FIELD_PATTERNS = {
    "patch_code": re.compile(r"^[A-Z0-9][A-Z0-9_:.\-]*$"),
    "version": re.compile(r"^v[0-9]+(?:\.[0-9]+)*(?:[A-Za-z0-9_.\-]*)?$"),
    "vector_origin": re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:.\-]*$"),
    "ethics_protocol": re.compile(r"^[A-Za-z0-9_.:\-]+$"),
    "sealed_in": re.compile(r"^.+\.zip$"),
    "timestamp": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"),
    "vector_released_as": re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:.\-]*$"),
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


def _validate_string_array(
    payload: Dict[str, Any], field: str, errors: List[str]
) -> None:
    items = payload[field]
    if not isinstance(items, list) or not items:
        errors.append(f"{field} must be a non-empty array")
        return
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item:
            errors.append(f"{field}[{index}] must be a non-empty string")


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

        if field in {"includes", "symbolic_glyphs"}:
            _validate_string_array(payload, field, errors)
            continue

        if not isinstance(payload[field], str):
            errors.append(f"field must be a string: {field}")
            continue
        if not FIELD_PATTERNS[field].match(payload[field]):
            errors.append(f"field does not match expected format: {field}")

    if "schema_version" in payload:
        if not isinstance(payload["schema_version"], int) or payload["schema_version"] < 1:
            errors.append("schema_version must be an integer >= 1")

    includes = payload.get("includes", [])
    if isinstance(includes, list) and any(
        "QEM-SN1-MOBILE_manifest.json" in item for item in includes if isinstance(item, str)
    ):
        warnings.append("includes references QEM-SN1-MOBILE_manifest.json, which is not currently recoverable in this workspace")

    return errors, warnings


def build_receipt(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if args.schema_version is not None:
        payload["schema_version"] = args.schema_version
    payload.update(
        {
            "patch_code": args.patch_code,
            "version": args.version,
            "vector_origin": args.vector_origin,
            "includes": args.includes,
            "symbolic_glyphs": args.symbolic_glyphs,
            "ethics_protocol": args.ethics_protocol,
            "sealed_in": args.sealed_in,
            "timestamp": args.timestamp or utc_now_iso(),
            "vector_released_as": args.vector_released_as,
        }
    )
    return canonicalize(payload)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or validate Aurora QEM patch-release receipts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate an Aurora QEM patch-release receipt.")
    generate.add_argument("--patch-code", required=True)
    generate.add_argument("--version", required=True)
    generate.add_argument("--vector-origin", required=True)
    generate.add_argument("--include", dest="includes", action="append", required=True)
    generate.add_argument("--glyph", dest="symbolic_glyphs", action="append", required=True)
    generate.add_argument("--ethics-protocol", default="Picard_Delta_3")
    generate.add_argument("--sealed-in", required=True)
    generate.add_argument("--timestamp", default=None)
    generate.add_argument("--vector-released-as", required=True)
    generate.add_argument("--schema-version", type=int, default=None)
    generate.add_argument("--out", default=None, help="Optional output JSON path.")

    validate = subparsers.add_parser("validate", help="Validate an existing Aurora QEM patch-release receipt.")
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
