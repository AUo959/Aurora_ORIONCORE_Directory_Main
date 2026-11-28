#!/usr/bin/env python3
"""Generate runnable watch-scenario fixtures from the L2 scenario seed shortlist.

Implements ``catalog/contracts/l2_scenario_fixture_generator_contract_v1.json``:
every ``fixture_ready_shortlist`` entry in ``catalog/l2_scenario_seed_catalog.json``
becomes a root watch-scenario overlay under ``catalog/generated_watch_scenarios/``
that the existing L1 harness (``tools/hour_aboard.py``) can execute, plus a
manifest (``index.json``) and a root receipt.

Seeds stay pressure fields, not scripts: the overlay carries roles, pressure
axes, knobs, and expected end states as *observation categories*; it never
selects an ending. Generation is deterministic (no timestamps in fixtures), so
``--check`` can gate drift between the catalog and the committed fixtures.

Usage:
    python3 tools/l2_scenario_fixture_generator.py            # write fixtures + manifest + receipt
    python3 tools/l2_scenario_fixture_generator.py --check    # exit 1 if fixtures drift from catalog
    python3 tools/l2_scenario_fixture_generator.py --ids SCN-0903 SCN-0708
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import l2_scenario_seed_uptake as uptake  # noqa: E402

CATALOG_REF = "catalog/l2_scenario_seed_catalog.json"
GENERATOR_CONTRACT_REF = "catalog/contracts/l2_scenario_fixture_generator_contract_v1.json"
DEFAULT_CATALOG = ROOT / CATALOG_REF
DEFAULT_GENERATOR_CONTRACT = ROOT / GENERATOR_CONTRACT_REF
DEFAULT_OUT_DIR = ROOT / "catalog" / "generated_watch_scenarios"
DEFAULT_RECEIPT_DIR = ROOT / "reports" / "analysis"
MANIFEST_NAME = "index.json"

ALLOWED_OUTPUT_PREFIXES = ("catalog/", "reports/")
FIXTURE_SCHEMA_VERSION = "1.0.0"

# Proper-noun lore that must not leak into setting-neutral fixtures. "Dune" on
# its own is allowed: it is the lineage label of the SCN-010x lane
# ("Dune-derived"), not setting lore.
LORE_PATTERN = re.compile(
    r"\b(Arrakis|melange|Fremen|Bene Gesserit|Atreides|Harkonnen|Mentat|Sardaukar|"
    r"Kwisatz|Landsraad|CHOAM|Shai-Hulud|sandworm|Jedi|Sith|Starfleet|Klingon)\b",
    re.IGNORECASE,
)

# Station intelligences that acknowledge each hour over the mesh (optional;
# fixture runs default to --no-mesh). Same agents as the L1 watch scenarios.
COMPANION_AGENTS = (
    ("aurora", "Arbitrate the scenario-seed hour; acknowledge the ethics gate status."),
    ("archy", "Archive the scenario-seed run records; acknowledge intake."),
    ("oppy", "Cross-check pressure carriers against the station plot; report alignment."),
    ("liora", "Read the crew wellbeing pulse under scenario pressure; report morale signal."),
    ("starling_au", "Verify comms integrity for the scenario-seed run; confirm channels."),
    ("riverthread_808", "Weave the run into the continuity thread (anchor EOS_SEED_ORION); confirm."),
)

# Task order inside the five-step blueprint. Framing gates mapping and solver
# selection; the ethics gate follows solver selection; end-state branching
# needs the map, solver, and ethics gate. Structure only: actors, timing, and
# outcome selection remain open to the simulation.
TASK_DEPENDENCIES = {
    "T1": [],
    "T2": ["T1"],
    "T3": ["T1"],
    "T4": ["T3"],
    "T5": ["T2", "T3", "T4"],
}


class FixtureGenerationError(ValueError):
    """Raised when a shortlist entry cannot become a runnable fixture."""


def load_json(path: Path) -> dict[str, Any]:
    return uptake.load_json(path)


def _suffix(task_id: str) -> str:
    return task_id.rsplit("-", 1)[-1]


def build_tasks(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    ids = {_suffix(str(t["id"])): str(t["id"]) for t in blueprint["task_blueprint"]}
    for task in blueprint["task_blueprint"]:
        out = {
            "id": task["id"],
            "name": task["name"],
            "hours": float(task["hours"]),
            "tags": list(task["tags"]),
            "source": task["source"],
        }
        deps = [ids[d] for d in TASK_DEPENDENCIES.get(_suffix(str(task["id"])), []) if d in ids]
        if deps:
            out["depends_on"] = deps
        tasks.append(out)
    return tasks


def ord_risk(blueprint: dict[str, Any]) -> float:
    """Dispatch risk scales with the number of pressure axes (bounded)."""
    return round(min(0.25 + 0.1 * len(blueprint["pressure"]), 0.65), 2)


def related_references(catalog: dict[str, Any], card_id: str) -> list[dict[str, Any]]:
    """Fusion pairings and wiring links that name this card, with their status."""
    support = catalog.get("normalized_support_structures", {})
    refs: list[dict[str, Any]] = []
    for pairing in support.get("fusion_pairings", []):
        ids = [r.get("id") for r in pairing.get("normalized_refs", [])]
        if card_id in ids:
            refs.append(
                {
                    "kind": "fusion_pairing",
                    "ref_id": pairing.get("pairing_id"),
                    "status": pairing.get("status"),
                    "card_ids": ids,
                }
            )
    for link in support.get("wiring_links", []):
        ids = [r.get("id") for r in link.get("normalized_refs", [])]
        if card_id == link.get("source_card_id") or card_id in ids:
            refs.append(
                {
                    "kind": "wiring_link",
                    "ref_id": link.get("source_card_id"),
                    "status": link.get("status"),
                    "card_ids": ids,
                }
            )
    return refs


def unresolved_self_references(catalog: dict[str, Any], card_id: str) -> list[str]:
    """IDs this card's own wiring links point at that resolve to no card."""
    support = catalog.get("normalized_support_structures", {})
    missing: list[str] = []
    for link in support.get("wiring_links", []):
        if link.get("source_card_id") != card_id:
            continue
        for ref in link.get("normalized_refs", []):
            if ref.get("status") == "unresolved_id":
                missing.append(str(ref.get("id")))
    return missing


def emission_basis(entry: dict[str, Any]) -> str:
    blueprint = entry["fixture_blueprint"]
    if blueprint["fixture_status"] == "ready_candidate" and "runtime_fixture" in entry.get("value_lanes", []):
        return "ready_candidate_with_runtime_fixture_lane"
    return "contract_candidate_emitted_by_owner_direction_2026-11-28"


def build_fixture(entry: dict[str, Any], card: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    blueprint = entry["fixture_blueprint"]
    card_id = str(entry["id"])
    missing = unresolved_self_references(catalog, card_id)
    if missing:
        raise FixtureGenerationError(f"{card_id}: unresolved wiring reference(s) {', '.join(missing)}")
    fixture_id = str(blueprint["fixture_id"])
    l3 = dict(blueprint["l3_audit_blueprint"])
    provenance = uptake.lineage_provenance(card)
    fixture = {
        "name": fixture_id,
        "about": (
            f"L2 scenario seed {card_id} ({entry['handle']}) overlaid on an Orion Station watch. "
            f"{blueprint['scenario_prompt']} The seed is a pressure field and initial-condition "
            "template: roles, pressure axes, and knobs shape the run; expected end states are "
            "observation categories, never required endings. Root fixture only; not canon."
        ),
        "seed": int(blueprint["seed"]),
        "ticks": int(blueprint["ticks"]),
        "anchor_seed": blueprint["anchor_seed"],
        "ethics_protocol": blueprint["ethics_protocol"],
        "full_roster": True,
        "tasks": build_tasks(blueprint),
        "ord_mission": {
            "mission_id": f"{fixture_id}-ethics-gate",
            "tool_name": "preflight_reconnaissance",
            "risk_level": ord_risk(blueprint),
            "destination": f"station://scenario_seed/{card_id.lower()}",
        },
        "companions": [{"agent": a, "role_line": line} for a, line in COMPANION_AGENTS],
        "l3_audit": l3,
        "source_scenario_seed": {
            "card_id": card_id,
            "handle": entry["handle"],
            "catalog_ref": f"{CATALOG_REF}#/cards/{card_id}",
            "promotion_status": card.get("promotion_status", "root_catalog_only_not_canon_or_runtime"),
            "fixture_status": blueprint["fixture_status"],
            "emission_basis": emission_basis(entry),
            "score": entry.get("score"),
            "value_lanes": list(entry.get("value_lanes", [])),
            "lineage_provenance": provenance,
        },
        "scenario_seed_overlay": {
            "objective": blueprint["objective"],
            "opposition": blueprint["opposition"],
            "roles": list(blueprint["roles"]),
            "pressure": list(blueprint["pressure"]),
            "knobs": dict(blueprint["knobs"]),
            "ethical_hook": blueprint["ethical_hook"],
            "expected_end_state_categories": list(blueprint["expected_end_states"]),
            "end_state_handling": "observation categories for branch coverage; not required endings",
            "related_references": related_references(catalog, card_id),
        },
        "fixture_meta": {
            "schema_version": FIXTURE_SCHEMA_VERSION,
            "generator": "tools/l2_scenario_fixture_generator.py",
            "generator_contract": GENERATOR_CONTRACT_REF,
            "runner": "tools/l2_scenario_fixture_run.py",
            "harness": "tools/hour_aboard.py",
            "harness_scenario_arg": f"generated_watch_scenarios/{fixture_id}",
            "boundary": {
                "root_control_plane_only": True,
                "writes_nested_repos": False,
                "canonrec_promotion": "not_authorized",
                "cloudbank_runtime_mutation": "not_authorized",
            },
        },
    }
    lint_fixture(fixture)
    return fixture


def _lint_shape(fixture: dict[str, Any], name: str) -> None:
    shape = load_json(DEFAULT_GENERATOR_CONTRACT)["candidate_fixture_shape"]
    missing = [k for k in shape["required_top_level_keys"] if k not in fixture]
    if missing:
        raise FixtureGenerationError(f"{name}: missing top-level key(s) {missing}")
    for task in fixture["tasks"]:
        lacking = [k for k in shape["task_required_keys"] if k not in task]
        if lacking:
            raise FixtureGenerationError(f"{name}: task {task.get('id')} missing {lacking}")
        if not str(task["source"]).startswith(CATALOG_REF):
            raise FixtureGenerationError(f"{name}: task {task['id']} source must point at {CATALOG_REF}")
    lacking = [k for k in shape["source_scenario_seed_required_keys"] if k not in fixture["source_scenario_seed"]]
    if lacking:
        raise FixtureGenerationError(f"{name}: source_scenario_seed missing {lacking}")
    if len(fixture["tasks"]) < 4:
        raise FixtureGenerationError(f"{name}: fewer than four task assertions")


def _lint_emergence(fixture: dict[str, Any], name: str) -> None:
    overlay = fixture["scenario_seed_overlay"]
    if len(overlay["roles"]) < 4 or len(overlay["pressure"]) < 2 or len(overlay["knobs"]) < 5:
        raise FixtureGenerationError(f"{name}: below emergence minimums (roles/pressure/knobs)")
    if len(overlay["expected_end_state_categories"]) < 3:
        raise FixtureGenerationError(f"{name}: fewer than three end-state categories")
    prohibited = uptake.PROHIBITED_BLUEPRINT_KEYS.intersection(uptake.iter_keys(fixture))
    if prohibited:
        raise FixtureGenerationError(f"{name}: prohibited outcome key(s) {sorted(prohibited)}")


def lint_fixture(fixture: dict[str, Any]) -> None:
    """Fail closed on contract violations before a fixture is emitted."""
    name = str(fixture.get("name", "?"))
    _lint_shape(fixture, name)
    _lint_emergence(fixture, name)
    lore = sorted({m.group(0) for m in LORE_PATTERN.finditer(json.dumps(fixture))})
    if lore:
        raise FixtureGenerationError(f"{name}: setting-specific lore present {lore}")


def check_output_path(rel: str) -> None:
    if not rel.startswith(ALLOWED_OUTPUT_PREFIXES) or uptake.nested_path(rel) or ".." in Path(rel).parts:
        raise FixtureGenerationError(f"output path escapes root catalog/reports: {rel}")


def generate(catalog: dict[str, Any], ids: list[str] | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Return ({relative_path: fixture}, manifest)."""
    cards = uptake.card_index(catalog)
    entries = uptake.selected_entries(catalog, ids)
    fixtures: dict[str, dict[str, Any]] = {}
    rows = []
    for entry in sorted(entries, key=lambda e: (-(e.get("score") or 0), e["id"])):
        card = cards.get(entry["id"])
        if card is None:
            raise FixtureGenerationError(f"{entry['id']}: no maintained catalog card")
        rel = str(entry["fixture_blueprint"]["candidate_output_path"])
        check_output_path(rel)
        fixture = build_fixture(entry, card, catalog)
        fixtures[rel] = fixture
        rows.append(
            {
                "card_id": entry["id"],
                "handle": entry["handle"],
                "fixture_id": fixture["name"],
                "path": rel,
                "score": entry.get("score"),
                "fixture_status": entry["fixture_blueprint"]["fixture_status"],
                "emission_basis": fixture["source_scenario_seed"]["emission_basis"],
                "task_count": len(fixture["tasks"]),
                "dune_lane": entry["id"].startswith("SCN-010"),
            }
        )
    manifest = {
        "artifact_id": "l2_scenario_generated_watch_scenarios",
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "source_catalog": CATALOG_REF,
        "generator_contract": GENERATOR_CONTRACT_REF,
        "generator": "tools/l2_scenario_fixture_generator.py",
        "runner": "tools/l2_scenario_fixture_run.py",
        "status": "runnable_root_fixtures_not_canon",
        "fixture_count": len(rows),
        "fixtures": rows,
    }
    return fixtures, manifest


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render_receipt(manifest: dict[str, Any], date: str) -> str:
    lines = [
        f"# L2 Scenario Fixture Generation Receipt ({date})",
        "",
        f"- Source catalog: `{manifest['source_catalog']}`",
        f"- Generator contract: `{manifest['generator_contract']}`",
        f"- Generator: `{manifest['generator']}`; runner: `{manifest['runner']}`",
        f"- Fixtures emitted: {manifest['fixture_count']} under `catalog/generated_watch_scenarios/`",
        "- Unresolved references in emitted cards: none (generation fails closed on `unresolved_id`)",
        "- Promotion status: root fixtures only; not CanonRec canon, not CloudBank runtime mutation.",
        "",
        "| Card | Handle | Score | Status | Emission basis |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in manifest["fixtures"]:
        score = "" if row["score"] is None else row["score"]
        lines.append(
            f"| {row['card_id']} | {row['handle']} | {score} | {row['fixture_status']} | {row['emission_basis']} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    fixtures: dict[str, dict[str, Any]],
    manifest: dict[str, Any] | None,
    out_dir: Path,
    receipt_dir: Path | None,
    date: str,
) -> list[Path]:
    written = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, fixture in fixtures.items():
        path = out_dir / Path(rel).name
        text = _dump(fixture)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written.append(path)
    if manifest is None:  # partial (--ids) run: leave the full-shortlist manifest alone
        return written
    mpath = out_dir / MANIFEST_NAME
    text = _dump(manifest)
    if not mpath.exists() or mpath.read_text(encoding="utf-8") != text:
        mpath.write_text(text, encoding="utf-8")
        written.append(mpath)
    if receipt_dir is not None and written:
        receipt_dir.mkdir(parents=True, exist_ok=True)
        rpath = receipt_dir / f"l2_scenario_fixture_generation__{date}.md"
        rpath.write_text(render_receipt(manifest, date), encoding="utf-8")
        written.append(rpath)
    return written


def check_drift(fixtures: dict[str, dict[str, Any]], manifest: dict[str, Any], out_dir: Path) -> list[str]:
    drift = []
    expected = {Path(rel).name: _dump(f) for rel, f in fixtures.items()}
    expected[MANIFEST_NAME] = _dump(manifest)
    for name, text in expected.items():
        path = out_dir / name
        if not path.exists():
            drift.append(f"missing: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
        elif path.read_text(encoding="utf-8") != text:
            drift.append(f"stale: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    if out_dir.exists():
        for path in sorted(out_dir.glob("*.json")):
            if path.name not in expected:
                drift.append(f"orphan: {path.name}")
    return drift


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--ids", nargs="+", help="Shortlist card ids to emit (default: all 25)")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--no-receipt", action="store_true", help="skip the reports/analysis receipt")
    parser.add_argument("--check", action="store_true", help="exit 1 when committed fixtures drift from the catalog")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    catalog = load_json(Path(args.catalog))
    try:
        fixtures, manifest = generate(catalog, args.ids)
    except (FixtureGenerationError, ValueError) as exc:
        print(f"fixture generation failed: {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir)
    if args.check:
        if args.ids:
            print("--check compares the full shortlist; do not combine with --ids", file=sys.stderr)
            return 2
        drift = check_drift(fixtures, manifest, out_dir)
        if drift:
            print("generated watch scenarios drift from catalog:", *drift, sep="\n  ", file=sys.stderr)
            print("regenerate: python3 tools/l2_scenario_fixture_generator.py", file=sys.stderr)
            return 1
        print(f"✓ {manifest['fixture_count']} generated watch scenarios match the catalog")
        return 0
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    written = write_outputs(
        fixtures,
        None if args.ids else manifest,
        out_dir,
        None if args.no_receipt else DEFAULT_RECEIPT_DIR,
        date,
    )
    print(f"{manifest['fixture_count']} fixtures generated; {len(written)} file(s) written")
    for path in written:
        print(f"  - {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
