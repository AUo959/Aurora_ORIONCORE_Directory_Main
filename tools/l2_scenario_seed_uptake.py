#!/usr/bin/env python3
"""Build and validate root L2 scenario seed uptake packets.

The uptake packet is a root control-plane handoff surface. It gives future
fixture, state-builder, simulation, ethics, narrative, and canon-review
adapters a consistent input shape without authorizing nested repo writes or
turning scenario seeds into scripted outcomes.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "catalog" / "l2_scenario_seed_catalog.json"
DEFAULT_CONTRACT = ROOT / "catalog" / "contracts" / "l2_scenario_seed_uptake_contract_v1.json"
NESTED_PREFIXES = (
    "GUMAS_SIM_2.5/CanonRec",
    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
)
PROHIBITED_BLUEPRINT_KEYS = {
    "forced_winner",
    "scripted_outcome",
    "single_required_ending",
    "canonical_outcome",
    "canon_fact_by_seed",
    "runtime_mutation_by_seed",
}
ALLOWED_FIXTURE_STATUSES = {"ready_candidate", "contract_candidate"}


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "scenario"


def nested_path(path: str) -> bool:
    normalized = path.strip().lstrip("./")
    return any(normalized.startswith(prefix) for prefix in NESTED_PREFIXES)


def iter_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(iter_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(iter_keys(item))
    return keys


def card_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(card["id"]): card
        for card in catalog.get("cards", [])
        if isinstance(card, dict) and card.get("id")
    }


def shortlist_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry["id"]): entry
        for entry in catalog.get("fixture_ready_shortlist", [])
        if isinstance(entry, dict) and entry.get("id")
    }


def required_consumers(contract: dict[str, Any]) -> list[str]:
    return [str(item) for item in contract.get("required_seed_consumers", [])]


def surface_index(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(surface["surface_id"]): surface
        for surface in contract.get("uptake_surfaces", [])
        if isinstance(surface, dict) and surface.get("surface_id")
    }


def validate_contract(contract: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    surfaces = surface_index(contract)
    for consumer_id in required_consumers(contract):
        if consumer_id not in surfaces:
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_uptake_surface",
                    "detail": f"Required seed consumer has no uptake surface: {consumer_id}",
                }
            )
    packet_consumers = set(contract.get("packet_shape", {}).get("consumer_payload_ids", []))
    for consumer_id in required_consumers(contract):
        if consumer_id not in packet_consumers:
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_packet_consumer",
                    "detail": f"Required seed consumer missing from packet shape: {consumer_id}",
                }
            )
    return findings


def blueprint_metrics(blueprint: dict[str, Any]) -> dict[str, int]:
    return {
        "roles": len(blueprint.get("roles", [])),
        "pressure_axes": len(blueprint.get("pressure", [])),
        "knob_axes": len(blueprint.get("knobs", {})),
        "expected_end_state_categories": len(blueprint.get("expected_end_states", [])),
    }


def finding(severity: str, code: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "detail": detail}


def assess_status_and_identity(
    entry: dict[str, Any],
    blueprint: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    card_id = str(entry.get("id", "unknown"))
    fixture_status = str(blueprint.get("fixture_status", ""))
    if fixture_status not in ALLOWED_FIXTURE_STATUSES:
        findings.append(
            finding(
                "error",
                "unsupported_fixture_status",
                f"{card_id} fixture_status is not an allowed uptake status: {fixture_status}",
            )
        )
    if fixture_status != "ready_candidate" and "runtime_fixture" in entry.get("value_lanes", []):
        findings.append(
            finding(
                "error",
                "runtime_lane_not_ready",
                f"{card_id} has runtime_fixture value lane but fixture_status is {fixture_status}",
            )
        )
    if blueprint.get("source_card_id") != card_id:
        findings.append(
            finding(
                "error",
                "source_card_mismatch",
                f"{card_id} fixture_blueprint.source_card_id mismatch",
            )
        )
    return findings


def assess_output_path(entry: dict[str, Any], blueprint: dict[str, Any]) -> list[dict[str, str]]:
    card_id = str(entry.get("id", "unknown"))
    output_path = str(blueprint.get("candidate_output_path", ""))
    if nested_path(output_path):
        return [
            finding(
                "error",
                "nested_output_path",
                f"{card_id} targets nested repo path: {output_path}",
            )
        ]
    return []


def assess_emergence_capacity(
    entry: dict[str, Any],
    blueprint: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    card_id = str(entry.get("id", "unknown"))
    minimum = contract["emergence_policy"]["minimum_degrees_of_freedom"]
    metrics = blueprint_metrics(blueprint)
    for field, actual in metrics.items():
        required = int(minimum[field])
        if actual < required:
            findings.append(
                finding(
                    "error",
                    "low_emergence_capacity",
                    f"{card_id} has {actual} {field}, requires {required}",
                )
            )
    return findings


def assess_prohibited_semantics(
    entry: dict[str, Any],
    blueprint: dict[str, Any],
) -> list[dict[str, str]]:
    card_id = str(entry.get("id", "unknown"))
    prohibited_keys = PROHIBITED_BLUEPRINT_KEYS.intersection(iter_keys(blueprint))
    if prohibited_keys:
        return [
            finding(
                "error",
                "scripted_outcome_key",
                f"{card_id} contains prohibited key(s): {sorted(prohibited_keys)}",
            )
        ]
    return []


def assess_task_sources(entry: dict[str, Any], blueprint: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    card_id = str(entry.get("id", "unknown"))
    for task in blueprint.get("task_blueprint", []):
        source = str(task.get("source", ""))
        if "catalog/l2_scenario_seed_catalog.json" not in source:
            findings.append(
                finding(
                    "error",
                    "untraceable_task_source",
                    f"{card_id} task source does not point to the root catalog",
                )
            )
    return findings


def assess_promotion_status(entry: dict[str, Any], card: dict[str, Any]) -> list[dict[str, str]]:
    card_id = str(entry.get("id", "unknown"))
    if card.get("promotion_status") not in {None, "root_catalog_only_not_canon_or_runtime"}:
        return [
            finding(
                "warning",
                "unexpected_promotion_status",
                f"{card_id} promotion_status is {card.get('promotion_status')}",
            )
        ]
    return []


def assess_blueprint(
    entry: dict[str, Any],
    card: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    card_id = str(entry.get("id", "unknown"))
    blueprint = entry.get("fixture_blueprint", {})
    if not isinstance(blueprint, dict):
        return [
            finding("error", "missing_fixture_blueprint", f"{card_id} has no fixture_blueprint object")
        ]

    findings.extend(assess_status_and_identity(entry, blueprint))
    findings.extend(assess_output_path(entry, blueprint))
    findings.extend(assess_emergence_capacity(entry, blueprint, contract))
    findings.extend(assess_prohibited_semantics(entry, blueprint))
    findings.extend(assess_task_sources(entry, blueprint))
    findings.extend(assess_promotion_status(entry, card))
    return findings


def lineage_provenance(card: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id",
        "handle",
        "source_version",
        "source_status",
        "source_path",
        "original_category",
        "promotion_basis",
        "promotion_status",
    ]
    return {key: card.get(key) for key in keys if key in card}


def source_seed_payload(entry: dict[str, Any]) -> dict[str, Any]:
    blueprint = entry["fixture_blueprint"]
    return {
        "source_card_id": blueprint["source_card_id"],
        "source_handle": blueprint["source_handle"],
        "scenario_prompt": blueprint["scenario_prompt"],
        "objective": blueprint["objective"],
        "opposition": blueprint["opposition"],
        "roles": blueprint["roles"],
        "pressure": blueprint["pressure"],
        "knobs": blueprint["knobs"],
        "ethical_hook": blueprint["ethical_hook"],
        "expected_end_state_categories": blueprint["expected_end_states"],
    }


def build_consumer_payloads(
    entry: dict[str, Any],
    card: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    blueprint = entry["fixture_blueprint"]
    fixture_status = str(blueprint["fixture_status"])
    runtime_ready = fixture_status == "ready_candidate" and "runtime_fixture" in entry.get("value_lanes", [])
    source_seed = source_seed_payload(entry)
    freedoms = contract["emergence_policy"]["required_runtime_freedoms"]
    outcome_handling = contract["emergence_policy"]["outcome_handling"]
    provenance = lineage_provenance(card)
    return {
        "root_fixture_generator": {
            "fixture_status": fixture_status,
            "emission_status": (
                "ready_for_root_fixture_export"
                if runtime_ready
                else "contract_packet_only_not_runtime_fixture_ready"
            ),
            "target_shape": blueprint["target_shape"],
            "candidate_output_path": blueprint["candidate_output_path"],
            "task_blueprint": blueprint["task_blueprint"],
            "source_scenario_seed": {
                "card_id": blueprint["source_card_id"],
                "handle": blueprint["source_handle"],
                "catalog_ref": "catalog/l2_scenario_seed_catalog.json",
                "promotion_status": card.get("promotion_status", "root_catalog_only_not_canon_or_runtime"),
            },
        },
        "state_builder_evidence_envelope": {
            "state_builder_input": source_seed,
            "state_builder_rule": "Build candidate initial state and pressure maps only; do not assert final facts.",
        },
        "simulation_initializer": {
            "seed": blueprint["seed"],
            "ticks": blueprint["ticks"],
            "anchor_seed": blueprint["anchor_seed"],
            "initial_condition_vector": {
                "roles": blueprint["roles"],
                "pressure": blueprint["pressure"],
                "knobs": blueprint["knobs"],
            },
            "runtime_freedoms": freedoms,
            "expected_end_state_handling": outcome_handling,
        },
        "ethics_gate": {
            "ethics_protocol": blueprint["ethics_protocol"],
            "ethical_hook": blueprint["ethical_hook"],
            "l3_audit_blueprint": blueprint["l3_audit_blueprint"],
            "gate_rule": "Review pressure handling and consent/agency risk without selecting the runtime ending.",
        },
        "narrative_renderer": {
            "render_rule": "Render from observed simulation events and source provenance after a run.",
            "source_prompt": blueprint["scenario_prompt"],
            "lineage_provenance": provenance,
        },
        "canon_promotion_gate": {
            "status": "blocked_without_explicit_canon_task",
            "rule": "Seed intent alone is never canon fact; only post-simulation evidence can enter a canon review packet.",
            "required_future_inputs": [
                "simulation_receipt",
                "ethics_review_result",
                "continuity_review_packet",
            ],
        },
    }


def build_packet(entry: dict[str, Any], card: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    blueprint = entry["fixture_blueprint"]
    fixture_status = str(blueprint["fixture_status"])
    return {
        "packet_id": f"uptake_{slug(blueprint['fixture_id'])}",
        "packet_status": (
            "ready_for_root_fixture_export"
            if fixture_status == "ready_candidate"
            else "contract_packet_only_not_runtime_fixture_ready"
        ),
        "source_card_id": entry["id"],
        "source_handle": entry["handle"],
        "lineage_provenance": lineage_provenance(card),
        "consumer_payloads": build_consumer_payloads(entry, card, contract),
        "emergence_policy": {
            "principle": contract["emergence_policy"]["principle"],
            "metrics": blueprint_metrics(blueprint),
            "runtime_freedoms": contract["emergence_policy"]["required_runtime_freedoms"],
            "outcome_handling": contract["emergence_policy"]["outcome_handling"],
            "boundedness_guard": contract["emergence_policy"]["boundedness_guard"],
        },
        "boundary_assertions": {
            "root_control_plane_only": True,
            "writes_nested_repos": False,
            "cloudbank_runtime_wiring": "not_authorized_by_this_packet",
            "canonrec_promotion": "not_authorized_by_this_packet",
        },
    }


def selected_entries(catalog: dict[str, Any], ids: list[str] | None) -> list[dict[str, Any]]:
    entries = shortlist_index(catalog)
    if not ids:
        return list(entries.values())
    missing = [card_id for card_id in ids if card_id not in entries]
    if missing:
        raise ValueError(f"Requested id(s) are not fixture-ready shortlist entries: {', '.join(missing)}")
    return [entries[card_id] for card_id in ids]


def build_report(
    catalog: dict[str, Any],
    contract: dict[str, Any],
    ids: list[str] | None = None,
) -> dict[str, Any]:
    cards = card_index(catalog)
    findings = validate_contract(contract)
    packets: list[dict[str, Any]] = []
    for entry in selected_entries(catalog, ids):
        card_id = str(entry["id"])
        card = cards.get(card_id)
        if card is None:
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_catalog_card",
                    "detail": f"Fixture entry has no maintained catalog card: {card_id}",
                }
            )
            continue
        findings.extend(assess_blueprint(entry, card, contract))
        packets.append(build_packet(entry, card, contract))

    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    warning_count = sum(1 for finding in findings if finding["severity"] == "warning")
    required = required_consumers(contract)
    return {
        "artifact_id": "l2_scenario_seed_uptake_packet",
        "generated_at_utc": now_iso_utc(),
        "status": "valid" if error_count == 0 else "invalid",
        "source_catalog": contract["source_catalog"],
        "uptake_contract": "catalog/contracts/l2_scenario_seed_uptake_contract_v1.json",
        "summary": {
            "selected_seed_count": len(packets),
            "required_consumer_count": len(required),
            "emergence_validated_seed_count": len(packets) if error_count == 0 else 0,
            "error_count": error_count,
            "warning_count": warning_count,
        },
        "required_seed_consumers": required,
        "emergence_policy": contract["emergence_policy"],
        "packets": packets,
        "findings": findings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--ids", nargs="+", help="Fixture-ready scenario ids to export. Defaults to all shortlist entries.")
    parser.add_argument("--limit", type=int, help="Limit selected packets after id filtering.")
    parser.add_argument("--out", type=Path, help="Write the uptake packet report to this path.")
    parser.add_argument("--summary", action="store_true", help="Print only status and summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog = load_json(args.catalog)
    contract = load_json(args.contract)
    ids = args.ids
    if ids and args.limit is not None:
        ids = ids[: args.limit]
    report = build_report(catalog, contract, ids)
    if args.limit is not None and not args.ids:
        report["packets"] = report["packets"][: args.limit]
        report["summary"]["selected_seed_count"] = len(report["packets"])
        if report["summary"]["error_count"] == 0:
            report["summary"]["emergence_validated_seed_count"] = len(report["packets"])
    if args.out:
        write_json(args.out, report)
    if args.summary:
        print(json.dumps({"status": report["status"], "summary": report["summary"]}, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
