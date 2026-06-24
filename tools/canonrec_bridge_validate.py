#!/usr/bin/env python3
"""Validate CanonRec bridge promotion packets.

This tool is intentionally read-only. It checks packet shape, gate posture, and
mutation boundaries before any future CanonRec branch or PR is opened.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT
    / "catalog"
    / "contracts"
    / "AURORA_CANONREC__CONTRACT__BRIDGE_CONTROL_PLANE__v1.0__2026-06-24.json"
)
DEFAULT_PACKET_GLOB = "reports/automation/AURORA_CANONREC__PACKET__*.json"


WRITE_OPERATIONS = {"create", "update"}
REVIEW_OPERATIONS = {"review_only", "no_op", "none"}
DELETE_OPERATIONS = {"delete", "remove"}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def finding(severity: str, code: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "detail": detail}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def gate_status(packet: dict[str, Any], gate_name: str) -> str:
    gate = packet.get(gate_name)
    if not isinstance(gate, dict):
        return ""
    return str(gate.get("status", ""))


def target_operations(packet: dict[str, Any]) -> list[str]:
    operations: list[str] = []
    for target in as_list(packet.get("target_paths")):
        if isinstance(target, dict):
            op = str(target.get("intended_operation", "")).strip().lower()
            if op:
                operations.append(op)
    return operations


def canonrec_write_requested(packet: dict[str, Any]) -> bool:
    boundary = packet.get("boundary_assertions")
    if isinstance(boundary, dict) and boundary.get("canonrec_write_requested") is True:
        return True
    return any(op in WRITE_OPERATIONS for op in target_operations(packet))


def validate_required_fields(packet: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for field in contract.get("promotion_packet_required_fields", []):
        if field not in packet:
            findings.append(finding("error", "missing_required_field", f"Missing required field: {field}"))
    return findings


def validate_vocab(packet: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    allowed_layers = set(str(item) for item in contract.get("allowed_layers", []))
    allowed_statuses = set(str(item) for item in contract.get("claim_status_vocabulary", []))

    layer = str(packet.get("layer", ""))
    if layer not in allowed_layers:
        findings.append(finding("error", "invalid_layer", f"Layer is not allowed: {layer!r}"))

    claim_status = str(packet.get("claim_status", ""))
    if claim_status not in allowed_statuses:
        findings.append(
            finding("error", "invalid_claim_status", f"Claim status is not allowed: {claim_status!r}")
        )
    return findings


def validate_repo_and_merge_gate(packet: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    canon_target = str(contract.get("repositories", {}).get("canon_target", ""))
    if packet.get("target_repo") != canon_target:
        findings.append(
            finding(
                "error",
                "invalid_target_repo",
                f"target_repo must be {canon_target!r}, got {packet.get('target_repo')!r}",
            )
        )
    if packet.get("merge_approval_required") is not True:
        findings.append(finding("error", "merge_approval_not_required", "merge_approval_required must be true"))
    return findings


def validate_targets(packet: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    targets = as_list(packet.get("target_paths"))
    operations = target_operations(packet)

    if not targets:
        findings.append(finding("error", "missing_target_paths", "target_paths must contain at least one target"))
        return findings

    for index, target in enumerate(targets):
        if not isinstance(target, dict):
            findings.append(finding("error", "invalid_target", f"target_paths[{index}] must be an object"))
            continue
        path = str(target.get("path", "")).strip()
        operation = str(target.get("intended_operation", "")).strip().lower()
        if not path:
            findings.append(finding("error", "missing_target_path", f"target_paths[{index}] is missing path"))
        if not operation:
            findings.append(
                finding("error", "missing_intended_operation", f"target_paths[{index}] is missing intended_operation")
            )
        if operation in DELETE_OPERATIONS:
            findings.append(finding("error", "delete_operation_blocked_v1", f"v1 blocks delete operation for {path}"))
        if operation == "update" and not target.get("current_blob_sha"):
            findings.append(finding("error", "missing_current_blob_sha", f"update requires current_blob_sha for {path}"))

    if canonrec_write_requested(packet) and not any(op in WRITE_OPERATIONS for op in operations):
        findings.append(
            finding(
                "error",
                "write_requested_without_write_operation",
                "canonrec_write_requested is true but no create/update target operation is present",
            )
        )
    return findings


def validate_gates(packet: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    evidence = as_list(packet.get("evidence_receipts"))
    if not evidence:
        findings.append(finding("error", "missing_evidence_receipts", "evidence_receipts must not be empty"))

    for gate in ("ethics_gate", "continuity_gate"):
        status = gate_status(packet, gate)
        if not status:
            findings.append(finding("error", "missing_gate_status", f"{gate}.status is required"))

    if canonrec_write_requested(packet):
        if gate_status(packet, "ethics_gate").startswith("PASS") is False:
            findings.append(finding("error", "write_without_passing_ethics_gate", "CanonRec writes require ethics gate PASS"))
        if gate_status(packet, "continuity_gate").startswith("PASS") is False:
            findings.append(
                finding("error", "write_without_passing_continuity_gate", "CanonRec writes require continuity gate PASS")
            )
    return findings


def validate_boundaries(packet: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    boundary = packet.get("boundary_assertions")
    if not isinstance(boundary, dict):
        findings.append(finding("error", "missing_boundary_assertions", "boundary_assertions object is required"))
        return findings
    if boundary.get("scenario_seed_not_promoted") is not True:
        findings.append(
            finding("error", "scenario_seed_boundary_missing", "scenario_seed_not_promoted must be true")
        )
    if boundary.get("cloudbank_mirror_write_requested") is True:
        findings.append(
            finding(
                "error",
                "cloudbank_write_blocked",
                "Bridge packets must not request CloudBank mirror writes directly",
            )
        )
    return findings


def validate_packet(packet: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    findings.extend(validate_required_fields(packet, contract))
    findings.extend(validate_vocab(packet, contract))
    findings.extend(validate_repo_and_merge_gate(packet, contract))
    findings.extend(validate_targets(packet))
    findings.extend(validate_gates(packet))
    findings.extend(validate_boundaries(packet))

    error_count = sum(1 for item in findings if item["severity"] == "error")
    warning_count = sum(1 for item in findings if item["severity"] == "warning")
    return {
        "packet_id": packet.get("packet_id", "<unknown>"),
        "status": "valid" if error_count == 0 else "invalid",
        "summary": {"error_count": error_count, "warning_count": warning_count},
        "findings": findings,
    }


def discover_packets(root: Path, packet_args: list[str] | None) -> list[Path]:
    if packet_args:
        return [Path(item) if Path(item).is_absolute() else root / item for item in packet_args]
    return sorted(root.glob(DEFAULT_PACKET_GLOB))


def build_report(contract_path: Path, packet_paths: list[Path]) -> dict[str, Any]:
    contract = load_json(contract_path)
    reports = []
    for path in packet_paths:
        packet = load_json(path)
        result = validate_packet(packet, contract)
        result["path"] = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        reports.append(result)
    error_count = sum(report["summary"]["error_count"] for report in reports)
    return {
        "artifact_id": "canonrec_bridge_validation_report",
        "status": "valid" if error_count == 0 else "invalid",
        "contract": str(contract_path.relative_to(ROOT) if contract_path.is_relative_to(ROOT) else contract_path),
        "summary": {"packet_count": len(reports), "error_count": error_count},
        "reports": reports,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT, help="Bridge contract JSON path")
    parser.add_argument("--packet", action="append", help="Packet JSON path; may be supplied more than once")
    parser.add_argument("--summary", action="store_true", help="Print only status and summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet_paths = discover_packets(ROOT, args.packet)
    report = build_report(args.contract if args.contract.is_absolute() else ROOT / args.contract, packet_paths)
    if args.summary:
        print(json.dumps({"status": report["status"], "summary": report["summary"]}, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
