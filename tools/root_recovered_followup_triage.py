#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from _workspace_common import REPORTS_ANALYSIS_DIR, ROOT, ensure_parent, now_iso_utc, write_json


BUNDLE_DIR = REPORTS_ANALYSIS_DIR / "recovered_root_text_batch__2026-03-20"
CANON_SUPPORT_DIR = REPORTS_ANALYSIS_DIR / "canon_support" / "l1_promoted_character_packets__2026-03-20"
PROMOTION_PACKET_DIR = CANON_SUPPORT_DIR / "packets"
TRIAGE_JSON = BUNDLE_DIR / "importance_triage__2026-03-20.json"
TRIAGE_CSV = BUNDLE_DIR / "importance_triage__2026-03-20.csv"
TRIAGE_MD = BUNDLE_DIR / "DEEP_IMPORTANCE_TRIAGE__2026-03-20.md"
TRIAGE_QUEUE_MD = BUNDLE_DIR / "DEEP_TRIAGE_QUEUE__2026-03-20.md"
PROMOTION_MANIFEST_JSON = CANON_SUPPORT_DIR / "promotion_manifest.json"
PROMOTION_README_MD = CANON_SUPPORT_DIR / "README.md"

L1_LEDGER_JSON = REPORTS_ANALYSIS_DIR / "L1_ENTITY_LEDGER__2026-03-08.json"
PROMOTION_AUDIT_MD = BUNDLE_DIR / "corpus" / "CHARACTER_PROMOTION_AUDIT__2026-03-20.md"
ARTIFACT_INDEX_CSV = BUNDLE_DIR / "artifact_index.csv"

PROMOTED_L1 = [
    {
        "entity_id": "ORION.ENTITY.0028",
        "name": "Lt. Nakamura",
        "slug": "lt_nakamura",
        "evidence": [
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/ORION_STATION_CREW_MANIFEST.md",
                "note": "Names Nakamura as commander of Guardian Sentinel with threat-assessment and perimeter-patrol specialization.",
            },
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/orion_station_full_technical_readout.md",
                "note": "Preserves Guardian Sentinel as the active perimeter-security vessel with 18 crew.",
            },
            {
                "path": "reports/analysis/ORION_COMMAND_WATCH_SECURITY_MATRIX__2026-03-09.md",
                "note": "Routes perimeter response through Lt. Nakamura in station security command.",
            },
        ],
    },
    {
        "entity_id": "ORION.ENTITY.0015",
        "name": "Lt. Hassan",
        "slug": "lt_hassan",
        "evidence": [
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/ORION_STATION_CREW_MANIFEST.md",
                "note": "Names Hassan as commander of Logistics Alpha and preserves cargo and stasis-pod responsibilities.",
            },
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/orion_station_full_technical_readout.md",
                "note": "Preserves Logistics Alpha class, capacity, and active loading state.",
            },
            {
                "path": "reports/analysis/ORION_COMMAND_WATCH_SECURITY_MATRIX__2026-03-09.md",
                "note": "Keeps Lt. Hassan in the named support-command surface.",
            },
        ],
    },
    {
        "entity_id": "ORION.ENTITY.0007",
        "name": "Chief Thomson",
        "slug": "chief_thomson",
        "evidence": [
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/ORION_STATION_CREW_MANIFEST.md",
                "note": "Names Thomson as commander of Repair Tender Beta with engineering-support and emergency-response scope.",
            },
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/orion_station_full_technical_readout.md",
                "note": "Preserves Repair Tender Beta crew count, equipment, and docked-rotation status.",
            },
            {
                "path": "reports/analysis/ORION_COMMAND_WATCH_SECURITY_MATRIX__2026-03-09.md",
                "note": "Keeps Chief Thomson in the named support-command surface.",
            },
        ],
    },
    {
        "entity_id": "ORION.ENTITY.0036",
        "name": "Samantha Gray",
        "slug": "samantha_gray",
        "evidence": [
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/ORION_STATION_CREW_MANIFEST.md",
                "note": "Names Gray as Lacewing senior pilot with atmospheric and training-flight specialization.",
            },
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/orion_station_full_technical_readout.md",
                "note": "Preserves Lacewing as the training and diplomatic shuttle with active training operations.",
            },
            {
                "path": "reports/analysis/non_can_reports/AURORA_QUANTUM_FORGE_DEEP_DIVE.md",
                "note": "Places Gray under Flight Control pilots, reinforcing the pilot-role placement.",
            },
        ],
    },
    {
        "entity_id": "ORION.ENTITY.0034",
        "name": "Ren Takahashi",
        "slug": "ren_takahashi",
        "evidence": [
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/ORION_STATION_CREW_MANIFEST.md",
                "note": "Names Takahashi as Lacewing psycho-acoustic engineer with cultural-contact calibration duties.",
            },
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/orion_station_full_technical_readout.md",
                "note": "Preserves the Lacewing mission context used by the engineering profile.",
            },
            {
                "path": "reports/analysis/non_can_reports/AURORA_QUANTUM_FORGE_DEEP_DIVE.md",
                "note": "Places Takahashi under systems specialists, reinforcing the specialty assignment.",
            },
        ],
    },
    {
        "entity_id": "ORION.ENTITY.0004",
        "name": "Cadet Mira Chen",
        "slug": "cadet_mira_chen",
        "evidence": [
            {
                "path": "reports/analysis/ORION_COMMAND_WATCH_SECURITY_MATRIX__2026-03-09.md",
                "note": "Preserves Mira Chen as a named L1 training and support character.",
            },
            {
                "path": "projects/Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/orion_station_full_technical_readout.md",
                "note": "Documents Training-EVA-03 as a Lacewing cadet-certification mission; this supports the training-track bio even though the specific Mira-Chen link remains inferential.",
            },
        ],
    },
]

TRIAGE_FIELDS = [
    "source_file",
    "triage_score",
    "triage_tier",
    "importance_band",
    "triage_reason",
    "suggested_destination",
    "category",
    "usefulness",
    "action",
    "future_bucket",
    "theme_tags",
    "exact_duplicate_group",
    "normalized_duplicate_group",
    "extracted_to",
    "first_line",
]

MANUAL_TRIAGE_OVERRIDES: dict[str, tuple[str, str, str, str]] = {
    "text_symbiosis_graft.txt": (
        "P1",
        "critical_salvage",
        "Executable patch-graft script with concrete file mutations and anchor binding; preserve as a recovered prototype and do not run unreviewed.",
        "tools/prototypes/python",
    ),
    "text_Au_Shuttlecraft.txt": (
        "P2",
        "canon_followup",
        "Structured shuttlecraft registry with named agents, manifests, and thread bindings; treat as worldbuilding or protocol follow-up, not prompt residue.",
        "GUMAS_SIM_2.5/draft_worldbuilding or docs/draft_protocols",
    ),
    "text_recovery_README.txt": (
        "P3",
        "ops_recovery",
        "ZIPWIZ recovery protocol surface with fallback and restoration procedures worth preserving as ops documentation.",
        "docs/draft_protocols or archives/ops_recovery",
    ),
    "text_47.txt": (
        "P3",
        "ops_recovery",
        "Structured SIGMA ingestion controller capsule misclassified as a fragment; preserve with draft manifests.",
        "catalog/draft_manifests",
    ),
    "text_oppy_integration.txt": (
        "P3",
        "ops_recovery",
        "Manual symbolic integration guide for Oppy memory architecture; preserve as protocol documentation.",
        "docs/draft_protocols",
    ),
    "text_stellar_sync_patch.txt": (
        "P3",
        "ops_recovery",
        "Patch manifest with explicit system-change summary and reliquary path; preserve as a draft manifest.",
        "catalog/draft_manifests",
    ),
    "text_Orion_deploy_prototype.txt": (
        "P3",
        "ops_recovery",
        "Structured deploy prototype snapshot with system-state fields worth preserving alongside ops manifests.",
        "catalog/draft_manifests",
    ),
    "text_GitDeploy_Prototype.txt": (
        "P3",
        "ops_recovery",
        "Narrative deploy snapshot that still records concrete module, security, and panel state worth preserving as ops history.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_relay_deploy_prototype.txt": (
        "P3",
        "ops_recovery",
        "Finalized export-package snapshot with included modules and deployment targets; preserve with deploy manifests.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_Orion_Crew.txt": (
        "P2",
        "canon_followup",
        "Recovered L1 crew registry already proved useful for character reconciliation and should remain elevated for canon follow-up.",
        "reports/analysis/canon_support or L1 recovery corpus",
    ),
    "text_42.txt": (
        "P2",
        "canon_followup",
        "Symbiosis module graft capsule bundles named ecosystem modules and continuity bindings; treat as worldbuilding and continuity follow-up.",
        "GUMAS_SIM_2.5/draft_worldbuilding or docs/draft_protocols",
    ),
    "text_GitChain.txt": (
        "P3",
        "ops_recovery",
        "Vector-chain seed manifest with deployment, security, and continuity fields; preserve as a draft deploy manifest.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_GitBridge.txt": (
        "P3",
        "ops_recovery",
        "THREADCORE output block linking governance capsule, restore script, and system map; preserve as a continuity manifest.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_46.txt": (
        "P3",
        "ops_recovery",
        "Structured ingestion-pipeline capsule v1.1 complements the recovered ingestion blueprint and should be preserved as a manifest companion.",
        "catalog/draft_manifests or docs/draft_protocols",
    ),
    "text_45.txt": (
        "P3",
        "ops_recovery",
        "THREADCORE orientation block with active command, drift, and seal state; preserve as continuity metadata.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_Loom.txt": (
        "P3",
        "ops_recovery",
        "THREADCORE output block with command sequence, driftlog, and inventory state; preserve as continuity output history.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_GitBridge_Capsule.txt": (
        "P3",
        "ops_recovery",
        "Constellation registration capsule with repository and artifact index; preserve as a draft manifest.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_103.txt": (
        "P3",
        "ops_recovery",
        "Injectable patch capsule template defines a transferable context-update format worth preserving as protocol scaffolding.",
        "docs/draft_protocols or catalog/draft_manifests",
    ),
    "text_vector_chain_transfer.txt": (
        "P3",
        "ops_recovery",
        "Vector-chain context-transfer capsule records deploy, recovery, and continuity state; preserve as an ops manifest.",
        "catalog/draft_manifests or ops archive",
    ),
    "text_deploy_a1.txt": (
        "P3",
        "ops_recovery",
        "Constellation deploy capsule enumerates included modules and beacon configuration; preserve as a deploy manifest.",
        "catalog/draft_manifests or ops archive",
    ),
}


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "artifact"


def format_primary_additional(data: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for key, value in data.items():
        lines.append(f"- {key}: {value}")
    return lines


def load_l1_entities() -> dict[str, dict[str, Any]]:
    data = json.loads(L1_LEDGER_JSON.read_text(encoding="utf-8"))
    return {row["entity_id"]: row for row in data["humans"]}


def build_character_packets(generated_at: str) -> list[dict[str, Any]]:
    ledger = load_l1_entities()
    packets: list[dict[str, Any]] = []

    for item in PROMOTED_L1:
        entity = ledger[item["entity_id"]]
        packet_name = f"{entity['entity_id']}__{item['slug']}__promotion_packet__2026-03-20.md"
        packet_path = PROMOTION_PACKET_DIR / packet_name
        support_relpath = packet_path.relative_to(ROOT).as_posix()
        sources = [entry["path"] for entry in item["evidence"]]
        lines = [
            f"# {entity['name']} Promotion Support Packet",
            "",
            f"Generated: `{generated_at}`",
            "",
            "## Canon State",
            "",
            f"- Entity ID: `{entity['entity_id']}`",
            f"- Name: `{entity['name']}`",
            f"- Role: `{entity['role']}`",
            f"- Division: `{entity['division']}`",
            f"- Status: `{entity['status']}`",
            f"- Certainty: `{entity['certainty']}`",
            f"- Registry authority: `{entity['registry_authority']}`",
            "",
            "## Canon Destinations",
            "",
            "- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.json`",
            "- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md`",
            "- `reports/analysis/recovered_root_text_batch__2026-03-20/corpus/CHARACTER_PROMOTION_AUDIT__2026-03-20.md`",
            "",
            "## Routed Support Artifact",
            "",
            f"- Permanent support packet: `{support_relpath}`",
            "",
            "## Summary",
            "",
            f"- Primary summary: {entity['primary_summary']}",
            f"- Related assets: {', '.join(entity.get('related_assets', [])) or 'None recorded'}",
            "",
            "## Promotion Addenda",
            "",
        ]
        lines.extend(format_primary_additional(entity.get("primary_additional", {})))
        lines.extend(
            [
                "",
                "## Evidence Sources",
                "",
            ]
        )
        for source in item["evidence"]:
            lines.append(f"- `{source['path']}`: {source['note']}")

        legacy = entity.get("legacy_drift") or {}
        if legacy:
            lines.extend(
                [
                    "",
                    "## Legacy Drift",
                    "",
                    f"- Certainty trace: `{legacy.get('certainty', '')}`",
                    f"- Name variants: {', '.join(legacy.get('name_variants', [])) or 'None recorded'}",
                    f"- Older roles: {', '.join(legacy.get('roles', [])) or 'None recorded'}",
                    f"- Provenance sources: {', '.join(legacy.get('sources', [])) or 'None recorded'}",
                    f"- Notes: {', '.join(legacy.get('notes', [])) or 'None recorded'}",
                ]
            )

        packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        packets.append(
            {
                "entity_id": entity["entity_id"],
                "name": entity["name"],
                "role": entity["role"],
                "division": entity["division"],
                "support_packet": support_relpath,
                "ledger_json": "reports/analysis/L1_ENTITY_LEDGER__2026-03-08.json",
                "ledger_markdown": "reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md",
                "promotion_audit": PROMOTION_AUDIT_MD.relative_to(ROOT).as_posix(),
                "source_artifacts": sources,
                "related_assets": entity.get("related_assets", []),
            }
        )

    readme_lines = [
        "# L1 Promoted Character Packets",
        "",
        f"Generated: `{generated_at}`",
        "",
        "This directory holds permanent canon-support packets for the six L1 characters",
        "promoted from recovered support-crew material on 2026-03-20.",
        "",
        "## Purpose",
        "",
        "- Preserve promotion evidence in one stable analysis lane.",
        "- Keep the canonical destination explicit: the L1 entity ledger remains the source of truth.",
        "- Avoid moving or renaming the original recovered root artifacts until the broader naming pass is complete.",
        "",
        "## Included Packets",
        "",
    ]
    for packet in packets:
        readme_lines.append(f"- `{packet['support_packet']}`")
    readme_lines.extend(
        [
            "",
            "## Canon Destinations",
            "",
            "- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.json`",
            "- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md`",
            "",
            "## Companion Evidence",
            "",
            "- `reports/analysis/recovered_root_text_batch__2026-03-20/corpus/CHARACTER_PROMOTION_AUDIT__2026-03-20.md`",
        ]
    )
    PROMOTION_README_MD.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    write_json(
        PROMOTION_MANIFEST_JSON,
        {
            "generated_at": generated_at,
            "packet_count": len(packets),
            "packets": packets,
        },
    )
    return packets


def load_artifact_rows() -> list[dict[str, Any]]:
    with ARTIFACT_INDEX_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_source_text(name: str) -> str:
    path = ROOT / name
    return path.read_text(encoding="utf-8", errors="replace")


def has_theme(row: dict[str, Any], theme: str) -> bool:
    tags = [tag.strip() for tag in str(row.get("theme_tags", "")).split(",") if tag.strip()]
    return theme in tags


def control_surface_risk(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "command_tokens",
        "authority_invocation",
        "unauthorized command token",
        "activation_mode",
        "resetcore",
        "threadwake",
        "commandauth",
        "overwrite authorization",
        "invoke core authority",
    )
    return any(marker in lowered for marker in markers)


def triage_score(row: dict[str, Any], text: str) -> int:
    usefulness = {"high": 60, "review": 45, "medium": 30, "low": 10}
    actions = {
        "extract_and_route": 20,
        "quarantine_and_review": 25,
        "review_for_naming": 10,
        "dedupe_then_review": 5,
        "archive_or_discard": 0,
    }
    categories = {
        "python_prototype": 18,
        "javascript_module": 18,
        "worldbuilding_registry": 17,
        "simulation_logic": 16,
        "blueprint_or_protocol": 16,
        "config_manifest": 12,
        "research_brief": 8,
        "prompt_template_or_agent": 7,
        "sensitive_or_auth": 12,
        "conversation_or_chat_export": -4,
        "fragment_or_note": -10,
    }
    score = usefulness[row["usefulness"]] + actions[row["action"]] + categories[row["category"]]
    if row["exact_duplicate_group"] or row["normalized_duplicate_group"]:
        score -= 8
    if has_theme(row, "security_sensitive"):
        score += 10
    if has_theme(row, "threadcore_continuity"):
        score += 6
    if has_theme(row, "memory_system"):
        score += 6
    if has_theme(row, "gumas_worldbuilding"):
        score += 5
    if has_theme(row, "aurora_interface"):
        score += 4
    if control_surface_risk(text):
        score += 12
    score += min(
        10,
        int(row["python_score"])
        + int(row["javascript_score"])
        + int(row["config_score"]) // 3
        + int(row["formula_score"]) // 2,
    )
    return score


def classify_tier(row: dict[str, Any], text: str) -> tuple[str, str, str, str]:
    manual = MANUAL_TRIAGE_OVERRIDES.get(row["source_file"])
    if manual:
        return manual
    if row["category"] == "sensitive_or_auth":
        return (
            "P0",
            "critical_risk",
            "High-risk auth or key-like material requiring quarantine before reuse.",
            "_entropy_quarantine",
        )
    if control_surface_risk(text) and row["category"] in {"config_manifest", "javascript_module"}:
        return (
            "P0",
            "critical_risk",
            "Control-surface artifact with command or authority markers; review before any routing.",
            "_entropy_quarantine or catalog/draft_manifests",
        )
    if row["category"] in {"python_prototype", "javascript_module", "blueprint_or_protocol"} and row["usefulness"] == "high":
        return (
            "P1",
            "critical_salvage",
            "Directly reusable code or protocol surface with strong salvage value.",
            row["future_bucket"],
        )
    if row["category"] in {"worldbuilding_registry", "simulation_logic"} and row["usefulness"] == "high":
        return (
            "P2",
            "canon_followup",
            "High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.",
            row["future_bucket"],
        )
    if row["category"] == "config_manifest" and row["usefulness"] == "high":
        return (
            "P3",
            "ops_recovery",
            "Structured manifest or config fragment worth preserving, but not ahead of code and canon material.",
            row["future_bucket"],
        )
    if row["usefulness"] in {"medium", "review"}:
        return (
            "P4",
            "context_archive",
            "Context-rich prompt, research, or transcript material to archive after naming review.",
            row["future_bucket"],
        )
    return (
        "P5",
        "low_residue",
        "Low-signal fragment or residue; archive, dedupe, or discard after spot checks.",
        row["future_bucket"],
    )


def triage_rows() -> list[dict[str, Any]]:
    rows = load_artifact_rows()
    triaged: list[dict[str, Any]] = []
    for row in rows:
        text = load_source_text(row["source_file"])
        score = triage_score(row, text)
        tier, band, reason, destination = classify_tier(row, text)
        triaged_row = dict(row)
        triaged_row["triage_score"] = score
        triaged_row["triage_tier"] = tier
        triaged_row["importance_band"] = band
        triaged_row["triage_reason"] = reason
        triaged_row["suggested_destination"] = destination
        triaged.append(triaged_row)
    triaged.sort(key=lambda item: (-int(item["triage_score"]), item["source_file"]))
    return triaged


def write_triage_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAGE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TRIAGE_FIELDS})


def render_triage_report(generated_at: str, rows: list[dict[str, Any]]) -> str:
    tier_counts = Counter(row["triage_tier"] for row in rows)
    action_counts = Counter(row["action"] for row in rows)
    lines = [
        "# Deep Importance Triage",
        "",
        f"Generated: `{generated_at}`",
        "",
        "This pass revisits the recovered root text batch with a deeper importance model.",
        "It separates high-value salvage from high-risk control surfaces so that the next",
        "naming pass does not confuse importance with safety.",
        "",
        "## Summary",
        "",
        f"- Artifacts reviewed: `{len(rows)}`",
        f"- P0 critical-risk hold: `{tier_counts['P0']}`",
        f"- P1 critical salvage: `{tier_counts['P1']}`",
        f"- P2 canon and logic follow-up: `{tier_counts['P2']}`",
        f"- P3 ops and config recovery: `{tier_counts['P3']}`",
        f"- P4 context archive: `{tier_counts['P4']}`",
        f"- P5 low residue: `{tier_counts['P5']}`",
        "",
        "## Notes",
        "",
        "- P0 means important because it can affect control surfaces, invocation paths, or auth-like behavior.",
        "- P1 means important because the artifact is directly reusable code or a protocol surface worth preserving quickly.",
        "- P2 means important because it should feed canon or mechanics reconciliation, even if it is not executable code.",
        "",
        "## P0 Critical-Risk Hold",
        "",
    ]
    for row in [item for item in rows if item["triage_tier"] == "P0"][:15]:
        lines.append(
            f"- `{row['source_file']}` -> `{row['category']}` "
            f"[score `{row['triage_score']}`; destination `{row['suggested_destination']}`] {row['triage_reason']}"
        )

    lines.extend(["", "## P1 Critical Salvage", ""])
    for row in [item for item in rows if item["triage_tier"] == "P1"][:20]:
        lines.append(
            f"- `{row['source_file']}` -> `{row['category']}` "
            f"[score `{row['triage_score']}`; destination `{row['suggested_destination']}`] "
            f"first line: `{row['first_line']}`"
        )

    lines.extend(["", "## P2 Canon And Logic Follow-Up", ""])
    for row in [item for item in rows if item["triage_tier"] == "P2"][:20]:
        lines.append(
            f"- `{row['source_file']}` -> `{row['category']}` "
            f"[score `{row['triage_score']}`; destination `{row['suggested_destination']}`] "
            f"themes: `{row['theme_tags']}`"
        )

    lines.extend(["", "## P3 Ops And Config Recovery", ""])
    for row in [item for item in rows if item["triage_tier"] == "P3"][:15]:
        lines.append(
            f"- `{row['source_file']}` [score `{row['triage_score']}`] destination `{row['suggested_destination']}`"
        )

    lines.extend(["", "## P4 And P5 Snapshot", ""])
    lines.append(f"- Review-for-naming or archive-context artifacts: `{tier_counts['P4']}`")
    lines.append(f"- Low-signal residue artifacts: `{tier_counts['P5']}`")
    lines.append(f"- Original first-pass actions still map to: `{dict(sorted(action_counts.items()))}`")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append("- `importance_triage__2026-03-20.json`")
    lines.append("- `importance_triage__2026-03-20.csv`")
    lines.append("- `DEEP_TRIAGE_QUEUE__2026-03-20.md`")
    return "\n".join(lines) + "\n"


def render_triage_queue(rows: list[dict[str, Any]]) -> str:
    queue_sections = [
        (
            "Immediate Hold",
            "P0",
            "Do not route these into operational folders until someone reviews the control-surface or auth implications.",
        ),
        (
            "Immediate Salvage",
            "P1",
            "These are the strongest code or protocol recoveries to name and place next.",
        ),
        (
            "Canon And Logic Follow-Up",
            "P2",
            "These should feed worldbuilding, mechanics, or reconciliation passes soon after the immediate salvage set.",
        ),
        (
            "Ops Recovery",
            "P3",
            "These are structured manifests worth preserving after the first two tiers.",
        ),
    ]
    lines = [
        "# Deep Triage Queue",
        "",
        "This queue is the second-pass importance sort for the recovered root text batch.",
        "It is intended to drive the next naming and routing work.",
        "",
    ]
    for title, tier, description in queue_sections:
        lines.append(f"## {title}")
        lines.append("")
        lines.append(description)
        lines.append("")
        for row in [item for item in rows if item["triage_tier"] == tier][:20]:
            lines.append(
                f"- `{row['source_file']}` -> `{row['suggested_destination']}` "
                f"[{row['category']}; score `{row['triage_score']}`] {row['triage_reason']}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate follow-up canon packets and deep triage for recovered root text artifacts.")
    _ = parser.parse_args()

    generated_at = now_iso_utc()
    PROMOTION_PACKET_DIR.mkdir(parents=True, exist_ok=True)

    build_character_packets(generated_at)
    triaged_rows = triage_rows()

    write_json(
        TRIAGE_JSON,
        {
            "generated_at": generated_at,
            "artifact_count": len(triaged_rows),
            "rows": triaged_rows,
        },
    )
    write_triage_csv(TRIAGE_CSV, triaged_rows)
    TRIAGE_MD.write_text(render_triage_report(generated_at, triaged_rows), encoding="utf-8")
    TRIAGE_QUEUE_MD.write_text(render_triage_queue(triaged_rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
