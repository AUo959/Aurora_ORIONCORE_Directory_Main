from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
FORGE_DIR = REPO_ROOT / "GUMAS_SIM_2.5" / "FORGE__GUMAS_v3.0__2026-02-19"

for path in (str(SIM_DIR), str(FORGE_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from engine_advanced import GUMASAdvancedEngine  # noqa: E402
from l2_state import build_l2_registry, build_l2_state_bundle  # noqa: E402


@pytest.fixture(scope="module")
def runtime() -> tuple[GUMASAdvancedEngine, object]:
    engine = GUMASAdvancedEngine(seed=42)
    state = engine.init_scenario()
    return engine, state


@pytest.fixture(scope="module")
def registry(runtime: tuple[GUMASAdvancedEngine, object]):
    _, state = runtime
    return build_l2_registry(REPO_ROOT, state)


@pytest.fixture(scope="module")
def bundle(runtime: tuple[GUMASAdvancedEngine, object]):
    _, state = runtime
    return build_l2_state_bundle(REPO_ROOT, state)


def test_l2_manifest_source_files_exist() -> None:
    manifest = json.loads((FORGE_DIR / "l2_source_manifest.json").read_text(encoding="utf-8"))
    missing = [
        source["path"]
        for source in manifest.get("sources", [])
        if not (REPO_ROOT / str(source["path"])).exists()
    ]
    assert missing == []


def test_engine_initializes_additive_l2_state(runtime: tuple[GUMASAdvancedEngine, object]) -> None:
    engine, state = runtime
    v3_state = engine.get_v3_state()
    assert v3_state is not None
    assert v3_state.l2_state is not None
    assert set(state.factions) == set(v3_state.l2_state.indexes["by_faction_id"])


@pytest.mark.parametrize(
    ("query", "entity_kind"),
    [
        ("Zylox", "character"),
        ("Galactic Marshals", "organization"),
        ("Kaelor's Rift", "location"),
    ],
)
def test_registry_exposes_acceptance_entities(registry, query: str, entity_kind: str) -> None:
    assert registry.find_entities(query, entity_kind=entity_kind)


@pytest.mark.parametrize("query", ["Cross", "Vorn", "Roake", "Kade"])
def test_sim_capture_characters_exist_with_provenance(registry, query: str) -> None:
    matches = registry.find_entities(query, entity_kind="character")
    assert matches
    assert any(ref.source_id == "marshals_sim_capture" for match in matches for ref in match.source_refs)


@pytest.mark.parametrize(
    "query",
    ["Kaelor's Rift", "Vel-Surak", "Xyphos Prime ruins", "Xyphos Ruins"],
)
def test_alias_resolution_for_locations(registry, query: str) -> None:
    assert registry.find_entities(query, entity_kind="location")


def test_prime_construct_claims_remain_separate_and_flagged(registry, bundle) -> None:
    matches = registry.find_entities("Prime Construct")
    assert len(matches) >= 2
    assert any(match.conflict_flags for match in matches)
    assert bundle.unresolved_conflict_count >= 1


def test_l2_bundle_is_deterministic(runtime: tuple[GUMASAdvancedEngine, object]) -> None:
    _, state = runtime
    first = json.dumps(build_l2_state_bundle(REPO_ROOT, state).to_dict(), sort_keys=True)
    second = json.dumps(build_l2_state_bundle(REPO_ROOT, state).to_dict(), sort_keys=True)
    assert first == second


def test_all_factions_have_binding_buckets(runtime: tuple[GUMASAdvancedEngine, object], bundle) -> None:
    _, state = runtime
    by_faction_id = bundle.indexes["by_faction_id"]
    assert len(state.factions) == 13
    for faction_id in sorted(state.factions):
        assert faction_id in by_faction_id
        assert set(by_faction_id[faction_id]) == {"characters", "organizations", "locations", "mobile_assets", "logistics_nodes", "pressure_locations", "warnings"}


def test_export_contains_top_level_l2_state(tmp_path: Path) -> None:
    engine = GUMASAdvancedEngine(seed=42)
    engine.init_scenario()
    engine.run(3)
    output_path = tmp_path / "advanced_state.json"
    engine.export_advanced_state(str(output_path))
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert "latest_metrics" in payload
    assert "l2_state" in payload
    assert set(payload["l2_state"]["indexes"]["by_faction_id"]) == set(engine.get_state().factions)
    assert payload["l2_state"]["schema_version"] == "l2-state-bundle-v1"


def test_phase2_layers_are_present(bundle) -> None:
    assert bundle.mobile_assets
    assert bundle.logistics_nodes
    assert bundle.location_pressures
    assert bundle.operational_views


def test_mobile_assets_include_named_union_and_non_union_ships(bundle) -> None:
    asset_names = {asset["name"] for asset in bundle.mobile_assets.values()}
    assert "G.U.S. Judicator Prime" in asset_names
    assert "Nemesis Prime" in asset_names


def test_phase2_hotspots_include_logistics_and_pressure_locations(bundle) -> None:
    logistics_names = {node["name"] for node in bundle.logistics_nodes.values()}
    pressure_names = {pressure["name"] for pressure in bundle.location_pressures.values()}
    assert "Vel-Surak" in logistics_names
    assert "Rethos IV" in logistics_names
    assert "Xyphos Prime ruins" in pressure_names or "Hollow Expanse" in pressure_names


@pytest.mark.parametrize(
    "query",
    [
        "SRC-0001 (Primary excerpt)",
        "Marshal-Operative",
        "Sentinel-Class Power Suit",
        "Sentinel variants",
        "Marshal starship classes",
        "Sentinel-Class Tactical Carrier",
    ],
)
def test_ledger_noise_does_not_become_character_entities(registry, query: str) -> None:
    assert registry.find_entities(query, entity_kind="character") == []


@pytest.mark.parametrize("query", ["Commander Aric Thal", "Lior Serath", "Veyna Koris", "Kael Voss", "Darek Voss"])
def test_ledger_named_sentinels_survive_cleanup(registry, query: str) -> None:
    matches = registry.find_entities(query, entity_kind="character")
    assert matches
    assert any(ref.source_id == "marshals_ledger" for match in matches for ref in match.source_refs)


def test_registry_warnings_drop_excerpt_alias_noise(bundle) -> None:
    warnings = "\n".join(bundle.warnings)
    assert "Ambiguous alias 'excerpt'" not in warnings
    assert "Ambiguous alias 'primary excerpt'" not in warnings
