#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _workspace_common import REPORTS_ANALYSIS_DIR, ROOT, ensure_parent, now_iso_utc, write_json


BUNDLE_DIR = REPORTS_ANALYSIS_DIR / "recovered_root_text_batch__2026-03-20"
WAVE1_JSON = BUNDLE_DIR / "placement_wave_1__2026-03-20.json"
WAVE2_JSON = BUNDLE_DIR / "placement_wave_2__2026-03-21.json"
AGENT_PASS_JSON = BUNDLE_DIR / "agent_pass__2026-03-21.json"
RESIDUAL_SWEEP_JSON = BUNDLE_DIR / "residual_sweep__2026-03-21.json"
EXTRACTION_MANIFEST_JSON = BUNDLE_DIR / "extraction_manifest.json"
ESSENTIAL_MODULES_JSON = BUNDLE_DIR / "essential_recovered_modules_manifest__2026-03-21.json"

ROUTED_DIRS = [
    ROOT / "tools" / "prototypes" / "python" / "recovered",
    ROOT / "tools" / "prototypes" / "javascript" / "recovered",
    ROOT / "docs" / "draft_protocols" / "recovered",
    ROOT / "GUMAS_SIM_2.5" / "draft_logic" / "recovered",
    ROOT / "GUMAS_SIM_2.5" / "draft_worldbuilding" / "recovered",
    ROOT / "catalog" / "draft_manifests" / "recovered",
    ROOT / "reports" / "analysis" / "canon_support" / "recovered_root_sources__2026-03-21",
]

CSV_FIELDS = [
    "module_id",
    "destination",
    "exists",
    "lane",
    "category",
    "decision",
    "decision_source",
    "specialist",
    "workshop_track",
    "workshop_use",
    "routed_via",
    "manifest_scope",
    "root_originals_preserved",
    "source_files",
    "source_count",
    "duplicate_collapse",
    "extraction_transforms",
    "extraction_intermediates",
    "telemetry",
    "utility_score",
    "improvement_score",
    "maintenance_burden",
    "conflict_risk",
    "file_ext",
    "file_size_bytes",
    "preview",
    "inference_basis",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_text_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*") if path.is_file())


def relpath(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def first_nonempty_line(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            return line[:180]
    return ""


def lane_for_destination(destination: str) -> str:
    if destination.startswith("tools/prototypes/python/recovered/"):
        return "python_recovered_prototype"
    if destination.startswith("tools/prototypes/javascript/recovered/"):
        return "javascript_recovered_module"
    if destination.startswith("docs/draft_protocols/recovered/agents/"):
        return "agent_protocol"
    if destination.startswith("docs/draft_protocols/recovered/"):
        return "protocol_doc"
    if destination.startswith("GUMAS_SIM_2.5/draft_logic/recovered/"):
        return "simulation_logic"
    if destination.startswith("GUMAS_SIM_2.5/draft_worldbuilding/recovered/"):
        return "worldbuilding_registry"
    if destination.startswith("catalog/draft_manifests/recovered/agents/"):
        return "agent_manifest"
    if destination.startswith("catalog/draft_manifests/recovered/"):
        return "control_manifest"
    if destination.startswith("reports/analysis/canon_support/recovered_root_sources__2026-03-21/"):
        return "canon_support"
    return "other"


def infer_category(destination: str, lane: str, essential: dict[str, Any] | None) -> str:
    if essential:
        return str(essential.get("category", "unspecified"))
    lane_map = {
        "python_recovered_prototype": "python_prototype",
        "javascript_recovered_module": "javascript_module",
        "agent_protocol": "agent_protocol",
        "protocol_doc": "protocol_doc",
        "simulation_logic": "simulation_logic",
        "worldbuilding_registry": "worldbuilding_registry",
        "agent_manifest": "config_manifest",
        "control_manifest": "config_manifest",
        "canon_support": "canon_support",
    }
    return lane_map.get(lane, "unspecified")


def infer_specialist(destination: str, lane: str, category: str, essential: dict[str, Any] | None) -> str:
    if essential and essential.get("specialist"):
        return str(essential["specialist"])
    lowered = destination.lower()
    if "threadcore" in lowered or "vector_chain" in lowered or "constellation" in lowered:
        return "THREADCORE"
    if "quantum" in lowered or "qforge" in lowered:
        return "Quantum Forge"
    if "character" in lowered or "crew" in lowered or "faction" in lowered or "shuttlecraft" in lowered:
        return "CharacterForge / Worldbuilding"
    if lane in {"python_recovered_prototype", "javascript_recovered_module"}:
        return "Prototype Systems"
    if lane == "simulation_logic":
        return "Simulation Logic"
    if lane in {"protocol_doc", "agent_protocol"}:
        return "Aurora Core / Workshop Protocols"
    if lane in {"control_manifest", "agent_manifest"}:
        return "Manifest / Control Surfaces"
    if category == "canon_support":
        return "Canon Support"
    return "Unassigned"


def infer_workshop_track(destination: str, lane: str, category: str, specialist: str) -> str:
    lowered = destination.lower()
    if category in {"worldbuilding_registry", "canon_support"} or any(
        token in lowered for token in ("character", "crew", "faction", "shuttlecraft")
    ):
        return "characterforge_seed"
    if "quantum" in lowered or "qforge" in lowered:
        return "quantum_forge"
    if any(token in lowered for token in ("threadcore", "vector_chain", "constellation", "reflection_chamber")):
        return "threadcore_support"
    if lane in {"python_recovered_prototype", "javascript_recovered_module", "simulation_logic"}:
        return "simulation_workshop"
    if lane in {"protocol_doc", "agent_protocol", "control_manifest", "agent_manifest"}:
        return "aurora_workshop_ops"
    if "CharacterForge" in specialist:
        return "characterforge_seed"
    return "general_workshop"


def infer_workshop_use(track: str, lane: str) -> str:
    mapping = {
        "characterforge_seed": "Draft seed stock for CharacterForge capsules, crew dossiers, and non-convergent agent pools.",
        "quantum_forge": "Raw module material for Quantum Forge reconstruction, vector generation, and research packaging.",
        "threadcore_support": "THREADCORE and vector-chain support material for continuity, capsule control, and workshop orchestration.",
        "simulation_workshop": "Prototype logic for simulation workshop experiments, rule extraction, and deterministic system rebuilds.",
        "aurora_workshop_ops": "Aurora workshop protocol or manifest material for ingestion, deployment, module coordination, and agent scaffolding.",
        "general_workshop": "Recovered workshop material requiring case-by-case integration review.",
    }
    if track in mapping:
        return mapping[track]
    if lane == "canon_support":
        return "Recovered reference material for canon-support review and reconciliation evidence."
    return "Recovered workshop material requiring case-by-case integration review."


def manifest_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    wave1 = load_json(WAVE1_JSON)
    for item in wave1["placements"]:
        records.append(
            {
                "destination": item["destination"],
                "source_files": list(item["source_files"]),
                "routed_via": "placement_wave_1",
                "manifest_scope": wave1["scope"],
                "root_originals_preserved": bool(wave1["root_originals_preserved"]),
                "notes": item.get("notes", ""),
            }
        )

    wave2 = load_json(WAVE2_JSON)
    for group in wave2["groups"]:
        for item in group["items"]:
            records.append(
                {
                    "destination": item["destination"],
                    "source_files": list(item["source_files"]),
                    "routed_via": "placement_wave_2",
                    "manifest_scope": wave2["scope"],
                    "root_originals_preserved": bool(wave2["root_originals_preserved"]),
                    "notes": "",
                }
            )

    agent_pass = load_json(AGENT_PASS_JSON)
    for group in agent_pass["routed_groups"]:
        for item in group["items"]:
            records.append(
                {
                    "destination": item["destination"],
                    "source_files": list(item["source_files"]),
                    "routed_via": "agent_pass",
                    "manifest_scope": agent_pass["scope"],
                    "root_originals_preserved": True,
                    "notes": "",
                }
            )

    residual = load_json(RESIDUAL_SWEEP_JSON)
    for item in residual["newly_routed"]:
        records.append(
            {
                "destination": item["destination"],
                "source_files": [item["source_file"]],
                "routed_via": "residual_sweep",
                "manifest_scope": residual["scope"],
                "root_originals_preserved": bool(residual["root_originals_preserved"]),
                "notes": item.get("reason", ""),
            }
        )

    return records


def actual_routed_files() -> list[str]:
    paths: list[str] = []
    for directory in ROUTED_DIRS:
        for path in iter_text_files(directory):
            paths.append(relpath(path))
    return sorted(set(paths))


def extraction_maps() -> tuple[dict[str, str], dict[str, str]]:
    transform_map: dict[str, str] = {}
    intermediate_map: dict[str, str] = {}
    for item in load_json(EXTRACTION_MANIFEST_JSON):
        source_file = str(item["source_file"])
        transform_map[source_file] = str(item.get("transform", "identity"))
        intermediate_map[source_file] = str(item.get("extracted_to", ""))
    return transform_map, intermediate_map


def essential_map() -> dict[str, dict[str, Any]]:
    return {str(item["path"]): item for item in load_json(ESSENTIAL_MODULES_JSON)}


def build_catalog() -> dict[str, Any]:
    records = manifest_records()
    transform_map, intermediate_map = extraction_maps()
    essential_by_path = essential_map()

    items: list[dict[str, Any]] = []
    for record in records:
        destination = str(record["destination"])
        path = ROOT / destination
        essential = essential_by_path.get(destination)
        lane = lane_for_destination(destination)
        category = infer_category(destination, lane, essential)
        specialist = infer_specialist(destination, lane, category, essential)
        workshop_track = infer_workshop_track(destination, lane, category, specialist)

        transforms = sorted(
            {transform_map[source] for source in record["source_files"] if source in transform_map}
        )
        intermediates = sorted(
            {intermediate_map[source] for source in record["source_files"] if source in intermediate_map}
        )

        item = {
            "module_id": Path(destination).stem,
            "destination": destination,
            "exists": path.exists(),
            "lane": lane,
            "category": category,
            "decision": essential.get("decision", "routed_only") if essential else "routed_only",
            "decision_source": "essential_manifest" if essential else "route_manifest_only",
            "specialist": specialist,
            "workshop_track": workshop_track,
            "workshop_use": infer_workshop_use(workshop_track, lane),
            "routed_via": record["routed_via"],
            "manifest_scope": record["manifest_scope"],
            "root_originals_preserved": bool(record["root_originals_preserved"]),
            "source_files": list(record["source_files"]),
            "source_count": len(record["source_files"]),
            "duplicate_collapse": len(record["source_files"]) > 1,
            "extraction_transforms": transforms,
            "extraction_intermediates": intermediates,
            "telemetry": list(essential.get("telemetry", [])) if essential else [],
            "utility_score": essential.get("utility_score") if essential else None,
            "improvement_score": essential.get("improvement_score") if essential else None,
            "maintenance_burden": essential.get("maintenance_burden") if essential else None,
            "conflict_risk": essential.get("conflict_risk") if essential else None,
            "file_ext": path.suffix.lower(),
            "file_size_bytes": path.stat().st_size if path.exists() else None,
            "preview": first_nonempty_line(path) if path.exists() else "",
            "notes": str(record.get("notes", "")),
            "inference_basis": "decision and specialist from essential manifest where available; otherwise inferred from routed lane and file naming.",
        }
        items.append(item)

    items.sort(key=lambda item: (item["lane"], item["destination"]))

    actual_files = actual_routed_files()
    item_destinations = {item["destination"] for item in items}
    uncataloged_actual = sorted(path for path in actual_files if path not in item_destinations)
    missing_manifest_destinations = sorted(path for path in item_destinations if path not in actual_files)

    summary = {
        "generated_at": now_iso_utc(),
        "scope": "Detailed catalog of routed recovered modules across Waves 1, 2, residual sweep, and agent pass.",
        "root_originals_preserved": True,
        "cataloged_items": len(items),
        "actual_routed_files_discovered": len(actual_files),
        "decision_counts": dict(Counter(item["decision"] for item in items)),
        "lane_counts": dict(Counter(item["lane"] for item in items)),
        "workshop_track_counts": dict(Counter(item["workshop_track"] for item in items)),
        "uncataloged_actual_files": uncataloged_actual,
        "missing_manifest_destinations": missing_manifest_destinations,
    }
    return {"summary": summary, "items": items}


def write_csv(path: Path, items: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in items:
            row = dict(item)
            row["source_files"] = " | ".join(item["source_files"])
            row["extraction_transforms"] = " | ".join(item["extraction_transforms"])
            row["extraction_intermediates"] = " | ".join(item["extraction_intermediates"])
            row["telemetry"] = " | ".join(item["telemetry"])
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    items = payload["items"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[item["lane"]].append(item)

    lines = [
        "# Detailed Routed Recovered Module Catalog",
        "",
        f"Generated: {summary['generated_at']}",
        "Status: staged, derived, non-canon",
        "",
        "## Summary",
        "",
        f"- Cataloged routed items: `{summary['cataloged_items']}`",
        f"- Actual routed files discovered: `{summary['actual_routed_files_discovered']}`",
        f"- Uncataloged actual files: `{len(summary['uncataloged_actual_files'])}`",
        f"- Missing manifest destinations: `{len(summary['missing_manifest_destinations'])}`",
        "",
        "## Decision Counts",
        "",
    ]
    for key, value in sorted(summary["decision_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Lane Counts", ""])
    for key, value in sorted(summary["lane_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Workshop Track Counts", ""])
    for key, value in sorted(summary["workshop_track_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    if summary["uncataloged_actual_files"]:
        lines.extend(["", "## Uncataloged Actual Files", ""])
        for value in summary["uncataloged_actual_files"]:
            lines.append(f"- `{value}`")

    if summary["missing_manifest_destinations"]:
        lines.extend(["", "## Missing Manifest Destinations", ""])
        for value in summary["missing_manifest_destinations"]:
            lines.append(f"- `{value}`")

    for lane in sorted(grouped):
        lines.extend(["", f"## {lane}", ""])
        for item in grouped[lane]:
            lines.append(
                f"- `{item['module_id']}` -> `{item['decision']}` | `{item['workshop_track']}` | `{item['specialist']}`"
            )
            lines.append(f"  Destination: `{item['destination']}`")
            lines.append(f"  Source: `{', '.join(item['source_files'])}`")
            lines.append(f"  Routed via: `{item['routed_via']}`")
            lines.append(f"  Workshop use: {item['workshop_use']}")
            if item["notes"]:
                lines.append(f"  Notes: {item['notes']}")
            if item["preview"]:
                lines.append(f"  Preview: `{item['preview']}`")

    ensure_parent(path)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a detailed catalog of routed recovered modules."
    )
    parser.add_argument(
        "--date-tag",
        default=now_iso_utc()[:10],
        help="Date tag for output filenames (default: today in UTC YYYY-MM-DD).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_catalog()

    json_path = BUNDLE_DIR / f"detailed_routed_module_catalog__{args.date_tag}.json"
    csv_path = BUNDLE_DIR / f"detailed_routed_module_catalog__{args.date_tag}.csv"
    md_path = BUNDLE_DIR / f"DETAILED_ROUTED_MODULE_CATALOG__{args.date_tag}.md"

    write_json(json_path, payload)
    write_csv(csv_path, payload["items"])
    write_markdown(md_path, payload)

    print(json_path)
    print(csv_path)
    print(md_path)
    print(f"cataloged_items={payload['summary']['cataloged_items']}")
    print(f"uncataloged_actual_files={len(payload['summary']['uncataloged_actual_files'])}")
    print(f"missing_manifest_destinations={len(payload['summary']['missing_manifest_destinations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
