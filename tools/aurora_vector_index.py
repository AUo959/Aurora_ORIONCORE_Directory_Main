#!/usr/bin/env python3
"""Generate and validate Aurora vector index registries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

FAMILY = "aurora_vector_index"
ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "catalog/schemas/aurora_vector_index.schema.json"
REQUIRED_FIELDS = ["default", "vectors"]
OPTIONAL_FIELDS = ["schema_version"]
VECTOR_REQUIRED_FIELDS = ["code", "description", "type"]
VECTOR_OPTIONAL_FIELDS = [
    "rituals",
    "bundle",
    "ethics_protocol",
    "exported",
    "anchored_glyphs",
    "manifest_file",
    "linked_threads",
]
CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:.\-]*$")
ETHICS_PATTERN = re.compile(r"^[A-Za-z0-9_.:\-]+$")
FILE_ZIP_PATTERN = re.compile(r"^.+\.zip$")
FILE_JSON_PATTERN = re.compile(r"^.+\.json$")
VALID_TYPES = {"active", "release", "sandbox", "lockpoint", "meta"}


def canonicalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    if "schema_version" in payload:
        ordered["schema_version"] = payload["schema_version"]
    ordered["default"] = payload["default"]
    ordered["vectors"] = payload["vectors"]
    return ordered


def _validate_string_array(vector: Dict[str, Any], field: str, errors: List[str], index: int) -> None:
    items = vector[field]
    if not isinstance(items, list) or not items:
        errors.append(f"vectors[{index}].{field} must be a non-empty array")
        return
    for item_index, item in enumerate(items):
        if not isinstance(item, str) or not item:
            errors.append(f"vectors[{index}].{field}[{item_index}] must be a non-empty string")


def validate_payload(payload: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(payload, dict):
        return ["payload must be a JSON object"], warnings

    allowed = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    unknown = sorted(set(payload.keys()) - allowed)
    if unknown:
        errors.append(f"unknown root fields: {', '.join(unknown)}")

    if "default" not in payload:
        errors.append("missing required field: default")
    elif not isinstance(payload["default"], str) or not CODE_PATTERN.match(payload["default"]):
        errors.append("field does not match expected format: default")

    if "vectors" not in payload:
        errors.append("missing required field: vectors")
        return errors, warnings
    if not isinstance(payload["vectors"], list) or not payload["vectors"]:
        errors.append("vectors must be a non-empty array")
        return errors, warnings

    seen_codes: set[str] = set()
    for index, vector in enumerate(payload["vectors"]):
        if not isinstance(vector, dict):
            errors.append(f"vectors[{index}] must be an object")
            continue

        allowed_vector = set(VECTOR_REQUIRED_FIELDS) | set(VECTOR_OPTIONAL_FIELDS)
        unknown_vector = sorted(set(vector.keys()) - allowed_vector)
        if unknown_vector:
            errors.append(f"vectors[{index}] has unknown fields: {', '.join(unknown_vector)}")

        for field in VECTOR_REQUIRED_FIELDS:
            if field not in vector:
                errors.append(f"vectors[{index}] missing required field: {field}")

        code = vector.get("code")
        if not isinstance(code, str) or not CODE_PATTERN.match(code):
            errors.append(f"vectors[{index}].code does not match expected format")
        else:
            if code in seen_codes:
                errors.append(f"duplicate vector code: {code}")
            seen_codes.add(code)

        description = vector.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"vectors[{index}].description must be a non-empty string")

        vector_type = vector.get("type")
        if not isinstance(vector_type, str) or vector_type not in VALID_TYPES:
            errors.append(f"vectors[{index}].type does not match expected format")

        if "rituals" in vector:
            _validate_string_array(vector, "rituals", errors, index)
        if "anchored_glyphs" in vector:
            _validate_string_array(vector, "anchored_glyphs", errors, index)
        if "linked_threads" in vector:
            _validate_string_array(vector, "linked_threads", errors, index)

        if "bundle" in vector:
            bundle = vector["bundle"]
            if not isinstance(bundle, str) or not FILE_ZIP_PATTERN.match(bundle):
                errors.append(f"vectors[{index}].bundle does not match expected format")

        if "manifest_file" in vector:
            manifest_file = vector["manifest_file"]
            if not isinstance(manifest_file, str) or not FILE_JSON_PATTERN.match(manifest_file):
                errors.append(f"vectors[{index}].manifest_file does not match expected format")

        if "ethics_protocol" in vector:
            ethics_protocol = vector["ethics_protocol"]
            if not isinstance(ethics_protocol, str) or not ETHICS_PATTERN.match(ethics_protocol):
                errors.append(f"vectors[{index}].ethics_protocol does not match expected format")

        if "exported" in vector and not isinstance(vector["exported"], bool):
            errors.append(f"vectors[{index}].exported must be a boolean")

        if vector_type == "active" and "ethics_protocol" not in vector:
            warnings.append(f"active vector missing ethics_protocol: {code}")

    if isinstance(payload.get("default"), str) and payload["default"] not in seen_codes:
        errors.append(f"default vector not found in vectors: {payload['default']}")

    if "schema_version" in payload:
        if not isinstance(payload["schema_version"], int) or payload["schema_version"] < 1:
            errors.append("schema_version must be an integer >= 1")

    return errors, warnings


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_vectors_source(path: Path) -> Tuple[str | None, List[Dict[str, Any]]]:
    source = load_json(path)
    if isinstance(source, dict):
        default = source.get("default") if isinstance(source.get("default"), str) else None
        vectors = source.get("vectors")
        if isinstance(vectors, list):
            return default, vectors
        raise SystemExit("vectors-json must contain either an array or an object with a vectors array")
    if isinstance(source, list):
        return None, source
    raise SystemExit("vectors-json must contain either an array or an object with a vectors array")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or validate Aurora vector index registries."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate an Aurora vector index registry.")
    generate.add_argument("--default", dest="default_code", default=None)
    generate.add_argument("--vectors-json", required=True, help="Path to a JSON file containing either a vectors array or a full vector_index object.")
    generate.add_argument("--schema-version", type=int, default=None)
    generate.add_argument("--out", default=None, help="Optional output JSON path.")

    validate = subparsers.add_parser("validate", help="Validate an existing Aurora vector index registry.")
    validate.add_argument("artifact", help="Path to the JSON artifact to validate.")
    validate.add_argument("--report-out", default=None, help="Optional JSON report path.")

    return parser


def run_generate(args: argparse.Namespace) -> int:
    vectors_path = Path(args.vectors_json).resolve()
    inferred_default, vectors = _load_vectors_source(vectors_path)
    default_code = args.default_code or inferred_default
    if default_code is None:
        raise SystemExit("generate requires --default unless vectors-json contains a root default field")

    payload: Dict[str, Any] = {"default": default_code, "vectors": vectors}
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
        "normalized_payload": canonicalize(payload) if isinstance(payload, dict) and "default" in payload and "vectors" in payload else None,
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
