#!/usr/bin/env python3
"""Validate recovered THREADCORE deploy seal bundles."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

CONTRACT_PATH = ROOT / "catalog/contracts/threadcore_deploy_seal_contract.json"
VECTOR_PATTERN = re.compile(r"QEM-[A-Za-z0-9_.:-]+")
ETHICS_PATTERN = re.compile(r"^(?:Picard_Delta_3|[A-Za-z0-9_.:-]+)$")
NODE_PATTERN = re.compile(r"^(VISIBLE_NODE\[[0-9]+\]|THREADCORE::VISIBLE_NODE\.[A-Z0-9][A-Z0-9_.\-]*)$")
CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def canonicalize_visible_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "node_id": payload.get("node_id"),
        "vector": payload.get("vector"),
        "type": payload.get("type"),
        "linked_manifest": payload.get("linked_manifest"),
        "patch_id": payload.get("patch_id"),
        "bundle": payload.get("bundle"),
        "registered": payload.get("registered"),
        "alias": payload.get("alias"),
        "ethics": payload.get("ethics"),
    }


def validate_visible_node_payload(payload: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    required = [
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
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"], warnings
    for field in required:
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
    if not isinstance(payload["registered"], str) or not TIMESTAMP_PATTERN.match(payload["registered"]):
        errors.append("field does not match expected format: registered")
    if not isinstance(payload["alias"], str) or not payload["alias"].strip():
        errors.append("field must be a non-empty string: alias")
    if not isinstance(payload["ethics"], str) or not ETHICS_PATTERN.fullmatch(payload["ethics"]):
        errors.append("field does not match expected format: ethics")
    if isinstance(payload["node_id"], str) and payload["node_id"].startswith("VISIBLE_NODE["):
        warnings.append("node_id uses legacy shortform; fully qualified registry tags are also supported")
    return errors, warnings


def canonicalize_echochain(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "node": payload.get("node"),
        "linked_to": payload.get("linked_to"),
        "type": payload.get("type"),
        "status": payload.get("status"),
        "glyphs": payload.get("glyphs"),
        "approved_by": payload.get("approved_by"),
        "integration": payload.get("integration"),
        "timestamp": payload.get("timestamp"),
    }


def validate_echochain_payload(payload: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    required = [
        "node",
        "linked_to",
        "type",
        "status",
        "glyphs",
        "approved_by",
        "integration",
        "timestamp",
    ]
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"], warnings
    for field in required:
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
    if not isinstance(payload["approved_by"], str) or not payload["approved_by"].strip():
        errors.append("field must be a non-empty string: approved_by")
    if not isinstance(payload["integration"], str) or not payload["integration"].strip():
        errors.append("field must be a non-empty string: integration")
    if not isinstance(payload["timestamp"], str) or not TIMESTAMP_PATTERN.match(payload["timestamp"]):
        errors.append("field does not match expected format: timestamp")
    if payload.get("approved_by") == "THREADCORE":
        warnings.append("approved_by is symbolic authority metadata, not cryptographic provenance")
    return errors, warnings


def load_contract() -> Dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def load_zip_text(bundle_path: Path, name: str) -> str:
    with zipfile.ZipFile(bundle_path) as archive:
        return archive.read(name).decode("utf-8")


def load_zip_json(bundle_path: Path, name: str) -> Any:
    return json.loads(load_zip_text(bundle_path, name))


def validate_mygpt_payload(payload: Any, bundle_entries: set[str]) -> Tuple[List[str], List[str], Dict[str, Any] | None]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(payload, dict):
        return ["Aurora_Toolset_MyGPT_v1.json must be a JSON object"], warnings, None

    required = [
        "gpt_toolset_id",
        "description",
        "tools",
        "includes_vector_index",
        "ethics_protocol",
        "compatible_with",
    ]
    for field in required:
        if field not in payload:
            errors.append(f"Aurora_Toolset_MyGPT_v1.json missing required field: {field}")

    if errors:
        return errors, warnings, payload

    if not isinstance(payload["gpt_toolset_id"], str) or not payload["gpt_toolset_id"].strip():
        errors.append("Aurora_Toolset_MyGPT_v1.json field must be a non-empty string: gpt_toolset_id")
    if not isinstance(payload["description"], str) or not payload["description"].strip():
        errors.append("Aurora_Toolset_MyGPT_v1.json field must be a non-empty string: description")
    if not isinstance(payload["includes_vector_index"], bool):
        errors.append("Aurora_Toolset_MyGPT_v1.json includes_vector_index must be boolean")
    if not isinstance(payload["ethics_protocol"], str) or not ETHICS_PATTERN.fullmatch(payload["ethics_protocol"]):
        errors.append("Aurora_Toolset_MyGPT_v1.json ethics_protocol does not match expected format")
    if not isinstance(payload["compatible_with"], list) or not payload["compatible_with"]:
        errors.append("Aurora_Toolset_MyGPT_v1.json compatible_with must be a non-empty array")
    if not isinstance(payload["tools"], list) or not payload["tools"]:
        errors.append("Aurora_Toolset_MyGPT_v1.json tools must be a non-empty array")

    tool_entries = payload.get("tools", [])
    for index, tool_entry in enumerate(tool_entries):
        if not isinstance(tool_entry, dict):
            errors.append(f"Aurora_Toolset_MyGPT_v1.json tools[{index}] must be an object")
            continue
        for field in ("name", "entrypoint", "type", "description"):
            if not isinstance(tool_entry.get(field), str) or not tool_entry[field].strip():
                errors.append(f"Aurora_Toolset_MyGPT_v1.json tools[{index}].{field} must be a non-empty string")
        entrypoint = tool_entry.get("entrypoint")
        if isinstance(entrypoint, str) and entrypoint not in bundle_entries:
            warnings.append(
                f"MyGPT entrypoint is external to seal bundle: {entrypoint}"
            )

    if payload.get("includes_vector_index") and "vector_index.json" not in bundle_entries:
        warnings.append("MyGPT toolset expects vector_index.json, but the seal bundle does not include it")

    return errors, warnings, payload


def validate_threadcore_markdown(text: str) -> Tuple[List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {
        "has_identity_header": "THREADCORE :: Unified Thread Identity Record" in text,
        "vector_matches": VECTOR_PATTERN.findall(text),
        "ethics_matches": re.findall(r"Picard_Delta_3", text),
    }
    if not metadata["has_identity_header"]:
        errors.append("THREADCORE.md missing identity header")
    if not metadata["vector_matches"]:
        errors.append("THREADCORE.md missing vector marker")
    if not metadata["ethics_matches"]:
        errors.append("THREADCORE.md missing ethics marker")
    if "sandbox:/mnt/data/" in text:
        warnings.append("THREADCORE.md still points at sandbox:/mnt/data storage")
    return errors, warnings, metadata


def validate_beacon_script(text: str) -> Tuple[List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    metadata = {
        "imports_gui": "from aurora_zip_gui import AuroraZipGUI" in text,
        "launches_gui": "AuroraZipGUI()" in text,
    }
    if not metadata["imports_gui"]:
        errors.append("aurora_auto_launch_beacon.py missing AuroraZipGUI import")
    if not metadata["launches_gui"]:
        errors.append("aurora_auto_launch_beacon.py missing AuroraZipGUI launch")
    warnings.append("aurora_auto_launch_beacon.py depends on aurora_zip_gui.py, which is external to the seal bundle")
    return errors, warnings, metadata


def validate_bundle(bundle_path: Path) -> Dict[str, Any]:
    contract = load_contract()
    with zipfile.ZipFile(bundle_path) as archive:
        entries = [info.filename for info in archive.infolist() if not info.is_dir()]

    entry_set = set(entries)
    required_entries = contract["required_entries"]
    missing_entries = [entry for entry in required_entries if entry not in entry_set]
    extra_entries = sorted(entry_set - set(required_entries))

    errors: List[str] = []
    warnings: List[str] = []
    reports: Dict[str, Any] = {}

    if missing_entries:
        errors.extend([f"missing required bundle entry: {entry}" for entry in missing_entries])
    if extra_entries:
        warnings.append(f"bundle contains extra entries: {', '.join(extra_entries)}")

    visible_node_payload = None
    visible_node_report: Dict[str, Any] | None = None
    echochain_payload = None
    echochain_report: Dict[str, Any] | None = None
    mygpt_payload = None
    mygpt_report: Dict[str, Any] | None = None
    markdown_meta: Dict[str, Any] | None = None

    if "THREADCORE_VISIBLE_NODE_01.json" in entry_set:
        visible_node_payload = load_zip_json(bundle_path, "THREADCORE_VISIBLE_NODE_01.json")
        entry_errors, entry_warnings = validate_visible_node_payload(visible_node_payload)
        visible_node_report = {
            "ok": not entry_errors,
            "errors": entry_errors,
            "warnings": entry_warnings,
            "normalized_payload": canonicalize_visible_node(visible_node_payload),
        }
        errors.extend([f"THREADCORE_VISIBLE_NODE_01.json: {item}" for item in entry_errors])
        warnings.extend([f"THREADCORE_VISIBLE_NODE_01.json: {item}" for item in entry_warnings])
        reports["THREADCORE_VISIBLE_NODE_01.json"] = visible_node_report

    if "QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json" in entry_set:
        echochain_payload = load_zip_json(bundle_path, "QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json")
        entry_errors, entry_warnings = validate_echochain_payload(echochain_payload)
        echochain_report = {
            "ok": not entry_errors,
            "errors": entry_errors,
            "warnings": entry_warnings,
            "normalized_payload": canonicalize_echochain(echochain_payload),
        }
        errors.extend([f"QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json: {item}" for item in entry_errors])
        warnings.extend([f"QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json: {item}" for item in entry_warnings])
        reports["QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json"] = echochain_report

    if "Aurora_Toolset_MyGPT_v1.json" in entry_set:
        mygpt_payload = load_zip_json(bundle_path, "Aurora_Toolset_MyGPT_v1.json")
        entry_errors, entry_warnings, normalized = validate_mygpt_payload(mygpt_payload, entry_set)
        mygpt_report = {
            "ok": not entry_errors,
            "errors": entry_errors,
            "warnings": entry_warnings,
            "normalized_payload": normalized,
        }
        errors.extend([f"Aurora_Toolset_MyGPT_v1.json: {item}" for item in entry_errors])
        warnings.extend([f"Aurora_Toolset_MyGPT_v1.json: {item}" for item in entry_warnings])
        reports["Aurora_Toolset_MyGPT_v1.json"] = mygpt_report

    if "THREADCORE.md" in entry_set:
        markdown_text = load_zip_text(bundle_path, "THREADCORE.md")
        entry_errors, entry_warnings, markdown_meta = validate_threadcore_markdown(markdown_text)
        reports["THREADCORE.md"] = {
            "ok": not entry_errors,
            "errors": entry_errors,
            "warnings": entry_warnings,
            "metadata": markdown_meta,
        }
        errors.extend([f"THREADCORE.md: {item}" for item in entry_errors])
        warnings.extend([f"THREADCORE.md: {item}" for item in entry_warnings])

    if "aurora_auto_launch_beacon.py" in entry_set:
        beacon_text = load_zip_text(bundle_path, "aurora_auto_launch_beacon.py")
        entry_errors, entry_warnings, beacon_meta = validate_beacon_script(beacon_text)
        reports["aurora_auto_launch_beacon.py"] = {
            "ok": not entry_errors,
            "errors": entry_errors,
            "warnings": entry_warnings,
            "metadata": beacon_meta,
        }
        errors.extend([f"aurora_auto_launch_beacon.py: {item}" for item in entry_errors])
        warnings.extend([f"aurora_auto_launch_beacon.py: {item}" for item in entry_warnings])

    if visible_node_payload and echochain_payload:
        if visible_node_payload.get("vector") != echochain_payload.get("node"):
            errors.append("cross-check: visible node vector does not match echochain node")

    if visible_node_payload and mygpt_payload:
        if visible_node_payload.get("ethics") != mygpt_payload.get("ethics_protocol"):
            errors.append("cross-check: visible node ethics does not match MyGPT ethics_protocol")

    if visible_node_payload and markdown_meta:
        vector = visible_node_payload.get("vector")
        if isinstance(vector, str) and vector not in markdown_meta.get("vector_matches", []):
            errors.append("cross-check: THREADCORE.md does not mention visible node vector")
        ethics = visible_node_payload.get("ethics")
        if isinstance(ethics, str) and ethics not in load_zip_text(bundle_path, "THREADCORE.md"):
            errors.append("cross-check: THREADCORE.md does not mention visible node ethics")

    return {
        "ok": not errors,
        "family": "threadcore_deploy_seal",
        "artifact": str(bundle_path),
        "contract_path": str(CONTRACT_PATH),
        "entries": entries,
        "missing_entries": missing_entries,
        "extra_entries": extra_entries,
        "errors": errors,
        "warnings": warnings,
        "entry_reports": reports,
        "optional_companions": contract.get("optional_companions", []),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate recovered THREADCORE deploy seal bundles.")
    parser.add_argument("bundle", help="Path to THREADCORE_DEPLOY_SEAL_v1.zip")
    parser.add_argument("--report-out", default=None, help="Optional JSON report path.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    bundle_path = Path(args.bundle).resolve()
    report = validate_bundle(bundle_path)
    if args.report_out:
        Path(args.report_out).resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
